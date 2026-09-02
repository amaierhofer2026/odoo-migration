#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ITK Abschnitt-1-Korrekturen (Freigabe Anna 02.09.2026, Session 81).
Setzt gezielte de_DE-Slots (Menues, Actions, Felder) per ORM-write mit lang-Context
(jsonb_set-Aequivalent) gegen die VM (https://k001959vsx.ipax.at, DB odoo18_test,
Credentials aus C:\Odoo-Test\.env ODOO18_*). Idempotent; nach jedem Restore aus einem
Backup VOR dem Fix erneut ausfuehren (bzw. beim naechsten Setup-Lauf).
Nur dokumentierte Stellen - keine globale Ersetzung.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Freigabe Anna 02.09.: Encoding-Fixes VM - res_currency-Symbole (EUR->€ u. a. defekte),
F26 (3 de_DE-Uebersetzungs-Mojibake), F7 account_payment shortdesc."""
import json, os, re, urllib.request, http.cookiejar

URL = "https://k001959vsx.ipax.at"
env = {}
for line in open(r"C:\Odoo-Test\.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
DB, LOGIN, PWD = env.get("ODOO18_DB", "odoo18_test"), env.get("ODOO18_USER", ""), env.get("ODOO18_PWD", "")
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def rpc(url, params, timeout=120):
    body = json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode())
    if "error" in resp:
        raise RuntimeError("RPC-Fehler: %s" % str(resp["error"])[:400])
    return resp.get("result")
res = rpc(URL + "/web/session/authenticate", {"db": DB, "login": LOGIN, "password": PWD})
uid = res.get("uid")
def exec_kw(model, method, args=None, kwargs=None):
    return rpc(URL + "/web/dataset/call_kw", {"model": model, "method": method,
               "args": args or [], "kwargs": kwargs or {}})

# --- 1) res_currency Symbole ---
MOJI = re.compile(r"[\u251c\u00d4\u00e2\u201a\u00ac\u2514\u2500\u252c\u2534\u253c\u2550\u258c\u2590\u2588\u017e\u00c5\u00c9\u00cd\u2502\u2518]")
CUR_SYM = {"EUR": "\u20ac", "USD": "$", "GBP": "\u00a3", "CZK": "K\u010d", "PLN": "z\u0142",
           "CHF": "CHF", "SEK": "kr", "DKK": "kr", "HUF": "Ft", "HRK": "kn", "RON": "lei",
           "BGN": "lv", "NOK": "kr", "PLN": "z\u0142"}
cur = exec_kw("res.currency", "search_read", [[], ["id", "name", "symbol", "active", "position"]])
print("Waehrungen gesamt:", len(cur))
for c in cur:
    sym = c.get("symbol") or ""
    code = (c.get("name") or "")
    if MOJI.search(sym):
        target = CUR_SYM.get(code, "?")
        if target == "?":
            print("  KEIN ZIEL bekannt fuer %s (id %s): %r" % (code, c["id"], sym))
            continue
        exec_kw("res.currency", "write", [[c["id"]], {"symbol": target}])
        print("  res.currency %s (id %s): %r -> %r" % (code, c["id"], sym, target))

# --- 2) F26: de_DE-Uebersetzungs-Mojibake ---
def fix_field_de(model, name, de_text):
    f = exec_kw("ir.model.fields", "search_read", [[["model", "=", model], ["name", "=", name]], ["id"]])
    if not f:
        print("  Feld nicht gefunden: %s.%s" % (model, name))
        return
    exec_kw("ir.model.fields", "write", [[f[0]["id"]], {"field_description": de_text}], {"context": {"lang": "de_DE"}})
    print("  ir.model.fields %s.%s de -> %r" % (model, name, de_text))

fix_field_de("account.move", "status_in_payment", "Status \u201eIn Zahlung\u201c")
fix_field_de("account.reconcile.model.line", "show_force_tax_included", "\u201eSteuer inklusive erzwingen\u201c anzeigen")

# peppol_eas Auswahlwert 0245 (res.partner) - alle Modelle mit dem Feld abdecken
for model in ("res.partner", "res.users", "res.company"):
    f = exec_kw("ir.model.fields", "search_read", [[["model", "=", model], ["name", "=", "peppol_eas"]], ["id"]])
    if not f:
        continue
    sel = exec_kw("ir.model.fields.selection", "search_read",
                  [[["field_id", "=", f[0]["id"]], ["value", "=", "0245"]], ["id"]])
    if sel:
        exec_kw("ir.model.fields.selection", "write", [[sel[0]["id"]], {"name": "SK-Steueridentifikationsnummer (DI\u010d)"}],
                {"context": {"lang": "de_DE"}})
        print("  selection peppol_eas/0245 (%s) de -> 'SK-Steueridentifikationsnummer (DI\u010d)'" % model)

# --- 3) F7: account_payment shortdesc (nur Encoding: En-Dash korrekt) ---
mod = exec_kw("ir.module.module", "search_read", [[["name", "=", "account_payment"]], ["id", "shortdesc"]],
              {"context": {"lang": "de_DE"}})
if mod:
    exec_kw("ir.module.module", "write", [[mod[0]["id"]], {"shortdesc": "Zahlung \u2013 Konto"}], {"context": {"lang": "de_DE"}})
    print("  account_payment shortdesc de -> 'Zahlung \u2013 Konto' (war: %r)" % (mod[0].get("shortdesc"),))
print("FERTIG")
