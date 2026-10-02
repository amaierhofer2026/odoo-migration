"""Zeigt den vollstaendigen Serverfehler des Zahlungsformulars."""
import http.cookiejar
import json
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

env = lade_env(r"C:/Odoo-Test/.env")
url = "https://k001959vsx.ipax.at" if sys.argv[1:2] == ["vm"] else "http://localhost:8069"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=60)
sid = next(c.value for c in jar if c.name == "session_id")

daten = {"jsonrpc": "2.0", "method": "call", "params": {
    "model": "account.payment", "method": "get_views",
    "args": [[[False, "form"]]], "kwargs": {"context": {"lang": "de_DE"}}}}
req = urllib.request.Request(url + "/web/dataset/call_kw", data=json.dumps(daten).encode(),
                             headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
antwort = json.loads(op.open(req, timeout=120).read().decode())
if "error" in antwort:
    fehler = antwort["error"]["data"]
    print("FEHLERART:", fehler.get("name"))
    print("MELDUNG  :", (fehler.get("message") or "")[:500])
    debug = (fehler.get("debug") or "").strip().splitlines()
    print("--- letzte Zeilen ---")
    for zeile in debug[-12:]:
        print("   " + zeile.strip()[:200])
else:
    print("Kein Fehler - Arch geladen")
