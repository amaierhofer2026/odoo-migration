"""Datenmigration PERSONAL: Odoo 11 (Produktiv, read-only) -> Odoo 18.

Standard ist der TROCKENLAUF (keine Schreibzugriffe). Schreiben nur mit
    --ausfuehren --ich-habe-freigabe

 Aufruf:
    python scripts/hr_migration.py --instanz lokal
    python scripts/hr_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe

Regeln (Anna, 21.10.2026):
  * Odoo 11 wird ausschliesslich gelesen.
  * Ziel nur die Testdatenbank (ODOO18_DB muss auf odoo18_test enden).
  * Zuordnung ueber fachliche Schluessel (Arbeits-E-Mail, dann Name), nie ueber IDs.
  * Bei Mehrdeutigkeit Abbruch mit Klartext, kein Raten, kein stilles Ueberspringen.
  * Protokoll ausserhalb des Repos (%LOCALAPPDATA%\\Temp\\hr_migration\\).

Umfang (Entscheidungen Anna): Mitarbeiter samt Beziehungen, 9 Arbeitszeitmodelle,
Arbeitsorte, 28->21 Urlaubsarten (1:1 nach bereinigtem Namen), 69 Urlaubsansprueche,
482 Urlaubsantraege, 192 Anwesenheiten. Keine Zeiterfassung (Projektbereich).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "hr_migration")


class Blocker(Exception):
    pass


def norm_email(wert):
    return (wert or "").strip().lower()


def norm_name(wert):
    return " ".join((wert or "").split()).lower()


def norm_typ(wert):
    return " ".join((wert or "").split())


class Migration:
    def __init__(self, instanz: str, schreiben: bool):
        self.k11 = o11()
        self.k18 = o18(instanz)
        self.instanz = instanz
        self.schreiben = schreiben
        self.protokoll = []
        self.blocker = []
        self.fehler_ansprueche = []
        self.hinweise = []
        self.zahlen = {}

    # ------------------------------------------------------------------ lesen
    def lese_o11(self):
        k = self.k11
        ctx = dict(CTX, active_test=False)
        self.e11 = k.kw("hr.employee", "read",
                        [k.kw("hr.employee", "search", [[]], context=ctx, order="id"),
                         ["id", "name", "firstname", "lastname", "active", "gender", "marital",
                          "birthday", "country_id", "identification_id", "passport_id", "visa_no",
                          "permit_no", "visa_expire", "sinid", "ssnid", "bank_account_id",
                          "address_id", "address_home_id", "work_email", "work_phone",
                          "mobile_phone", "work_location", "notes", "barcode", "pin",
                          "department_id", "job_id", "parent_id", "coach_id", "user_id",
                          "company_id", "resource_calendar_id", "category_ids", "create_date"]],
                        context=ctx)
        self.abt11 = k.kw("hr.department", "search_read", [[]], fields=["id", "name"],
                          context=ctx)
        self.stellen11 = k.kw("hr.job", "search_read", [[]], fields=["id", "name"], context=ctx)
        self.tags11 = k.kw("hr.employee.category", "search_read", [[]], fields=["id", "name"],
                           context=ctx)
        self.kal11 = k.kw("resource.calendar", "search_read", [[]],
                          fields=["id", "name", "tz", "company_id"], context=ctx)
        self.zeiten11 = k.kw("resource.calendar.attendance", "search_read", [[]],
                             fields=["calendar_id", "name", "dayofweek", "hour_from", "hour_to",
                                     "day_period"], context=ctx,
                             order="calendar_id,dayofweek,hour_from")
        self.typen11 = k.kw("hr.holidays.status", "search_read", [[]],
                            fields=["id", "name", "limit", "color_name"], context=ctx)
        self.ansprueche11 = k.kw("hr.holidays", "search_read", [[("type", "=", "add")]],
                                 fields=["id", "name", "employee_id", "holiday_status_id",
                                         "number_of_days_temp", "state", "holiday_type",
                                         "create_date"], context=ctx, order="id")
        self.antraege11 = k.kw("hr.holidays", "search_read", [[("type", "=", "remove")]],
                               fields=["id", "name", "employee_id", "holiday_status_id",
                                       "date_from", "date_to", "number_of_days_temp", "state",
                                       "holiday_type"], context=ctx, order="id")
        self.anw11 = k.kw("hr.attendance", "search_read", [[]],
                          fields=["id", "employee_id", "check_in", "check_out"], context=ctx,
                          order="check_in,id")
        self.benutzer11 = k.kw("res.users", "search_read", [[]],
                               fields=["id", "login", "name", "active"], context=ctx)

    def lese_o18(self):
        k = self.k18
        ctx = dict(CTX, active_test=False)
        self.e18 = k.kw("hr.employee", "search_read", [[]],
                        fields=["id", "name", "firstname", "lastname", "active", "gender",
                                "marital", "birthday", "country_id", "address_id", "work_email",
                                "work_phone", "mobile_phone", "work_location_id", "notes",
                                "barcode", "pin", "department_id", "job_id", "parent_id",
                                "coach_id", "user_id", "company_id", "resource_calendar_id",
                                "category_ids"], context=ctx, order="id")
        self.abt18 = k.kw("hr.department", "search_read", [[]], fields=["id", "name"], context=ctx)
        self.stellen18 = k.kw("hr.job", "search_read", [[]], fields=["id", "name"], context=ctx)
        self.tags18 = k.kw("hr.employee.category", "search_read", [[]], fields=["id", "name"],
                           context=ctx)
        self.kal18 = k.kw("resource.calendar", "search_read", [[]],
                          fields=["id", "name", "company_id"], context=ctx)
        self.orte18 = k.kw("hr.work.location", "search_read", [[]],
                           fields=["id", "name", "location_type", "address_id"], context=ctx)
        self.typen18 = k.kw("hr.leave.type", "search_read", [[]],
                            fields=["id", "name", "requires_allocation"], context=ctx)
        self.benutzer18 = k.kw("res.users", "search_read", [[]],
                               fields=["id", "login", "name", "active"], context=ctx)
        self.firmen18 = k.kw("res.company", "search_read", [[]],
                             fields=["id", "name", "partner_id"], context=ctx)
        self.partner18 = k.kw("res.partner", "search_read", [[]], fields=["id", "name"],
                              context=ctx)

    # ---------------------------------------------------------------- helfen
    @staticmethod
    def genau_einer(treffer, was):
        treffer = list(treffer)
        if len(treffer) == 1:
            return treffer[0]
        if not treffer:
            raise Blocker("%s: kein Treffer" % was)
        raise Blocker("%s: %d Treffer %s" % (was, len(treffer), treffer[:5]))

    def nach_name(self, liste, name, was):
        gesucht = norm_name(name)
        treffer = [x for x in liste if norm_name(x["name"]) == gesucht]
        if len(treffer) == 1:
            return treffer[0]["id"]
        if not treffer:
            return None
        raise Blocker("%s '%s': %d gleichnamige Datensaetze" % (was, name, len(treffer)))

    # ---------------------------------------------------------------- planen
    def plane(self):
        # 1. Arbeitszeitmodelle: Odoo 11 hat 9 Modelle, davon zwei mit identischem Namen
        #    UND identischen Zeiten (IDs 4 und 7) -> diese werden zu EINEM Modell.
        #    Gruppe = (Name, Zeitsignatur); Null-Zeilen (0-0) werden nicht uebernommen.
        def signatur(zeiten):
            return tuple(sorted((int(z["dayofweek"]), z["hour_from"], z["hour_to"])
                                for z in zeiten if z["hour_to"] > z["hour_from"]))

        gruppen, reihenfolge = {}, []
        for kal in self.kal11:
            zeiten = [z for z in self.zeiten11
                      if z["calendar_id"] and z["calendar_id"][0] == kal["id"]]
            schluessel = (norm_name(kal["name"]), signatur(zeiten))
            if schluessel not in gruppen:
                gruppen[schluessel] = {"name": kal["name"], "tz": kal.get("tz") or "Europe/Vienna",
                                       "zeiten": zeiten, "o11_ids": [], "o18_id": None,
                                       "neu": True, "signatur": schluessel[1]}
                reihenfolge.append(schluessel)
            gruppen[schluessel]["o11_ids"].append(kal["id"])
        self.kalender_gruppen = [gruppen[k] for k in reihenfolge]

        # vorhandene Odoo-18-Modelle gleichen Namens zuordnen (auch mit abweichenden Zeiten -
        # die Zeiten werden spaeter angeglichen)
        for g in self.kalender_gruppen:
            treffer = [k for k in self.kal18 if norm_name(k["name"]) == norm_name(g["name"])]
            if treffer:
                g["o18_id"] = min(k["id"] for k in treffer)
                g["neu"] = False
        # doppelte Odoo-18-Modelle gleichen Namens (aus einem früheren Lauf) zusammenführen
        self.kalender_dubletten = []
        for g in self.kalender_gruppen:
            gleiche = [k for k in self.kal18 if norm_name(k["name"]) == norm_name(g["name"])
                       and g["o18_id"] and k["id"] != g["o18_id"]]
            for k in gleiche:
                self.kalender_dubletten.append({"quelle": k["id"], "ziel": g["o18_id"],
                                                "name": k["name"]})

        # Odoo-11-Kalender -> Odoo-18-Modell (fuer die Mitarbeiterzuordnung)
        # Referenz auf die Gruppe (nicht auf eine Kopie), damit die beim Anlegen
        # vergebene Odoo-18-ID auch fuer die Mitarbeiterzuordnung gilt.
        self.kalender_map = {}
        for g in self.kalender_gruppen:
            for o11_id in g["o11_ids"]:
                self.kalender_map[o11_id] = g

        # 2. Arbeitsorte aus den O11-Texten
        texte = {}
        for m in self.e11:
            if m.get("work_location"):
                text = " ".join(m["work_location"].split())
                # Adressvariante "A-1210" und "1210" bezeichnen dieselbe Adresse
                text = re.sub(r"\bA-(\d{4})\b", r"\1", text)
                texte.setdefault(text, []).append(m["id"])
        self.orte_plan = []
        for text, ids in texte.items():
            ziel_name = text
            typ = "home" if "home" in text.lower() else "office"
            vorhanden = [o for o in self.orte18 if norm_name(o["name"]) == norm_name(ziel_name)]
            self.orte_plan.append({"text": text, "name": ziel_name, "typ": typ,
                                   "mitarbeiter_o11": ids,
                                   "o18_id": vorhanden[0]["id"] if len(vorhanden) == 1 else None,
                                   "neu": not vorhanden})

        # 3. Urlaubsarten: 1:1 nach bereinigtem Namen (Leerzeichen normalisiert).
        # Mehrere Odoo-11-Eintraege mit gleichem Namen zeigen auf dieselbe Odoo-18-Art.
        namen = {}
        for typ in self.typen11:
            name = norm_typ(typ["name"])
            if name not in namen:
                ziel = None
                for t18 in self.typen18:
                    if norm_typ(t18["name"]) == name:
                        ziel = t18["id"]
                        break
                namen[name] = {"name": name, "neu": ziel is None, "o18_id": ziel,
                               "o11_ids": [], "limit": False}
            namen[name]["o11_ids"].append(typ["id"])
            namen[name]["limit"] = namen[name]["limit"] or bool(typ.get("limit"))
            # Odoo 11 'limit' = Urlaubsanspruch erforderlich; das ist die 1:1-Entsprechung
            # zu Odoo 18 'requires_allocation'.
        self.typen_namen = list(namen.values())
        self.typen_map = {}
        for eintrag in self.typen_namen:
            for o11_id in eintrag["o11_ids"]:
                self.typen_map[o11_id] = eintrag
        self.typen_zusammen = {e["name"]: e["o11_ids"] for e in self.typen_namen
                               if len(e["o11_ids"]) > 1}

        # Gating: Odoo 11 fuehrt 'limit' als Hinweis, hat Antraege ohne Anspruch aber
        # zugelassen (Datenbefund). Odoo 18 blockiert sie hart. Deshalb
        # 'requires_allocation' = 'yes' nur, wenn in Odoo 11 JEDER Antrag dieser Art
        # durch einen persoenlichen Anspruch gedeckt war; sonst 'no'.
        gedeckt = {(a["employee_id"][0], a["holiday_status_id"][0]) for a in self.ansprueche11
                   if a.get("employee_id") and a["state"] in ("validate", "confirm")}
        for eintrag in self.typen_namen:
            ungedeckt = 0
            for antrag in self.antraege11:
                if antrag["holiday_status_id"][0] not in eintrag["o11_ids"]:
                    continue
                if (antrag["employee_id"][0], antrag["holiday_status_id"][0]) not in gedeckt:
                    ungedeckt += 1
            eintrag["ungedeckte_antraege"] = ungedeckt
            eintrag["gating"] = "yes" if (eintrag["limit"] and ungedeckt == 0) else "no"

        # 4. Mitarbeiter zuordnen
        self.email18 = {}
        for e in self.e18:
            em = norm_email(e.get("work_email"))
            if em:
                self.email18.setdefault(em, []).append(e)
        self.name18 = {}
        for e in self.e18:
            self.name18.setdefault(norm_name(e["name"]), []).append(e)

        self.ma_plan = []
        belegt = set()
        for m in self.e11:
            em = norm_email(m.get("work_email"))
            ziel = None
            schluessel = None
            if em and em in self.email18:
                treffer = self.email18[em]
                if len(treffer) != 1:
                    raise Blocker("Arbeits-E-Mail %s bei %d Odoo-18-Mitarbeitern" % (em, len(treffer)))
                ziel = treffer[0]
                schluessel = "arbeits_email"
            elif norm_name(m["name"]) in self.name18:
                treffer = self.name18[norm_name(m["name"])]
                if len(treffer) != 1:
                    raise Blocker("Name '%s' bei %d Odoo-18-Mitarbeitern" % (m["name"], len(treffer)))
                ziel = treffer[0]
                schluessel = "name"
            if ziel is not None:
                if ziel["id"] in belegt:
                    raise Blocker("Odoo-18-Mitarbeiter %s doppelt zugeordnet" % ziel["id"])
                belegt.add(ziel["id"])
            self.ma_plan.append({"o11_id": m["id"], "o11": m, "o18_id": ziel["id"] if ziel else None,
                                 "schluessel": schluessel, "neu": ziel is None})
        self.ma_map = {p["o11_id"]: p for p in self.ma_plan}

        # 5. Anwesenheiten / Ansprueche / Antraege auf Zuordnung pruefen
        self.ohne_ma = [a for a in self.ansprueche11 if not a.get("employee_id")]
        for a in self.anw11 + [x for x in self.antraege11 if x.get("employee_id")] + \
                [x for x in self.ansprueche11 if x.get("employee_id")]:
            eid = a["employee_id"][0]
            if eid not in self.ma_map:
                raise Blocker("Bezug auf unbekannten Odoo-11-Mitarbeiter %s" % eid)

        self.zahlen = {
            "mitarbeiter_o11": len(self.e11),
            "mitarbeiter_o11_aktiv": sum(1 for m in self.e11 if m["active"]),
            "mitarbeiter_o18_vorher": len(self.e18),
            "mitarbeiter_neu": sum(1 for p in self.ma_plan if p["neu"]),
            "mitarbeiter_update": sum(1 for p in self.ma_plan if not p["neu"]),
            "zuordnung_email": sum(1 for p in self.ma_plan if p["schluessel"] == "arbeits_email"),
            "zuordnung_name": sum(1 for p in self.ma_plan if p["schluessel"] == "name"),
            "kalender_neu": sum(1 for k in self.kalender_gruppen if k["neu"]),
            "kalender_vorhanden": sum(1 for k in self.kalender_gruppen if not k["neu"]),
            "orte_neu": sum(1 for o in self.orte_plan if o["neu"]),
            "typen_neu": sum(1 for t in self.typen_namen if t["neu"]),
            "typen_vorhanden": sum(1 for t in self.typen_namen if not t["neu"]),
            "typen_o11": len(self.typen11),
            "typen_o18_namen": len(self.typen_namen),
            "ansprueche": len(self.ansprueche11),
            "ansprueche_ohne_mitarbeiter": len(self.ohne_ma),
            "antraege": len(self.antraege11),
            "anwesenheiten": len(self.anw11),
        }

    def zeige_plan(self):
        z = self.zahlen
        print("=" * 78)
        print("TROCKENLAUF  (keine Schreibzugriffe)  Instanz: %s" % self.instanz)
        print("=" * 78)
        print("Mitarbeiter Odoo 11        : %d (%d aktiv)" % (z["mitarbeiter_o11"],
                                                             z["mitarbeiter_o11_aktiv"]))
        print("Mitarbeiter Odoo 18 vorher : %d" % z["mitarbeiter_o18_vorher"])
        print("  Zuordnung ueber E-Mail   : %d" % z["zuordnung_email"])
        print("  Zuordnung ueber Name     : %d" % z["zuordnung_name"])
        print("  zu aktualisieren         : %d" % z["mitarbeiter_update"])
        print("  neu anzulegen            : %d" % z["mitarbeiter_neu"])
        print("Arbeitszeitmodelle         : %d neu, %d vorhanden" % (z["kalender_neu"],
                                                                    z["kalender_vorhanden"]))
        print("Arbeitsorte                : %d neu" % z["orte_neu"])
        print("Urlaubsarten               : %d Odoo-11-Eintraege -> %d Namen (%d neu, %d vorhanden)"
              % (z["typen_o11"], z["typen_o18_namen"], z["typen_neu"], z["typen_vorhanden"]))
        print("Urlaubsansprueche          : %d (davon %d ohne Mitarbeiter - nicht migrierbar)"
              % (z["ansprueche"], z["ansprueche_ohne_mitarbeiter"]))
        print("Urlaubsantraege            : %d" % z["antraege"])
        print("Anwesenheiten              : %d" % z["anwesenheiten"])
        if self.typen_zusammen:
            print("\nUrlaubsarten mit mehreren Odoo-11-Eintraegen (werden zusammengefuehrt):")
            for name, ids in sorted(self.typen_zusammen.items()):
                print("  %-60s O11-IDs %s" % (name[:60], ids))
        if self.orte_plan:
            print("\nArbeitsorte aus Odoo-11-Texten:")
            for o in self.orte_plan:
                print("  %-40s Typ %-7s O18-ID %-5s Mitarbeiter O11 %s"
                      % (o["text"], o["typ"], o["o18_id"], o["mitarbeiter_o11"]))
        print("\nMitarbeiter im Einzelnen:")
        for p in self.ma_plan:
            m = p["o11"]
            print("  O11 %-3s -> O18 %-4s %-32s %-9s %s" % (
                p["o11_id"], p["o18_id"] or "neu", (m["name"] or "")[:32],
                p["schluessel"] or "neu",
                "aktiv" if m["active"] else "archiviert"))
        if self.blocker:
            print("\nBLOCKER:")
            for b in self.blocker:
                print("  - %s" % b)

    # --------------------------------------------------------------- schreiben
    def schreibe(self):
        if not self.schreiben:
            return
        k = self.k18
        env = lade_env()
        if not env.get("ODOO18_DB", "").endswith("odoo18_test"):
            raise SystemExit("ABBRUCH: Ziel-DB ist nicht odoo18_test")

        # Vor dem ersten Schreibzugriff alle Mitarbeiterwerte bilden: eine mehrdeutige
        # Zuordnung bricht damit ab, BEVOR irgendetwas geschrieben wurde.
        for p in self.ma_plan:
            p["vals"] = self._vals_mitarbeiter(p)

        # Arbeitszeitmodelle anlegen und Zeiten exakt auf Odoo 11 setzen
        for kal in self.kalender_gruppen:
            if kal["neu"]:
                kal["o18_id"] = k.kw("resource.calendar", "create", [{
                    "name": kal["name"],
                    "tz": kal["tz"],
                    "company_id": 1,
                }])
                self.protokoll.append({"modell": "resource.calendar", "id": kal["o18_id"],
                                       "schluessel": kal["name"], "neu": True})
            else:
                # Name in der Odoo-11-Schreibweise (z. B. "Standard 40 Hours/Week")
                ist_name = k.kw("resource.calendar", "read", [[kal["o18_id"]], ["name"]],
                                context=CTX)[0]["name"]
                if ist_name != kal["name"]:
                    k.kw("resource.calendar", "write", [[kal["o18_id"]], {"name": kal["name"]}])
                    self.protokoll.append({"modell": "resource.calendar", "id": kal["o18_id"],
                                           "name": kal["name"], "umbenannt": ist_name})
            ist = k.kw("resource.calendar.attendance", "search_read",
                       [[("calendar_id", "=", kal["o18_id"])]],
                       fields=["id", "dayofweek", "hour_from", "hour_to"], context=CTX)
            ist_sig = tuple(sorted((int(z["dayofweek"]), z["hour_from"], z["hour_to"]) for z in ist))
            if ist_sig != kal["signatur"]:
                if ist:
                    k.kw("resource.calendar.attendance", "unlink", [[z["id"] for z in ist]])
                for z in kal["zeiten"]:
                    if z["hour_to"] <= z["hour_from"]:
                        continue              # Null-Zeile aus Odoo 11 nicht uebernehmen
                    von, bis = z["hour_from"], z["hour_to"]
                    periode = ("lunch" if von >= 12.0 and bis <= 13.0
                               else "morning" if von < 12.0 else "afternoon")
                    k.kw("resource.calendar.attendance", "create", [{
                        "calendar_id": kal["o18_id"],
                        "name": z.get("name") or "Arbeitszeit",
                        "dayofweek": z["dayofweek"],
                        "hour_from": von,
                        "hour_to": bis,
                        "day_period": periode,
                    }])
                self.protokoll.append({"modell": "resource.calendar.attendance",
                                       "calendar": kal["name"], "zeiten": len(kal["zeiten"])})
        # doppelte Modelle gleichen Namens: Mitarbeiter umhaengen, Dublette entfernen
        for dub in self.kalender_dubletten:
            k.kw("hr.employee", "write",
                 [k.kw("hr.employee", "search", [[("resource_calendar_id", "=", dub["quelle"])]],
                       context=dict(CTX, active_test=False)), {"resource_calendar_id": dub["ziel"]}])
            k.kw("resource.calendar", "unlink", [[dub["quelle"]]])
            self.protokoll.append({"modell": "resource.calendar", "id": dub["quelle"],
                                   "schluessel": dub["name"], "entfernt": "Dublette"})

        # Arbeitsorte
        firma = self.firmen18[0] if self.firmen18 else {"partner_id": [1, ""]}
        for ort in self.orte_plan:
            if ort["neu"]:
                ort["o18_id"] = k.kw("hr.work.location", "create", [{
                    "name": ort["name"],
                    "location_type": ort["typ"],
                    "address_id": firma["partner_id"][0],
                    "company_id": 1,
                }])
                self.protokoll.append({"modell": "hr.work.location", "id": ort["o18_id"],
                                       "schluessel": ort["name"], "neu": True})

        # Urlaubsarten (je bereinigtem Namen eine Odoo-18-Art)
        for typ in self.typen_namen:
            if typ["neu"]:
                typ["o18_id"] = k.kw("hr.leave.type", "create", [{
                    "name": typ["name"],
                    "request_unit": "day",
                    "requires_allocation": typ["gating"],
                    "leave_validation_type": "hr",
                    "allocation_validation_type": "hr",
                    "employee_requests": "yes",
                    "allows_negative": True,
                    "max_allowed_negative": 100,
                    "show_on_dashboard": True,
                }])
                self.protokoll.append({"modell": "hr.leave.type", "id": typ["o18_id"],
                                       "schluessel": typ["name"], "neu": True})

        # Bereits frueher angelegte ITK-Urlaubsarten (id > 6 = nicht Odoo-Standard):
        # Gating aus Odoo 11 ('limit') nachziehen, solange Odoo es noch zulaesst.
        # Odoo verbietet die Aenderung, sobald Urlaube dieser Art existieren.
        for typ in self.typen_namen:
            if typ["o18_id"] and typ["o18_id"] > 6:
                soll = typ["gating"]
                ist = k.kw("hr.leave.type", "read", [[typ["o18_id"]], ["requires_allocation"]],
                           context=CTX)[0]["requires_allocation"]
                if ist == soll:
                    continue
                try:
                    k.kw("hr.leave.type", "write", [[typ["o18_id"]],
                                                    {"requires_allocation": soll}])
                    self.protokoll.append({"modell": "hr.leave.type", "id": typ["o18_id"],
                                           "requires_allocation": soll})
                except Exception as exc:  # noqa: BLE001
                    if "kann nicht mehr ge" in str(exc) or "cannot be changed" in str(exc):
                        self.hinweise.append("requires_allocation von '%s' bleibt %s "
                                             "(Odoo erlaubt keine Aenderung mehr)"
                                             % (typ["name"], ist))
                    else:
                        raise

        # Mitarbeiter: erst alle Felder ohne parent_id
        for p in self.ma_plan:
            vals = self._vals_mitarbeiter(p)
            p["vals"] = vals
            if p["neu"]:
                p["o18_id"] = k.kw("hr.employee", "create", [vals])
                self.protokoll.append({"modell": "hr.employee", "id": p["o18_id"],
                                       "schluessel": p["o11"]["name"], "neu": True})
            else:
                k.kw("hr.employee", "write", [[p["o18_id"]], vals])
                self.protokoll.append({"modell": "hr.employee", "id": p["o18_id"],
                                       "schluessel": p["o11"]["name"], "neu": False})

        # zweite Phase: Vorgesetzte
        for p in self.ma_plan:
            eltern = p["o11"].get("parent_id")
            ziel = self.ma_map[eltern[0]]["o18_id"] if eltern else False
            if ziel is None:
                raise Blocker("Vorgesetzter fuer %s noch nicht angelegt" % p["o11"]["name"])
            k.kw("hr.employee", "write", [[p["o18_id"]], {"parent_id": ziel}])

        if getattr(self, "ohne_belegdaten", False):
            self.protokoll.append({"modell": "belegdaten", "uebersprungen": "Stammdatenlauf"})
            return

        # Anwesenheiten
        angelegt = 0
        for a in self.anw11:
            eid = self.ma_map[a["employee_id"][0]]["o18_id"]
            vorhanden = k.kw("hr.attendance", "search_count",
                             [[("employee_id", "=", eid), ("check_in", "=", a["check_in"])]])
            if vorhanden:
                continue
            k.kw("hr.attendance", "create", [{
                "employee_id": eid,
                "check_in": a["check_in"],
                "check_out": a.get("check_out") or False,
            }])
            angelegt += 1
        self.protokoll.append({"modell": "hr.attendance", "anzahl": angelegt, "neu": True})

        # Urlaubsansprueche (nur mit Mitarbeiter)
        angelegt, uebersprungen = 0, 0
        ohne_tage = []
        for a in self.ansprueche11:
            if not a.get("employee_id"):
                uebersprungen += 1
                continue
            eid = self.ma_map[a["employee_id"][0]]["o18_id"]
            typ = self.typen_map[a["holiday_status_id"][0]]
            tage = a.get("number_of_days_temp") or 0.0
            if tage <= 0:
                ohne_tage.append(a["id"])
                continue
            vorhanden = k.kw("hr.leave.allocation", "search_count",
                             [[("employee_id", "=", eid), ("holiday_status_id", "=", typ["o18_id"]),
                               ("number_of_days", "=", tage)]])
            if vorhanden:
                continue
            try:
                aid = k.kw("hr.leave.allocation", "create", [{
                    "employee_id": eid,
                    "holiday_status_id": typ["o18_id"],
                    "number_of_days": tage,
                    "date_from": self._anspruch_start(a, eid),
                    "name": a.get("name") or typ["name"],
                }])
                ziel = a.get("state") if a.get("state") in ("validate", "refuse", "confirm") else "validate"
                k.kw("hr.leave.allocation", "write", [[aid], {"state": ziel}])
                angelegt += 1
            except Exception as exc:  # noqa: BLE001
                self.fehler_ansprueche.append((a["id"], typ["name"], str(exc)[-300:]))
        self.protokoll.append({"modell": "hr.leave.allocation", "anzahl": angelegt,
                               "uebersprungen": uebersprungen,
                               "ohne_tage": ohne_tage,
                               "fehler": len(self.fehler_ansprueche)})

        # Urlaubsantraege
        angelegt, fehler = 0, []
        zustand = {"validate": "validate", "refuse": "refuse", "confirm": "confirm"}
        for a in self.antraege11:
            eid = self.ma_map[a["employee_id"][0]]["o18_id"]
            typ = self.typen_map[a["holiday_status_id"][0]]
            von = (a.get("date_from") or "")[:10]
            bis = (a.get("date_to") or "")[:10]
            if not von or not bis:
                fehler.append((a["id"], "ohne Datum"))
                continue
            vorhanden = k.kw("hr.leave", "search_count",
                             [[("employee_id", "=", eid), ("holiday_status_id", "=", typ["o18_id"]),
                               ("request_date_from", "=", von), ("request_date_to", "=", bis)]])
            if vorhanden:
                continue
            try:
                # Kontrollierte Ausnahme NUR fuer die Migration historischer Daten:
                # Odoo 11 erlaubte ueberschneidende Antraege, Odoo 18 nicht. Der
                # Kontextschalter wirkt ausschliesslich in diesem einen Aufruf.
                lid = k.kw("hr.leave", "create", [{
                    "employee_id": eid,
                    "holiday_status_id": typ["o18_id"],
                    "request_date_from": von,
                    "request_date_to": bis,
                    "name": a.get("name") or typ["name"],
                }], context=dict(CTX, leave_skip_date_check=True))
                ziel_state = zustand.get(a["state"], "confirm")
                if ziel_state != "draft":
                    k.kw("hr.leave", "write", [[lid], {"state": ziel_state}])
                angelegt += 1
            except Exception as exc:  # noqa: BLE001
                fehler.append((a["id"], str(exc)[:120]))
        self.protokoll.append({"modell": "hr.leave", "anzahl": angelegt,
                               "fehler": len(fehler), "fehlerliste": fehler[:20]})
        self.fehler = fehler

    def _anspruch_start(self, a, o18_employee_id):
        """Fruehestes belegtes Datum fuer Mitarbeiter + Urlaubsart: Anspruchsdatum in Odoo 11
        oder - falls frueher - das Datum des fruehesten Antrags dieser Art."""
        kandidaten = []
        if a.get("create_date"):
            kandidaten.append(a["create_date"][:10])
        typ_o11 = a["holiday_status_id"][0]
        for antrag in self.antraege11:
            if antrag["holiday_status_id"][0] == typ_o11 and \
                    self.ma_map[antrag["employee_id"][0]]["o18_id"] == o18_employee_id:
                if antrag.get("date_from"):
                    kandidaten.append(antrag["date_from"][:10])
        if not kandidaten:
            return "2000-01-01"
        return min(kandidaten)

    def _hat_anspruch(self, o11_typ_ids):
        return any(a.get("holiday_status_id") and a["holiday_status_id"][0] in o11_typ_ids
                   for a in self.ansprueche11)

    def _vals_mitarbeiter(self, p):
        m = p["o11"]
        vals = {
            "firstname": m.get("firstname") or False,
            "lastname": m.get("lastname") or False,
            "active": bool(m["active"]),
            "gender": m.get("gender") or False,
            "marital": m.get("marital") or "single",
            "work_email": m.get("work_email") or False,
            "work_phone": m.get("work_phone") or False,
            "mobile_phone": m.get("mobile_phone") or False,
            "barcode": m.get("barcode") or False,
            "pin": m.get("pin") or False,
            "notes": m.get("notes") or False,
            "coach_id": False,
            "company_id": 1,
        }
        if m.get("birthday"):
            vals["birthday"] = m["birthday"]
        if m.get("country_id"):
            vals["country_id"] = self._land(m["country_id"])
        if m.get("identification_id"):
            vals["identification_id"] = m["identification_id"]
        # Arbeitsadresse (Partner ueber fachlichen Namen)
        if m.get("address_id"):
            vals["address_id"] = self._partner(m["address_id"])
        # Abteilung / Stelle / Tags / Arbeitsort / Kalender
        if m.get("department_id"):
            ziel = self.nach_name(self.abt18, m["department_id"][1], "Abteilung")
            if ziel is None:
                raise Blocker("Abteilung '%s' fehlt in Odoo 18" % m["department_id"][1])
            vals["department_id"] = ziel
        else:
            vals["department_id"] = False
        if m.get("job_id"):
            ziel = self.nach_name(self.stellen18, m["job_id"][1], "Stelle")
            if ziel is None:
                raise Blocker("Stelle '%s' fehlt in Odoo 18" % m["job_id"][1])
            vals["job_id"] = ziel
        else:
            vals["job_id"] = False
        if m.get("resource_calendar_id"):
            vals["resource_calendar_id"] = self.kalender_map[m["resource_calendar_id"][0]]["o18_id"]
        if m.get("category_ids"):
            tag_ids = []
            for tag_id in m["category_ids"]:
                name = next((t["name"] for t in self.tags11 if t["id"] == tag_id), None)
                ziel = self.nach_name(self.tags18, name, "Stichwort") if name else None
                if ziel is None:
                    raise Blocker("Stichwort '%s' fehlt in Odoo 18" % name)
                tag_ids.append(ziel)
            vals["category_ids"] = [(6, 0, tag_ids)]
        else:
            vals["category_ids"] = [(6, 0, [])]
        if m.get("work_location"):
            text = re.sub(r"\bA-(\d{4})\b", r"\1", " ".join(m["work_location"].split()))
            ort = next((o for o in self.orte_plan if o["text"] == text), None)
            if ort is None:
                raise Blocker("Arbeitsort '%s' nicht im Plan" % text)
            vals["work_location_id"] = ort["o18_id"]
        else:
            vals["work_location_id"] = False
        # Benutzer: nur verknuepfen, wenn es den Odoo-18-Benutzer gibt (Entscheidung Anna)
        vals["user_id"] = self._benutzer(m)
        return vals

    def _land(self, land):
        code = None
        try:
            daten = self.k11.kw("res.country", "read", [[land[0]], ["code"]], context=CTX)
            code = daten[0]["code"]
        except Exception:  # noqa: BLE001
            code = None
        if code:
            treffer = self.k18.kw("res.country", "search", [[("code", "=", code)]], context=CTX)
            if len(treffer) == 1:
                return treffer[0]
        raise Blocker("Land '%s' nicht eindeutig in Odoo 18" % (land[1],))

    def _partner(self, partner):
        """Arbeitsadresse: Odoo-11-Partner auf Odoo-18-Partner abbilden.
        Firmenadresse -> Firmenpartner; sonst ueber den bereinigten Namen."""
        pid, pname = partner
        firma = self.firmen18[0]["partner_id"][0] if self.firmen18 else None
        name = pname or ""
        ist_firma = name.startswith("[ITK] ") or name.endswith("[ITK] IT-Kommunal GmbH")
        if ist_firma and firma:
            return firma
        bereinigt = name.split(" - [ITK]")[0].replace("[ITK]", "").strip()
        treffer = [x for x in self.partner18 if norm_name(x["name"]) == norm_name(bereinigt)]
        if len(treffer) == 1:
            return treffer[0]["id"]
        if firma:
            self.blocker.append("Arbeitsadresse '%s' nicht eindeutig - Firmenadresse verwendet"
                                % name)
            return firma
        raise Blocker("Arbeitsadresse '%s' nicht aufloesbar" % name)

    def _benutzer(self, m):
        """Benutzer nur verknuepfen, wenn es ihn in Odoo 18 gibt (Entscheidung Anna).
        Reihenfolge: Name, Login, bestehende Verknuepfung des zugeordneten Mitarbeiters.
        Benutzer, die schon zu einem ANDEREN Mitarbeiter gehoeren, sind ausgeschlossen
        (sonst ValidationError 'Benutzer ist bereits verknuepft')."""
        if not m.get("user_id"):
            return False
        b11 = next((b for b in self.benutzer11 if b["id"] == m["user_id"][0]), None)
        if not b11:
            return False
        plan = self.ma_map.get(m["id"])
        eigener_mitarbeiter = plan["o18_id"] if plan else None
        belegt = {}
        for e in self.e18:
            if e.get("user_id"):
                belegt[e["user_id"][0]] = e["id"]
        kandidaten = [b for b in self.benutzer18
                      if belegt.get(b["id"]) in (None, eigener_mitarbeiter)]
        for b in kandidaten:
            if norm_name(b["name"]) == norm_name(b11["name"]):
                return b["id"]
        for b in kandidaten:
            if norm_email(b["login"]) == norm_email(b11["login"]):
                return b["id"]
        if plan and plan["o18_id"]:
            e = next((x for x in self.e18 if x["id"] == plan["o18_id"]), None)
            if e and e.get("user_id"):
                return e["user_id"][0]
        return False

    # ------------------------------------------------------------------ lauf
    def lauf(self):
        self.lese_o11()
        self.lese_o18()
        self.plane()
        self.zeige_plan()
        if self.blocker:
            print("\nABBRUCH: Blocker vorhanden, es wird nichts geschrieben.")
            return 2
        if not self.schreiben:
            print("\nTrockenlauf beendet - keine Aenderung in Odoo 18.")
            return 0
        print("\n>>> SCHREIBLAUF <<<")
        self.schreibe()
        os.makedirs(PROTO, exist_ok=True)
        pfad = os.path.join(PROTO, "protokoll_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
        with open(pfad, "w", encoding="utf-8") as fh:
            json.dump({"zahlen": self.zahlen, "protokoll": self.protokoll}, fh,
                      ensure_ascii=False, indent=1, default=str)
        print("Protokoll: %s" % pfad)
        print("Neu angelegt / aktualisiert:")
        for eintrag in self.protokoll:
            print("  %-24s %s" % (eintrag["modell"], {k: v for k, v in eintrag.items()
                                                      if k != "modell"}))
        for h in self.hinweise:
            print("  HINWEIS: %s" % h)
        if self.fehler_ansprueche:
            print("\nFEHLER bei %d Urlaubsanspruechen:" % len(self.fehler_ansprueche))
            for fid, name, text in self.fehler_ansprueche[:20]:
                print("  O11-ID %s (%s): %s" % (fid, name, text))
        if getattr(self, "fehler", None):
            print("\nFEHLER bei %d Urlaubsantraegen:" % len(self.fehler))
            for fid, text in self.fehler[:20]:
                print("  O11-ID %s: %s" % (fid, text))
        return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--ausfuehren", action="store_true")
    p.add_argument("--ich-habe-freigabe", action="store_true")
    p.add_argument("--ohne-belegdaten", action="store_true",
                   help="nur Stammdaten und Mitarbeiter abgleichen (keine Anwesenheiten/Urlaube)")
    a = p.parse_args()
    schreiben = a.ausfuehren and a.ich_habe_freigabe
    if a.ausfuehren and not a.ich_habe_freigabe:
        raise SystemExit("--ausfuehren verlangt zusaetzlich --ich-habe-freigabe")
    m = Migration(a.instanz, schreiben)
    m.ohne_belegdaten = a.ohne_belegdaten
    try:
        return m.lauf()
    except Blocker as exc:
        print("BLOCKER: %s" % exc)
        print("Es wurde nichts geschrieben.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
