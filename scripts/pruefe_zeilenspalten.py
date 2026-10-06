"""Prueft die Rechnungszeilen-Liste im Odoo-18-Formular: Feldknoten, Reihenfolge, Doppelungen."""
import re
import sys
from collections import Counter

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
for typ in ("out_invoice", "out_refund", "in_invoice", "in_refund"):
    r = k.kw("account.move", "get_view", [False, "form"],
             context={"lang": "de_DE", "default_move_type": typ})
    arch = r["arch"]
    i = arch.find("invoice_line_ids")
    if i < 0:
        print("%s: invoice_line_ids nicht gefunden" % typ)
        continue
    start = arch.rfind("<field", 0, i)
    ende = arch.find("</list>", i)
    block = arch[start:ende]
    knoten = re.findall(r"<field name=\"([^\"]+)\"([^>]*)/?>", block)
    namen = [n for n, _ in knoten]
    print("\n=== %s | %d Feldknoten ===" % (typ, len(namen)))
    for pos, (name, attr) in enumerate(knoten, 1):
        attr = attr.strip()
        merker = []
        m = re.search(r'string="([^"]*)"', attr)
        if m:
            merker.append("string=%s" % m.group(1))
        m = re.search(r'optional="([^"]*)"', attr)
        if m:
            merker.append("optional=%s" % m.group(1))
        m = re.search(r'widget="([^"]*)"', attr)
        if m:
            merker.append("widget=%s" % m.group(1))
        m = re.search(r'column_invisible="([^"]*)"', attr)
        if m:
            merker.append("column_invisible=%s" % m.group(1))
        m = re.search(r'id="([^"]*)"', attr)
        if m:
            merker.append("id=%s" % m.group(1))
        print("  %2d %-24s %s" % (pos, name, " ".join(merker)))
    doppelt = [n for n, c in Counter(namen).items() if c > 1]
    print("  Doppelte Feldknoten:", doppelt or "keine")
