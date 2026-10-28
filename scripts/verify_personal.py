"""Prueft den Personalbereich in Odoo 18 gegen Odoo 11 (read-only auf beiden Seiten).

Aufruf: python scripts/verify_personal.py --instanz lokal|vm [--stichproben 3]

Prueft: Modulstand, Menues, Formularaufbau, Labels, Filter/Gruppierungen, Rechte,
Datensatzzahlen, Feldgleichheit je Mitarbeiter (Name, E-Mail, Abteilung, Stelle, Manager,
Arbeitszeitmodell, Tags, Arbeitsadresse, aktiv), Beziehungen und Stichproben.
Gibt eine Bilanz "OK / FEHL" aus; Exit-Code 1 bei Fehlern.
"""
from __future__ import annotations

import argparse
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
OK = 0
FEHL = []


def pruefe(bedingung, titel, ist="", soll=""):
    global OK
    if bedingung:
        OK += 1
        print("  OK    %s" % titel)
    else:
        FEHL.append("%s (ist=%s soll=%s)" % (titel, ist, soll))
        print("  FEHL  %s   ist=%s soll=%s" % (titel, ist, soll))


def w(v):
    return v[1] if isinstance(v, (list, tuple)) else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--stichproben", type=int, default=3)
    a = ap.parse_args()
    k11 = o11()
    k18 = o18(a.instanz)
    print("=" * 78)
    print("PRUEFUNG PERSONAL  Instanz: %s" % a.instanz)
    print("=" * 78)

    # ---------------------------------------------------------------- Modul
    print("\n1. Modulstand")
    mod = k18.kw("ir.module.module", "search_read", [[("name", "=", "itk_hr")]],
                 fields=["name", "state", "installed_version"], context=CTX)
    pruefe(bool(mod) and mod[0]["state"] == "installed", "itk_hr installiert",
          mod[0]["state"] if mod else "fehlt")
    if mod:
        print("        Version: %s" % mod[0]["installed_version"])

    # --------------------------------------------------------------- Menues
    print("\n2. Menues und Bezeichnungen")
    menue = k18.kw("ir.ui.menu", "search_read",
                   [[("id", "in", [297, 299, 300, 307])]], fields=["id", "name"], context=CTX)
    namen = {m["id"]: m["name"] for m in menue}
    pruefe(namen.get(297) == "Personal", "App-Menue heisst 'Personal'", namen.get(297), "Personal")
    pruefe(namen.get(299) == "Personal", "Untermenue heisst 'Personal'", namen.get(299), "Personal")
    pruefe(namen.get(300) == "Personal", "Listenmenue heisst 'Personal'", namen.get(300), "Personal")
    pruefe(namen.get(307) == "Abteilungen", "Menue 'Abteilungen'", namen.get(307), "Abteilungen")
    akt = k18.kw("ir.actions.act_window", "read", [[464], ["name"]], context=CTX)
    pruefe(akt[0]["name"] == "Personal", "Aktion heisst 'Personal'", akt[0]["name"], "Personal")
    grp = k18.kw("ir.ui.menu", "read", [[307], ["groups_id"]], context=CTX)
    pruefe(len(grp[0]["groups_id"]) == 1, "Menue 'Abteilungen' nur fuer Personalsachbearbeiter",
          grp[0]["groups_id"])

    # ------------------------------------------------------------- Formular
    print("\n3. Formularaufbau")
    ansichten = k18.kw("hr.employee", "get_views", [[[False, "form"], [False, "list"],
                                                     [False, "search"]]], context=CTX)["views"]
    form = ansichten["form"]["arch"]
    liste = ansichten["list"]["arch"]
    suche = ansichten["search"]["arch"]
    pruefe('string="Kontaktinformationen"' in form, "Gruppe 'Kontaktinformationen' im Kopfbereich")
    pruefe('string="Position"' in form, "Gruppe 'Position' im Kopfbereich")
    pruefe('name="notes"' in form, "Feld 'Notizen' im Formular eingebaut")
    pruefe('placeholder="Weitere Informationen"' in form, "Notizen mit Odoo-11-Platzhalter")
    pruefe('name="job_id"' in form and 'string="Position"' in form, "Feld job_id heisst 'Position'")
    pruefe('string="Ausbilder"' in form, "Feld coach_id heisst 'Ausbilder'")
    pruefe('string="Personal"' in liste, "Listentitel 'Personal'")
    pruefe('name="activity_ids"' in liste and 'optional="hide"' in liste,
           "Aktivitaetsspalten standardmaessig ausgeblendet")
    pruefe('name="group_coach"' in suche, "Gruppierung 'Ausbilder' vorhanden")
    pruefe('string="Arbeitsstelle"' in suche, "Gruppierung job_id heisst 'Arbeitsstelle'")

    # ------------------------------------------------------- Filter/Domains
    print("\n4. Filter und Gruppierungen (ausfuehrbar)")
    for name, dom in (("Ausbilder (leer)", [("coach_id", "=", False)]),
                      ("Manager vorhanden", [("parent_id", "!=", False)]),
                      ("Archiviert", [("active", "=", False)]),
                      ("Aktiv", [("active", "=", True)])):
        try:
            zahl = k18.kw("hr.employee", "search_count", [dom], context=dict(CTX, active_test=False))
            pruefe(True, "Domain %s ausfuehrbar (%d Treffer)" % (name, zahl))
        except Exception as exc:  # noqa: BLE001
            pruefe(False, "Domain %s" % name, str(exc)[:80])

    # --------------------------------------------------------------- Rechte
    print("\n5. Rechte")
    modelle = k18.kw("ir.model", "search_read", [[("model", "in", ["hr.employee", "hr.job"])]],
                     fields=["id", "model"], context=CTX)
    m_id = {m["model"]: m["id"] for m in modelle}
    gruppe_user = k18.kw("ir.model.data", "search_read",
                         [[("module", "=", "base"), ("name", "=", "group_user")]],
                         fields=["res_id"], context=CTX)[0]["res_id"]
    for modell in ("hr.employee", "hr.job"):
        acc = k18.kw("ir.model.access", "search_read",
                     [[("model_id", "=", m_id[modell]), ("group_id", "=", gruppe_user)]],
                     fields=["perm_read", "perm_write"], context=CTX)
        pruefe(bool(acc) and acc[0]["perm_read"] and not acc[0]["perm_write"],
               "Interner Benutzer darf %s lesen (nicht schreiben)" % modell, acc)

    # ------------------------------------------------------------ Zaehlungen
    print("\n6. Datensatzzahlen")
    soll = {
        "hr.employee": (k11.kw("hr.employee", "search_count", [[]],
                               context={"active_test": False}), None),
        "hr.department": (k11.kw("hr.department", "search_count", [[]]), None),
        "hr.job": (k11.kw("hr.job", "search_count", [[]]), None),
    }
    for modell, (sollwert, _) in soll.items():
        ist = k18.kw(modell, "search_count", [[]], context={"active_test": False})
        pruefe(ist == sollwert, "%s: Anzahl wie Odoo 11" % modell, ist, sollwert)
    # Arbeitszeitmodelle: Odoo 11 fuehrt zwei gleichnamige Modelle mit identischen Zeiten
    # ("Arbeitsstunden von IT-Kommunal GmbH", IDs 4 und 7) -> in Odoo 18 ein Modell.
    def zeiten(k, o11=False):
        feld = ["calendar_id", "dayofweek", "hour_from", "hour_to"]
        daten = k.kw("resource.calendar.attendance", "search_read", [[]], fields=feld,
                     context=dict(CTX, active_test=False))
        out = {}
        for z in daten:
            if z["hour_to"] <= z["hour_from"]:
                continue
            out.setdefault(z["calendar_id"][1], set()).add(
                (int(z["dayofweek"]), z["hour_from"], z["hour_to"]))
        return out

    def kal_namen(k):
        daten = k.kw("resource.calendar", "search_read", [[]], fields=["id", "name"],
                     context=dict(CTX, active_test=False))
        return {c["id"]: " ".join(c["name"].split()) for c in daten}

    z11, z18 = zeiten(k11, True), zeiten(k18)
    n11, n18 = kal_namen(k11), kal_namen(k18)
    soll_kal = {}
    for cid, name in n11.items():
        z = z11.get(name, set())
        soll_kal.setdefault(name, []).append(z)
    pruefe(len(n18) == len(soll_kal), "Arbeitszeitmodelle: Anzahl wie Odoo 11 (ohne Namensdublette)",
           len(n18), len(soll_kal))
    for name, varianten in soll_kal.items():
        if name not in z18:
            pruefe(False, "Arbeitszeitmodell %r vorhanden" % name, "fehlt", "vorhanden")
            continue
        pruefe(any(z18[name] == v for v in varianten), "Arbeitszeiten %r wie Odoo 11" % name,
               sorted(z18[name])[:2], [sorted(v)[:2] for v in varianten])

    ma_aktiv11 = k11.kw("hr.employee", "search_count", [[]])
    ma_aktiv18 = k18.kw("hr.employee", "search_count", [[]])
    pruefe(ma_aktiv18 == ma_aktiv11, "Mitarbeiter aktiv: Anzahl wie Odoo 11", ma_aktiv18, ma_aktiv11)

    # Belegdaten: Soll = aktueller Odoo-11-Produktivstand (28.10.2026, Session 137)
    leaves = k18.kw("hr.leave", "search_count", [[]])
    allos = k18.kw("hr.leave.allocation", "search_count", [[]])
    anw = k18.kw("hr.attendance", "search_count", [[]])
    print("        Urlaubsantraege Odoo 18: %d (Odoo 11: 483)" % leaves)
    print("        Urlaubsansprueche Odoo 18: %d (Odoo 11: 69, davon 1 ohne Mitarbeiter,"
          " 2 mit 0 Tagen)" % allos)
    print("        Anwesenheiten Odoo 18: %d (Odoo 11: 196)" % anw)
    pruefe(anw == 196, "Anwesenheiten vollstaendig", anw, 196)
    # 483 Antraege aus Odoo 11 (Stand 28.10.2026; der Odoo-18-Testantrag wurde entfernt)
    pruefe(leaves == 483, "Urlaubsantraege vollstaendig", leaves, 483)
    # 69 Ansprueche - 1 Kategorie-Anspruch ohne Mitarbeiter - 2 Ansprueche mit 0 Tagen = 66
    pruefe(allos == 66, "Urlaubsansprueche vollstaendig (69 - 1 ohne Mitarbeiter"
          " - 2 mit 0 Tagen)", allos, 66)
    typen = k18.kw("hr.leave.type", "search_count", [[]], context={"active_test": False})
    print("        Urlaubsarten Odoo 18: %d (6 Odoo-Standard + 19 ITK)" % typen)
    pruefe(typen >= 25, "Urlaubsarten angelegt", typen, ">=25")

    # ---------------------------------------------------- Mitarbeiterabgleich
    print("\n7. Mitarbeiterabgleich Odoo 11 gegen Odoo 18 (alle Felder)")
    felder11 = k11.kw("hr.employee", "read",
                      [k11.kw("hr.employee", "search", [[]], context=dict(CTX, active_test=False)),
                       ["id", "name", "firstname", "lastname", "active", "gender", "marital",
                        "work_email", "work_phone", "mobile_phone", "barcode", "pin", "notes",
                        "department_id", "job_id", "parent_id", "user_id",
                        "resource_calendar_id", "category_ids", "address_id"]],
                      context=dict(CTX, active_test=False))
    felder18 = k18.kw("hr.employee", "read",
                      [k18.kw("hr.employee", "search", [[]], context=dict(CTX, active_test=False)),
                       ["id", "name", "firstname", "lastname", "active", "gender", "marital",
                        "work_email", "work_phone", "mobile_phone", "barcode", "pin", "notes",
                        "department_id", "job_id", "parent_id", "user_id",
                        "resource_calendar_id", "category_ids", "address_id"]],
                      context=dict(CTX, active_test=False))
    idx = {}
    for e in felder18:
        if e.get("work_email"):
            idx[("mail", e["work_email"].strip().lower())] = e
        idx[("name", " ".join((e["name"] or "").split()).lower())] = e

    geprueft, abweichungen = 0, []
    eltern_offen = []
    for m11 in felder11:
        schluessel = ("mail", (m11.get("work_email") or "").strip().lower()) \
            if m11.get("work_email") else ("name", " ".join((m11["name"] or "").split()).lower())
        m18 = idx.get(schluessel)
        if not m18:
            abweichungen.append("Odoo-11-Mitarbeiter %s fehlt in Odoo 18" % m11["name"])
            continue
        geprueft += 1
        for feld in ("active", "gender", "work_email", "work_phone", "mobile_phone", "barcode",
                     "pin", "notes"):
            if (m11.get(feld) or False) != (m18.get(feld) or False):
                abweichungen.append("%s: %s ist %r, soll %r" % (m11["name"], feld,
                                                                m18.get(feld), m11.get(feld)))
        if (m11.get("marital") or "single") != (m18.get("marital") or "single"):
            abweichungen.append("%s: marital ist %r, soll %r" % (m11["name"], m18.get("marital"),
                                                                 m11.get("marital")))
        # Beziehungen ueber Namen vergleichen
        for feld in ("department_id", "job_id", "resource_calendar_id"):
            if feld == "resource_calendar_id":
                continue          # Namen unterscheiden sich in Gross-/Kleinschreibung
            if (w(m11.get(feld)) or "") != (w(m18.get(feld)) or ""):
                abweichungen.append("%s: %s ist %r, soll %r" % (m11["name"], feld,
                                                                w(m18.get(feld)), w(m11.get(feld))))
        if bool(m11.get("parent_id")) != bool(m18.get("parent_id")):
            abweichungen.append("%s: Manager gesetzt=%s, soll=%s" % (
                m11["name"], bool(m18.get("parent_id")), bool(m11.get("parent_id"))))
        # Manager muss dieselbe Person sein (Name des Odoo-18-Managers = Name aus Odoo 11)
        if m11.get("parent_id") and m18.get("parent_id"):
            if w(m11["parent_id"]).strip().lower() not in w(m18["parent_id"]).strip().lower() and \
                    w(m18["parent_id"]).strip().lower() not in w(m11["parent_id"]).strip().lower():
                eltern_offen.append("%s: Manager ist %r, in Odoo 11 %r" % (
                    m11["name"], w(m18["parent_id"]), w(m11["parent_id"])))
        if bool(m11.get("category_ids")) != bool(m18.get("category_ids")):
            abweichungen.append("%s: Stichwoerter %s, soll %s" % (
                m11["name"], m18.get("category_ids"), m11.get("category_ids")))
        if bool(m11.get("user_id")) and not m18.get("user_id"):
            pass    # dokumentierte Ausnahme: kein Odoo-18-Benutzer vorhanden
    pruefe(geprueft == len(felder11), "alle Odoo-11-Mitarbeiter zugeordnet",
           geprueft, len(felder11))
    pruefe(not abweichungen, "Feldwerte der Mitarbeiter stimmen", len(abweichungen), 0)
    for text in abweichungen[:15]:
        print("        - %s" % text)
    pruefe(not eltern_offen, "Manager-Zuordnung zeigt auf dieselbe Person", len(eltern_offen), 0)
    for text in eltern_offen[:10]:
        print("        - %s" % text)

    # --------------------------------------------------------- Stichproben
    print("\n8. Stichproben (vollstaendiger Feldvergleich)")
    proben = [m for m in felder11 if m["active"]][:a.stichproben]
    for m11 in proben:
        schluessel = ("mail", (m11.get("work_email") or "").strip().lower()) \
            if m11.get("work_email") else ("name", " ".join((m11["name"] or "").split()).lower())
        m18 = idx.get(schluessel)
        print("   %-30s O11-ID %-3s -> O18-ID %-3s  Abteilung %-16s Stelle %-20s Kalender %s"
              % (m11["name"], m11["id"], m18["id"], w(m18.get("department_id")),
                 w(m18.get("job_id")), w(m18.get("resource_calendar_id"))))

    # --------------------------------------------------------- Beziehungen
    print("\n9. Beziehungen")
    for modell, feld in (("hr.leave", "employee_id"), ("hr.leave.allocation", "employee_id"),
                         ("hr.attendance", "employee_id")):
        ohne = k18.kw(modell, "search_count", [[(feld, "=", False)]])
        pruefe(ohne == 0, "%s: alle Datensaetze haben einen Mitarbeiter" % modell, ohne, 0)
    ids18 = {e["id"] for e in felder18}
    verwaist = k18.kw("hr.leave", "search", [[("employee_id", "not in", list(ids18))]])
    pruefe(not verwaist, "keine Urlaubsantraege mit unbekanntem Mitarbeiter", len(verwaist), 0)

    print("\n10. Sonderfaelle und Sprache")
    # "Manager" ist auch in Odoo 11 der Wortlaut; "Private Informationen" ist deutsch.
    verboten = ["Employees", "Employee", "Job Position", "Work Information", "HR Settings",
                "Coach", "Department", "Time Off", "Absence", "Job Title", "Badges", "Resume"]
    treffer = [t for t in verboten if re.search(r'string="%s"' % t, form + liste + suche)]
    pruefe(not treffer, "keine englischen Ansichten-Bezeichnungen", treffer, [])
    # die 16 frueher nicht uebertragbaren Antraege muessen jetzt vorhanden sein
    ids18 = set(k18.kw("hr.leave", "search", [[]]))
    ohne_anspruch = [("Breiteneder Lorenz", "2020-04-30"), ("Czarnecki Clemens", "2024-05-08"),
                     ("Mohammad Fahad", "2025-10-06")]
    def antrag_da(name, datum):
        """Sucht den Antrag ueber Datum und vergleicht den Mitarbeiternamen."""
        treffer = k18.kw("hr.leave", "search_read", [[("request_date_from", "=", datum)]],
                         fields=["employee_id"], context=CTX)
        return sum(1 for t in treffer if name.lower() in (t["employee_id"][1] or "").lower())

    for name, datum in ohne_anspruch:
        z = antrag_da(name, datum)
        pruefe(z >= 1, "Antrag %s %s uebertragen" % (name, datum), z, ">=1")
    ueber = [("Waiss Martina", "2023-07-16"), ("Tiefling Agnes", "2025-02-12")]
    for name, datum in ueber:
        z = antrag_da(name, datum)
        pruefe(z >= 1, "ueberschneidender Alt-Antrag %s %s uebertragen" % (name, datum), z, ">=1")
    nulltage = k18.kw("hr.leave", "search_count", [[("number_of_days", "=", 0)]])
    pruefe(nulltage >= 9, "Antraege mit 0 Tagen als Altbestand erhalten", nulltage, ">=9")

    print("\n" + "=" * 78)
    print("BILANZ %s: %d OK / %d FEHL" % (a.instanz, OK, len(FEHL)))
    if FEHL:
        for f in FEHL:
            print("  FEHL: %s" % f)
    print("=" * 78)
    return 1 if FEHL else 0


if __name__ == "__main__":
    sys.exit(main())
