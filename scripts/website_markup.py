"""Markup-Konverter Odoo 11 (Bootstrap 3) -> Odoo 18 (Bootstrap 5).

Reine Funktionen, keine Datenbankzustaende. Wird vom Migrationsskript
`migrate_website.py` je Seite aufgerufen und kann einzeln geprueft werden:

    python scripts/website_markup.py --verzeichnis <ordner-mit-o11-archs> --ziel <ordner>

Bewusst nur Standardbibliothek (`xml.etree.ElementTree`), damit das Skript auf
jedem Rechner ohne Zusatzpakete laeuft. Die Odoo-11-Seiten sind wohlgeformtes
XML (alle 17 Seiten geprueft), deshalb bleibt die Selbstschliessung `<br/>`
erhalten - ein HTML-Parser wuerde sie in Verschachtelungen umdeuten.

Umgesetzt (Entscheidungen E1/E2/E3, Session 142):

* `<font>` -> `<span>` (Farbe als style, `color=`-Attribut als style)
* Bootstrap 3 -> Bootstrap 5:
  `col-*-offset-N` -> `offset-*-N`, `pull-left/right` -> `float-start/end`,
  `text-left/right` -> `text-start/end`, `img-responsive` -> `img-fluid`,
  `center-block` -> `mx-auto d-block`, `btn-xs` -> `btn-sm`,
  `btn-default` -> `btn-outline-secondary`, `hidden-*`/`visible-*` -> `d-none`-Klassen,
  `well`/`thumbnail`/`label`/`caret` -> BS5-Gegenstuecke
* Odoo-11-Themefarben ohne BS5-Gegenstueck -> exakte Odoo-11-Werte als style
  (aus dem Live-CSS von Odoo 11 belegt: gamma #ba3c3d, beta #875a7b,
  gray-lighter #cccccc/#666666, white-50 rgba(255,255,255,.5), schwarz #000000)
* Odoo-11-Abstandsklassen ohne exaktes BS5-Gegenstueck -> style
  (mb16 -> `mb-3` = exakt 16px; mb32/mb64/mt8/mt16/mt32 -> style)
* `panel-group`/`panel`/`panel-heading`/`panel-collapse` (261 FAQ-Aufklapper)
  -> Bootstrap-5-Akkordeon (`accordion`, `accordion-item`, `accordion-header`,
  `accordion-button`, `accordion-collapse`, `accordion-body`) mit
  `data-bs-toggle="collapse"`; offene Panels (`in`) -> `show`
* `s_panel`/`o_panel`/`panel-default` ohne Aufklapper -> BS5-Karte (`card`)
* `jumbotron` -> `s_text_block` mit Abstand/Innenabstand (BS5 kennt kein Jumbotron)
* Bausteine, die es in Odoo 18 nicht mehr gibt (`s_feature_grid`, `s_big_message`,
  `s_button`) -> `s_text_block`
* Doppelt escapte Zeichen (E3): `&amp;nbsp;` -> geschuetztes Leerzeichen,
  `&amp;amp;` -> `&`; je Seite gezaehlt
* Leere Editor-Reste (`<ul/>`, `<p/>`), `data-original-title=""`, `title=""`,
  `role="tab|tabpanel"`, `style="height: 0px;"` entfernt
* Word-Paste-Klassen (`MsoNormal`) entfernt

Nicht umgestellt (bewusst): `<br/>`-Setzung, Fettschrift, Tabellen, Inline-Styles
der Redaktion, Base64-Bilder, externe Links, `target="_blank"`.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Klassenzuordnung Bootstrap 3 -> Bootstrap 5 (Token fuer Token)
# ---------------------------------------------------------------------------
BS5_KLASSEN = {
    "pull-left": "float-start",
    "pull-right": "float-end",
    "text-left": "text-start",
    "text-right": "text-end",
    "img-responsive": "img-fluid",
    "img-circle": "rounded-circle",
    "img-rounded": "rounded",
    "center-block": "mx-auto d-block",
    "btn-xs": "btn-sm",
    "btn-default": "btn-outline-secondary",
    "btn-group-justified": "d-flex",
    "caret": "dropdown-toggle",
    "well": "card bg-light p-3",
    "thumbnail": "img-thumbnail",
    "label-default": "badge bg-secondary",
    "label-primary": "badge bg-primary",
    "label-success": "badge bg-success",
    "label-info": "badge bg-info",
    "label-warning": "badge bg-warning text-dark",
    "label-danger": "badge bg-danger",
    "hidden": "d-none",
    "visible-xs": "d-block d-sm-none",
    "hidden-xs": "d-none d-sm-block",
    "visible-sm": "d-none d-md-block d-lg-none",
    "hidden-sm": "d-md-none d-lg-block",
    "visible-md": "d-none d-md-block d-lg-none",
    "hidden-md": "d-md-none d-lg-block",
    "visible-lg": "d-lg-block",
    "hidden-lg": "d-lg-none",
    "text-black": "text-dark",
    "text-gray-darker": "text-body",
    "mb0": "mb-0",
    "mt0": "mt-0",
    "mb16": "mb-3",          # Bootstrap 5: 1rem = 16px, exakt gleich
    "ml-auto": "ms-auto",
    "mr-auto": "me-auto",
}

# Odoo-11-Werte ohne BS5-Gegenstueck -> exakte Inline-Styles (Belege: Odoo-11-CSS)
STYLE_AUS_KLASSE = {
    "bg-gray-lighter": "background-color: #cccccc; color: #666666;",
    "bg-white-50": "background-color: rgba(255, 255, 255, 0.5); color: #666666;",
    "text-gamma": "color: #ba3c3d;",
    "bg-gamma": "background-color: #ba3c3d; color: #ffffff;",
    "text-beta": "color: #875a7b;",
    "bg-beta": "background-color: #875a7b; color: #ffffff;",
    "mb8": "margin-bottom: 8px;",
    "mb32": "margin-bottom: 32px;",
    "mb64": "margin-bottom: 64px;",
    "mt8": "margin-top: 8px;",
    "mt16": "margin-top: 16px;",
    "mt32": "margin-top: 32px;",
    "page-header": "padding-bottom: 9px; margin: 40px 0 20px; border-bottom: 1px solid #cccccc;",
}

# Bausteine, die es in Odoo 18 nicht mehr gibt
SNIPPET_ERSATZ = {
    "s_big_message": "s_text_block",
    "s_feature_grid": "s_text_block",
    "s_button": "s_text_block",
}

LEERE_TAGS = {"ul", "p", "span", "b", "strong", "i", "h1", "h2", "h3", "h4", "h5", "div"}

# Doppelt escapte Zeichen (E3): Quelltext -> sichtbares Zeichen
ENTITIES = {
    "&nbsp;": "\u00a0",
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
}

OFFSET_RE = re.compile(r"^col-(xs|sm|md|lg)-offset-(\d+)$")


# ---------------------------------------------------------------------------
# Element-Hilfen
# ---------------------------------------------------------------------------
def klassen(el) -> list:
    return (el.get("class") or "").split()


def setze_klassen(el, liste) -> None:
    neu = " ".join(k for k in liste if k)
    if neu:
        el.set("class", neu)
    elif "class" in el.attrib:
        del el.attrib["class"]


def style_anhaengen(el, zusatz: str) -> None:
    alt = (el.get("style") or "").strip()
    if alt and not alt.endswith(";"):
        alt += ";"
    el.set("style", (alt + " " + zusatz).strip())


# ---------------------------------------------------------------------------
# Einzelne Umbauten
# ---------------------------------------------------------------------------
def ersetze_klassen(el, bericht: dict) -> None:
    liste = klassen(el)
    if not liste:
        return
    neu = []
    for k in liste:
        treffer = OFFSET_RE.match(k)
        if treffer:
            # col-md-offset-1 -> offset-md-1 (BS5 stellt den Offset vor die Spalte)
            neu.insert(0, "offset-%s-%s" % (treffer.group(1), treffer.group(2)))
            bericht["col_offset"] += 1
            continue
        if k.startswith("col-xs-"):
            neu.append("col-" + k.split("-")[-1])
            bericht["col_xs"] += 1
            continue
        if k in STYLE_AUS_KLASSE:
            style_anhaengen(el, STYLE_AUS_KLASSE[k])
            bericht["style_aus_klasse"][k] += 1
            continue
        if k in SNIPPET_ERSATZ:
            neu.append(SNIPPET_ERSATZ[k])
            bericht["snippet_ersatz"][k] += 1
            continue
        if k in BS5_KLASSEN:
            neu.append(BS5_KLASSEN[k])
            bericht["bs5_klasse"][k] += 1
            continue
        if k.startswith("Mso"):
            bericht["mso_entfernt"] += 1
            continue
        if k == "jumbotron":
            continue
        neu.append(k)
    setze_klassen(el, neu)


FONT_SIZE_PX = {1: "10px", 2: "13px", 3: "16px", 4: "18px", 5: "24px", 6: "32px", 7: "48px"}


def font_zu_span(el, bericht: dict) -> None:
    el.tag = "span"
    farbe = el.get("color")
    if farbe:
        del el.attrib["color"]
        style_anhaengen(el, "color: %s;" % farbe)
    groesse = (el.get("size") or "").strip()
    if groesse.isdigit() and int(groesse) in FONT_SIZE_PX:
        del el.attrib["size"]
        style_anhaengen(el, "font-size: %s;" % FONT_SIZE_PX[int(groesse)])
        bericht["font_size_umgesetzt"] += 1
    el.attrib.pop("face", None)
    bericht["font_zu_span"] += 1


def jumbotron(el, bericht: dict) -> None:
    liste = [k for k in klassen(el) if k not in ("jumbotron", "s_big_message", "s_button")]
    if "s_text_block" not in liste:
        liste.append("s_text_block")
    setze_klassen(el, liste)
    style_anhaengen(el, "padding-top: 48px; padding-bottom: 48px;")
    bericht["jumbotron"] += 1


def panel_zu_karte(el, bericht: dict) -> None:
    """`s_panel`/`o_panel` ohne Aufklapper -> BS5-Karte."""
    liste = [k for k in klassen(el) if k not in ("panel", "panel-default", "o_panel", "s_panel")]
    setze_klassen(el, ["card", "mb-2"] + liste)
    for kind in el:
        if "panel-heading" in klassen(kind):
            setze_klassen(kind, ["card-body", "py-2"])
            for unter in kind:
                if "panel-title" in klassen(unter):
                    setze_klassen(unter, [k for k in klassen(unter) if k != "panel-title"])
            ersetze_klassen(kind, bericht)
    bericht["panel_zu_karte"] += 1


def _titel_teile(kopf) -> list:
    teile = [k for k in kopf if "panel-title" in klassen(k)]
    return teile or list(kopf)


def akkordeon(gruppe, bericht: dict) -> None:
    """`panel-group` in ein Bootstrap-5-Akkordeon umbauen (E2)."""
    gruppe_id = gruppe.get("id") or ""
    neue_kinder = []
    for panel in list(gruppe):
        tail = panel.tail
        if panel.tag != "div" or "panel" not in klassen(panel):
            neue_kinder.append(panel)
            continue
        kopf = korpus = None
        for kind in panel:
            k = klassen(kind)
            if "panel-heading" in k and kopf is None:
                kopf = kind
            elif ("panel-collapse" in k or "panel-body" in k) and korpus is None:
                korpus = kind
        ziel = (kopf.get("data-target") or "").lstrip("#") if kopf is not None else ""
        if not ziel and korpus is not None:
            ziel = korpus.get("id") or ""
        if kopf is None or not ziel:
            bericht["akkordeon_ohne_ziel"] += 1
            neue_kinder.append(panel)
            continue
        offen = (kopf.get("aria-expanded") == "true") or (
            korpus is not None and "in" in klassen(korpus))

        artikel = ET.Element("div", {"class": "accordion-item"})
        h = ET.SubElement(artikel, "h4", {"class": "accordion-header"})
        if kopf.get("style"):
            h.set("style", kopf.get("style"))
        button = ET.SubElement(h, "button", {
            "class": "accordion-button" + ("" if offen else " collapsed"),
            "type": "button",
            "data-bs-toggle": "collapse",
            "data-bs-target": "#" + ziel,
            "aria-expanded": "true" if offen else "false",
            "aria-controls": ziel,
        })
        for i, teil in enumerate(_titel_teile(kopf)):
            if i:
                trenner = ET.SubElement(button, "span")
                trenner.text = " "
                trenner.tail = None
            if "panel-title" in klassen(teil):
                # Ueberschrift aufloesen: Inhalt direkt in den Knopf (kein <h4> im <button>)
                if teil.text:
                    button.text = (button.text or "") + teil.text
                for unter in list(teil):
                    unter.tail = unter.tail
                    button.append(unter)
            else:
                teil.tail = None
                button.append(teil)

        wrapper = ET.SubElement(artikel, "div", {
            "id": ziel,
            "class": "accordion-collapse collapse" + (" show" if offen else ""),
        })
        if gruppe_id:
            wrapper.set("data-bs-parent", "#" + gruppe_id)
        wrapper.set("aria-labelledby", ziel)
        korpus_div = ET.SubElement(wrapper, "div", {"class": "accordion-body"})
        inhalt = korpus
        if korpus is not None:
            for kind in korpus:
                if "panel-body" in klassen(kind):
                    inhalt = kind
                    break
        if inhalt is not None:
            # `panel-body` aufloesen: sein Inhalt gehoert in `accordion-body`
            if inhalt.text and inhalt.text.strip():
                korpus_div.text = inhalt.text
            if inhalt.get("style") and "accordion-body" not in klassen(inhalt):
                korpus_div.set("style", inhalt.get("style"))
            for kind in list(inhalt):
                korpus_div.append(kind)
        artikel.tail = tail
        neue_kinder.append(artikel)
        bericht["akkordeon"] += 1

    gruppe[:] = neue_kinder
    setze_klassen(gruppe, ["accordion"])
    gruppe.attrib.pop("role", None)
    bericht["akkordeon_gruppen"] += 1


def attribute_saeubern(root) -> None:
    for el in root.iter():
        for attr in ("data-original-title", "title"):
            if el.get(attr) == "":
                del el.attrib[attr]
        if el.get("style") == "":
            del el.attrib["style"]
        if "style" in el.attrib and "height: 0px" in el.get("style"):
            rest = ";".join(t for t in el.get("style").split(";") if "height: 0px" not in t).strip(" ;")
            if rest:
                el.set("style", rest)
            else:
                del el.attrib["style"]
        if el.get("role") in ("tab", "tabpanel", "tablist"):
            del el.attrib["role"]
        if el.get("aria-expanded") and el.tag != "button":
            del el.attrib["aria-expanded"]


def enthaelt_inhalt(el) -> bool:
    if el.text and el.text.strip():
        return True
    if len(el):
        return True
    for attr in ("class", "href", "src", "id", "style"):
        if (el.get(attr) or "").strip():
            return True
    return False


def leere_entfernen(el, bericht: dict) -> None:
    for kind in list(el):
        leere_entfernen(kind, bericht)
    for kind in list(el):
        if kind.tag in LEERE_TAGS and not enthaelt_inhalt(kind):
            el.remove(kind)
            bericht["leer_entfernt"] += 1


def escaping(root, bericht: dict) -> None:
    """Doppelt escapte Zeichen in sichtbaren Textknoten bereinigen (E3)."""
    def bereinige(text):
        if not text:
            return text
        for alt, neu in ENTITIES.items():
            if alt in text:
                bericht["escaped"][alt] += text.count(alt)
                text = text.replace(alt, neu)
        return text

    for el in root.iter():
        if not isinstance(el.tag, str) or el.tag in ("script", "style"):
            continue
        el.text = bereinige(el.text)
        for kind in el:
            kind.tail = bereinige(kind.tail)


def haengende_leerzeichen(root) -> None:
    for el in root.iter():
        if el.tag in ("p", "h1", "h2", "h3", "h4", "h5", "td", "li", "span"):
            if el.text and el.text.endswith("\u00a0"):
                el.text = el.text.rstrip("\u00a0")
            for kind in el:
                if kind.tail and kind.tail.strip("\u00a0 ") == "":
                    kind.tail = ""


def verarbeite(el, bericht: dict) -> None:
    """Rekursiv: Aufklapper/Karten umbauen, dann Klassen und Tags."""
    for kind in list(el):
        k = klassen(kind)
        if kind.tag == "div" and "panel-group" in k:
            akkordeon(kind, bericht)
        elif "s_panel" in k or ("panel" in k and "panel-default" in k):
            panel_zu_karte(kind, bericht)
        verarbeite(kind, bericht)
        if "jumbotron" in klassen(kind) or "s_big_message" in klassen(kind):
            jumbotron(kind, bericht)
        if kind.tag == "font":
            font_zu_span(kind, bericht)
        ersetze_klassen(kind, bericht)


def konvertiere(arch: str) -> tuple:
    """Wandelt eine Odoo-11-Seite um. Rueckgabe: (neues_arch, bericht)."""
    root = ET.fromstring(arch)
    bericht = {
        "font_zu_span": 0, "col_offset": 0, "col_xs": 0, "jumbotron": 0, "font_size_umgesetzt": 0,
        "akkordeon": 0, "akkordeon_gruppen": 0, "akkordeon_ohne_ziel": 0,
        "panel_zu_karte": 0, "leer_entfernt": 0, "mso_entfernt": 0,
        "bs5_klasse": collections.Counter(), "style_aus_klasse": collections.Counter(),
        "snippet_ersatz": collections.Counter(), "escaped": collections.Counter(),
    }
    verarbeite(root, bericht)
    attribute_saeubern(root)
    escaping(root, bericht)
    haengende_leerzeichen(root)
    leere_entfernen(root, bericht)

    neu = ET.tostring(root, encoding="unicode")
    bericht["zeichen_vorher"] = len(arch)
    bericht["zeichen_nachher"] = len(neu)
    return neu, _als_dict(bericht)


def _als_dict(bericht: dict) -> dict:
    return {k: ({kk: vv for kk, vv in sorted(v.items())} if isinstance(v, collections.Counter) else v)
            for k, v in bericht.items()}


def restpruefung(neu: str) -> dict:
    """Restpruefung auf nicht uebersetzte Bootstrap-3-Muster."""
    return {
        "panel_klassen": len(re.findall(r"\bpanel(?:-group|-heading|-collapse|-body|-title)?\b", neu)),
        "data_toggle": neu.count("data-toggle="),
        "col_offset": len(re.findall(r"\bcol-(?:xs|sm|md|lg)-offset-\d", neu)),
        "pull": neu.count("pull-left") + neu.count("pull-right"),
        "jumbotron": neu.count("jumbotron"),
        "font_tag": neu.count("<font"),
        "escaped_nbsp": neu.count("&amp;nbsp;"),
        "escaped_amp": neu.count("&amp;amp;"),
        "accordion": neu.count("accordion-button"),
        "fontsize_attrs": neu.count('size="'),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verzeichnis", required=True, help="Ordner mit o11_seite_NNN.html")
    ap.add_argument("--ziel", help="Zielordner fuer die umgewandelten Seiten")
    ap.add_argument("--json")
    args = ap.parse_args()
    if args.ziel:
        os.makedirs(args.ziel, exist_ok=True)

    gesamt = collections.Counter()
    berichte = {}
    for name in sorted(os.listdir(args.verzeichnis)):
        if not name.endswith(".html"):
            continue
        arch = open(os.path.join(args.verzeichnis, name), encoding="utf-8").read()
        neu, bericht = konvertiere(arch)
        bericht["rest"] = restpruefung(neu)
        berichte[name] = bericht
        for k in ("font_zu_span", "col_offset", "jumbotron", "akkordeon", "panel_zu_karte",
                  "leer_entfernt", "mso_entfernt"):
            gesamt[k] += bericht[k]
        for k, v in bericht["escaped"].items():
            gesamt["escaped " + k] += v
        for k, v in bericht["bs5_klasse"].items():
            gesamt["bs5:" + k] += v
        for k, v in bericht["style_aus_klasse"].items():
            gesamt["style:" + k] += v
        if args.ziel:
            with open(os.path.join(args.ziel, name), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(neu)
        print("%-22s %6d -> %6d | Akkordeon %3d | Karten %2d | font %4d | leer %3d | Rest %s"
              % (name, bericht["zeichen_vorher"], bericht["zeichen_nachher"], bericht["akkordeon"],
                 bericht["panel_zu_karte"], bericht["font_zu_span"], bericht["leer_entfernt"],
                 json.dumps(bericht["rest"], ensure_ascii=False)))

    print("\nSumme:", json.dumps({k: v for k, v in sorted(gesamt.items()) if v}, ensure_ascii=False))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(berichte, fh, ensure_ascii=False, indent=1)
        print("JSON:", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
