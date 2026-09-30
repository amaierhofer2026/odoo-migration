"""K2: Nachbildung des Odoo-18-Nummernregelwerks gegen die echten Odoo-11-Nummern (read-only).

Die Regexe und die Entscheidungslogik sind woertlich aus dem Odoo-18-Quellcode uebernommen
(addons/account/models/sequence_mixin.py, Stand der Testumgebung 18.0-20260817) und werden hier
lokal nachgerechnet. Es wird NICHTS geschrieben, weder in Odoo 11 noch in Odoo 18.

Aufruf:  python scripts/pruefe_k2_nummernformat.py
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11

# --- Regexe woertlich aus Odoo 18 (sequence_mixin.py) ------------------------------------------
PREFIX = r'(?P<prefix1>.*?)'
PREFIX2 = r'(?P<prefix2>\D)'
PREFIX3 = r'(?P<prefix3>\D+?)'
SEQ = r'(?P<seq>\d*)'
MONTH = r'(?P<month>(0[1-9]|1[0-2]))'
YEAR = r'(?P<year>((?<=\D)|(?<=^))((19|20|21)\d{2}|(\d{2}(?=\D))))'
YEAR_END = r'(?P<year_end>((?<=\D)|(?<=^))((19|20|21)\d{2}|(\d{2}(?=\D))))'
SUFFIX = r'(?P<suffix>\D*?)'

R_YEAR_RANGE_MONTHLY = fr'^{PREFIX}{YEAR}{PREFIX2}{YEAR_END}(?P<prefix3>\D){MONTH}(?P<prefix4>\D+?){SEQ}{SUFFIX}$'
R_YEAR_RANGE = fr'^(?:{PREFIX}{YEAR}{PREFIX2}{YEAR_END}{PREFIX3})?{SEQ}{SUFFIX}$'
R_MONTHLY = fr'^{PREFIX}{YEAR}(?P<prefix2>\D*?){MONTH}{PREFIX3}{SEQ}{SUFFIX}$'
R_YEARLY = fr'^{PREFIX}(?P<year>((?<=\D)|(?<=^))((19|20|21)?\d{{2}}))(?P<prefix2>\D+?){SEQ}{SUFFIX}$'
R_FIXED = fr'^{PREFIX}(?P<seq>\d{{0,9}}){SUFFIX}$'

# Kandidaten fuer sequence_override_regex (Journalfeld in Odoo 18)
KANDIDATEN = {
    "Jahr + laufende Nummer (empfohlen)": r'^(?P<prefix1>R-)(?P<year>\d{2})(?P<seq>\d+)$',
    "durchlaufend ohne Jahreswechsel": r'^(?P<prefix1>R-)(?P<seq>\d+)$',
}


def make_non_capturing(regex: str) -> str:
    """Nachbildung von sequence.mixin._make_regex_non_capturing."""
    out, tiefe, i = [], 0, 0
    while i < len(regex):
        if regex.startswith("(?P<", i):
            ende = regex.index(">", i) + 1
            name = regex[i + 3:ende - 1]
            out.append(name if name == "seq" else "(?:")
            tiefe += 1
            i = ende
        elif regex[i] == ")" and tiefe:
            out.append(")")
            tiefe -= 1
            i += 1
        else:
            out.append(regex[i])
            i += 1
    return "".join(out)


def deduce_reset(name, override=None):
    """Nachbildung von _deduce_sequence_number_reset (gibt Typ oder None = Fehler)."""
    regexe = [R_YEAR_RANGE_MONTHLY, R_MONTHLY, R_YEAR_RANGE, R_YEARLY, R_FIXED]
    if override:
        regexe = [override] * 5
    anforderungen = [("year_range_month", ["seq", "year", "year_end", "month"]),
                     ("month", ["seq", "month", "year"]),
                     ("year_range", ["seq", "year", "year_end"]),
                     ("year", ["seq", "year"]),
                     ("never", ["seq"])]
    for regex, (rueck, bedingungen) in zip(regexe, anforderungen):
        m = re.match(regex, name or "")
        if m:
            gd = m.groupdict()
            jahr, jahr_ende = gd.get("year"), gd.get("year_end")
            if jahr and jahr_ende and len(jahr) < len(jahr_ende):
                continue
            if all(gd.get(b) is not None for b in bedingungen):
                return rueck
    return None


def format_param(previous, override=None):
    """Nachbildung von _get_sequence_format_param (Format und Werte)."""
    reset = deduce_reset(previous, override)
    if reset is None:
        return None, None
    regex = {"year": R_YEARLY, "year_range": R_YEAR_RANGE, "month": R_MONTHLY,
             "year_range_month": R_YEAR_RANGE_MONTHLY, "never": R_FIXED}[reset]
    if override:
        regex = override
    gd = re.match(regex, previous).groupdict()
    werte = dict(gd)
    werte["seq_length"] = len(gd.get("seq") or "")
    werte["year_length"] = len(gd.get("year") or "")
    werte["year_end_length"] = len(gd.get("year_end") or "")
    for feld in ("seq", "year", "month", "year_end"):
        werte[feld] = int(werte.get(feld) or 0)
    platzhalter = re.findall(r'\b(prefix\d|seq|suffix\d?|year|year_end|month)\b', regex)
    fmt = "".join(
        "{seq:0%dd}" % werte["seq_length"] if p == "seq" else
        "{month:02d}" if p == "month" else
        "{year:0%dd}" % werte["year_length"] if p == "year" else
        "{year_end:0%dd}" % werte["year_end_length"] if p == "year_end" else
        "{%s}" % p
        for p in platzhalter)
    return fmt, werte


def aufteilen(name):
    """Nachbildung von _compute_split_sequence: sequence_prefix und sequence_number."""
    if not name:
        return "", 0
    regex = make_non_capturing(R_FIXED.replace(r"?P<seq>", ""))
    m = re.match(regex, name)
    if not m:
        return name, 0
    return name[:m.start(1)], int(m.group(1) or 0)


def letzte_nummer(belege, override=None, neues_datum=None):
    """Nachbildung von _get_last_sequence/_get_last_sequence_domain.

    belege: Liste von (nummer, datum) in der Reihenfolge der ids (aeltester Beleg zuerst).
    1) Bezugsbeleg = Beleg mit dem spaetesten Datum (date desc, limit 1) -> Reset-Typ ableiten
    2) bei Reset 'year' wird auf das Jahr des neuen Datums eingeschraenkt
    3) Prefix = sequence_prefix des zuletzt angelegten Belegs (hoechste id)
    4) darin die hoechste sequence_number
    """
    if not belege:
        return None, None, None
    neues_datum = neues_datum or max(d for _, d in belege)
    bezug = max(belege, key=lambda b: (b[1], b[0]))
    reset = deduce_reset(bezug[0], override)
    kandidaten = list(belege)
    if reset == "year":
        kandidaten = [b for b in belege if b[1][:4] == neues_datum[:4]]
    prefix = aufteilen(belege[-1][0])[0]
    kandidaten = [b for b in kandidaten if aufteilen(b[0])[0] == prefix]
    if not kandidaten:
        # Odoo greift dann auf _get_last_sequence(relaxed=True) zurueck (Vorperiode)
        kandidaten = [b for b in belege if aufteilen(b[0])[0] == prefix]
        bezug_alt = max(kandidaten, key=lambda b: aufteilen(b[0])[1])
        return bezug_alt[0], reset, prefix
    letzte = max(kandidaten, key=lambda b: aufteilen(b[0])[1])
    return letzte[0], reset, prefix


def naechste_nummer(belege, override=None, neues_datum=None):
    """Was Odoo 18 als naechste Nummer berechnen wuerde (ohne Schreibvorgang)."""
    if not belege:
        return None
    letzte, reset, prefix = letzte_nummer(belege, override, neues_datum)
    neues_datum = neues_datum or max(d for _, d in belege)
    fmt, werte = format_param(letzte, override)
    if fmt is None:
        return "FEHLER: Format nicht bestimmbar"
    werte = dict(werte)
    if werte.get("year_length"):
        jahr = int(neues_datum[:4])
        neu = jahr % (10 ** werte["year_length"])
        if neu != werte["year"]:
            werte["year"] = neu
            werte["seq"] = 0
    werte["seq"] += 1
    return "%s (Reset %s, Vorlage %s, Prefix %r, Datum %s)" % (
        fmt.format(**werte), reset, letzte, prefix, neues_datum)


def main() -> int:
    k = o11()
    daten = k.kw("account.invoice", "search_read",
                 [[("number", "!=", False)], ["number", "date_invoice", "type"]], order="id")
    belege = [(d["number"], d["date_invoice"] or "1970-01-01") for d in daten]
    alle = [b[0] for b in belege]
    print("Rechnungsnummern aus Odoo 11 (read-only gelesen): %d" % len(alle))

    print("\n=== 1) Standardverhalten (ohne sequence_override_regex) ===")
    reset_typen = Counter(deduce_reset(n) for n in alle)
    print("vom Odoo-18-Regelwerk erkannte Reset-Typen: %s" % dict(reset_typen))
    pruefung = Counter()
    for n in alle:
        fmt, _ = format_param(n)
        pruefung[fmt] = pruefung.get(fmt, 0) + 1
    print("abgeleitete Formate:")
    for fmt, anzahl in pruefung.most_common():
        print("   %-28s %d Nummern" % (fmt, anzahl))
    print("\nAufteilung sequence_prefix / sequence_number (Beispiele):")
    for n in ("R-1900001", "R-19578", "R-20001", "R-25001", "R-26989"):
        print("   %-12s -> prefix=%r number=%s" % (n, aufteilen(n)[0], aufteilen(n)[1]))
    print("\n-> naechste Nummer (neuer Beleg im letzten Datenjahr %s): %s"
          % (max(b[1] for b in belege), naechste_nummer(belege)))
    print("-> naechste Nummer (neuer Beleg 2027-01-15): %s"
          % naechste_nummer(belege, neues_datum="2027-01-15"))

    print("\n=== 2) Mit sequence_override_regex (Kandidaten) ===")
    for bez, regex in KANDIDATEN.items():
        nicht_passend = [n for n in alle if not re.match(regex, n)]
        print("\n-- %s" % bez)
        print("   Regex: %s" % regex)
        print("   deckt %d von %d Nummern ab (%d ohne Treffer)"
              % (len(alle) - len(nicht_passend), len(alle), len(nicht_passend)))
        if nicht_passend:
            print("   Beispiele ohne Treffer: %s" % nicht_passend[:5])
            continue
        print("   erkannter Reset-Typ: %s" % dict(Counter(deduce_reset(n, regex) for n in alle)))
        print("   Format aus R-26989: %s" % format_param("R-26989", regex)[0])
        print("   naechste Nummer (2026): %s" % naechste_nummer(belege, regex))
        print("   naechste Nummer (2027-01-15): %s"
              % naechste_nummer(belege, regex, neues_datum="2027-01-15"))

    print("\n=== 3) Kollisionsprobe der heutigen Nummern ===")
    doppelt = [n for n, anzahl in Counter(alle).items() if anzahl > 1]
    print("Nummern, die im selben Journal mehrfach vorkommen: %s" % doppelt)
    for n in doppelt:
        for d in daten:
            if d["number"] == n:
                print("   %s | %-12s | %s" % (n, d["type"], d["date_invoice"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
