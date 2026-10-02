"""Erzeugt die vollstaendige Liste der noch nicht dokumentierten belegten Odoo-11-Felder
und haengt sie als Tabelle an die Abschlusspruefung an.

Aufruf: python scripts/ergaenze_feldabdeckung.py
"""
import glob
import io
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")
DOKU = r"C:/Odoo-Test/docs/o11-o18-abrechnung-abschlusspruefung.md"

MODELLE = ["account.invoice", "account.invoice.line", "account.payment", "account.move",
           "res.partner", "product.template", "product.product", "account.tax",
           "account.journal", "account.payment.term", "account.analytic.account",
           "account.account", "account.fiscal.position"]
OHNE = {"id", "create_uid", "create_date", "write_uid", "write_date", "__last_update", "display_name",
        "message_ids", "message_follower_ids", "message_partner_ids", "message_attachment_count",
        "message_main_attachment_id", "access_token", "website_message_ids", "activity_ids",
        "activity_state", "activity_user_id", "activity_date_deadline", "activity_summary",
        "activity_type_id", "my_activity_date_deadline", "rating_ids", "message_needaction",
        "message_needaction_counter", "message_has_error", "message_has_error_counter",
        "message_has_sms_error", "message_unread", "message_unread_counter", "message_is_follower",
        "message_channel_ids", "website_url", "seo_name", "website_published"}

doku = ""
for muster in (r"C:/Odoo-Test/docs/o11-o18-*.md", r"C:/Odoo-Test/docs/*abrechnung*.md"):
    for datei in glob.glob(muster):
        doku += io.open(datei, encoding="utf-8").read()

zeilen = []
for modell in MODELLE:
    try:
        felder11 = k11.kw(modell, "fields_get", [[], ["type", "compute", "related", "store", "string", "relation"]], context=CTX)
    except Exception as fehler:
        print("%s nicht lesbar: %s" % (modell, str(fehler)[:60]))
        continue
    zielmodell = {"account.invoice": "account.move", "account.invoice.line": "account.move.line"}.get(modell, modell)
    try:
        felder18 = k18.kw(zielmodell, "fields_get", [[], ["type"]], context=CTX)
    except Exception:
        felder18 = {}
    gesamt = k11.kw(modell, "search_count", [[]], context=CTX)
    for name, info in sorted(felder11.items()):
        if info.get("type") in ("binary", "image") or name in OHNE:
            continue
        if info.get("compute") or info.get("related") or info.get("store") is False:
            continue
        if name in doku:
            continue
        anzahl = k11.kw(modell, "search_count", [[[name, "!=", False]]], context=CTX)
        if not anzahl:
            continue
        vorhanden = name in felder18
        if info.get("type") in ("many2one", "many2many", "one2many"):
            regel = "1:1 ueber fachlichen Schluessel" if vorhanden else "nicht migrieren (kein Zielfeld)"
        elif not vorhanden:
            regel = "nicht migrieren (in Odoo 18 nicht vorhanden)"
        else:
            regel = "1:1"
        print("%-28s %-26s %5d/%-5d %s -> %s" % (modell, name, anzahl, gesamt,
                                                 (info.get("string") or "")[:28], regel))
        zeilen.append("| %s.%s | %d/%d | %s |" % (modell, name, anzahl, gesamt, regel))

print("\nNoch nicht dokumentierte belegte Felder: %d" % len(zeilen))
if zeilen:
    block = ["\n## 12. Vollstaendige Restliste belegter Felder (automatisch erzeugt)\n",
             "| Odoo 11 Feld | Belegung | Behandlung |", "|---|---|---|"] + zeilen + [""]
    with io.open(DOKU, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(block) + "\n")
    print("Tabelle an %s angehaengt" % DOKU)
