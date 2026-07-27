#!/usr/bin/env python3
"""
Validierungsskript: Odoo 11 → Odoo 18 Kontakt-Integrität
Vergleicht migrierte Kontakte auf Feld-Ebene und gibt Abweichungen aus.

Verwendung: python3 validate_contacts.py
Voraussetzung: Odoo 11 (93.189.28.204) und Odoo 18 (192.168.56.1:8069) müssen laufen.
"""

import json
import urllib.request
import sys

# ─── Konfiguration ───
O11_URL = "http://93.189.28.204:8069"
O11_DB = "ITK_V1_a"
O11_USER = "anna.maierhofer@it-kommunal.at"
O11_PW = "anma120126!"

O18_URL = "http://192.168.56.1:8069"
O18_DB = "odoo18_test"
O18_USER = "anna.maierhofer@it-kommunal.at"
O18_PW = "PulIqN8j"

# Felder für Vergleich — mit Anzeigenamen
COMPARE_FIELDS = [
    ("name", "Name"),
    ("ref", "GKZ"),
    ("vat", "UID"),
    ("email", "E-Mail"),
    ("phone", "Telefon"),
    ("mobile", "Mobil"),
    ("website", "Website"),
    ("lang", "Sprache"),
    ("street", "Strasse"),
    ("zip", "PLZ"),
    ("city", "Ort"),
    ("type", "Kontaktart"),
    ("is_company", "Ist Unternehmen"),
    ("active", "Aktiv"),
    ("comment", "Notizen"),
    ("function", "Funktion"),
    ("population", "Einwohnerzahl"),
    ("community_magnitude", "Groessenklasse"),
    ("multi_factor", "Multiplikations-Faktor"),
    ("trust", "Vertrauen"),
    ("total_invoiced", "Fakturiert"),
    ("sale_order_count", "Anzahl Verkaufsauftraege"),
    ("subscription_count", "Anzahl Abonnements"),
    ("opportunity_count", "Anzahl Chancen"),
    ("meeting_count", "Anzahl Meetings"),
]

RELATION_FIELDS = [
    ("user_id", "Verkaeufer", "res.users"),
    ("state_id", "Bundesland", "res.country.state"),
    ("country_id", "Land", "res.country"),
    ("status_of_community", "Gemeindestatus", "itk_crm.statusofcommunity"),
    ("category_id", "Tags", "res.partner.category"),
    ("parent_id", "Uebergeordnet", "res.partner"),
]


def rpc_o11(service, method, args, cookie):
    payload = {"jsonrpc": "2.0", "method": "call",
               "params": {"service": service, "method": method, "args": args}}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{O11_URL}/jsonrpc", data=data,
                                  headers={"Content-Type": "application/json"})
    req.add_header("Cookie", cookie)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read()).get("result")


def rpc_o18(service, method, args, kwargs=None):
    payload = {"jsonrpc": "2.0", "method": "call",
               "params": {"service": service, "method": method, "args": args}, "id": 1}
    if kwargs:
        payload["params"]["kwargs"] = kwargs
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{O18_URL}/jsonrpc", data=data,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read()).get("result")


def auth_o11():
    ap = json.dumps({"jsonrpc": "2.0", "method": "call",
                      "params": {"db": O11_DB, "login": O11_USER, "password": O11_PW}}).encode()
    req = urllib.request.Request(f"{O11_URL}/web/session/authenticate",
                                  data=ap, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        for c in resp.headers.get_all("Set-Cookie"):
            if "session_id=" in c:
                return f"session_id={c.split('session_id=')[1].split(';')[0]}"


def main():
    print("=" * 70)
    print("Kontakt-Validierung Odoo 11 → Odoo 18")
    print("=" * 70)

    # Auth
    print("\nVerbinde...")
    ck = auth_o11()
    o18_uid = rpc_o18("common", "authenticate", [O18_DB, O18_USER, O18_PW, {}])
    print(f"O18 verbunden (uid={o18_uid})")

    # Alle O18-Kontakte mit ref holen
    print("\nLade O18-Kontakte...")
    o18_all = rpc_o18("object", "execute_kw",
                       [O18_DB, o18_uid, O18_PW, "res.partner", "search_read",
                        [[["ref", "!=", False]]]],
                       {"fields": ["ref"] + [f[0] for f in COMPARE_FIELDS] +
                        [f[0] for f in RELATION_FIELDS] + ["child_ids"]})

    if not o18_all:
        print("KEINE migrierten Kontakte in O18 gefunden!")
        return 1

    print(f"{len(o18_all)} Kontakte in O18 mit ref gefunden.")

    results = []
    critical = 0
    warning = 0
    ok_count = 0

    for o18p in o18_all:
        ref = o18p["ref"]
        name = o18p.get("name", "?")
        diffs = []

        # O11-Partner suchen
        o11p_list = rpc_o11("object", "execute_kw",
                             [O11_DB, 87, O11_PW, "res.partner", "search_read",
                              [[["ref", "=", ref]]]],
                             {"fields": [f[0] for f in COMPARE_FIELDS] +
                              [f[0] for f in RELATION_FIELDS]},
                             cookie=ck)

        if not o11p_list:
            print(f"\n  {ref} ({name}): ⚠ NICHT IN ODOO 11 GEFUNDEN")
            warning += 1
            continue

        o11p = o11p_list[0]

        # Direkte Felder vergleichen
        for fname, flabel in COMPARE_FIELDS:
            v11 = o11p.get(fname)
            v18 = o18p.get(fname)
            # Normalisieren
            if v11 is False:
                v11 = ""
            if v18 is False:
                v18 = ""
            if fname == "vat" and not v11:
                v11 = ""
            if fname == "vat" and not v18:
                v18 = ""
            if str(v11).strip() != str(v18).strip():
                diffs.append(("Feld", flabel, str(v11)[:80], str(v18)[:80]))

        # Relations-Felder vergleichen (nur IDs)
        for fname, flabel, model in RELATION_FIELDS:
            v11 = o11p.get(fname)
            v18 = o18p.get(fname)
            if v11 and isinstance(v11, list):
                v11 = v11[0]
            if v18 and isinstance(v18, list):
                v18 = v18[0]
            if not v11 and not v18:
                continue
            if v11 != v18:
                diffs.append(("Relation", flabel, str(v11), str(v18)))

        # Children count
        c11 = len(o11p.get("child_ids", []) or [])
        c18 = len(o18p.get("child_ids", []) or [])
        if c11 != c18:
            diffs.append(("Count", "Unterkontakte", str(c11), str(c18)))

        if diffs:
            critical += 1
            print(f"\n  {ref} ({name}): ✗ {len(diffs)} Abweichungen")
            for cat, field, v11, v18 in diffs:
                print(f"    [{cat}] {field}: O11='{v11}' → O18='{v18}'")
        else:
            ok_count += 1

        results.append((ref, name, diffs))

    # Summary
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"  Geprüfte Kontakte: {len(results)}")
    print(f"  ✓ OK:              {ok_count}")
    print(f"  ✗ Abweichungen:    {critical}")
    print(f"  ⚠ Nicht in O11:    {warning}")

    if critical > 0:
        print(f"\n  FAZIT: {critical} Kontakte mit Abweichungen — Migration NICHT bereit!")
        return 1
    else:
        print(f"\n  FAZIT: Alle Kontakte fehlerfrei — Migration bereit ✓")
        return 0


if __name__ == "__main__":
    sys.exit(main())
