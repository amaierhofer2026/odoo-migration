"""Datenmigration E-Mail-Marketing Odoo 11 -> Odoo 18 (ohne Personenbezug).

Auftrag Session 138: Mailings, Mailinglisten (reine Listenstruktur), Kampagnen,
Kampagnenstufen, Tags, Betreff, Inhalt, Status, historische Versanddaten und
aggregierte Kennzahlen uebernehmen. NICHT uebernommen werden Kontakte, Personen,
Partner, E-Mail-Adressen, Listenmitglieder, Empfaenger, mailing.trace-Zeilen,
Blacklist-/Opt-out-Adressen und Event-Teilnehmer.

Sicherungen gegen erneuten Versand:
  * Warteschlangen- und Mailing-Crons werden fuer die Dauer des Laufs deaktiviert
    und danach auf ihren vorherigen Zustand zurueckgesetzt.
  * Uebernommene Mailings erhalten niemals state in_queue/sending und kein
    schedule_date (das Odoo-11-Datum steht nur in x_o11_schedule_date).
  * Das Modul itk_mass_mailing_compat sperrt action_send_mail, action_launch,
    action_put_in_queue, action_schedule und action_set_sending fuer historische
    Mailings (x_o11_id gesetzt).
  * Nach dem Lauf wird geprueft, dass keine neue mail.mail-Zeile und keine
    mailing.trace-Zeile entstanden ist.

Odoo 11 wird ausschliesslich gelesen.

Aufruf:
    python scripts/marketing_migration.py --instanz lokal                 # Trockenlauf
    python scripts/marketing_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

DE = {"lang": "de_DE"}
BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "marketing_migration")
CSV_PFAD = os.path.join(BASIS, "docs", "o11-o18-email-marketing-nachverknuepfung-%s.csv")

# Odoo-11-Modell -> Odoo-18-Modell (umbenannte Modelle)
MODELL_MAP = {
    "account.invoice": "account.move",
    "mail.mass_mailing.list": "mailing.list",
    "mail.mass_mailing.contact": "mailing.contact",
}
# Odoo-11 reply_to_mode -> Odoo 18
REPLY_MAP = {"email": "new", "thread": "update"}
# Odoo-11-State -> Odoo 18 (nur diese beiden Werte kommen in Odoo 11 vor)
STATE_MAP = {"draft": "draft", "done": "done"}


class Lauf:
    def __init__(self, instanz: str, schreiben: bool):
        self.instanz = instanz
        self.schreiben = schreiben
        self.k11 = o11()
        self.k18 = o18(instanz)
        self.zahlen = collections.OrderedDict()
        self.offen = []
        self.hinweise = []
        self.nach = []

    # ---------------------------------------------------------------- lesen 11
    def lese(self):
        k = self.k11
        ctx = {"lang": "de_DE", "active_test": False}
        self.stages11 = k.kw("mail.mass_mailing.stage", "search_read",
                             [[], ["id", "name", "sequence"]], context=ctx, order="sequence")
        self.tags11 = k.kw("mail.mass_mailing.tag", "search_read",
                           [[], ["id", "name", "color"]], context=ctx)
        self.camps11 = k.kw("mail.mass_mailing.campaign", "search_read",
                            [[], ["id", "name", "user_id", "stage_id", "tag_ids",
                                  "total_mailings", "sent", "delivered", "opened", "replied",
                                  "bounced", "received_ratio", "opened_ratio", "replied_ratio",
                                  "clicks_ratio", "sent_date", "unique_ab_testing"]],
                            context=ctx, order="id")
        self.listen11 = k.kw("mail.mass_mailing.list", "search_read",
                             [[], ["id", "name", "active"]], context=ctx, order="id")
        self.mails11 = k.kw("mail.mass_mailing", "search_read",
                            [[], ["id", "name", "body_html", "email_from",
                                  "reply_to", "reply_to_mode", "state", "sent_date",
                                  "schedule_date", "mailing_model_name", "mailing_domain",
                                  "contact_list_ids", "mass_mailing_campaign_id", "active",
                                  "keep_archives", "color", "sent", "delivered", "opened",
                                  "replied", "bounced", "failed", "total", "contact_ab_pc",
                                  "source_id"]], context=ctx, order="id")

    # --------------------------------------------------------- Sicherheitsnetz
    def crons_aus(self):
        self.cron_zustand = []
        for c in self.k18.kw("ir.cron", "search_read",
                             [[("name", "ilike", "Mail")], ["name", "active", "model_id"]],
                             context={"active_test": False}):
            modell = (c["model_id"] or ["-", "-"])[1]
            if "mail" in c["name"].lower() or "Mailing" in modell or modell == "Postausgang":
                self.cron_zustand.append((c["id"], c["name"], c["active"]))
        print("=== Crons fuer die Dauer des Laufs deaktiviert ===")
        for cid, name, aktiv in self.cron_zustand:
            print("  %-46s war aktiv=%s" % (name, aktiv))
            if self.schreiben and aktiv:
                self.k18.kw("ir.cron", "write", [[cid], {"active": False}])
        self.queue_vorher = self.k18.kw("mail.mail", "search_count", [[]])
        self.traces_vorher = self.k18.kw("mailing.trace", "search_count", [[]])
        print("  mail.mail vorher:", self.queue_vorher, "| mailing.trace vorher:", self.traces_vorher)

    def crons_zurueck(self):
        for cid, name, aktiv in getattr(self, "cron_zustand", []):
            if self.schreiben:
                self.k18.kw("ir.cron", "write", [[cid], {"active": aktiv}])
        self.queue_nachher = self.k18.kw("mail.mail", "search_count", [[]])
        self.traces_nachher = self.k18.kw("mailing.trace", "search_count", [[]])
        print("\n=== Sicherheitspruefung ===")
        print("  mail.mail vorher/nachher:", self.queue_vorher, "/", self.queue_nachher)
        print("  mailing.trace vorher/nachher:", self.traces_vorher, "/", self.traces_nachher)
        if self.queue_nachher > self.queue_vorher:
            self.offen.append("Es sind neue mail.mail-Zeilen entstanden!")
        if self.traces_nachher > self.traces_vorher:
            self.offen.append("Es sind neue mailing.trace-Zeilen entstanden!")
        self.zahlen["mail.mail vorher/nachher"] = "%s / %s" % (self.queue_vorher, self.queue_nachher)
        self.zahlen["mailing.trace vorher/nachher"] = "%s / %s" % (self.traces_vorher, self.traces_nachher)

    # ------------------------------------------------------------- Demodaten
    def demo_entfernen(self):
        modelle = ["mailing.trace", "mailing.contact", "mailing.mailing", "mailing.list"]
        self.zahlen["Demodaten entfernt"] = 0
        for modell in modelle:
            ds = self.k18.kw("ir.model.data", "search_read",
                             [[("module", "=", "mass_mailing"), ("model", "=", modell)],
                              ["name", "res_id"]])
            ids = [d["res_id"] for d in ds]
            if not ids:
                continue
            # nur Datensaetze, die wirklich aus dem Demo-Datensatz stammen
            vorhanden = self.k18.kw(modell, "search_read", [[("id", "in", ids)], ["id"]],
                                    context={"active_test": False})
            ids = [v["id"] for v in vorhanden]
            print("  Demo %-18s %d Datensaetze" % (modell, len(ids)))
            if self.schreiben and ids:
                try:
                    self.k18.kw(modell, "unlink", [ids])
                    self.zahlen["Demodaten entfernt"] += len(ids)
                except Exception as exc:  # noqa: BLE001
                    self.hinweise.append("Demodaten %s nicht loeschbar: %s" % (modell, str(exc)[:80]))

    def restdemo_entfernen(self):
        """Demo-Mailings ohne XML-ID (Odoo 18-Demodaten) entfernen.

        Die Odoo-18-Demodaten zu mailing.mailing/mailing.trace haben keine
        ir.model.data-Verknuepfung. Entfernt werden deshalb ausschliesslich
        Mailings OHNE Odoo-11-Referenz, die vor der ersten uebernommenen
        Veranstaltung bzw. vor dem Migrationslauf entstanden sind, samt ihren
        Versandprotokollen. Personenbezug: die Protokolle enthalten
        Demo-Empfaenger und verschwinden mit ihnen.
        """
        erste = self.k18.kw("mailing.mailing", "search_read",
                            [[("x_o11_id", "!=", False)], ["create_date"]],
                            context={"active_test": False})
        if not erste:
            return
        grenze = min(m["create_date"] for m in erste)
        alt = self.k18.kw("mailing.mailing", "search_read",
                          [[("x_o11_id", "=", False), ("create_date", "<", grenze)],
                           ["id", "subject", "create_date"]], context={"active_test": False})
        if not alt:
            return
        print("  Demo-Mailings ohne Odoo-11-Referenz:", [(a["id"], a["subject"][:30]) for a in alt])
        if not self.schreiben:
            return
        ids = [a["id"] for a in alt]
        traces = self.k18.kw("mailing.trace", "search_read",
                             [[("mass_mailing_id", "in", ids)], ["id"]], context={"active_test": False})
        if traces:
            self.k18.kw("mailing.trace", "unlink", [[t["id"] for t in traces]])
        self.k18.kw("mailing.mailing", "unlink", [ids])
        self.zahlen["Demo-Mailings entfernt"] = len(ids)
        self.zahlen["Demo-Versandprotokolle entfernt"] = len(traces)

    # ------------------------------------------------------------- Migration
    def migrieren(self):
        # Stufen
        stage_map, neu_stage = {}, 0
        for s in self.stages11:
            da = self.k18.kw("itk.mailing.campaign.stage", "search_read",
                             [[("name", "=", s["name"])], ["id"]], context={"active_test": False})
            if da:
                stage_map[s["id"]] = da[0]["id"]
                continue
            neu_stage += 1
            if self.schreiben:
                r = self.k18.kw("itk.mailing.campaign.stage", "create", [{
                    "name": s["name"], "sequence": s["sequence"], "x_o11_id": s["id"]}])
                stage_map[s["id"]] = r[0]["id"] if isinstance(r, list) else r

        # Tags
        tag_map, neu_tag = {}, 0
        for t in self.tags11:
            da = self.k18.kw("itk.mailing.tag", "search_read", [[("name", "=", t["name"])], ["id"]])
            if da:
                tag_map[t["id"]] = da[0]["id"]
                continue
            neu_tag += 1
            if self.schreiben:
                r = self.k18.kw("itk.mailing.tag", "create", [{
                    "name": t["name"], "color": t["color"] or 0, "x_o11_id": t["id"]}])
                tag_map[t["id"]] = r[0]["id"] if isinstance(r, list) else r

        # Benutzer (nur vorhandene, keine neuen)
        logins11 = {u["id"]: (u["login"] or "").lower() for u in
                    self.k11.kw("res.users", "read",
                                [sorted({c["user_id"][0] for c in self.camps11 if c["user_id"]}),
                                 ["login"]], context={"active_test": False})}
        benutzer18 = {u["login"].lower(): u["id"] for u in
                      self.k18.kw("res.users", "search_read", [[], ["id", "login"]],
                                  context={"active_test": False})}

        # Kampagnen
        camp_map, neu_camp, upd_camp = {}, 0, 0
        for c in self.camps11:
            uid = benutzer18.get(logins11.get((c["user_id"] or [0])[0], ""), False)
            werte = {
                "name": c["name"],
                "stage_id": stage_map.get((c["stage_id"] or [0])[0]),
                "user_id": uid or False,
                "tag_ids": [(6, 0, [tag_map[t] for t in c["tag_ids"] if t in tag_map])],
                "x_o11_id": c["id"],
                "x_o11_total_mailings": c.get("total_mailings") or 0,
                "x_o11_sent": c.get("sent") or 0,
                "x_o11_delivered": c.get("delivered") or 0,
                "x_o11_opened": c.get("opened") or 0,
                "x_o11_replied": c.get("replied") or 0,
                "x_o11_bounced": c.get("bounced") or 0,
                "x_o11_received_ratio": c.get("received_ratio") or 0,
                "x_o11_opened_ratio": c.get("opened_ratio") or 0,
                "x_o11_replied_ratio": c.get("replied_ratio") or 0,
                "x_o11_clicks_ratio": c.get("clicks_ratio") or 0,
                "x_o11_sent_date": c.get("sent_date") or False,
                "x_o11_unique_ab_testing": bool(c.get("unique_ab_testing")),
            }
            da = self.k18.kw("itk.mailing.campaign", "search_read",
                             [[("x_o11_id", "=", c["id"])], ["id"]], context={"active_test": False})
            if da:
                camp_map[c["id"]] = da[0]["id"]
                upd_camp += 1
                if self.schreiben:
                    self.k18.kw("itk.mailing.campaign", "write", [[da[0]["id"]], werte])
                continue
            neu_camp += 1
            if self.schreiben:
                r = self.k18.kw("itk.mailing.campaign", "create", [werte])
                camp_map[c["id"]] = r[0]["id"] if isinstance(r, list) else r

        # Mailinglisten (nur Struktur, keine Kontakte)
        list_map, neu_liste = {}, 0
        for l in self.listen11:
            da = self.k18.kw("mailing.list", "search_read",
                             [[("name", "=", l["name"])], ["id"]], context={"active_test": False})
            if da:
                list_map[l["id"]] = da[0]["id"]
                continue
            neu_liste += 1
            if self.schreiben:
                r = self.k18.kw("mailing.list", "create", [{"name": l["name"]}])
                list_map[l["id"]] = r[0]["id"] if isinstance(r, list) else r

        # Quelle: Odoo 18 verlangt ein Pflichtfeld. Alle uebernommenen Mailings
        # bekommen die eine Quelle "Odoo 11"; der Odoo-11-Quellenname bleibt im
        # Feld x_o11_source erhalten (Odoo 18 legt sonst je Mailing eigene
        # Quellen an und laeuft in die Eindeutigkeitspruefung).
        def quelle():
            da = self.k18.kw("utm.source", "search_read", [[("name", "=", "Odoo 11")], ["id"]],
                             context={"active_test": False})
            if da:
                return da[0]["id"]
            if not self.schreiben:
                return None
            r = self.k18.kw("utm.source", "create", [{"name": "Odoo 11"}])
            return r[0]["id"] if isinstance(r, list) else r

        quelle_id = quelle()

        # Einmalige Reparatur: Mailings, deren Quelle Odoo 18 automatisch aus dem
        # Betreff erzeugt hat, bekommen zuerst die gemeinsame Quelle "Odoo 11".
        # Ohne diesen Schritt wuerde ein Betreff-Write die automatisch erzeugten
        # Quellennamen neu bilden und an der Eindeutigkeit scheitern.
        falsch = self.k18.kw("mailing.mailing", "search_read",
                             [[("x_o11_id", "!=", False), ("source_id", "!=", quelle_id)],
                              ["id"]], context={"active_test": False})
        if falsch and self.schreiben and quelle_id:
            for f in falsch:
                try:
                    self.k18.kw("mailing.mailing", "write", [[f["id"]], {"source_id": quelle_id}])
                except Exception as exc:  # noqa: BLE001
                    self.hinweise.append("Quelle fuer Mailing %s nicht setzbar: %s"
                                         % (f["id"], str(exc)[-120:]))
            self.zahlen["Quellen auf 'Odoo 11' gesetzt"] = len(falsch)

        modell18 = {m["model"]: m["id"] for m in self.k18.kw("ir.model", "search_read",
                                                            [[], ["model"]])}

        # Mailings
        neu_mail, upd_mail, skip_mail, ohne_modell = 0, 0, 0, 0
        for m in self.mails11:
            modell_name = m["mailing_model_name"] or ""
            ziel = MODELL_MAP.get(modell_name, modell_name)
            if not ziel or ziel not in modell18:
                ohne_modell += 1
                self.hinweise.append(
                    "Mailing %s (%r) nicht migriert: Empfaengermodell %r gibt es in Odoo 18 nicht "
                    "bzw. Odoo 11 hatte keines (Odoo 18: Pflichtfeld)."
                    % (m["id"], (m["name"] or "")[:40], modell_name))
                self.nach.append(("mailing", m["id"], "", m["name"] or "", "", "nicht migriert: Modell fehlt"))
                continue
            if m["state"] not in STATE_MAP:
                skip_mail += 1
                self.offen.append("Mailing %s hat unbekannten Status %r" % (m["id"], m["state"]))
                continue
            werte = {
                # Odoo 11 hat kein eigenes Betreff-Feld: der Name ist der Betreff.
                "subject": (m["name"] or "(ohne Betreff)")[:250],
                "body_html": m["body_html"] or False,
                "body_arch": m["body_html"] or False,
                "email_from": m["email_from"] or "noreply@it-kommunal.at",
                "reply_to_mode": REPLY_MAP.get(m["reply_to_mode"], "update"),
                "reply_to": m["reply_to"] or False,
                "mailing_model_id": modell18[ziel],
                "mailing_domain": m["mailing_domain"] or "[]",
                "mailing_type": "mail",
                "schedule_type": "now",
                "source_id": quelle_id,
                "x_o11_source": (m["source_id"] or [None, False])[1] or False,
                "state": STATE_MAP[m["state"]],
                "active": bool(m["active"]),
                "keep_archives": bool(m["keep_archives"]),
                "color": m["color"] or 0,
                "contact_list_ids": [(6, 0, [list_map[x] for x in m["contact_list_ids"] if x in list_map])],
                "itk_campaign_id": camp_map.get((m["mass_mailing_campaign_id"] or [0])[0]) or False,
                "x_o11_id": m["id"],
                "x_o11_name": m["name"] or False,
                "x_o11_schedule_date": m["schedule_date"] or False,  # nur Information
                "x_o11_sent": m["sent"] or 0,
                "x_o11_delivered": m["delivered"] or 0,
                "x_o11_opened": m["opened"] or 0,
                "x_o11_replied": m["replied"] or 0,
                "x_o11_bounced": m["bounced"] or 0,
                "x_o11_failed": m["failed"] or 0,
                "x_o11_total": m["total"] or 0,
                "x_o11_contact_ab_pc": m["contact_ab_pc"] or 0,
            }
            if m["sent_date"]:
                werte["sent_date"] = m["sent_date"]
            da = self.k18.kw("mailing.mailing", "search_read",
                             [[("x_o11_id", "=", m["id"])], ["id"]], context={"active_test": False})
            if da:
                upd_mail += 1
                self.nach.append(("mailing", m["id"], da[0]["id"], m["name"] or "", "",
                                  "%s %s" % (m["state"], m["sent_date"] or "")))
                if self.schreiben:
                    try:
                        self.k18.kw("mailing.mailing", "write", [[da[0]["id"]], werte])
                    except Exception as exc:  # noqa: BLE001
                        self.offen.append("Mailing %s (%r) nicht aktualisierbar: %s"
                                          % (m["id"], (m["name"] or "")[:30], str(exc)[-200:]))
                continue
            neu_mail += 1
            if self.schreiben:
                try:
                    r = self.k18.kw("mailing.mailing", "create", [werte])
                except Exception as exc:  # noqa: BLE001
                    self.offen.append("Mailing %s (%r) nicht anlegbar: %s"
                                      % (m["id"], (m["name"] or "")[:30], str(exc)[-200:]))
                    continue
                mid = r[0]["id"] if isinstance(r, list) else r
                self.nach.append(("mailing", m["id"], mid, m["name"] or "", "",
                                  "%s %s" % (m["state"], m["sent_date"] or "")))
            else:
                self.nach.append(("mailing", m["id"], "", m["name"] or "", "",
                                  "Trockenlauf %s" % m["state"]))

        # Nachverknuepfung der Listen (nur Kennungen)
        for l in self.listen11:
            self.nach.append(("liste", l["id"], list_map.get(l["id"], ""), l["name"], "",
                              "Liste ohne Mitglieder (Personendaten folgen spaeter)"))
        for c in self.camps11:
            self.nach.append(("kampagne", c["id"], camp_map.get(c["id"], ""), c["name"], "",
                              "Stufe: %s" % (c["stage_id"] or ["", ""])[1]))

        # Odoo 18 leitet den Namen der Quelle beim Schreiben aus dem Mailing ab.
        # Nach dem Lauf wird die gemeinsame Quelle deshalb wieder auf ihren
        # fachlichen Namen gesetzt (die Odoo-11-Quellennamen stehen je Mailing
        # in x_o11_source).
        if self.schreiben and quelle_id:
            self.k18.kw("utm.source", "write", [[quelle_id], {"name": "Odoo 11"}])

        self.zahlen["Kampagnenstufen Odoo 11"] = len(self.stages11)
        self.zahlen["Kampagnenstufen neu"] = neu_stage
        self.zahlen["Kampagnen Odoo 11"] = len(self.camps11)
        self.zahlen["Kampagnen neu"] = neu_camp
        self.zahlen["Kampagnen aktualisiert"] = upd_camp
        self.zahlen["Tags Odoo 11"] = len(self.tags11)
        self.zahlen["Tags neu"] = neu_tag
        self.zahlen["Mailinglisten Odoo 11"] = len(self.listen11)
        self.zahlen["Mailinglisten neu"] = neu_liste
        self.zahlen["Mailings Odoo 11"] = len(self.mails11)
        self.zahlen["Mailings neu"] = neu_mail
        self.zahlen["Mailings aktualisiert"] = upd_mail
        self.zahlen["Mailings nicht migriert (Modell fehlt)"] = ohne_modell
        self.zahlen["Kontakte/Teilnehmer uebernommen"] = 0
        self.zahlen["mailing.trace uebernommen"] = 0

    def schreibe_csv(self):
        if not self.schreiben:
            return
        pfad = CSV_PFAD % self.instanz
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["typ", "o11_id", "o18_id", "bezeichnung", "partner_o11_id", "hinweis"])
            for zeile in self.nach:
                w.writerow(zeile)

    def bericht(self):
        print("\n=== Zahlen ===")
        for k, v in self.zahlen.items():
            print("  %-46s %s" % (k, v))
        if self.hinweise:
            print("\n=== Hinweise (%d) ===" % len(self.hinweise))
            for h in self.hinweise[:15]:
                print("   -", h)
        if self.offen:
            print("\n=== Offen (%d) ===" % len(self.offen))
            for o in self.offen:
                print("   -", o)
        print("\nModus:", "AUSGEFUEHRT" if self.schreiben else "TROCKENLAUF (nichts geschrieben)")
        if self.schreiben:
            print("Nachverknuepfung:", CSV_PFAD % self.instanz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    a = ap.parse_args()
    if a.ausfuehren and not a.ich_habe_freigabe:
        sys.exit("FEHLER: --ausfuehren nur mit --ich-habe-freigabe")
    os.makedirs(PROTO, exist_ok=True)
    lauf = Lauf(a.instanz, bool(a.ausfuehren))
    lauf.lese()
    lauf.crons_aus()
    lauf.demo_entfernen()
    lauf.migrieren()
    lauf.restdemo_entfernen()
    lauf.schreibe_csv()
    lauf.bericht()
    lauf.crons_zurueck()
    with open(os.path.join(PROTO, "lauf_%s.json" % a.instanz), "w", encoding="utf-8") as fh:
        json.dump({"zahlen": lauf.zahlen, "hinweise": lauf.hinweise, "offen": lauf.offen,
                   "modus": "ausgefuehrt" if a.ausfuehren else "trockenlauf"},
                  fh, ensure_ascii=False, indent=1)
    return 0 if not lauf.offen else 1


if __name__ == "__main__":
    sys.exit(main())
