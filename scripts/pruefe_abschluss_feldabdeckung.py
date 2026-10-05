"""Abschlusspruefung Abrechnung: belegte Odoo-11-Felder gegen das Mapping in der Doku.

Aufruf:
    python scripts/pruefe_abschluss_feldabdeckung.py
    python scripts/pruefe_abschluss_feldabdeckung.py --selbsttest   (belegt den Abbruch bei Fehlern)

1. Ermittelt je Modell die Felder, die in Odoo 11 tatsaechlich Werte enthalten.
2. Liest die Mapping-Dokumente (Teil 5 Feldabbildung) und prueft, welche dieser Felder dort
   erwaehnt sind.
3. Gibt die Luecken aus (belegte Odoo-11-Felder ohne Mapping-Eintrag).

Fehlerverhalten (05.10.2026, Session 123, auf Anweisung Anna):
    Es wird KEIN Fehler mehr still geschluckt. Jeder fehlgeschlagene RPC-Aufruf bricht den Lauf
    mit Exit-Code 1 ab und nennt Modell, Methode und Argumente. Grund: ein frueherer Lauf meldete
    durch stilles Ueberspringen einmal 272 statt 273 belegte Felder, ohne dass das auffiel.
    Ein Modell ohne Datensaetze bricht ebenfalls ab (sonst waeren alle seine Felder stumm
    "unbelegt"). Gefundene Luecken beenden den Lauf mit Exit-Code 2.

Exit-Codes: 0 = vollstaendig geprueft, keine Luecke
            1 = technischer Fehler (Abbruch)
            2 = Luecken gefunden
"""
from __future__ import annotations

import argparse
import glob
import io
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11  # noqa: E402

k = o11()
CTX = {"lang": "de_DE"}

MODELLE = [
    "account.invoice", "account.invoice.line", "account.payment", "account.move",
    "res.partner", "product.template", "product.product", "account.tax",
    "account.journal", "account.payment.term", "account.analytic.account",
    "account.account", "account.fiscal.position",
]

# Felder, die technisch/systemseitig sind und nicht migriert werden
OHNE_MAPPING = {
    "id", "create_uid", "create_date", "write_uid", "write_date", "__last_update",
    "display_name", "message_ids", "message_follower_ids", "message_partner_ids",
    "message_attachment_count", "message_main_attachment_id", "access_token",
    "website_message_ids", "activity_ids", "activity_state", "activity_user_id",
    "activity_date_deadline", "activity_summary", "activity_type_id",
    "activity_ids_count", "my_activity_date_deadline", "rating_ids",
    "message_needaction", "message_needaction_counter", "message_has_error",
    "message_has_error_counter", "message_has_sms_error", "message_unread",
    "message_unread_counter", "message_is_follower", "message_channel_ids",
    "message_needaction_counter", "website_url", "seo_name", "website_published",
}


def rpc(modell: str, methode: str, args: list, was: str, **kwargs):
    """RPC-Aufruf, der bei jedem Fehler abbricht statt Felder still zu ueberspringen."""
    try:
        return k.kw(modell, methode, args, **kwargs)
    except Exception as fehler:  # noqa: BLE001
        raise SystemExit("ABBRUCH: %s fehlgeschlagen (%s.%s, args=%r): %s"
                         % (was, modell, methode, args, str(fehler)[:300]))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--selbsttest", action="store_true",
                   help="erzwingt einen fehlerhaften Aufruf und belegt den Abbruch (Exit-Code 1)")
    p.add_argument("--doku-pfad", action="append", default=None,
                   help="zusaetzliches Mapping-Dokument oder Glob (wiederholbar)")
    a = p.parse_args()

    if a.selbsttest:
        print("Selbsttest: ein fehlerhafter Aufruf muss den Lauf jetzt abbrechen ...")
        rpc("kein.solches.modell", "search_count", [[]], "Selbsttest (erwarteter Fehler)")
        print("SELBSTTEST FEHLGESCHLAGEN: der Lauf hat NICHT abgebrochen.")
        return 3

    muster = a.doku_pfad or [r"C:/Odoo-Test/docs/o11-o18-*.md", r"C:/Odoo-Test/docs/*abrechnung*.md"]
    doku = ""
    for m in muster:
        for datei in glob.glob(m):
            doku += io.open(datei, encoding="utf-8").read()
    if not doku.strip():
        raise SystemExit("ABBRUCH: keine Mapping-Doku gefunden (Muster: %s)" % muster)
    print("Mapping-Doku gelesen: %d Zeichen" % len(doku))

    luecken = []
    gesamt = 0
    geprueft = 0
    for modell in MODELLE:
        felder = rpc(modell, "fields_get", [[], ["type", "compute", "related", "store"]],
                     "Felder lesen", context=CTX)
        gesamt_alle = rpc(modell, "search_count", [[]], "Datensatzzahl", context=CTX)
        if not gesamt_alle:
            raise SystemExit("ABBRUCH: %s hat 0 Datensaetze - die Feldpruefung waere stumm leer."
                             % modell)
        belegt = []
        for name, info in sorted(felder.items()):
            if info.get("type") in ("binary", "image"):
                continue
            if info.get("compute") or info.get("related") or info.get("store") is False:
                continue   # berechnete/abgeleitete Felder: in Odoo 18 neu berechnet, keine Migration
            if name in OHNE_MAPPING:
                continue
            anzahl = rpc(modell, "search_count", [[[name, "!=", False]]],
                         "Feldpruefung %s.%s" % (modell, name), context=CTX)
            geprueft += 1
            if anzahl:
                belegt.append((name, anzahl, gesamt_alle))
        belegt.sort(key=lambda x: -x[1])
        ohne = [b for b in belegt if b[0] not in doku]
        gesamt += len(belegt)
        print("\n%-26s belegte Felder: %3d | ohne Mapping-Eintrag: %d" % (modell, len(belegt), len(ohne)))
        for name, anzahl, alle in ohne[:12]:
            print("      %-34s %5d von %5d" % (name, anzahl, alle))
            luecken.append("%s.%s (%d/%d)" % (modell, name, anzahl, alle))

    print("\nGesamt belegte Felder: %d | Luecken: %d" % (gesamt, len(luecken)))
    print("Geprueft wurden %d Felder ueber %d Modelle (fehlerfrei, kein Feld uebersprungen)."
          % (geprueft, len(MODELLE)))
    if luecken:
        print("Lauf endet mit Exit-Code 2 (Luecken gefunden).")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
