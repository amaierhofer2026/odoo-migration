"""Datenmigration Veranstaltungen (Events) Odoo 11 -> Odoo 18.

Auftrag Session 138: NUR die nicht personenbezogenen Veranstaltungsdaten
uebernehmen. Ausdruecklich NICHT uebernommen werden Kontakte, Unternehmen,
Personen, Ansprechpartner, Teilnehmer, Teilnehmer-E-Mail-Adressen und
Partnerverknuepfungen. Es werden daher keine res.partner-Datensaetze
angelegt, geaendert oder zusammengefuehrt.

Uebernommen werden:
  * Anlasskategorien (event.type)
  * Veranstaltungen (event.event) mit Name, Beginn, Ende, Zeitzone,
    Status (Phase), Kategorie, Platzbegrenzung, Hoechstzahl,
    Online-Kennzeichen, Mindestzahl, Veroeffentlichungsstatus,
    verantwortlicher Benutzer, Firma, Aktiv-Kennzeichen
  * Odoo-11-Referenzfelder (x_o11_id, x_o11_state, x_o11_registrations,
    x_o11_organizer_id, x_o11_address_id) fuer Idempotenz und spaetere
    Nachverknuepfung
  * historische Mailplaner (event.mail) - ausnahmslos als bereits
    erledigt (mail_done = True) gekennzeichnet und damit stillgelegt
  * Nachverknuepfungsliste docs/o11-o18-events-nachverknuepfung.csv

Odoo 11 wird ausschliesslich gelesen.

Aufruf:
    python scripts/events_migration.py --instanz lokal                 # Trockenlauf
    python scripts/events_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
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
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "events_migration")
# Die Odoo-18-IDs sind je Instanz verschieden -> eine Liste je Instanz
CSV_PFAD = os.path.join(BASIS, "docs", "o11-o18-events-nachverknuepfung-%s.csv")

# Odoo-11-Status -> Reihenfolge der Odoo-18-Phase
STATUS_PHASE = {"draft": 1, "confirm": 2, "done": 5, "cancel": 6}

# Odoo-11-Vorlage -> Odoo-18-Vorlage (nach abweichendem Namen)
VORLAGE_ERSATZ = {
    "Reminder2": "event.event_reminder",
    "Event: Reminder": "event.event_reminder",
    "Event: Registration": "event.event_subscription",
    "Event: Registration Badge": "event.event_registration_mail_template_badge",
}


class Lauf:
    def __init__(self, instanz: str, schreiben: bool):
        self.instanz = instanz
        self.schreiben = schreiben
        self.k11 = o11()
        self.k18 = o18(instanz)
        self.zahlen = collections.OrderedDict()
        self.offen = []
        self.hinweise = []
        self.nach = []  # Nachverknuepfungszeilen

    # ---------------------------------------------------------------- lesen 11
    def lese(self):
        k = self.k11
        ctx11 = dict(DE, active_test=False)
        self.events11 = k.kw("event.event", "search_read", [[("id", ">", 0)], [
            "id", "name", "active", "state", "date_begin", "date_end", "date_tz",
            "event_type_id", "seats_max", "seats_min", "seats_availability",
            "organizer_id", "address_id", "user_id", "company_id",
            "is_online", "website_published", "create_uid",
        ]], context=ctx11, order="id")
        self.typen11 = k.kw("event.type", "search_read", [[], [
            "id", "name", "has_seats_limitation", "default_registration_min",
            "default_registration_max", "default_timezone", "is_online", "auto_confirm",
            "use_mail_schedule", "use_questions",
        ]], context=ctx11, order="id")
        self.reg11 = k.kw("event.registration", "search_read", [[], [
            "id", "event_id", "partner_id", "state", "create_date",
        ]], context=ctx11, order="id")
        self.mail11 = k.kw("event.mail", "search_read", [[], [
            "id", "event_id", "template_id", "interval_nbr", "interval_type",
            "interval_unit", "sequence", "done", "mail_sent",
        ]], context=ctx11, order="id")

        self.anzahl_je_event = collections.Counter(r["event_id"][0] for r in self.reg11 if r["event_id"])
        self.teilnehmer_je_event = collections.Counter(
            (r["event_id"][0], r["partner_id"][0] if r["partner_id"] else None)
            for r in self.reg11 if r["event_id"])

    # --------------------------------------------------------------- Odoo 18
    def phasen(self):
        st = self.k18.kw("event.stage", "search_read", [[], ["id", "name", "sequence"]], context=DE)
        return {s["sequence"]: s["id"] for s in st}

    def benutzer(self):
        us = self.k18.kw("res.users", "search_read", [[], ["id", "login"]], context={"active_test": False})
        return {u["login"].lower(): u["id"] for u in us}

    def kategorie(self, typ):
        """event.type ueber den fachlichen Schluessel (Name) suchen oder anlegen."""
        treffer = self.k18.kw("event.type", "search_read",
                              [[("name", "=", typ["name"])], ["id", "name"]], context={"active_test": False})
        if treffer:
            return treffer[0]["id"], False
        if not self.schreiben:
            return None, True
        # Keine Odoo-18-Standardmailplaner und keine Standardfragen: Odoo 11
        # hatte 0 Fragen, Mailversand ist nicht Teil dieser Migration.
        werte = {
            "name": typ["name"],
            "sequence": (typ.get("id") or 10),  # Odoo 11 hat kein sequence-Feld
            "has_seats_limitation": bool(typ["has_seats_limitation"]),
            "default_timezone": typ["default_timezone"] or "Europe/Vienna",
            "event_type_mail_ids": [(5, 0, 0)],
            "question_ids": [(5, 0, 0)],
        }
        if typ["has_seats_limitation"]:
            werte["seats_max"] = typ["default_registration_max"] or 0
        neu = self.k18.kw("event.type", "create", [werte], context=DE)
        return neu[0]["id"] if isinstance(neu, list) else neu, True

    def vorhandene_events(self):
        daten = self.k18.kw("event.event", "search_read",
                            [[("x_o11_id", "!=", False)], ["id", "x_o11_id"]],
                            context={"active_test": False})
        return {d["x_o11_id"]: d["id"] for d in daten}

    def benutzer_logins(self, ids):
        if not ids:
            return {}
        us = self.k11.kw("res.users", "read", [sorted(ids), ["login"]], context={"active_test": False})
        return {u["id"]: (u["login"] or "").lower() for u in us}

    # ------------------------------------------------------------- Migration
    def planen_und_schreiben(self):
        phasen = self.phasen()
        benutzer = self.benutzer()
        vorhanden = self.vorhandene_events()
        logins11 = self.benutzer_logins({e["user_id"][0] for e in self.events11 if e["user_id"]})
        typ_map = {}
        neu_typen = []
        for typ in self.typen11:
            tid, neu = self.kategorie(typ)
            typ_map[typ["id"]] = tid
            if neu:
                neu_typen.append(typ["name"])

        neu_events, akt_events, uebersprungen = 0, 0, 0
        id_map = {}

        for e in self.events11:
            seq = STATUS_PHASE.get(e["state"])
            if not seq:
                self.offen.append("Veranstaltung %s: unbekannter Status %r" % (e["id"], e["state"]))
                continue
            stage_id = phasen.get(seq)
            uid = False
            if e["user_id"]:
                login = logins11.get(e["user_id"][0], "")
                uid = benutzer.get(login)
                if not uid and login == "admin":
                    uid = 2  # Odoo-18-Administrator (Odoo 11 Login "admin")
                if not uid:
                    self.hinweise.append("Benutzer %r zu Veranstaltung %s fehlt in Odoo 18"
                                         % (login, e["id"]))

            werte = {
                "name": e["name"],
                "date_begin": e["date_begin"],
                "date_end": e["date_end"],
                "date_tz": e["date_tz"],
                "event_type_id": typ_map.get((e["event_type_id"] or [None])[0]) or False,
                "stage_id": stage_id,
                "seats_limited": e["seats_availability"] == "limited",
                "x_is_online": bool(e["is_online"]),
                "x_seats_min": e["seats_min"],
                "x_o11_id": e["id"],
                "x_o11_state": e["state"],
                "x_o11_registrations": self.anzahl_je_event.get(e["id"], 0),
                "x_o11_organizer_id": (e["organizer_id"] or [False])[0] or False,
                "x_o11_address_id": (e["address_id"] or [False])[0] or False,
                "website_published": bool(e["website_published"]),
                # KEINE Partnerverknuepfung: Odoo 18 wuerde sonst per Default
                # den Firmenkontakt als Veranstalter und Ort eintragen und damit
                # eine nicht belegte Beziehung vortaeuschen. Die Odoo-11-IDs
                # stehen in x_o11_organizer_id / x_o11_address_id.
                "organizer_id": False,
                "address_id": False,
                "user_id": uid or False,
                "company_id": (e["company_id"] or [1])[0],
                "active": bool(e["active"]),
                "description": False,
            }
            platz = {"seats_limited": werte["seats_limited"],
                     "seats_max": e["seats_max"] if werte["seats_limited"] else 0}

            if e["id"] in vorhanden:
                o18_id = vorhanden[e["id"]]
                if self.schreiben:
                    # Unveraenderte Kategorie nicht schreiben: ein Write auf
                    # event_type_id loest in Odoo 18 die Neuberechnung der
                    # Mailplaner aus (Standardplaner werden sonst neu angelegt).
                    ist = self.k18.kw("event.event", "read", [[o18_id], ["event_type_id"]], context=DE)[0]
                    zu_schreiben = dict(werte, **platz)
                    if (ist["event_type_id"] or [False])[0] == werte["event_type_id"]:
                        zu_schreiben.pop("event_type_id", None)
                    self.k18.kw("event.event", "write", [[o18_id], zu_schreiben], context=DE)
                akt_events += 1
                id_map[e["id"]] = o18_id
                continue

            # Doppelte ohne Referenz erkennen (Teillauf ohne x_o11_id)
            gleich = self.k18.kw("event.event", "search_read",
                                 [[("name", "=", e["name"]), ("date_begin", "=", e["date_begin"]),
                                   ("x_o11_id", "=", False)], ["id"]],
                                 context={"active_test": False})
            if gleich:
                self.hinweise.append(
                    "Veranstaltung %s (%r %s) hat in Odoo 18 bereits einen Datensatz ohne "
                    "Odoo-11-Referenz (id %s) - nicht angelegt, bitte pruefen."
                    % (e["id"], e["name"][:40], e["date_begin"], gleich[0]["id"]))
                uebersprungen += 1
                self.nach.append(("veranstaltung", e["id"], "", "%s | %s" % (e["name"], e["date_begin"]),
                                  "", "Odoo-18-Datensatz ohne Referenz vorhanden (id %s)" % gleich[0]["id"]))
                continue

            if not self.schreiben:
                neu_events += 1
                continue

            anlegen = dict(werte, event_mail_ids=[(5, 0, 0)])  # keine Odoo-18-Standardplaner
            neu = self.k18.kw("event.event", "create", [anlegen], context=DE)
            o18_id = neu[0]["id"] if isinstance(neu, list) else neu
            # seats_limited/seats_max erst nach dem Anlegen: die Compute-Regel
            # von event.event ueberschreibt beide beim Setzen der Kategorie.
            self.k18.kw("event.event", "write", [[o18_id], platz], context=DE)
            neu_events += 1
            id_map[e["id"]] = o18_id

        # Nachverknuepfung: Veranstaltungen, Veranstalter, Ort, Teilnehmer
        for e in self.events11:
            self.nach.append(("veranstaltung", e["id"], id_map.get(e["id"], ""),
                              "%s | %s" % (e["name"], e["date_begin"]), "",
                              "" if id_map.get(e["id"]) else "nicht angelegt"))
            o18_id = id_map.get(e["id"], "")
            if e["organizer_id"]:
                self.nach.append(("veranstalter", e["id"], o18_id, e["name"],
                                  e["organizer_id"][0], "Kontaktmigration ausstehend"))
            if e["address_id"]:
                self.nach.append(("ort", e["id"], o18_id, e["name"],
                                  e["address_id"][0], "Kontaktmigration ausstehend"))

        # Teilnehmer: nur Kennungen, keine Namen und keine E-Mail-Adressen
        for r in self.reg11:
            ev_id = (r["event_id"] or [None])[0]
            self.nach.append((
                "teilnehmer",
                r["id"],
                "",  # in Odoo 18 (noch) nicht angelegt
                "%s|%s|%s" % (ev_id, r["state"], r["create_date"]),
                (r["partner_id"] or [False])[0] or "",
                "Personendaten nicht migriert (Kontakt- und Personendatenmigration ausstehend)",
            ))

        # Historische Mailplaner, ausnahmslos stillgelegt
        neu_mails, skip_mails, fehlende_vorlagen = 0, 0, set()
        bekannte_event_ids = {e["id"] for e in self.events11}
        for m in self.mail11:
            ev_id = (m["event_id"] or [None])[0]
            o18_id = id_map.get(ev_id)
            if not o18_id:
                if not self.schreiben and ev_id in bekannte_event_ids:
                    neu_mails += 1  # Trockenlauf: Veranstaltung wuerde angelegt
                continue
            xmlid = VORLAGE_ERSATZ.get((m["template_id"] or ["", ""])[1])
            tpl_id = None
            if xmlid:
                modul, name = xmlid.split(".")
                d = self.k18.kw("ir.model.data", "search_read",
                                [[("module", "=", modul), ("name", "=", name)], ["res_id"]])
                tpl_id = d[0]["res_id"] if d else None
            if not tpl_id:
                fehlende_vorlagen.add((m["template_id"] or ["", "?"])[1])
                continue
            ref = "mail.template,%s" % tpl_id
            da = self.k18.kw("event.mail", "search_read",
                             [[("event_id", "=", o18_id), ("template_ref", "=", ref),
                               ("interval_type", "=", m["interval_type"]),
                               ("interval_unit", "=", m["interval_unit"]),
                               ("interval_nbr", "=", m["interval_nbr"])], ["id"]])
            if da:
                skip_mails += 1
                continue
            if not self.schreiben:
                neu_mails += 1
                continue
            self.k18.kw("event.mail", "create", [{
                "event_id": o18_id,
                "template_ref": ref,
                "interval_nbr": m["interval_nbr"],
                "interval_type": m["interval_type"],
                "interval_unit": m["interval_unit"],
                "sequence": m["sequence"],
                "mail_done": True,          # historisch: bereits erledigt, kein Versand
            }], context=DE)
            neu_mails += 1

        # Aufraeumen: Odoo 18 legt bei Veranstaltungen ohne Kategorie eigene
        # Standardplaner an (mail_done = False). Sie gehoeren nicht zur
        # Odoo-11-Historie und koennten spaeter Mails ausloesen.
        standard_planer = self.k18.kw("event.mail", "search_read",
                                      [[("mail_done", "=", False), ("event_id.x_o11_id", "!=", False)], ["id"]])
        if standard_planer and self.schreiben:
            self.k18.kw("event.mail", "unlink", [[p["id"] for p in standard_planer]])
        self.zahlen["Odoo-18-Standardplaner entfernt"] = len(standard_planer)

        self.zahlen["Kategorien Odoo 11"] = len(self.typen11)
        self.zahlen["Kategorien neu angelegt"] = len(neu_typen)
        self.zahlen["Veranstaltungen Odoo 11"] = len(self.events11)
        self.zahlen["Veranstaltungen neu angelegt"] = neu_events
        self.zahlen["Veranstaltungen aktualisiert"] = akt_events
        self.zahlen["Veranstaltungen uebersprungen (Konflikt)"] = uebersprungen
        self.zahlen["davon archiviert uebernommen"] = sum(1 for e in self.events11 if not e["active"])
        self.zahlen["Mailplaner Odoo 11"] = len(self.mail11)
        self.zahlen["Mailplaner neu (stillgelegt)"] = neu_mails
        self.zahlen["Mailplaner bereits vorhanden"] = skip_mails
        self.zahlen["Teilnehmer Odoo 11 (nicht migriert)"] = len(self.reg11)
        self.zahlen["referenzierte Kontakte Odoo 11 (nicht migriert)"] = len(
            set([e["organizer_id"][0] for e in self.events11 if e["organizer_id"]]
                + [e["address_id"][0] for e in self.events11 if e["address_id"]]
                + [r["partner_id"][0] for r in self.reg11 if r["partner_id"]]))
        if fehlende_vorlagen:
            self.offen.append("Vorlagen ohne Odoo-18-Gegenstueck: %s" % sorted(fehlende_vorlagen))

    def schreibe_csv(self):
        if not self.schreiben:
            return
        pfad = CSV_PFAD % self.instanz
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["typ", "o11_id", "o18_id", "schluessel", "partner_o11_id", "hinweis"])
            for zeile in self.nach:
                w.writerow(zeile)

    def bericht(self):
        print("\n=== Zahlen ===")
        for k, v in self.zahlen.items():
            print("  %-52s %s" % (k, v))
        if self.hinweise:
            print("\n=== Hinweise (%d) ===" % len(self.hinweise))
            for h in self.hinweise[:20]:
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
    lauf.planen_und_schreiben()
    lauf.schreibe_csv()
    lauf.bericht()
    with open(os.path.join(PROTO, "lauf_%s.json" % a.instanz), "w", encoding="utf-8") as fh:
        json.dump({"zahlen": lauf.zahlen, "hinweise": lauf.hinweise, "offen": lauf.offen,
                   "modus": "ausgefuehrt" if a.ausfuehren else "trockenlauf"},
                  fh, ensure_ascii=False, indent=1)
    return 0 if not lauf.offen else 1


if __name__ == "__main__":
    sys.exit(main())
