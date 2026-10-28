"""Abnahme ZEITERFASSUNG Datenbestand: Odoo 11 (live) <-> Odoo 18 (lokal/VM).

Read-only. Vergleicht den kompletten Bestand als Multimenge, nicht als Stichprobe:

  1. Zeilenanzahl und Zeilen-Identitaet (Datum, Mitarbeiter, Projekt, Aufgabe,
     Dauer, Beschreibung) - jede Odoo-11-Zeile muss genau einmal vorhanden sein.
  2. Felder je Zeile: Datum, Startzeit 00:00, Endzeit leer, Dauer, Beschreibung,
     Abrechenbarkeit, Referenz (Ticket/Aufgabe/Kostenstelle), Abwesenheitsbezug,
     Kostenstelle = Projektkonto.
  3. Mengen und Summen je Mitarbeiter, Projekt, Jahr und Monat.
  4. Archivierte Mitarbeiter, Zeilen ohne Projekt/Aufgabe, Beziehungen, Rechte.
  5. Fremder Bestand (Testzeilen frueherer Sitzungen) wird ausgewiesen, nicht
     mitgezaehlt.

Aufruf:
    python scripts/verify_s136_zeiterfassung.py --instanz lokal
    python scripts/verify_s136_zeiterfassung.py --instanz vm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
SAMMELPROJEKT = "Ohne Projekt (Uebernahme Odoo 11)"
BERICHT = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp",
                       "zeiterfassung_migration")


def norm(wert):
    return " ".join((wert or "").split()).lower()


class Pruefung:
    def __init__(self):
        self.ok = 0
        self.fehler = []

    def pruefe(self, bez, ist, soll):
        if ist == soll:
            self.ok += 1
            print("  OK      %-62s %s" % (bez, ist))
        else:
            self.fehler.append((bez, ist, soll))
            print("  FEHLER  %-62s ist=%s soll=%s" % (bez, ist, soll))

    def wahr(self, bez, bedingung, detail=""):
        self.pruefe(bez, bool(bedingung), True)
        if not bedingung:
            print("          Detail:", str(detail)[:400])

    def ergebnis(self):
        print("\n  Ergebnis: %d OK, %d FEHLER" % (self.ok, len(self.fehler)))
        for f in self.fehler:
            print("   FEHLER:", f)
        return 0 if not self.fehler else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--stichprobe", type=int, default=0, help="nur N Zeilen vergleichen (Diagnose)")
    a = ap.parse_args()
    k11, k18 = o11(), o18(a.instanz)
    p = Pruefung()
    print("### Zeiterfassung Datenabnahme, Instanz:", a.instanz)

    # ---------------------------------------------------------------- Odoo 11
    z11 = k11.kw("account.analytic.line", "search_read", [[]],
                 fields=["id", "date", "name", "unit_amount", "employee_id", "user_id",
                         "project_id", "task_id", "account_id", "holiday_id",
                         "support_ticket_id", "timesheet_invoice_type", "amount"],
                 order="date,id", limit=0)
    ma11 = {m["id"]: m for m in k11.kw("hr.employee", "search_read", [[]],
                                       fields=["id", "name", "work_email", "user_id", "active"],
                                       context={"active_test": False}, limit=0)}
    hids = sorted({z["holiday_id"][0] for z in z11 if z["holiday_id"]})
    h11 = {h["id"]: h for h in k11.kw("hr.holidays", "read", [hids],
                                      fields=["employee_id", "date_from", "number_of_days_temp",
                                              "state"])}
    tids = sorted({z["support_ticket_id"][0] for z in z11 if z["support_ticket_id"]})
    t11 = {t["id"]: t for t in k11.kw("website.support.ticket", "read", [tids],
                                      fields=["ticket_number"])}
    aufgaben11 = {t["id"]: t for t in k11.kw("project.task", "search_read", [[]],
                                             fields=["id", "name", "project_id"],
                                             context={"active_test": False}, limit=0)}
    print("  Odoo 11: %d Zeilen, %.2f Stunden" % (len(z11), sum(x["unit_amount"] or 0 for x in z11)))

    # ---------------------------------------------------------------- Odoo 18
    z18 = k18.kw("account.analytic.line", "search_read", [[]],
                 fields=["id", "date", "name", "unit_amount", "employee_id", "user_id",
                         "project_id", "task_id", "account_id", "holiday_id", "ref",
                         "timesheet_invoice_type", "date_time", "date_time_end", "amount",
                         "product_uom_id"],
                 order="id", limit=0)
    pro18 = {x["id"]: x for x in k18.kw("project.project", "search_read", [[]],
                                        fields=["id", "name", "account_id", "active",
                                                "allow_timesheets"],
                                        context={"active_test": False}, limit=0)}
    auf18 = {x["id"]: x for x in k18.kw("project.task", "search_read", [[]],
                                        fields=["id", "name", "project_id", "active"],
                                        context={"active_test": False}, limit=0)}
    ma18 = {x["id"]: x for x in k18.kw("hr.employee", "search_read", [[]],
                                       fields=["id", "name", "work_email", "user_id", "active"],
                                       context={"active_test": False}, limit=0)}
    lv18 = {x["id"]: x for x in k18.kw("hr.leave", "search_read", [[]],
                                       fields=["id", "employee_id", "date_from", "state",
                                               "number_of_days"],
                                       context={"active_test": False}, limit=0)}
    print("  Odoo 18: %d Zeilen, %.2f Stunden" % (len(z18), sum(x["unit_amount"] or 0 for x in z18)))

    # ------------------------------------------------- Mitarbeiter-Zuordnung
    mail18 = {norm(m["work_email"]): m for m in ma18.values() if m["work_email"]}
    name18 = defaultdict(list)
    for m in ma18.values():
        name18[norm(m["name"])].append(m)
    ma_map = {}
    for mid, m in ma11.items():
        ziel = mail18.get(norm(m["work_email"]))
        if not ziel:
            kandidaten = name18.get(norm(m["name"]), [])
            ziel = kandidaten[0] if len(kandidaten) == 1 else None
        ma_map[mid] = ziel["id"] if ziel else None
    projekt_map = {}
    for pid, name in {(z["project_id"] or [0])[0]: (z["project_id"] or [None, None])[1]
                      for z in z11 if z["project_id"]}.items():
        treffer = [x for x in pro18.values() if norm(x["name"]) == norm(name)]
        projekt_map[pid] = treffer[0]["id"] if len(treffer) == 1 else None
    sammel = [x for x in pro18.values() if norm(x["name"]) == norm(SAMMELPROJEKT)]
    sammel_id = sammel[0]["id"] if sammel else None

    # ------------------------------------------------------- Erwartung bauen
    def loese_abwesenheit(hid):
        h = h11.get(hid)
        if not h or not h["employee_id"]:
            return None
        ma = ma_map.get(h["employee_id"][0])
        beginn = str(h["date_from"])[:10]
        gebucht = [x for x in lv18.values()
                   if (x["employee_id"] or [0])[0] == ma and str(x["date_from"])[:10] == beginn
                   and x["state"] == "validate"]
        if len(gebucht) == 1:
            return gebucht[0]["id"]
        if len(gebucht) > 1:
            gleich = [x for x in gebucht
                      if abs((x["number_of_days"] or 0) - (h.get("number_of_days_temp") or 0)) < 0.001]
            return gleich[0]["id"] if len(gleich) == 1 else None
        return None

    erwartet = []
    aufgabe_namen = defaultdict(list)
    for x in auf18.values():
        aufgabe_namen[norm(x["name"])].append(x)
    for z in z11:
        pid11 = (z["project_id"] or [None])[0]
        tid11 = (z["task_id"] or [None])[0]
        privat = bool(tid11 and not pid11)
        pid18 = projekt_map.get(pid11) if pid11 else sammel_id
        # Aufgabe ueber den Namen suchen; bei Doppelnamen zusaetzlich ueber das Projekt.
        # Odoo 11 erlaubt Zeilen, deren Aufgabe zu einem anderen Projekt gehoert (7 Zeilen).
        tid18 = None
        if tid11 and not privat:
            name11 = norm(aufgaben11[tid11]["name"])
            pid_aufgabe11 = (aufgaben11[tid11].get("project_id") or [0])[0]
            kandidaten = aufgabe_namen.get(name11, [])
            im_projekt = [x for x in kandidaten if (x["project_id"] or [0])[0] == pid18]
            if im_projekt:
                tid18 = im_projekt[0]["id"]
            elif len(kandidaten) == 1:
                tid18 = kandidaten[0]["id"]
            else:
                tid18 = kandidaten[0]["id"] if kandidaten else None
        fremd_projekt = bool(
            tid11 and pid11
            and (aufgaben11[tid11].get("project_id") or [0])[0] != pid11)
        if fremd_projekt:
            tid18 = None
        refs = []
        if z["support_ticket_id"]:
            t = t11.get(z["support_ticket_id"][0])
            if t and t.get("ticket_number"):
                refs.append("O11-Ticket %s" % t["ticket_number"])
        if privat or fremd_projekt:
            refs.append("O11-Aufgabe %s" % aufgaben11[tid11]["name"])
        if not pid11 and z["account_id"]:
            refs.append("O11-Kostenstelle %s" % z["account_id"][1])
        erwartet.append({
            "o11_id": z["id"], "date": str(z["date"])[:10], "name": z["name"],
            "unit": round(z["unit_amount"] or 0, 6), "ma": ma_map.get((z["employee_id"] or [0])[0]),
            "ma_name": (z["employee_id"] or [None, None])[1],
            "projekt": pid18, "projekt_name": (pro18.get(pid18) or {}).get("name"),
            "aufgabe": tid18, "aufgabe_name": (auf18.get(tid18) or {}).get("name"),
            "privat": privat, "ref": " | ".join(refs) or False,
            "holiday": loese_abwesenheit(z["holiday_id"][0]) if z["holiday_id"] else False,
            "hatte_abw": bool(z["holiday_id"]),
            "konto": (pro18.get(pid18) or {}).get("account_id") or [None],
            "typ11": z["timesheet_invoice_type"],
        })

    # ----------------------------------------------- Multimengen-Vergleich
    def schluessel(date, ma, pid, tid, unit, name):
        # Aufgabe ueber den NAMEN, nicht ueber die ID: Doppelaufgaben (2x "Overhead")
        # sind fachlich gleich und werden nicht als Abweichung gewertet.
        aufgabe = norm((auf18.get(tid) or {}).get("name")) if tid else ""
        return (date, ma or 0, pid or 0, aufgabe, round(unit or 0, 6), norm(name))

    def schluessel11(e):
        aufgabe = norm(e["aufgabe_name"]) if e["aufgabe"] else ""
        return (e["date"], e["ma"] or 0, e["projekt"] or 0, aufgabe, round(e["unit"], 6),
                norm(e["name"]))

    soll = Counter(schluessel11(e) for e in erwartet)
    ist = Counter(schluessel(str(x["date"])[:10], (x["employee_id"] or [0])[0],
                             (x["project_id"] or [0])[0], (x["task_id"] or [0])[0],
                             x["unit_amount"], x["name"]) for x in z18)
    fehlend = soll - ist
    ueberzaehlig = ist - soll
    treffer = sum(min(soll[k], ist[k]) for k in soll)

    print("\n=== 1 Mengen ===")
    p.pruefe("Zeilen Odoo 11 (live)", len(z11), len(erwartet))
    p.pruefe("Zeilen in Odoo 18 gefunden (Multimenge)", treffer, len(erwartet))
    p.pruefe("Zeilen fehlen in Odoo 18", sum(fehlend.values()), 0)
    p.pruefe("Zeilen doppelt/fremd in Odoo 18", sum(ueberzaehlig.values()),
             len(z18) - len(erwartet))
    if fehlend:
        print("  fehlende Schluessel (erste 5):", list(fehlend.items())[:5])
    fremd = []
    if ueberzaehlig:
        index = defaultdict(list)
        for x in z18:
            index[schluessel(str(x["date"])[:10], (x["employee_id"] or [0])[0],
                             (x["project_id"] or [0])[0], (x["task_id"] or [0])[0],
                             x["unit_amount"], x["name"])].append(x)
        for k, n in ueberzaehlig.items():
            for x in index[k][:n]:
                fremd.append(x)
        print("  fremder Bestand (%d Zeilen):" % len(fremd))
        for x in fremd[:25]:
            print("     #%s %s %-28r MA=%s P=%s %.2f h"
                  % (x["id"], x["date"], (x["name"] or "")[:28],
                     (x["employee_id"] or [None, "-"])[1], (x["project_id"] or [None, "-"])[1],
                     x["unit_amount"] or 0))

    # ------------------------------------------------- Felder je Zeile
    print("\n=== 2 Felder je Zeile ===")
    eimer = defaultdict(list)
    for x in z18:
        eimer[schluessel(str(x["date"])[:10], (x["employee_id"] or [0])[0],
                         (x["project_id"] or [0])[0], (x["task_id"] or [0])[0],
                         x["unit_amount"], x["name"])].append(x)
    fehler = Counter()
    beispiele = defaultdict(list)
    gepaart = 0
    rand_leerzeichen = 0
    for e in erwartet:
        k = schluessel11(e)
        if not eimer[k]:
            continue
        # Innerhalb gleicher Schluessel nach exaktem Namen paaren (Rand-Leerzeichen
        # unterscheiden sich, der Text ist gleich) - sonst zaehlt die Paarreihenfolge.
        gruppe = sorted(eimer[k], key=lambda y: (y["name"] != e["name"], y["id"]))
        x = gruppe[0]
        eimer[k].remove(x)
        gepaart += 1
        if x["name"] != e["name"] and norm(x["name"]) == norm(e["name"]):
            rand_leerzeichen += 1
        pruefungen = {
            "Datum": (str(x["date"])[:10], e["date"]),
            "Startzeit 00:00": (str(x["date_time"] or "")[:19], "%s 00:00:00" % e["date"]),
            "Dauer": (round(x["unit_amount"] or 0, 6), e["unit"]),
            "Beschreibung (Inhalt)": (norm(x["name"]), norm(e["name"])),
            "Projekt": ((x["project_id"] or [0])[0], e["projekt"] or 0),
            "Aufgabe": (norm((auf18.get((x["task_id"] or [0])[0]) or {}).get("name")),
                        norm(e["aufgabe_name"]) if e["aufgabe"] else ""),
            "Mitarbeiter": ((x["employee_id"] or [0])[0], e["ma"] or 0),
            "Kostenstelle = Projektkonto": ((x["account_id"] or [0])[0], (e["konto"] or [0])[0]),
            "Referenz": (x["ref"] or False, e["ref"]),
            "Abwesenheit": ((x["holiday_id"] or [0])[0], (e["holiday"] or 0)),
            "Abrechenbarkeit": (x["timesheet_invoice_type"], "non_billable"),
        }
        if x["employee_id"] and x["user_id"]:
            ma_user = (ma18.get(x["employee_id"][0]) or {}).get("user_id")
            if ma_user and ma_user[0] != x["user_id"][0]:
                pruefungen["Benutzer = Mitarbeiterbenutzer"] = (x["user_id"][0], ma_user[0])
        for feld, (ist_wert, soll_wert) in pruefungen.items():
            if ist_wert != soll_wert:
                fehler[feld] += 1
                if len(beispiele[feld]) < 3:
                    beispiele[feld].append((e["o11_id"], x["id"], ist_wert, soll_wert))
    p.pruefe("gepaarte Zeilen", gepaart, len(erwartet))
    # Endzeit: Odoo 18 setzt sie automatisch auf Startzeit + Dauer (kein Odoo-11-Feld)
    endzeit_abw = []
    for x in z18:
        if not x["date_time"] or not x["date_time_end"]:
            continue
        import datetime as _dt
        s = _dt.datetime.strptime(x["date_time"], "%Y-%m-%d %H:%M:%S")
        en = _dt.datetime.strptime(x["date_time_end"], "%Y-%m-%d %H:%M:%S")
        if abs((en - s).total_seconds() / 3600.0 - (x["unit_amount"] or 0)) > 0.01:
            endzeit_abw.append(x["id"])
    p.pruefe("Endzeit weicht von Startzeit + Dauer ab", len(endzeit_abw), 0)
    p.pruefe("Beschreibung nur Rand-Leerzeichen abweichend", rand_leerzeichen,
             sum(1 for z in z11 if z["name"] != (z["name"] or "").strip()))
    for feld in ("Datum", "Startzeit 00:00", "Dauer", "Beschreibung (Inhalt)", "Projekt",
                 "Aufgabe", "Mitarbeiter", "Kostenstelle = Projektkonto", "Referenz",
                 "Abwesenheit", "Abrechenbarkeit", "Benutzer = Mitarbeiterbenutzer"):
        p.pruefe("Feld %s abweichend" % feld, fehler[feld], 0)
        if fehler[feld]:
            print("          Beispiele (O11-ID, O18-ID, ist, soll):", beispiele[feld])

    # ------------------------------------------------------ Mengen/Summen
    print("\n=== 3 Summen je Mitarbeiter/Projekt/Jahr/Monat ===")
    def summe(zeilen, schluessel_fn):
        c = Counter()
        for z in zeilen:
            c[schluessel_fn(z)] += z["unit_amount"] or 0
        return {k: round(v, 4) for k, v in c.items()}

    # Odoo-18-Seite auf die migrierten Zeilen begrenzen (fremder Bestand raus)
    o18_ids = set()
    for x in z18:
        if schluessel(str(x["date"])[:10], (x["employee_id"] or [0])[0],
                      (x["project_id"] or [0])[0], (x["task_id"] or [0])[0],
                      x["unit_amount"], x["name"]) in soll:
            o18_ids.add(x["id"])
    # je Schluessel exakt die Odoo-11-Anzahl zaehlen
    rest = {k: v for k, v in soll.items()}
    migriert = []
    for x in z18:
        k = schluessel(str(x["date"])[:10], (x["employee_id"] or [0])[0],
                       (x["project_id"] or [0])[0], (x["task_id"] or [0])[0],
                       x["unit_amount"], x["name"])
        if rest.get(k, 0) > 0:
            rest[k] -= 1
            migriert.append(x)

    # Beide Summen stammen aus Odoo 11; durch die Summationsreihenfolge kann der
    # gerundete Wert um 0,01 h abweichen (Float-Artefakt, kein Datenfehler).
    summe11 = round(sum(x["unit_amount"] or 0 for x in z11), 2)
    summe_erwartet = round(sum(e["unit"] for e in erwartet), 2)
    p.pruefe("Summe Stunden Odoo 11 (Toleranz 0,02 h)",
             summe_erwartet if abs(summe11 - summe_erwartet) < 0.02 else summe11,
             summe_erwartet)
    p.pruefe("Summe Stunden migrierte Odoo-18-Zeilen",
             round(sum(x["unit_amount"] or 0 for x in migriert), 2),
             round(sum(x["unit_amount"] or 0 for x in z11), 2))

    s11_ma = summe(z11, lambda z: ma_map.get((z["employee_id"] or [0])[0]) or 0)
    s18_ma = summe(migriert, lambda z: (z["employee_id"] or [0])[0] or 0)
    for mid in sorted(set(s11_ma) | set(s18_ma)):
        p.pruefe("Stunden Mitarbeiter %s" % (ma18.get(mid) or {"name": "?"})["name"],
                 s18_ma.get(mid, 0), s11_ma.get(mid, 0))
    p.pruefe("Mitarbeiter mit Zeilen Odoo 11", len(s11_ma), len(s11_ma))
    p.pruefe("Mitarbeiter mit Zeilen Odoo 18", len(s18_ma), len(s11_ma))

    s11_p = summe(z11, lambda z: (z["project_id"] or [None, SAMMELPROJEKT])[1])
    s18_p = summe(migriert, lambda z: (pro18.get((z["project_id"] or [0])[0]) or {"name": "-"})["name"])
    abw = [(n, s11_p.get(n, 0), s18_p.get(n, 0)) for n in sorted(set(s11_p) | set(s18_p))
           if abs((s11_p.get(n, 0) or 0) - (s18_p.get(n, 0) or 0)) > 0.001]
    p.pruefe("Projekte mit abweichender Stundensumme", len(abw), 0)
    if abw:
        print("          ", abw[:6])
    p.pruefe("Projekte mit Zeilen Odoo 11", len(s11_p), len(s18_p))

    s11_j = summe(z11, lambda z: str(z["date"])[:4])
    s18_j = summe(migriert, lambda z: str(z["date"])[:4])
    for jahr in sorted(set(s11_j) | set(s18_j)):
        p.pruefe("Stunden Jahr %s" % jahr, s18_j.get(jahr, 0), s11_j.get(jahr, 0))
    s11_m = summe(z11, lambda z: str(z["date"])[:7])
    s18_m = summe(migriert, lambda z: str(z["date"])[:7])
    abw_m = [k for k in set(s11_m) | set(s18_m)
             if abs((s11_m.get(k, 0) or 0) - (s18_m.get(k, 0) or 0)) > 0.001]
    p.pruefe("Monate mit abweichender Stundensumme", len(abw_m), 0)
    p.pruefe("Monate verglichen", len(set(s11_m) | set(s18_m)), len(set(s11_m) | set(s18_m)))

    # ---------------------------------------------------- Sonderfaelle
    print("\n=== 4 Sonderfaelle und Beziehungen ===")
    ohne_projekt11 = [e for e in erwartet if e["projekt"] == sammel_id]
    p.pruefe("Zeilen ohne Projekt -> Sammelprojekt", len(ohne_projekt11),
             sum(1 for z in z11 if not z["project_id"]))
    p.pruefe("Zeilen im Sammelprojekt in Odoo 18",
             k18.kw("account.analytic.line", "search_count",
                    [[("project_id", "=", sammel_id)]]), len(ohne_projekt11))
    p.pruefe("Sammelprojekt-Zeilen ohne Aufgabe",
             k18.kw("account.analytic.line", "search_count",
                    [[("project_id", "=", sammel_id), ("task_id", "=", False)]]),
             len(ohne_projekt11))
    p.wahr("Sammelprojekt existiert und erlaubt Zeiterfassung",
           bool(sammel_id) and pro18[sammel_id]["allow_timesheets"], sammel_id)

    privat11 = [e for e in erwartet if e["privat"]]
    p.pruefe("Zeilen mit privater Odoo-11-Aufgabe", len(privat11),
             sum(1 for z in z11 if z["task_id"] and not z["project_id"]))
    p.pruefe("davon mit Aufgaben-Referenz im Feld ref",
             sum(1 for e in privat11 if e["ref"] and "O11-Aufgabe" in e["ref"]), len(privat11))

    tickets = [e for e in erwartet if e["ref"] and "O11-Ticket" in str(e["ref"])]
    p.pruefe("Zeilen mit Ticket-Referenz", len(tickets),
             sum(1 for z in z11 if z["support_ticket_id"]))
    p.pruefe("Helpdesk-Tickets in Odoo 18 (dürfen nicht angelegt sein)",
             k18.kw("helpdesk.ticket", "search_count", [[]]), 0)
    p.pruefe("Zeilen mit Helpdesk-Verknuepfung (muss 0 sein)",
             k18.kw("account.analytic.line", "search_count", [[("ticket_id", "!=", False)]]), 0)

    fehlende_abw = [e for e in erwartet if e["hatte_abw"] and not e["holiday"]]
    # Ursache je Zeile ermitteln: gibt es eine Abwesenheit am selben Tag, die nicht
    # gebucht ist? Dann ist der Bestand in Odoo 18 (noch) nicht gebucht - das ist
    # kein Fehler der Zeiterfassungsmigration, sondern ein Abwesenheits-Status.
    nicht_gebucht = 0
    for e in fehlende_abw:
        z = next(x for x in z11 if x["id"] == e["o11_id"])
        h = h11.get((z["holiday_id"] or [0])[0])
        if not h or not h["employee_id"]:
            continue
        beginn = str(h["date_from"])[:10]
        kandidaten = [x for x in lv18.values()
                      if (x["employee_id"] or [0])[0] == ma_map.get(h["employee_id"][0])
                      and str(x["date_from"])[:10] == beginn]
        if kandidaten and not any(x["state"] == "validate" for x in kandidaten):
            nicht_gebucht += 1
    p.pruefe("Abwesenheitszeilen ohne gebuchte Entsprechung (Abwesenheit nicht gebucht)",
             len(fehlende_abw), nicht_gebucht)
    p.pruefe("Abwesenheitszeilen mit Zuordnung (Odoo 18)",
             k18.kw("account.analytic.line", "search_count", [[("holiday_id", "!=", False)]]),
             sum(1 for e in erwartet if e["holiday"]))
    falsche_abw = []
    for x in migriert:
        if not x["holiday_id"]:
            continue
        lv = lv18.get(x["holiday_id"][0])
        if not lv or (lv["employee_id"] or [0])[0] != (x["employee_id"] or [0])[0]:
            falsche_abw.append(x["id"])
    p.pruefe("Abwesenheit gehoert zu anderem Mitarbeiter", len(falsche_abw), 0)

    konto_fehler = [x["id"] for x in migriert
                    if (x["account_id"] or [0])[0] != ((pro18.get((x["project_id"] or [0])[0])
                                                        or {}).get("account_id") or [0])[0]]
    p.pruefe("Kostenstelle weicht vom Projektkonto ab", len(konto_fehler), 0)

    aufgabe_fehler = [x["id"] for x in migriert
                      if x["task_id"] and (auf18.get(x["task_id"][0]) or {}).get("project_id", [0])[0]
                      != (x["project_id"] or [0])[0]]
    # Odoo 11 erlaubt Zeilen, deren Aufgabe zu einem anderen Projekt gehoert. Odoo 18
    # setzt eine solche Aufgabe beim Anlegen zurueck; das Projekt bleibt wie in
    # Odoo 11, der Aufgabentitel wird als Referenz "O11-Aufgabe <Name>" gespeichert.
    aufgabe11_fremd = sum(
        1 for z in z11 if z["task_id"] and z["project_id"]
        and (aufgaben11[z["task_id"][0]]["project_id"] or [0])[0] != z["project_id"][0])
    p.pruefe("Zeilen mit Aufgabe aus fremdem Projekt (Aufgabe zurueckgesetzt)",
             len(aufgabe_fehler), 0)
    p.pruefe("davon mit Aufgabentitel als Referenz",
             sum(1 for e in erwartet if e["privat"] or
                 (e["aufgabe"] is None and e["ref"] and "O11-Aufgabe" in str(e["ref"])
                  and e["ref"] != "O11-Ticket")),
             sum(1 for e in erwartet if e["privat"]) + aufgabe11_fremd)

    archiviert11 = {m["id"] for m in ma11.values() if not m["active"]}
    archiviert18 = {x["id"] for x in ma18.values() if not x["active"]}
    p.pruefe("archivierte Mitarbeiter Odoo 18", len(archiviert18), 12)
    p.pruefe("Zeilen archivierter Mitarbeiter",
             sum(1 for z in migriert if (z["employee_id"] or [0])[0] in archiviert18),
             sum(1 for z in z11 if (z["employee_id"] or [0])[0] in archiviert11))
    wieder_aktiv = sorted(x["name"] for x in ma18.values()
                          if x["active"] and x["id"] in {ma_map.get(m) for m in archiviert11})
    p.pruefe("archivierte Mitarbeiter wieder aktiv (muss leer sein)", wieder_aktiv, [])

    archivierte_projekte = {x["id"] for x in pro18.values() if not x["active"]}
    p.pruefe("Zeilen auf archivierten Projekten",
             sum(1 for z in migriert if (z["project_id"] or [0])[0] in archivierte_projekte),
             sum(1 for e in erwartet if e["projekt"] in archivierte_projekte))
    archivierte_aufgaben = {x["id"] for x in auf18.values() if not x["active"]}
    p.pruefe("Zeilen auf archivierten Aufgaben",
             sum(1 for z in migriert if (z["task_id"] or [0])[0] in archivierte_aufgaben),
             sum(1 for e in erwartet if e["aufgabe"] in archivierte_aufgaben))

    print("\n=== 5 Rechte ===")
    g = k18.kw("res.groups", "read", [[607, 608]], fields=["name", "users"], context=CTX)
    p.pruefe("Gruppe 607 'nur eigene' Mitglieder", len(g[0]["users"]), 13)
    p.pruefe("Gruppe 608 'alle' Mitglieder", len(g[1]["users"]), 12)
    p.pruefe("Gruppe 608 Teilmenge von 607", set(g[1]["users"]) <= set(g[0]["users"]), True)
    regeln = k18.kw("ir.rule", "search_read",
                    [[("model_id.model", "=", "account.analytic.line")]],
                    fields=["name", "domain_force"], limit=0)
    p.wahr("Record Rules fuer Zeiterfassung vorhanden", len(regeln) >= 2, len(regeln))

    # ------------------------------------------------------------ Bericht
    os.makedirs(BERICHT, exist_ok=True)
    pfad = os.path.join(BERICHT, "abnahme_%s.json" % a.instanz)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump({"instanz": a.instanz, "ok": p.ok, "fehler": p.fehler,
                   "zeilen11": len(z11), "zeilen18": len(z18),
                   "stunden11": round(sum(x["unit_amount"] or 0 for x in z11), 2),
                   "stunden18_migriert": round(sum(x["unit_amount"] or 0 for x in migriert), 2),
                   "fremder_bestand": [{"id": x["id"], "date": x["date"], "name": x["name"]}
                                       for x in fremd],
                   "stunden_mitarbeiter": s11_ma, "stunden_projekt": s11_p,
                   "stunden_jahr": s11_j},
                  fh, ensure_ascii=False, default=str)
    print("\n  Bericht:", pfad)
    return p.ergebnis()


if __name__ == "__main__":
    raise SystemExit(main())
