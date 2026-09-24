"""Read-only RPC-Client fuer Odoo 11 Prod (nur oeffnende Aufrufe) und Odoo 18 (lokal/VM)."""
from __future__ import annotations

import http.cookiejar
import json
import os
import ssl
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def lade_env(pfad: str = None) -> dict:
    pfad = pfad or os.path.join(REPO, ".env")
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


class Client:
    def __init__(self, url: str, db: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar),
            urllib.request.HTTPSHandler(context=_CTX))
        self.rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def rufe(self, pfad: str, params: dict):
        req = urllib.request.Request(
            self.url + pfad,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=300) as antwort:
            daten = json.loads(antwort.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:500])
        return daten.get("result")

    def kw(self, model: str, methode: str, args: list, **kwargs):
        return self.rufe("/web/dataset/call_kw",
                         {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def o11() -> Client:
    """Odoo 11 Prod - ausschliesslich lesende Aufrufe."""
    e = lade_env()
    return Client("https://portal.it-kommunal.at", "ITK_V1_a", e["ODOO11_USER"], e["ODOO11_PWD"])


def o18(instanz: str = "lokal") -> Client:
    e = lade_env()
    url = e.get("ODOO18_URL", "http://localhost:8069") if instanz == "lokal" else "https://k001959vsx.ipax.at"
    return Client(url, e["ODOO18_DB"], e["ODOO18_USER"], e["ODOO18_PWD"])
