"""Auswertung von Sichtbarkeitsbedingungen (Domains und Python-Ausdruecke) fuer Buttons.

Odoo 11: attrs="{'invisible': [...]}" (Domain) oder states="draft,sent".
Odoo 18: invisible="<Python-Ausdruck>".

Beide werden in einen Python-Ausdruck uebersetzt und je Zustand ausgewertet. Bedingungen mit
weiteren Feldern werden als "bedingt durch: ..." gekennzeichnet; mit den Werten eines echten
Testdatensatzes laesst sich zusaetzlich pruefen, ob der Button dort sichtbar waere.

Hinweis: Die Arch-Ausgabe ist XML-maskiert (&amp; &gt; &lt; &#39;), daher werden die Entities
zuerst aufgeloest.
"""
from __future__ import annotations

import ast
import re

ENTITIES = {"&amp;": "&", "&gt;": ">", "&lt;": "<", "&quot;": '"', "&#39;": "'", "&apos;": "'"}

OPS = {"=": "==", "!=": "!=", ">": ">", ">=": ">=", "<": "<", "<=": "<=", "in": "in", "not in": "not in"}


def ohne_entities(text: str) -> str:
    if not text:
        return ""
    for zeichen, ersatz in ENTITIES.items():
        text = text.replace(zeichen, ersatz)
    return text


def _klammer_inhalt(text: str, start: int) -> str:
    """Der Inhalt der Klammer ab Position start (inklusive), Klammern gezaehlt, Texte beachtet."""
    tiefe, in_text, anfuehrung = 0, False, ""
    for i in range(start, len(text)):
        z = text[i]
        if in_text:
            if z == anfuehrung:
                in_text = False
            continue
        if z in "\"'":
            in_text, anfuehrung = True, z
        elif z in "[({":
            tiefe += 1
        elif z in "])}":
            tiefe -= 1
            if tiefe == 0:
                return text[start:i + 1]
    return ""


def domain_zu_python(domain: list) -> str:
    """Odoo-Domain (auch polnisch mit '|', '&', '!') in einen Python-Ausdruck umsetzen."""
    token = list(domain)

    def parse():
        if not token:
            return "True"
        item = token.pop(0)
        if item in ("|", "&"):
            links, rechts = parse(), parse()
            return "(%s %s %s)" % (links, "or" if item == "|" else "and", rechts)
        if item == "!":
            return "(not %s)" % parse()
        feld, op, wert = item
        return "(%s %s %r)" % (feld, OPS.get(op, "=="), wert)

    return parse()


def invisibles_o11(attrs_text: str) -> str:
    """Den Wert des Schluessels 'invisible' aus einem Odoo-11-attrs-Attribut holen."""
    text = ohne_entities(attrs_text)
    treffer = re.search(r"['\"]invisible['\"]\s*:\s*", text)
    if not treffer:
        return ""
    rest = text[treffer.end():]
    start = rest.find("[")
    if start < 0:
        return ""
    roh = _klammer_inhalt(rest, start)
    try:
        domain = ast.literal_eval(ohne_entities(roh))
    except Exception:
        return ""
    if not isinstance(domain, list):
        return ""
    return domain_zu_python(domain)


def fremde_felder(ausdruck: str) -> list:
    ohne_texte = re.sub(r"'[^']*'|\"[^\"]*\"", "''", ausdruck)
    namen = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", ohne_texte))
    erlaubt = {"state", "in", "not", "and", "or", "True", "False", "None"}
    return sorted(n for n in namen if n not in erlaubt)


def sichtbar(ausdruck: str, zustand: str):
    """True/False oder 'bedingt durch: feld1,feld2', wenn weitere Felder in der Bedingung stecken."""
    if not ausdruck:
        return True
    ausdruck = ohne_entities(ausdruck)
    fremd = fremde_felder(ausdruck)
    if fremd:
        return "bedingt durch: %s" % ", ".join(fremd)
    ersetzt = re.sub(r"\bstate\b", repr(zustand), ausdruck)
    try:
        return not bool(eval(ersetzt, {"__builtins__": {}}, {}))  # invisible -> sichtbar negieren
    except Exception:
        return "nicht auswertbar"


def sichtbar_mit_werten(ausdruck: str, zustand: str, werte: dict):
    """Wie sichtbar(), aber mit den Werten eines echten Testdatensatzes."""
    if not ausdruck:
        return True
    ersetzt = re.sub(r"\bstate\b", repr(zustand), ohne_entities(ausdruck))
    for name in sorted(werte, key=len, reverse=True):
        ersetzt = re.sub(r"\b%s\b" % re.escape(name), repr(werte[name]), ersetzt)
    fremd = fremde_felder(ersetzt)
    if fremd:
        return "bedingt durch: %s" % ", ".join(fremd)
    try:
        return not bool(eval(ersetzt, {"__builtins__": {}}, {}))
    except Exception:
        return "nicht auswertbar"
