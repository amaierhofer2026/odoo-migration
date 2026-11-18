# -*- coding: utf-8 -*-
"""CRM-Abgleich Odoo 11 gegen Odoo 18 (nur lesend, nur Zaehlwerte).

Teil des ITK-Migrationsprojekts (Session 145). Prueft nach der Migration:

- Mengen je Typ, Stufe, Team, Verkaeufer, Prioritaet, Status, Produktinteresse,
  Bundesland, Stichwort, aktiv/archiviert
- Beziehungen: Partner, Verkaeufer, Stufe, Team, Ablehnungsgrund, Medium
- Summen (erwarteter Umsatz) und Anzahl Vorgaenge mit Stichwort/Aktivitaet

Ausgabe: Vergleichstabelle und Abweichungsliste. Es werden keine Namen,
E-Mail-Adressen oder Freitexte ausgegeben.

Aufruf:
    python scripts/migration/crm_abgleich.py --instanz lokal
    python scripts/migration/crm_abgleich.py --instanz vm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX = {"lang": "de_DE"}

# Verbindliche Benutzerzuordnung (Freigabe Anna Maierhofer, Session 145):
# "Maierhofer Anna" (Odoo 11) ist dieselbe Person wie das bestehende Odoo-18-Konto
# "Administrator" - die Zuordnung ist korrekt und keine Abweichung.
BENUTZER_GLEICH = {
    "Maierhofer Anna": "Administrator",
}
FELDER = ["id", "type", "active", "stage_id", "team_id", "user_id", "partner_id", "priority",
          "tag_ids", "lost_reason", "lost_reason_id", "medium_id", "planned_revenue",
          "expected_revenue", "probability", "state_id", "x_lead_status", "x_Produktinteresse",
          "x_Lead_Quelle", "x_Anrede_Lead", "activity_ids", "date_deadline"]


def lade(k, o11: bool):
    ids = k.kw("crm.lead", "search", [[]], context=dict(CTX, active_test=False))
    felder = list(FELDER)
    if not o11:
        # Feldnamen, die sich zwischen Odoo 11 und Odoo 18 unterscheiden
        umbenannt = {"lost_reason": "lost_reason_id", "planned_revenue": "expected_revenue"}
        felder = [umbenannt.get(f, f) for f in felder]
    rows = []
    for i in range(0, len(ids), 500):
        rows += k.kw("crm.lead", "read", [ids[i:i + 500], felder],
                     context=dict(CTX, active_test=False))
    return rows


def m2o(w):
    return w[0] if isinstance(w, (list, tuple)) and w else None


def m2o_name(w):
    return w[1] if isinstance(w, (list, tuple)) and len(w) > 1 else None


def zaehl(rows, feld, name=True):
    c = Counter((m2o_name(r.get(feld)) if name else m2o(r.get(feld))) for r in rows)
    return {str(k): v for k, v in sorted(c.items(), key=lambda x: (-x[1], str(x[0])))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--json")
    args = ap.parse_args()

    k11 = client.o11()
    k18 = client.o18(args.instanz)
    r11 = lade(k11, True)
    r18 = lade(k18, False)
    print("=== CRM-Abgleich %s ===" % args.instanz)
    print("Odoo 11: %d Vorgaenge | Odoo 18: %d Vorgaenge" % (len(r11), len(r18)))

    bericht = {"o11": len(r11), "o18": len(r18), "felder": {}, "abweichungen": []}
    kennzahlen = {
        "gesamt": (len(r11), len(r18)),
        "aktiv": (sum(1 for r in r11 if r["active"]), sum(1 for r in r18 if r["active"])),
        "archiviert": (sum(1 for r in r11 if not r["active"]), sum(1 for r in r18 if not r["active"])),
        "interessenten": (sum(1 for r in r11 if r["type"] == "lead"),
                          sum(1 for r in r18 if r["type"] == "lead")),
        "verkaufschancen": (sum(1 for r in r11 if r["type"] == "opportunity"),
                            sum(1 for r in r18 if r["type"] == "opportunity")),
        "ohne_partner": (sum(1 for r in r11 if not r["partner_id"]),
                         sum(1 for r in r18 if not r["partner_id"])),
        "ohne_verkaeufer": (sum(1 for r in r11 if not r["user_id"]),
                            sum(1 for r in r18 if not r["user_id"])),
        "ohne_stufe": (sum(1 for r in r11 if not r["stage_id"]),
                       sum(1 for r in r18 if not r["stage_id"])),
        "ohne_team": (sum(1 for r in r11 if not r["team_id"]),
                      sum(1 for r in r18 if not r["team_id"])),
        "mit_stichwort": (sum(1 for r in r11 if r["tag_ids"]),
                          sum(1 for r in r18 if r["tag_ids"])),
        "stichwort_zuordnungen": (sum(len(r["tag_ids"]) for r in r11),
                                  sum(len(r["tag_ids"]) for r in r18)),
        "mit_aktivitaet": (sum(1 for r in r11 if r["activity_ids"]),
                           sum(1 for r in r18 if r["activity_ids"])),
        "aktivitaeten": (sum(len(r["activity_ids"]) for r in r11),
                         sum(len(r["activity_ids"]) for r in r18)),
        "mit_frist": (sum(1 for r in r11 if r["date_deadline"]),
                      sum(1 for r in r18 if r["date_deadline"])),
        "umsatz_anzahl": (sum(1 for r in r11 if (r["planned_revenue"] or 0) > 0),
                          sum(1 for r in r18 if (r["expected_revenue"] or 0) > 0)),
        "umsatz_summe": (round(sum(r["planned_revenue"] or 0 for r in r11), 2),
                         round(sum(r["expected_revenue"] or 0 for r in r18), 2)),
    }
    print("\n%-24s %10s %10s %s" % ("Kennzahl", "Odoo 11", "Odoo 18", "Status"))
    for name, (a, b) in kennzahlen.items():
        status = "OK" if a == b else "ABWEICHUNG"
        print("%-24s %10s %10s %s" % (name, a, b, status))
        bericht["felder"][name] = {"o11": a, "o18": b, "status": status}
        if a != b:
            bericht["abweichungen"].append("%s: O11 %s / O18 %s" % (name, a, b))

    gruppen = [
        ("Stufe", "stage_id"), ("Team", "team_id"), ("Verkaeufer", "user_id"),
        ("Prioritaet", "priority"), ("Interessentenstatus", "x_lead_status"),
        ("Produktinteresse", "x_Produktinteresse"), ("Anrede", "x_Anrede_Lead"),
        ("Bundesland", "state_id"), ("Medium", "medium_id"),
    ]
    for titel, feld in gruppen:
        a = zaehl(r11, feld, name=feld not in ("priority", "x_lead_status",
                                               "x_Produktinteresse", "x_Anrede_Lead"))
        b = zaehl(r18, feld, name=feld not in ("priority", "x_lead_status",
                                               "x_Produktinteresse", "x_Anrede_Lead"))
        print("\n-- %s" % titel)
        for wert in sorted(set(a) | set(b), key=lambda w: -(a.get(w, 0) + b.get(w, 0))):
            zeile = "   %-40s %8s %8s" % (wert[:40], a.get(wert, 0), b.get(wert, 0))
            if a.get(wert, 0) != b.get(wert, 0):
                zeile += "   ABWEICHUNG"
                bericht["abweichungen"].append("%s %s: O11 %s / O18 %s" % (
                    titel, wert, a.get(wert, 0), b.get(wert, 0)))
            print(zeile)

    # Stichwoerter
    ta = Counter(m2o_name(t) if isinstance(t, (list, tuple)) else t
                 for r in r11 for t in (r["tag_ids"] or []))
    tb = Counter(m2o_name(t) if isinstance(t, (list, tuple)) else t
                 for r in r18 for t in (r["tag_ids"] or []))
    print("\n-- Stichwoerter (Nutzung)")
    for wert in sorted(set(ta) | set(tb), key=lambda w: -(ta.get(w, 0) + tb.get(w, 0))):
        zeile = "   %-40s %8s %8s" % (str(wert)[:40], ta.get(wert, 0), tb.get(wert, 0))
        if ta.get(wert, 0) != tb.get(wert, 0):
            zeile += "   ABWEICHUNG"
            bericht["abweichungen"].append("Stichwort %s: O11 %s / O18 %s" % (
                wert, ta.get(wert, 0), tb.get(wert, 0)))
        print(zeile)

    # Beziehungen je Vorgang pruefen (nur die Vorgaenge, die auf beiden Seiten existieren)
    print("\n-- Beziehungen je Vorgang (Stichprobe ueber alle zugeordneten Vorgaenge)")
    ids18 = k18.kw("crm.lead", "search_read", [[["itk_o11_id", "!=", False]],
                                               ["id", "itk_o11_id"]],
                   context=dict(CTX, active_test=False), limit=30000)
    map18 = {r["itk_o11_id"]: r["id"] for r in ids18}
    fehlend = [r["id"] for r in r11 if r["id"] not in map18]
    doppelt = len(ids18) - len(map18)
    print("   Odoo-11-Vorgaenge ohne Ziel: %d" % len(fehlend))
    print("   doppelte itk_o11_id im Ziel: %d" % doppelt)
    if fehlend:
        bericht["abweichungen"].append("Vorgaenge ohne Ziel: %d" % len(fehlend))
    if doppelt:
        bericht["abweichungen"].append("doppelte itk_o11_id: %d" % doppelt)

    # Feldgleichheit je Vorgang
    felder_pruefen = ["type", "active", "stage_id", "team_id", "user_id", "partner_id",
                      "priority", "lost_reason", "medium_id", "x_lead_status",
                      "x_Produktinteresse", "x_Anrede_Lead"]
    roh11 = {r["id"]: r for r in r11}
    roh18 = {r["id"]: r for r in r18}
    # Partner ueber den Migrationsschluessel vergleichen (die Anzeigenamen
    # unterscheiden sich: Odoo 11 stellt die Referenz voran).
    p11 = {r["id"]: r["itk_o11_id"] for r in
           k18.kw("res.partner", "search_read", [[["itk_o11_id", "!=", False]],
                                                 ["id", "itk_o11_id"]],
                  context={"lang": "de_DE", "active_test": False}, limit=30000)}
    abw = Counter()
    beispiele = []
    for o11_id, o18_id in map18.items():
        a, b = roh11.get(o11_id), roh18.get(o18_id)
        if not a or not b:
            continue
        for feld in felder_pruefen:
            fa = a.get(feld)
            fb = b.get("lost_reason_id" if feld == "lost_reason" else feld)
            if feld == "partner_id":
                wa = fa[0] if fa else None
                wb = p11.get(fb[0]) if fb else None
            elif feld == "user_id":
                wa = BENUTZER_GLEICH.get(m2o_name(fa), m2o_name(fa))
                wb = m2o_name(fb)
            elif feld in ("stage_id", "team_id", "medium_id", "lost_reason"):
                # Namen vergleichen: die Datenbank-IDs unterscheiden sich zwischen
                # Odoo 11 und Odoo 18 zwangslaeufig, die Zuordnung laeuft ueber Namen.
                wa, wb = m2o_name(fa), m2o_name(fb)
            else:
                wa, wb = fa, fb
            if wa != wb:
                abw[feld] += 1
                if len(beispiele) < 20:
                    beispiele.append((o11_id, feld, wa, wb))
    # ---------------------------------------------------------- Chatter
    print("\n-- Chatter")
    msgs11 = k11.kw("mail.message", "search_read",
                    [[("model", "=", "crm.lead")], ["id", "body"]], context=CTX, limit=10000)
    mit_text = [m for m in msgs11 if (m.get("body") or "").strip()]
    ohne_text = len(msgs11) - len(mit_text)
    rows = k18.kw("mail.message", "search_read",
                  [[["itk_o11_msg_id", "!=", False]], ["itk_o11_msg_id"]],
                  context={"lang": "de_DE", "active_test": False}, limit=30000)
    migriert = len({r["itk_o11_msg_id"] for r in rows})
    print("   Odoo 11 gesamt %d | fachlich (mit Text) %d | reine Systemmeldung %d"
          % (len(msgs11), len(mit_text), ohne_text))
    print("   Odoo 18 migriert %d von %d fachlichen Nachrichten %s"
          % (migriert, len(mit_text), "OK" if migriert == len(mit_text) else "ABWEICHUNG"))
    if migriert != len(mit_text):
        bericht["abweichungen"].append("Chatter: %d von %d migriert" % (migriert, len(mit_text)))

    # ---------------------------------------------------------- Anhaenge
    print("\n-- Anhaenge")
    att11 = k11.kw("ir.attachment", "search_read",
                   [[("res_model", "=", "crm.lead")], ["id", "file_size"]], context=CTX, limit=1000)
    rows = k18.kw("ir.attachment", "search_read",
                  [[["itk_o11_att_id", "!=", False]], ["itk_o11_att_id", "file_size"]],
                  context={"lang": "de_DE", "active_test": False}, limit=5000)
    print("   Odoo 11: %d Anhaenge, %.1f MB" % (
        len(att11), sum(a["file_size"] or 0 for a in att11) / 1048576))
    print("   Odoo 18: %d Anhaenge, %.1f MB %s" % (
        len(rows), sum(a["file_size"] or 0 for a in rows) / 1048576,
        "OK" if len(rows) == len(att11) else "ABWEICHUNG"))
    if len(rows) != len(att11):
        bericht["abweichungen"].append("Anhaenge: %d von %d" % (len(rows), len(att11)))

    # ---------------------------------------------------------- Aktivitaeten
    print("\n-- Aktivitaeten")
    a11 = k11.kw("mail.activity", "search_count", [[("res_model", "=", "crm.lead")]], context=CTX)
    rows = k18.kw("mail.activity", "search_read",
                  [[["itk_o11_activity_id", "!=", False]], ["itk_o11_activity_id"]],
                  context={"lang": "de_DE", "active_test": False}, limit=5000)
    print("   Odoo 11: %d | Odoo 18 migriert: %d %s" % (
        a11, len(rows), "OK" if len(rows) == a11 else "ABWEICHUNG"))

    for feld, anzahl in abw.most_common():
        print("   Feld %-18s %d Vorgaenge abweichend" % (feld, anzahl))
        bericht["abweichungen"].append("Feld %s: %d Vorgaenge abweichend" % (feld, anzahl))
    if not abw:
        print("   alle geprueften Felder identisch")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(bericht, fh, ensure_ascii=False, indent=1)
        print("\nJSON: %s" % args.json)

    print("\nAbweichungen insgesamt: %d" % len(bericht["abweichungen"]))
    return 0 if not bericht["abweichungen"] else 1


if __name__ == "__main__":
    sys.exit(main())
