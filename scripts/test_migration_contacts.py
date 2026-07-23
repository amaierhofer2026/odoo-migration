#!/usr/bin/env python3
"""
Test-Migration: 15 Kontakte von Odoo 11 nach Odoo 18
Reproduzierbar, idempotent, mit Migrations-ID-Tracking.
"""
import json, urllib.request, ssl, http.cookiejar, time, sys

# === Konfiguration ===
ODOO11_URL = "https://93.189.28.204"
ODOO11_DB = "ITK_V1_a"
ODOO11_USER = "anna.maierhofer@it-kommunal.at"
ODOO11_PWD = "anma120126!"

ODOO18_URL = "http://192.168.56.1:8069"
ODOO18_DB = "odoo18_test"
ODOO18_USER = "anna.maierhofer@it-kommunal.at"
ODOO18_PWD = "PulIqN8j"

# === Odoo 11 Verbindung (mit SSL-Ignore) ===
ctx11 = ssl.create_default_context()
ctx11.check_hostname = False
ctx11.verify_mode = ssl.CERT_NONE
cj11 = http.cookiejar.CookieJar()
opener11 = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx11),
                                        urllib.request.HTTPCookieProcessor(cj11))

def rpc11(service, method, args, kwargs=None):
    payload = {"jsonrpc": "2.0", "method": "call",
               "params": {"service": service, "method": method, "args": args}}
    if kwargs: payload["params"]["kwargs"] = kwargs
    data = json.dumps(payload).encode()
    req = urllib.request.Request(ODOO11_URL + "/jsonrpc", data=data,
                                 headers={"Content-Type": "application/json"})
    with opener11.open(req, timeout=30) as resp:
        return json.loads(resp.read()).get("result")

# Auth Odoo 11
auth11 = {"jsonrpc": "2.0", "method": "call",
          "params": {"db": ODOO11_DB, "login": ODOO11_USER, "password": ODOO11_PWD}}
req11 = urllib.request.Request(ODOO11_URL + "/web/session/authenticate",
                                data=json.dumps(auth11).encode(),
                                headers={"Content-Type": "application/json"})
with opener11.open(req11, timeout=30) as resp:
    uid11 = json.loads(resp.read()).get("result", {}).get("uid")

# === Odoo 18 Verbindung ===
def rpc18(service, method, args, kwargs=None):
    payload = {"jsonrpc": "2.0", "method": "call",
               "params": {"service": service, "method": method, "args": args}}
    if kwargs: payload["params"]["kwargs"] = kwargs
    data = json.dumps(payload).encode()
    req = urllib.request.Request(ODOO18_URL + "/jsonrpc", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read()).get("result")

uid18 = rpc18("common", "authenticate", [ODOO18_DB, ODOO18_USER, ODOO18_PWD, {}])

# === Vorbereitung: Lookup-Caches ===
# States
states18 = {s["name"]: s["id"] for s in rpc18("object", "execute_kw", [
    ODOO18_DB, uid18, ODOO18_PWD, "res.country.state", "search_read",
    [[["country_id.code", "=", "AT"]]], {"fields": ["id", "name"]}
])}
# Users (by login email)
users18 = {u["login"]: u["id"] for u in rpc18("object", "execute_kw", [
    ODOO18_DB, uid18, ODOO18_PWD, "res.users", "search_read",
    [[["share", "=", False]]], {"fields": ["id", "name", "login"]}
])}
# Tags
tags18 = {t["name"]: t["id"] for t in rpc18("object", "execute_kw", [
    ODOO18_DB, uid18, ODOO18_PWD, "res.partner.category", "search_read",
    [[]], {"fields": ["id", "name"]}
])}
# Status
status18 = {s["name"]: s["id"] for s in rpc18("object", "execute_kw", [
    ODOO18_DB, uid18, ODOO18_PWD, "itk_crm.statusofpartner", "search_read",
    [[]], {"fields": ["id", "name"]}
])}

# User mapping Odoo11→Odoo18 (by login email)
user11 = {u["id"]: u for u in rpc11("object", "execute_kw", [
    ODOO11_DB, uid11, ODOO11_PWD, "res.users", "read",
    [[14, 17, 21, 63], ["id", "login", "name"]]
])}
user_map = {}
for u in user11.values():
    login = u["login"]
    if login in users18:
        user_map[u["id"]] = users18[login]
    else:
        # Fallback: try by name
        found = False
        for u18_login, u18_id in users18.items():
            if u["name"].lower() in u18_login.lower() or u18_login.lower() in u["name"].lower():
                user_map[u["id"]] = u18_id
                found = True
                break
        if not found:
            user_map[u["id"]] = None  # No match

# State mapping by name
state11_map = {
    "Burgenland": "Burgenland",
    "Kärnten": "Kärnten",
    "Niederösterreich": "Niederösterreich",
    "Oberösterreich": "Oberösterreich",
    "Salzburg": "Salzburg",
    "Steiermark": "Steiermark",
    "Tirol": "Tirol",
    "Vorarlberg": "Vorarlberg",
    "Wien": "Wien",
}

# === Ausgewählte Kontakte ===
# (Odoo11-ID, Migrations-ID, Typ)
TEST_CONTACTS = [
    (5792, "MIG-TEST-001", "Gemeinde aktiv mit GKZ"),
    (5793, "MIG-TEST-002", "Gemeinde aktiv mit GKZ"),
    (5796, "MIG-TEST-003", "Gemeinde aktiv mit GKZ, kein Kunde"),
    (5794, "MIG-TEST-004", "Gemeinde aktiv mit GKZ und Tags"),
    (12025, "MIG-TEST-005", "Unternehmen aktiv mit UID"),
    (13406, "MIG-TEST-006", "Unternehmen aktiv mit UID und Email offiziell"),
    (10288, "MIG-TEST-007", "Unternehmen mit Parent"),
    (9449, "MIG-TEST-008", "Einzelperson mit Parent (Bürgermeister)"),
    (9285, "MIG-TEST-009", "Einzelperson mit Parent (Bürgermeister)"),
    (13659, "MIG-TEST-010", "Einzelperson mit Parent, Telefon, Tags"),
    (10429, "MIG-TEST-011", "Einzelperson mit Verkäufer"),
    (13184, "MIG-TEST-012", "Einzelperson standalone, Telefon"),
    (10902, "MIG-TEST-013", "Einzelperson standalone, Telefon, Verkäufer"),
    (7469, "MIG-TEST-014", "Gemeinde ARCHIVIERT"),
    (10686, "MIG-TEST-015", "Unternehmen ARCHIVIERT"),
]

# === Migration ===
MIGRATION_REF_FIELD = "ref"  # Using GKZ field to store migration reference
results = {"imported": 0, "skipped": 0, "errors": 0, "details": []}

# Hole alle Kontaktdaten aus Odoo 11
ids11 = [t[0] for t in TEST_CONTACTS]
fields11 = ["id", "name", "is_company", "company_type", "active", "ref", "customer", "supplier",
            "street", "street2", "zip", "city", "state_id", "country_id", "vat",
            "user_id", "phone", "mobile", "email", "website", "lang",
            "category_id", "parent_id", "function",
            "attention_of", "community_salutation", "status_of_partner_id",
            "official_email", "multi_factor", "image"]
partners11 = {p["id"]: p for p in rpc11("object", "execute_kw", [
    ODOO11_DB, uid11, ODOO11_PWD, "res.partner", "read", [ids11, fields11]
])}

print(f"Odoo 18 Partner vor Import: {rpc18('object', 'execute_kw', [ODOO18_DB, uid18, ODOO18_PWD, 'res.partner', 'search_count', [[]]])}")
print(f"Starte Import von {len(TEST_CONTACTS)} Test-Kontakten...\n")

for odoo11_id, mig_id, desc in TEST_CONTACTS:
    p11 = partners11[odoo11_id]
    name = p11["name"]
    print(f"[{mig_id}] {name} ({desc})")

    # Prüfe ob bereits existiert (via GKZ/ref)
    gkz = p11.get("ref") or ""
    existing = False
    if gkz:
        existing_ids = rpc18("object", "execute_kw", [
            ODOO18_DB, uid18, ODOO18_PWD, "res.partner", "search",
            [[["ref", "=", gkz]]]
        ])
        if existing_ids:
            print(f"  ⚠️  Existiert bereits mit GKZ='{gkz}' → id={existing_ids[0]} → ÜBERSPRUNGEN")
            results["skipped"] += 1
            results["details"].append({"mig_id": mig_id, "status": "skipped", "reason": f"GKZ {gkz} exists"})
            continue

    # E-Mail-Check
    email = p11.get("email") or ""
    if email and email != "False":
        existing_ids = rpc18("object", "execute_kw", [
            ODOO18_DB, uid18, ODOO18_PWD, "res.partner", "search",
            [[["email", "=", email]]]
        ])
        if existing_ids:
            print(f"  ⚠️  Existiert bereits mit Email='{email}' → id={existing_ids[0]} → ÜBERSPRUNGEN")
            results["skipped"] += 1
            results["details"].append({"mig_id": mig_id, "status": "skipped", "reason": f"Email {email} exists"})
            continue

    # === Feld-Mapping ===
    vals = {
        "name": name,
        "is_company": p11.get("is_company", False),
        "company_type": "company" if p11.get("is_company") else "person",
        "active": p11.get("active", True),
        "street": (p11.get("street") or "").strip() if p11.get("street") else "",
        "street2": (p11.get("street2") or "").strip() if p11.get("street2") else "",
        "zip": (p11.get("zip") or "").strip() if p11.get("zip") else "",
        "city": (p11.get("city") or "").strip() if p11.get("city") else "",
        "vat": (p11.get("vat") or "").strip() if p11.get("vat") and p11.get("vat") != "False" else "",
        "phone": (p11.get("phone") or "").strip() if p11.get("phone") else "",
        "mobile": (p11.get("mobile") or "").strip() if p11.get("mobile") else "",
        "email": (p11.get("email") or "").strip() if p11.get("email") and p11.get("email") != "False" else "",
        "website": (p11.get("website") or "").strip() if p11.get("website") and p11.get("website") != "False" else "",
        "lang": p11.get("lang") or "de_DE",
        "function": (p11.get("function") or "").strip() if p11.get("function") else "",
        "ref": gkz,
    }

    # GKZ: nur setzen wenn tatsächlich vorhanden
    if not vals["ref"]:
        del vals["ref"]  # keine GKZ → Feld nicht setzen

    # Country (Austria = 12)
    if p11.get("country_id") and p11["country_id"][0] == 12:
        vals["country_id"] = 12

    # State mapping
    if p11.get("state_id"):
        state_name11 = p11["state_id"][1]
        state_name18 = state11_map.get(state_name11, state_name11)
        if state_name18 in states18:
            vals["state_id"] = states18[state_name18]

    # User/Salesperson
    if p11.get("user_id"):
        u11_id = p11["user_id"][0]
        u18_id = user_map.get(u11_id)
        if u18_id:
            vals["user_id"] = u18_id

    # Status of Partner
    if p11.get("status_of_partner_id"):
        s11_name = p11["status_of_partner_id"][1]
        if s11_name in status18:
            vals["status_of_partner_id"] = status18[s11_name]

    # Customer/Supplier ranks
    if p11.get("customer"):
        vals["customer_rank"] = 1
    if p11.get("supplier"):
        vals["supplier_rank"] = 1

    # Tags
    if p11.get("category_id"):
        tag_ids = []
        for tid in p11["category_id"]:
            tag11 = rpc11("object", "execute_kw", [
                ODOO11_DB, uid11, ODOO11_PWD, "res.partner.category", "read",
                [[tid], ["name"]]
            ])
            if tag11:
                tag_name = tag11[0]["name"]
                if tag_name in tags18:
                    tag_ids.append(tags18[tag_name])
                else:
                    # Create tag
                    new_id = rpc18("object", "execute_kw", [
                        ODOO18_DB, uid18, ODOO18_PWD, "res.partner.category", "create",
                        [{"name": tag_name}]
                    ])
                    tags18[tag_name] = new_id
                    tag_ids.append(new_id)
        if tag_ids:
            vals["category_id"] = [(6, 0, tag_ids)]

    # ITK fields
    if p11.get("attention_of") and p11["attention_of"] != "False":
        vals["attention_of"] = p11["attention_of"]
    if p11.get("community_salutation") and p11["community_salutation"] != "False":
        vals["community_salutation"] = p11["community_salutation"]
    if p11.get("official_email") and p11["official_email"] != "False":
        vals["official_email"] = p11["official_email"]
    if p11.get("multi_factor") is not None and p11["multi_factor"] != 0:
        vals["multi_factor"] = p11["multi_factor"]

    # Bild/Logo (Odoo 11: image → Odoo 18: image_1920, beide base64)
    if p11.get("image") and p11["image"] != "False":
        vals["image_1920"] = p11["image"]

    # === CREATE in Odoo 18 ===
    try:
        new_id = rpc18("object", "execute_kw", [
            ODOO18_DB, uid18, ODOO18_PWD, "res.partner", "create", [vals]
        ])
        print(f"  ✓ Erstellt als id={new_id}")
        results["imported"] += 1
        results["details"].append({
            "mig_id": mig_id, "odoo11_id": odoo11_id, "odoo18_id": new_id,
            "status": "imported", "name": name
        })
    except Exception as e:
        print(f"  ✗ FEHLER: {e}")
        results["errors"] += 1
        results["details"].append({
            "mig_id": mig_id, "odoo11_id": odoo11_id,
            "status": "error", "name": name, "error": str(e)
        })

# === Ergebnis ===
count_after = rpc18("object", "execute_kw", [
    ODOO18_DB, uid18, ODOO18_PWD, "res.partner", "search_count", [[]]
])
print(f"\n{'='*60}")
print(f"Odoo 18 Partner nach Import: {count_after}")
print(f"Importiert: {results['imported']}")
print(f"Übersprungen: {results['skipped']}")
print(f"Fehler: {results['errors']}")
print(f"\nDetails:")
for d in results["details"]:
    print(f"  {d['mig_id']}: {d['status']} - {d.get('name','?')}")
    if d.get("odoo18_id"):
        print(f"    Odoo18 ID: {d['odoo18_id']}")
