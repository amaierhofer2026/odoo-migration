"""Audit: Ansichten mit sichtbaren Pflichtfeldern (required in der View), die in Datensaetzen leer sind.

Ein solches Feld erzeugt beim Speichern die Meldung "Ungueltige Felder: <Bezeichnung>" und kann
Datensaetze unbrauchbar machen, die fachlich in Ordnung sind.

Aufruf: python scripts/pruefe_pflichtfelder.py lokal|vm
"""
import re
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

MODELLE = ["account.move", "account.move.line", "account.payment", "sale.subscription",
           "sale.subscription.line", "sale.subscription.template", "product.template",
           "account.journal", "account.analytic.account", "helpdesk.ticket"]

instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o18(instanz)
CTX = {"lang": "de_DE"}
print("Instanz:", instanz, "|", k.url)

knoten_re = re.compile(r"<field\s+[^>]*>", re.S)


def attribute(text):
    d = {}
    for m in re.finditer(r"(\w+)=\"([^\"]*)\"", text):
        d[m.group(1)] = m.group(2)
    return d


befunde = []
for model in MODELLE:
    try:
        felder = k.kw(model, "fields_get", [[], ["string", "type", "required", "relation", "store"]],
                      context=CTX)
    except Exception as e:
        print("  %-28s nicht verfuegbar (%s)" % (model, str(e)[:60]))
        continue
    views = k.kw("ir.ui.view", "search_read",
                 [[["model", "=", model], ["mode", "=", "primary"]],
                  ["id", "name", "type"]], context=CTX)
    gesamt = k.kw(model, "search_count", [[]], context=CTX)
    print("\n=== %-28s Datensaetze: %s | Ansichten: %s" % (model, gesamt, len(views)))
    geprueft = set()
    for v in views:
        if v["type"] not in ("form", "list"):
            continue
        try:
            arch = k.kw(model, "get_view", [v["id"], v["type"]], context=CTX)["arch"]
        except Exception as e:
            print("   View %s (%s) nicht lesbar: %s" % (v["id"], v["name"], str(e)[:70]))
            continue
        for m in knoten_re.finditer(arch):
            a = attribute(m.group(0))
            name = a.get("name")
            if not name or name not in felder:
                continue
            if a.get("required") not in ("1", "True", "true"):
                continue
            if a.get("readonly") in ("1", "True", "true") or a.get("invisible") in ("1", "True", "true"):
                continue
            schluessel = (model, name)
            if schluessel in geprueft:
                continue
            geprueft.add(schluessel)
            meta = felder[name]
            try:
                leer = k.kw(model, "search_count", [[[name, "=", False]]], context=CTX)
                leerstr = ""
                if meta.get("type") in ("char", "text"):
                    leerstr = k.kw(model, "search_count", [[[name, "=", ""]]], context=CTX)
            except Exception as e:
                leer, leerstr = -1, ""
                print("      (%s nicht zaehlbar: %s)" % (name, str(e)[:60]))
            zeile = ("   %-32s %-26s typ=%-10s Pflicht in View: %-6s Bedingung: %-14s"
                     % (model, name, meta.get("type"), "ja", a.get("required")))
            marke = "  "
            if leer > 0 or leerstr:
                marke = "!!"
                befunde.append((model, name, meta.get("string"), leer, leerstr))
            print("%s %s leer=%-4s %s (%-24s) [%s]" % (marke, zeile, leer,
                                                       ("+ ''=%s" % leerstr) if leerstr else "",
                                                       meta.get("string"), v["name"]))

print("\n=== Befunde: Pflichtfeld in der Ansicht, aber leer in Datensaetzen ===")
for model, name, label, leer, leerstr in befunde:
    print("   %-28s %-24s '%s'  leer=%s%s" % (model, name, label, leer,
                                              (" leer-String=%s" % leerstr) if leerstr else ""))
if not befunde:
    print("   keine")
