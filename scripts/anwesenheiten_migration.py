"""Datenmigration Anwesenheiten und Urlaubsantraege Odoo 11 -> Odoo 18.

Ergaenzt die Personal-Migration (hr_migration.py, Session 134) um die Punkte, die
in der Abnahme des Bereichs Anwesenheiten/Urlaub fehlten:

  * neue Odoo-11-Datensaetze seit dem letzten Lauf (Antraege, Anwesenheiten)
  * Anwesenheiten: Homeoffice-Kennzeichen x_homeoffice (Odoo-11-Studio-Feld)
  * Antraege: Beschreibung (Odoo 11 "name") -> private_name,
    historische Tagesanzahl -> x_o11_number_of_days,
    Erste/Zweite Genehmigung
  * Antraege: Statusabgleich (Odoo-11-Status ist massgeblich) - behebt den
    Fall Abwesenheit #87 auf der VM ("Zu genehmigen" statt "Genehmigt")
  * Ansprueche: fehlende Datensaetze werden nachgezogen, auch gleichnamige
    Ansprueche (Odoo 11 fuehrt z. B. zwei 25-Tage-Ansprueche desselben
    Mitarbeiters; Odoo 18 erlaubt das ebenfalls)
  * Aufraeumen: reine Odoo-18-Testdatensaetze (Mitarbeiter ohne
    Odoo-11-Gegenstueck, Abwesenheitsart nicht aus Odoo 11) werden entfernt

Odoo 11 wird ausschliesslich gelesen.

Aufruf:
    python scripts/anwesenheiten_migration.py --instanz lokal            # Trockenlauf
    python scripts/anwesenheiten_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

DE = {"lang": "de_DE"}
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "anwesenheiten_migration")


def norm_email(wert):
    return (wert or "").strip().lower()


def norm_name(wert):
    return " ".join((wert or "").split()).lower()


def norm_typ(wert):
    return " ".join((wert or "").split())


class Lauf:
    def __init__(self, instanz: str, schreiben: bool):
        self.instanz = instanz
        self.schreiben = schreiben
        self.k11 = o11()
        self.k18 = o18(instanz)
        self.protokoll = []
        self.offen = []
        self.hinweise = []

    # ------------------------------------------------------------------ lesen
    def lese(self):
        ctx11 = dict(DE, active_test=False)
        k = self.k11
        self.b11 = k.kw("hr.employee", "search_read", [[], ["id", "name", "work_email", "active"]],
                        context=ctx11, order="id")
        self.typen11 = {t["id"]: t for t in k.kw("hr.holidays.status", "search_read",
                                                 [[], ["id", "name", "limit", "active"]], context=ctx11)}
        self.h11 = k.kw("hr.holidays", "search_read",
                        [[], ["id", "name", "type", "holiday_type", "employee_id", "holiday_status_id",
                              "state", "date_from", "date_to", "number_of_days_temp", "create_date",
                              "first_approver_id", "second_approver_id", "manager_id"]],
                        context=ctx11, order="id")
        self.a11 = k.kw("hr.attendance", "search_read",
                        [[], ["id", "employee_id", "check_in", "check_out", "worked_hours",
                              "x_homeoffice"]],
                        context=ctx11, order="check_in,id")

        ctx18 = dict(DE, active_test=False)
        c = self.k18
        self.b18 = c.kw("hr.employee", "search_read", [[], ["id", "name", "work_email", "active"]],
                        context=ctx18, order="id")
        self.typen18 = {t["id"]: t for t in c.kw("hr.leave.type", "search_read",
                                                 [[], ["id", "name", "requires_allocation"]],
                                                 context=ctx18, order="id")}
        self.l18 = c.kw("hr.leave", "search_read",
                        [[], ["id", "employee_id", "holiday_status_id", "request_date_from",
                              "request_date_to", "number_of_days", "state", "private_name",
                              "x_o11_number_of_days", "first_approver_id", "second_approver_id",
                              "create_date"]], context=ctx18, order="id")
        self.al18 = c.kw("hr.leave.allocation", "search_read",
                         [[], ["id", "employee_id", "holiday_status_id", "number_of_days", "state",
                               "name", "date_from"]], context=ctx18, order="id")
        self.at18 = c.kw("hr.attendance", "search_read",
                         [[], ["id", "employee_id", "check_in", "check_out", "worked_hours",
                               "x_homeoffice"]],
                         context=ctx18, order="check_in,id")

    # -------------------------------------------------------------- zuordnung
    def baue_mapping(self):
        nach_email = {norm_email(e["work_email"]): e for e in self.b18 if e["work_email"]}
        nach_name = {norm_name(e["name"]): e for e in self.b18}
        self.ma = {}
        for e in self.b11:
            z = nach_email.get(norm_email(e["work_email"]))
            if not z:
                z = nach_name.get(norm_name(e["name"]))
            if z:
                self.ma[e["id"]] = z
        fehlend = [e["name"] for e in self.b11 if e["id"] not in self.ma]
        if fehlend:
            self.offen.append("Mitarbeiter ohne Odoo-18-Gegenstueck: %s" % fehlend)

        # Abwesenheitsarten: Odoo-11-Name (bereinigt) -> Odoo-18-Art
        nach_typname = collections.defaultdict(list)
        for t in self.typen18.values():
            nach_typname[norm_typ(t["name"])].append(t)
        self.ty = {}
        for tid, t in self.typen11.items():
            treffer = nach_typname.get(norm_typ(t["name"]))
            if treffer and len(treffer) == 1:
                self.ty[tid] = treffer[0]
        fehlende_typen = [t["name"] for tid, t in self.typen11.items() if tid not in self.ty]
        if fehlende_typen:
            self.offen.append("Urlaubsarten ohne Odoo-18-Gegenstueck: %s" % fehlende_typen)

    def emp18(self, m2o):
        if not m2o:
            return None
        return self.ma.get(m2o[0])

    # ------------------------------------------------------------------ planen
    def plane(self):
        # ---- Ansprueche: Multimengen-Abgleich (gleiche Datensaetze bleiben mehrfach erlaubt)
        vorhanden = collections.defaultdict(list)
        for a in self.al18:
            if not a["employee_id"] or not a["holiday_status_id"]:
                continue
            schluessel = (a["employee_id"][0], a["holiday_status_id"][0],
                          round(a["number_of_days"] or 0.0, 2), a["state"])
            vorhanden[schluessel].append(a)
        self.ansprueche_neu = []
        self.ansprueche_status = []
        for h in self.h11:
            if h["type"] != "add":
                continue
            if not h["employee_id"]:
                self.hinweise.append("Anspruch O11 %d ohne Mitarbeiter (Kategorie-Anspruch) - nicht uebertragbar"
                                  % h["id"])
                continue
            tage = round(h["number_of_days_temp"] or 0.0, 2)
            if tage <= 0:
                self.hinweise.append("Anspruch O11 %d: 0 Tage - Odoo 18 erlaubt Dauer 0 nicht" % h["id"])
                continue
            e = self.emp18(h["employee_id"])
            typ = self.ty.get(h["holiday_status_id"][0])
            if not e or not typ:
                continue
            schluessel = (e["id"], typ["id"], tage, h["state"])
            if vorhanden[schluessel]:
                vorhanden[schluessel].pop(0)
            else:
                self.ansprueche_neu.append({"o11": h, "employee": e, "typ": typ, "tage": tage})

        # ---- Antraege
        vorhanden_l = collections.defaultdict(list)
        for r in self.l18:
            if not r["employee_id"] or not r["holiday_status_id"]:
                continue
            schluessel = (r["employee_id"][0], r["holiday_status_id"][0],
                          r["request_date_from"], r["request_date_to"])
            vorhanden_l[schluessel].append(r)
        self.antraege_neu = []
        self.antraege_update = []
        for h in self.h11:
            if h["type"] != "remove":
                continue
            e = self.emp18(h["employee_id"])
            typ = self.ty.get(h["holiday_status_id"][0])
            von = (h["date_from"] or "")[:10]
            bis = (h["date_to"] or "")[:10]
            if not e or not typ or not von or not bis:
                self.offen.append("Antrag O11 %d nicht zuordenbar (Mitarbeiter/Art/Datum)" % h["id"])
                continue
            schluessel = (e["id"], typ["id"], von, bis)
            kandidaten = vorhanden_l[schluessel]
            if kandidaten:
                r = kandidaten.pop(0)
                # Status nur schreiben, wenn er abweicht: jedes Schreiben von
                # "state" laesst Odoo 18 die Anspruchspruefung erneut laufen.
                ziel = {}
                if r["state"] != h["state"]:
                    ziel["state"] = h["state"]
                soll_tage = round(h["number_of_days_temp"] or 0.0, 2)
                if abs((r["x_o11_number_of_days"] or 0.0) - soll_tage) > 0.001:
                    ziel["x_o11_number_of_days"] = soll_tage
                if h["name"] and norm_typ(h["name"]) != norm_typ(r["private_name"] or ""):
                    ziel["private_name"] = norm_typ(h["name"])
                for feld in ("first_approver_id", "second_approver_id"):
                    if h.get(feld) and not r.get(feld):
                        ziel[feld] = self.ma.get(h[feld][0], {}).get("id")
                        if not ziel[feld]:
                            ziel.pop(feld)
                if self.abgleich_noetig(r, ziel):
                    self.antraege_update.append({"o11": h, "o18": r, "vals": ziel})
            else:
                self.antraege_neu.append({"o11": h, "employee": e, "typ": typ, "von": von, "bis": bis})

        # ---- Anwesenheiten
        vorhanden_a = collections.defaultdict(list)
        for a in self.at18:
            if a["employee_id"]:
                vorhanden_a[(a["employee_id"][0], a["check_in"])].append(a)
        self.anw_neu = []
        self.anw_update = []
        for a in self.a11:
            e = self.emp18(a["employee_id"])
            if not e:
                continue
            kandidaten = vorhanden_a[(e["id"], a["check_in"])]
            if kandidaten:
                r = kandidaten.pop(0)
                vals = {}
                if bool(r["x_homeoffice"]) != bool(a.get("x_homeoffice")):
                    vals["x_homeoffice"] = bool(a.get("x_homeoffice"))
                if (r["check_out"] or False) != (a.get("check_out") or False):
                    vals["check_out"] = a.get("check_out") or False
                if abs((r["worked_hours"] or 0.0) - (a["worked_hours"] or 0.0)) > 0.001:
                    # Odoo 18 speichert die Arbeitsstunden berechnet; sie wurden
                    # beim ersten Import mit einem noch nicht gesetzten
                    # Kalender-Zeitzonenfeld ermittelt (genau 1 Stunde zu wenig).
                    # Neuschreiben von check_in loest die Neuberechnung aus.
                    vals.setdefault("check_in", a["check_in"])
                if vals:
                    self.anw_update.append({"o11": a, "o18": r, "vals": vals})
            else:
                self.anw_neu.append({"o11": a, "employee": e})

        # ---- reine Odoo-18-Testdatensaetze
        o11_mitarbeiter = {norm_name(e["name"]) for e in self.b11}
        o11_typen = {norm_typ(t["name"]) for t in self.typen11.values()}
        # Reine Odoo-18-Testdatensaetze: eine Abwesenheitsart, die es in Odoo 11
        # nicht gibt, kann nicht aus Odoo 11 stammen (alle Odoo-11-Arten wurden
        # uebernommen). Zusaetzlich: Mitarbeiter ohne Odoo-11-Gegenstueck.
        # Nur die Abwesenheitsart entscheidet: alle Odoo-11-Arten wurden
        # uebernommen, eine andere Art kann daher nicht aus Odoo 11 stammen.
        # (Der Mitarbeitername taugt nicht als Kriterium, weil Odoo 18 die
        # Schreibweise "Miglar Daniel" statt "Daniel Miglar" fuehrt.)
        self.fremd = []
        for r in self.l18:
            typname = norm_typ(self.typen18[r["holiday_status_id"][0]]["name"]) if r["holiday_status_id"] else ""
            if typname not in o11_typen:
                self.fremd.append(r)
        for a in self.al18:
            typname = norm_typ(self.typen18[a["holiday_status_id"][0]]["name"]) if a["holiday_status_id"] else ""
            if typname not in o11_typen:
                self.fremd.append(a)

    @staticmethod
    def abgleich_noetig(rec, vals):
        for feld, wert in vals.items():
            if feld == "state":
                if rec["state"] != wert:
                    return True
            elif feld in ("first_approver_id", "second_approver_id"):
                if (rec[feld][0] if rec[feld] else False) != wert:
                    return True
            elif feld == "x_o11_number_of_days":
                if abs((rec[feld] or 0.0) - wert) > 0.001:
                    return True
            elif feld == "private_name":
                if norm_typ(rec[feld] or "") != norm_typ(wert):
                    return True
        return False

    # ------------------------------------------------------------------ zeigen
    def zeige(self):
        print("Instanz %s - %s" % (self.instanz, "SCHREIBLAUF" if self.schreiben else "TROCKENLAUF"))
        print("  Odoo 11: %d Antraege, %d Ansprueche, %d Anwesenheiten, %d Mitarbeiter"
              % (sum(1 for h in self.h11 if h["type"] == "remove"),
                 sum(1 for h in self.h11 if h["type"] == "add"),
                 len(self.a11), len(self.b11)))
        print("  Odoo 18: %d Antraege, %d Ansprueche, %d Anwesenheiten, %d Mitarbeiter"
              % (len(self.l18), len(self.al18), len(self.at18), len(self.b18)))
        print("  Mitarbeiterzuordnung: %d von %d ueber E-Mail/Name" % (len(self.ma), len(self.b11)))
        print("  neue Antraege:              %d" % len(self.antraege_neu))
        for x in self.antraege_neu:
            h = x["o11"]
            print("     O11 %4d  %-30s %-38s %s bis %s  %s  %.2f Tage"
                  % (h["id"], x["employee"]["name"][:30], x["typ"]["name"][:38],
                     x["von"], x["bis"], h["state"], h["number_of_days_temp"] or 0))
        print("  neue Ansprueche:            %d" % len(self.ansprueche_neu))
        for x in self.ansprueche_neu:
            h = x["o11"]
            print("     O11 %4d  %-30s %-38s %.2f Tage  %s"
                  % (h["id"], x["employee"]["name"][:30], x["typ"]["name"][:38], x["tage"], h["state"]))
        print("  neue Anwesenheiten:         %d" % len(self.anw_neu))
        for x in self.anw_neu[:10]:
            print("     O11 %6d %-28s %s" % (x["o11"]["id"], x["employee"]["name"][:28], x["o11"]["check_in"]))
        print("  zu korrigierende Antraege:  %d" % len(self.antraege_update))
        for x in self.antraege_update:
            print("     O11 %4d  O18 %4d  %-30s %s bis %s  %s -> %s  %s"
                  % (x["o11"]["id"], x["o18"]["id"], x["o18"]["employee_id"][1][:30],
                     x["o18"]["request_date_from"], x["o18"]["request_date_to"],
                     x["o18"]["state"], x["vals"].get("state", x["o18"]["state"]), x["vals"]))
        arten = collections.Counter()
        for x in self.anw_update:
            for feld in x["vals"]:
                arten[feld] += 1
        print("  zu korrigierende Anwesenheiten: %d  %s" % (len(self.anw_update), dict(arten)))
        print("  reine Odoo-18-Testdatensaetze: %d" % len(self.fremd))
        for r in self.fremd:
            modell = "Anspruch" if "number_of_days" in r and "request_date_from" not in r else "Antrag"
            print("     %s id=%s %-28s %-30s %s  %s"
                  % (modell, r["id"], (r["employee_id"][1] if r["employee_id"] else "")[:28],
                     (self.typen18[r["holiday_status_id"][0]]["name"] if r["holiday_status_id"] else "")[:30],
                     r.get("request_date_from") or r.get("date_from"), r["state"]))
        if self.hinweise:
            print("  dokumentiert, nicht uebertragbar:")
            for o in self.hinweise:
                print("     -", o)
        if self.offen:
            print("  FEHLER:")
            for o in self.offen:
                print("     -", o)

    # ----------------------------------------------------------------- schreiben
    def schreibe(self):
        c = self.k18
        ctx = dict(DE, leave_skip_date_check=True)
        self.ergebnis = {"antraege_neu": 0, "ansprueche_neu": 0, "anw_neu": 0,
                         "antraege_korrigiert": 0, "anw_korrigiert": 0, "fremd_geloescht": 0}

        for x in self.ansprueche_neu:
            h = x["o11"]
            daten = []
            if h.get("create_date"):
                daten.append(h["create_date"][:10])
            for antrag in self.h11:
                if antrag["type"] != "remove" or not antrag.get("date_from"):
                    continue
                if antrag["holiday_status_id"][0] != h["holiday_status_id"][0]:
                    continue
                if self.emp18(antrag["employee_id"]) != x["employee"]:
                    continue
                daten.append(antrag["date_from"][:10])
            start = min(daten) if daten else "2000-01-01"
            aid = c.kw("hr.leave.allocation", "create", [{
                "employee_id": x["employee"]["id"],
                "holiday_status_id": x["typ"]["id"],
                "number_of_days": x["tage"],
                "date_from": start,
                "name": h.get("name") or x["typ"]["name"],
            }], context=ctx)
            c.kw("hr.leave.allocation", "write", [[aid], {"state": h["state"]}])
            self.ergebnis["ansprueche_neu"] += 1
            self.protokoll.append({"art": "anspruch_neu", "o11": h["id"], "o18": aid})

        for x in self.antraege_neu:
            h = x["o11"]
            lid = c.kw("hr.leave", "create", [{
                "employee_id": x["employee"]["id"],
                "holiday_status_id": x["typ"]["id"],
                "request_date_from": x["von"],
                "request_date_to": x["bis"],
                "private_name": norm_typ(h.get("name")) or x["typ"]["name"],
            }], context=ctx)
            vals = {"x_o11_number_of_days": round(h["number_of_days_temp"] or 0.0, 2)}
            if h["state"] != "confirm":
                vals["state"] = h["state"]
            for feld in ("first_approver_id", "second_approver_id"):
                if h.get(feld):
                    vals[feld] = self.ma.get(h[feld][0], {}).get("id") or False
            c.kw("hr.leave", "write", [[lid], vals])
            self.ergebnis["antraege_neu"] += 1
            self.protokoll.append({"art": "antrag_neu", "o11": h["id"], "o18": lid})

        for x in self.antraege_update:
            try:
                c.kw("hr.leave", "write", [[x["o18"]["id"]], x["vals"]])
                self.ergebnis["antraege_korrigiert"] += 1
                self.protokoll.append({"art": "antrag_korrigiert", "o11": x["o11"]["id"],
                                       "o18": x["o18"]["id"], "vals": x["vals"]})
            except Exception as exc:  # noqa: BLE001
                self.offen.append("Korrektur Antrag O11 %d / O18 %d fehlgeschlagen: %s"
                                  % (x["o11"]["id"], x["o18"]["id"], str(exc)[-400:]))

        # Erst korrigieren (u. a. offene Anmeldungen schliessen), dann anlegen:
        # Odoo 18 erlaubt je Mitarbeiter nur eine offene Anwesenheit.
        for x in self.anw_update:
            c.kw("hr.attendance", "write", [[x["o18"]["id"]], x["vals"]])
            self.ergebnis["anw_korrigiert"] += 1
            self.protokoll.append({"art": "anwesenheit_korrigiert", "o11": x["o11"]["id"],
                                   "o18": x["o18"]["id"], "vals": x["vals"]})

        for x in self.anw_neu:
            a = x["o11"]
            aid = c.kw("hr.attendance", "create", [{
                "employee_id": x["employee"]["id"],
                "check_in": a["check_in"],
                "check_out": a.get("check_out") or False,
                "x_homeoffice": bool(a.get("x_homeoffice")),
            }])
            self.ergebnis["anw_neu"] += 1
            self.protokoll.append({"art": "anwesenheit_neu", "o11": a["id"], "o18": aid})

        for r in self.fremd:
            modell = "hr.leave" if "request_date_from" in r else "hr.leave.allocation"
            try:
                if r["state"] == "refuse":
                    # Odoo 18 loescht abgelehnte Abwesenheiten nicht - vorher stornieren.
                    c.kw(modell, "write", [[r["id"]], {"state": "cancel"}], context=ctx)
                c.kw(modell, "unlink", [[r["id"]]], context=ctx)
                self.ergebnis["fremd_geloescht"] += 1
                self.protokoll.append({"art": "testdaten_geloescht", "modell": modell, "o18": r["id"]})
            except Exception as exc:  # noqa: BLE001
                self.offen.append("Testdatensatz %s id=%s nicht loeschbar: %s"
                                  % (modell, r["id"], str(exc)[-300:]))

    def lauf(self):
        self.lese()
        self.baue_mapping()
        self.plane()
        self.zeige()
        if not self.schreiben:
            print("\nTrockenlauf - nichts geschrieben. Schreiben mit --ausfuehren --ich-habe-freigabe.")
            return 0
        self.schreibe()
        print("\n=== geschrieben ===")
        for k, v in self.ergebnis.items():
            print("  %-22s %d" % (k, v))
        os.makedirs(PROTO, exist_ok=True)
        import datetime
        ziel = os.path.join(PROTO, "lauf_%s_%s.json" % (self.instanz,
                           datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
        with open(ziel, "w", encoding="utf-8") as fh:
            json.dump({"instanz": self.instanz, "ergebnis": self.ergebnis,
                       "hinweise": self.hinweise, "offen": self.offen,
                       "protokoll": self.protokoll}, fh,
                      ensure_ascii=False, indent=1, default=str)
        print("  Protokoll:", ziel)
        if self.offen:
            print("\n=== offene Punkte ===")
            for o in self.offen:
                print("  -", o)
            return 1
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    a = ap.parse_args()
    if a.ausfuehren and not a.ich_habe_freigabe:
        print("Schreiben nur mit --ausfuehren --ich-habe-freigabe")
        return 2
    return Lauf(a.instanz, a.ausfuehren).lauf()


if __name__ == "__main__":
    sys.exit(main())
