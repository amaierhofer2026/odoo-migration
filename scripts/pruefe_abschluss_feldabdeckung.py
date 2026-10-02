"""Abschlusspruefung Abrechnung: belegte Odoo-11-Felder gegen das Mapping in der Doku.

Aufruf: python scripts/pruefe_abschluss_feldabdeckung.py
1. Ermittelt je Modell die Felder, die in Odoo 11 tatsaechlich Werte enthalten.
2. Liest die Mapping-Dokumente (Teil 5 Feldabbildung) und prueft, welche dieser Felder dort
   erwaehnt sind.
3. Gibt die Luecken aus (belegte Odoo-11-Felder ohne Mapping-Eintrag).
"""
import glob
import io
import os
import re
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

doku = ""
for muster in (r"C:/Odoo-Test/docs/o11-o18-vergleich-abrechnung-teil5-feldabbildung.md",
               r"C:/Odoo-Test/docs/o11-o18-vergleich-abrechnung-teil5-umsetzung.md",
               r"C:/Odoo-Test/docs/o11-o18-abrechnung-*.md"):
    for datei in glob.glob(muster):
        doku += io.open(datei, encoding="utf-8").read()
print("Mapping-Doku gelesen: %d Zeichen" % len(doku))

luecken = []
gesamt = 0
for modell in MODELLE:
    try:
        felder = k.kw(modell, "fields_get", [[], ["type", "compute", "related", "store"]], context=CTX)
    except Exception as fehler:
        print("%-28s nicht lesbar: %s" % (modell, str(fehler)[:60]))
        continue
    belegt = []
    for name, info in felder.items():
        if info.get("type") in ("binary", "image"):
            continue
        if info.get("compute") or info.get("related") or info.get("store") is False:
            continue   # berechnete/abgeleitete Felder: in Odoo 18 neu berechnet, keine Migration
        if name in OHNE_MAPPING:
            continue
        try:
            anzahl = k.kw(modell, "search_count", [[[name, "!=", False]]], context=CTX)
            gesamt_alle = k.kw(modell, "search_count", [[]], context=CTX)
        except Exception:
            continue
        if anzahl and gesamt_alle:
            belegt.append((name, anzahl, gesamt_alle))
    belegt.sort(key=lambda x: -x[1])
    ohne = [b for b in belegt if b[0] not in doku]
    gesamt += len(belegt)
    print("\n%-26s belegte Felder: %3d | ohne Mapping-Eintrag: %d" % (modell, len(belegt), len(ohne)))
    for name, anzahl, alle in ohne[:12]:
        print("      %-34s %5d von %5d" % (name, anzahl, alle))
        luecken.append("%s.%s (%d/%d)" % (modell, name, anzahl, alle))

print("\nGesamt belegte Felder: %d | Luecken: %d" % (gesamt, len(luecken)))
