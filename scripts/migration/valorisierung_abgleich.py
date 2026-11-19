# -*- coding: utf-8 -*-
"""Valorisierung: Abgleich Odoo 11 gegen Odoo 18 (read-only).

Prueft die Hinweise feldweise (Code, Beschreibung inkl. Laenge und Pruefsumme,
Nummernfolge, Erstell-/Bearbeitungsdatum, Ersteller) und die Rechnungsnutzung.

Aufruf:
    python scripts/migration/valorisierung_abgleich.py --instanz lokal
    python scripts/migration/valorisierung_abgleich.py --instanz vm
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX11 = {"lang": "de_DE", "active_test": False}
CTX18 = {"lang": "de_DE", "active_test": False}
MODELL = "itk_valorisierung.valorisierung"

BENUTZER_MAPPING = {"admin": "anna.maierhofer@it-kommunal.at"}


def m2o(w):
    return w[0] if isinstance(w, (list, tuple)) and w else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    args = ap.parse_args()

    o11 = client.o11()
    o18 = client.o18(args.instanz)
    print("=== Valorisierungs-Abgleich Odoo 11 <-> Odoo 18 (%s) ===" % args.instanz)

    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    q = o11.kw(MODELL, "search_read",
               [[], ["id", "name", "description", "seq", "create_date", "write_date",
                     "create_uid", "write_uid"]], context=CTX11, order="id")
    z = o18.kw(MODELL, "search_read",
               [[["itk_o11_id", "!=", False]],
                ["id", "itk_o11_id", "name", "description", "seq", "create_date", "write_date",
                 "create_uid", "write_uid"]], context=CTX18, order="itk_o11_id")
    nutzung11 = {}
    for g in o11.kw("account.invoice", "read_group",
                    [[["valorisierung_id", "!=", False]], ["valorisierung_id"],
                     ["valorisierung_id"]], context=CTX11):
        nutzung11[m2o(g.get("valorisierung_id"))] = g.get("valorisierung_id_count", 0)

    login18 = {}
    name18 = {}
    for u in o18.kw("res.users", "search_read", [[], ["id", "login", "name"]], context=CTX18,
                    limit=500):
        if u.get("login"):
            login18.setdefault(u["login"].lower(), u["id"])
        if u.get("name"):
            name18.setdefault(u["name"], u["id"])
    login11 = {}
    for u_id in {m2o(r["create_uid"]) for r in q} | {m2o(r["write_uid"]) for r in q}:
        if u_id:
            info = o11.kw("res.users", "read", [[u_id], ["login", "name"]], context=CTX11)
            if info:
                login11[u_id] = info[0]

    def ziel_uid(uid11):
        info = login11.get(uid11)
        if not info:
            return None
        login = (info.get("login") or "").lower()
        if login in BENUTZER_MAPPING:
            return login18.get(BENUTZER_MAPPING[login])
        return login18.get(login) or name18.get(info.get("name"))

    pruefe(len(q) == 10, "Odoo 11 fuehrt %d Hinweise (erwartet 10)" % len(q))
    pruefe(len(z) == len(q), "Odoo 18 hat %d Hinweise mit Anker (Odoo 11: %d)"
           % (len(z), len(q)))

    zeilen18 = {r["itk_o11_id"]: r for r in z}
    inhalt_gleich = 0
    summe11 = summe18 = 0
    for s in q:
        r = zeilen18.get(s["id"])
        if not r:
            pruefe(False, "Hinweis O11 %d fehlt in Odoo 18" % s["id"])
            continue
        pruefe((r["name"] or "").strip() == (s["name"] or "").strip(),
               "Hinweis %d Code gleich" % s["id"])
        pruefe(r["seq"] == s["seq"], "Hinweis %d Nummernfolge gleich (%s)" % (s["id"], r["seq"]))
        soll_text = s["description"] or ""
        ist_text = r["description"] or ""
        summe11 += len(soll_text)
        summe18 += len(ist_text)
        gleich = hashlib.sha1(soll_text.encode("utf-8")).hexdigest() == \
            hashlib.sha1(ist_text.encode("utf-8")).hexdigest()
        pruefe(gleich, "Hinweis %d Beschreibung identisch (%d Zeichen, Pruefsumme)"
               % (s["id"], len(ist_text)))
        if gleich:
            inhalt_gleich += 1
        pruefe((r["create_date"] or "")[:19] == (s["create_date"] or "")[:19],
               "Hinweis %d Erstellungsdatum gleich" % s["id"])
        pruefe(m2o(r["create_uid"]) == ziel_uid(m2o(s["create_uid"])),
               "Hinweis %d Ersteller zugeordnet (%s -> %s)"
               % (s["id"], m2o(s["create_uid"]), m2o(r["create_uid"])))
        pruefe((r["write_date"] or "")[:19] == (s["write_date"] or "")[:19],
               "Hinweis %d Bearbeitungsdatum gleich" % s["id"])

    pruefe(inhalt_gleich == len(q), "Alle %d Beschreibungen identisch" % len(q))
    pruefe(summe11 == summe18, "Summe der Textlaengen gleich (%d Zeichen)" % summe11)

    # --------------------------------------------------------- Rechnungsbezug
    rechnungen11 = o11.kw("account.invoice", "search_count",
                          [[["valorisierung_id", "!=", False]]], context=CTX11)
    anker18 = "itk_o11_id" in o18.kw("account.move", "fields_get", [[], ["type"]])
    verbunden18 = 0
    falsch18 = []
    ids = []
    if anker18:
        bezug11 = {}
        ids11 = o11.kw("account.invoice", "search", [[["valorisierung_id", "!=", False]]],
                       context=CTX11, limit=200000)
        for i in range(0, len(ids11), 1000):
            for r in o11.kw("account.invoice", "read", [ids11[i:i + 1000], ["id",
                                                                            "valorisierung_id"]],
                            context=CTX11):
                bezug11[r["id"]] = m2o(r["valorisierung_id"])
        ziel_valo = {v["itk_o11_id"]: v["id"] for v in
                     o18.kw(MODELL, "search_read", [[["itk_o11_id", "!=", False]],
                                                    ["id", "itk_o11_id"]],
                            context=CTX18, limit=1000)}
        ids = o18.kw("account.move", "search", [[["itk_o11_id", "!=", False]]], context=CTX18,
                     limit=200000)
        for i in range(0, len(ids), 1000):
            for r in o18.kw("account.move", "read",
                            [ids[i:i + 1000], ["id", "itk_o11_id", "valorisierung_id"]],
                            context=CTX18):
                o11_id = r["itk_o11_id"]
                if o11_id not in bezug11:
                    if m2o(r.get("valorisierung_id")):
                        falsch18.append((o11_id, "Odoo-11-Rechnung ohne Hinweis"))
                    continue
                if m2o(r.get("valorisierung_id")) == ziel_valo.get(bezug11[o11_id]):
                    verbunden18 += 1
                else:
                    falsch18.append((o11_id, "falscher oder fehlender Hinweis"))
    print("  Rechnungen mit Hinweis: Odoo 11 = %d, in Odoo 18 verbunden = %d (Anker: %s)"
          % (rechnungen11, verbunden18, anker18))
    offen = 0
    if anker18 and not ids:
        offen += 1
        print("  OFFEN  Rechnungsverknuepfung nicht pruefbar: Anker vorhanden, aber keine "
              "migrierte Rechnung. Externe Abhaengigkeit Abrechnung (%d Verknuepfungen)."
              % rechnungen11)
    elif anker18:
        pruefe(not falsch18 and verbunden18 == rechnungen11,
               "Rechnungsverknuepfung fachlich vollstaendig (%d von %d, %d Abweichungen)"
               % (verbunden18, rechnungen11, len(falsch18)))
        for o11_id, grund in falsch18[:10]:
            print("       Abweichung Rechnung O11 %s: %s" % (o11_id, grund))
    else:
        print("  OFFENE EXTERNE ABHAENGIGKEIT ABRECHNUNG: %d Rechnungsverknuepfungen "
              "koennen erst nach der Rechnungsmigration gesetzt werden. Nachlauf: "
              "valorisierung_migration.py --nachlauf-rechnungen (Trockenlauf) bzw. "
              "mit --ausfuehren --ich-habe-freigabe.")

    # ------------------------------------------------------------- Sonderfall
    ohne_anker = o18.kw(MODELL, "search_count", [[["itk_o11_id", "=", False]]],
                        context=CTX18)
    print("  Saetze ohne Odoo-11-Anker in Odoo 18: %d (Testdatensatz, dokumentiert)"
          % ohne_anker)

    print()
    print("--- Ergebnis ---")
    print("Pruefungen OK ............... %d" % ok)
    print("Abweichungen ................ %d" % fehler)
    print("Offene externe Abhaengigkeiten %d (Rechnungsverknuepfung Abrechnung)" % offen)
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
