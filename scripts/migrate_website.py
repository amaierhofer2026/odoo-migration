"""Website / Webinhalte: Datenmigration Odoo 11 -> Odoo 18 (Session 142).

Entscheidungen E1-E14 (Anna, 11.11.2026). Odoo 11 Prod wird ausschliesslich
lesend befragt; geschrieben wird nur in Odoo 18 (lokal oder VM).

    python scripts/migrate_website.py --instanz lokal                  # Trockenlauf
    python scripts/migrate_website.py --instanz lokal --schreiben      # Schreiblauf
    python scripts/migrate_website.py --instanz lokal --schreiben --nur seiten

Schritte: seiten, menues, einstellungen, demo, anhang, tracker (Reihenfolge ist
Abhaengigkeit: Demo/Doppel-Homepage vor der Startseite, Anhang vor Seite 17).

Idempotenz: jeder Datensatz wird ueber einen fachlichen Schluessel gesucht
(Seite = View-Key, Menue = URL unter der Wurzel, Link-Tracker = Kurz-URL-Code,
Anhang = Name + Pruefsumme). Ein zweiter Lauf legt nichts neu an.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _o11o18_client as client  # noqa: E402
import website_markup as markup  # noqa: E402

SCHRITTE = ["anhang", "demo", "seiten", "menues", "einstellungen", "tracker"]

# --- Auswahl der Seiten (E4/E5) ------------------------------------------------
# Uebernommen: 1, 6, 10, 11, 14, 16, 17, 18, 19
# Nicht uebernommen: 2/3/4 (Odoo-Standard), 5 (Kopie), 7 (test), 9 (leer),
#                    12 (Testseite), 13 (Sicherung)
SEITEN = {
    1: {"key": "website.webseite", "name": "Webseite", "url": "/", "homepage": True,
        "arch": "homepage"},
    6: {"key": "website.wie-bestelle-ich-einen-kurs", "name": "Wie bestelle ich einen Kurs",
        "url": "/wie-bestelle-ich-einen-kurs"},
    10: {"key": "website.kurse", "name": "Kurse", "url": "/kurse"},
    11: {"key": "website.faqs-umstellung-zur-gemeindecloud",
         "name": "FAQs Umstellung zur Gemeindecloud",
         "url": "/faqs-umstellung-zur-gemeindecloud"},
    14: {"key": "website.gemeindecloud-at", "name": "Gemeindecloud.at", "url": "/gemeindecloud-at"},
    16: {"key": "website.faqs-stadtebund-academy", "name": "FAQs Städtebund-Academy",
         "url": "/faqs-staedtebund-academy"},
    17: {"key": "website.faq-ifg-portal-partner", "name": "FAQ IFG-Portal (Partner)",
         "url": "/faqs-ifg-portal-partner"},
    18: {"key": "website.faq-anonymisierungs-portal", "name": "FAQ Anonymisierungs-Portal",
         "url": "/faq-anonymisierungs-portal"},
    19: {"key": "website.faqs-ifg-portal-kunden", "name": "FAQS IFG-Portal (Kunden)",
         "url": "/faqs-ifg-portal-kunden"},
}
NICHT_UEBERNOMMEN = {2: "Odoo-Standardseite Contact Us", 3: "Odoo-Standardseite About us",
                     4: "Odoo-Standardseite Thanks", 5: "Kopie der Kursseite",
                     7: "leere Testseite", 9: "leere Seite Sicherung",
                     12: "Testseite mit Demo-Text", 13: "aeltere Sicherung der FAQs"}

# --- Menues (E6) ---------------------------------------------------------------
# (Odoo-11-Menue-id, Name, URL, verknuepfte Odoo-11-Seite, sequence)
MENUES = [
    (1, "ITK Portal", "/", 1, 1),
    (2, "ITK Webseite", "http://www.it-kommunal.at", None, 2),
    (3, "Ticket", "/support/ticket/submit", None, 3),
    (4, "Webinare", "/event", None, 4),
    (5, "Kurse", "/kurse", 10, 5),
    (6, "Wie bestelle ich einen Kurs", "/wie-bestelle-ich-einen-kurs", 6, 6),
    (7, "FAQ Umstellung Ebox - Gemeindecloud", "/faqs-umstellung-zur-gemeindecloud", 11, 7),
    (8, "FAQ IFG-Portal (Partner)", "/faqs-ifg-portal-partner", 17, 8),
    (9, "FAQ Anonymisierungs-Portal", "/faq-anonymisierungs-portal", 18, 9),
    (10, "FAQS IFG-Portal (Kunden)", "/faqs-ifg-portal-kunden", 19, 10),
]
WURZEL_NAME = "Top Menü"

# Odoo 18 hat Medien umbenannt (Odoo 11 -> Odoo 18)
MEDIUM_MAP = {"Banner Ads": "Banner", "Twitter Ads": "X", "Facebook Ads": "Facebook"}

# Odoo-11-Anhang, der von Seite 17 benutzt wird (E-Bereich Bilder/Medien)
ANHANG_ID = 54092


class Schreibschutz:
    """Verhindert Schreibaufrufe im Trockenlauf (Fehler statt stillem Schreiben)."""

    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client, schreiben: bool):
        self._client = client
        self._schreiben = schreiben

    def kw(self, modell: str, methode: str, args: list, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s %s"
                               % (modell, methode, json.dumps(args, default=str)[:200]))
        return self._client.kw(modell, methode, args, **kwargs)


class Lauf:
    """Zaehler und Ausgabe je Schritt."""

    def __init__(self, schreiben: bool):
        self.schreiben = schreiben
        self.zahlen = {}

    def zaehle(self, schritt: str, feld: str, wert: int = 1):
        d = self.zahlen.setdefault(schritt, {})
        d[feld] = d.get(feld, 0) + wert

    def zeile(self, schritt: str, text: str):
        print("  [%s] %s" % ("SCHREIBEN" if self.schreiben else "TROCKEN", text))
        self.zaehle(schritt, "_meldungen")


# ---------------------------------------------------------------------------
# Odoo 11 lesen (nur search_read/read)
# ---------------------------------------------------------------------------
def lade_o11(cl) -> dict:
    daten = {}
    pgs = cl.kw("website.page", "search_read", [[]],
                fields=["id", "name", "url", "key", "view_id", "website_published",
                        "website_indexed", "is_homepage", "website_meta_title",
                        "website_meta_description", "website_meta_keywords"], order="id")
    arch = {}
    vids = [p["view_id"][0] for p in pgs if p["view_id"]]
    for r in cl.kw("ir.ui.view", "read", [vids, ["arch_db"]]):
        arch[r["id"]] = r["arch_db"] or ""
    for p in pgs:
        p["arch"] = arch.get(p["view_id"][0] if p["view_id"] else 0, "")
    daten["seiten"] = pgs
    daten["menues"] = cl.kw("website.menu", "search_read", [[]],
                            fields=["id", "name", "url", "parent_id", "sequence", "page_id",
                                    "new_window"], order="sequence,id", context={"lang": "de_DE"})
    daten["website"] = cl.kw("website", "search_read", [[]],
                             fields=["id", "name", "domain", "social_twitter", "favicon",
                                     "crm_default_team_id", "salesteam_id", "google_analytics_key",
                                     "default_lang_id", "company_id"])[0]
    daten["tracker"] = cl.kw("link.tracker", "search_read", [[]],
                             fields=["id", "url", "title", "count", "code", "campaign_id",
                                     "medium_id", "source_id", "create_date"], order="id", limit=5000)
    daten["kampagnen"] = cl.kw("utm.campaign", "search_read", [[]], fields=["id", "name"], order="id")
    daten["medien"] = cl.kw("utm.medium", "search_read", [[]], fields=["id", "name"], order="id")
    daten["quellen"] = cl.kw("utm.source", "search_read", [[]], fields=["id", "name"],
                             order="id", limit=5000)
    klicks = cl.kw("link.tracker.click", "search_read", [[]],
                   fields=["id", "link_id", "create_date"], order="id", limit=5000)
    daten["klicks"] = klicks
    daten["anhang"] = cl.kw("ir.attachment", "read", [[ANHANG_ID],
                                                      ["name", "datas", "mimetype", "file_size"]])[0]
    # Odoo 11 zeigt im Kopf das Unternehmenslogo; Odoo 18 nimmt dafuer website.logo
    unternehmen = cl.kw("res.company", "read", [[1], ["name", "logo"]])[0]
    daten["unternehmenslogo"] = unternehmen.get("logo") or False
    return daten


def lade_o18(cl) -> dict:
    return {
        "seiten": cl.kw("website.page", "search_read", [[]],
                        fields=["id", "name", "url", "view_id", "key", "is_published",
                                "website_indexed", "website_id"], order="id"),
        "menues": cl.kw("website.menu", "search_read", [[]],
                        fields=["id", "name", "url", "parent_id", "sequence", "page_id",
                                "website_id", "new_window"], order="sequence,id",
                        context={"lang": "de_DE"}),
        "website": cl.kw("website", "search_read", [[]],
                         fields=["id", "name", "domain", "social_twitter", "favicon",
                                 "crm_default_team_id", "homepage_url", "menu_id",
                                 "company_id"])[0],
        "tracker": cl.kw("link.tracker", "search_count", [[]]),
        "klicks": cl.kw("link.tracker.click", "search_count", [[]]),
        "visitors": cl.kw("website.visitor", "search_count", [[]]),
        "tracks": cl.kw("website.track", "search_count", [[]]),
    }


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------
def finde_seite(cl, key: str, url: str, nur_key: bool = False):
    """Seite ueber den View-Key finden (idempotenter Schluessel).

    `nur_key` fuer die Startseite: dort darf NICHT ueber die URL gesucht werden,
    sonst traefe man die Odoo-Standard-Startseite (Moduldaten).
    """
    vids = cl.kw("ir.ui.view", "search", [[["key", "=", key]]])
    if vids:
        pids = cl.kw("website.page", "search", [[["view_id", "in", vids]]], order="id")
        if pids:
            return pids[0]
    if nur_key:
        return None
    pids = cl.kw("website.page", "search", [[["url", "=", url]]], order="id")
    return pids[0] if pids else None


def normalisiere(arch: str) -> str:
    """Arch fuer den Vergleich normalisieren.

    Odoo speichert beim Schreiben anders serialisiert zurueck (Entitaeten,
    Attribut-Reihenfolge). Fuer die Idempotenz wird deshalb geparst und neu
    serialisiert, statt Zeichen fuer Zeichen zu vergleichen.
    """
    if not arch:
        return ""
    try:
        return ET.tostring(ET.fromstring(arch), encoding="unicode")
    except ET.ParseError:
        return arch.strip()


def finde_view(cl, key: str):
    vids = cl.kw("ir.ui.view", "search", [[["key", "=", key]]])
    return vids[0] if vids else None


def eins(wert):
    """Odoo liefert bei create je nach Modell eine id oder eine Liste von ids."""
    return wert[0] if isinstance(wert, list) else wert


def finde_team(cl, name: str):
    ids = cl.kw("crm.team", "search", [[["name", "=", name]]], limit=1, context={"lang": "de_DE"})
    if not ids:
        ids = cl.kw("crm.team", "search", [[["name", "=", name]]], limit=1, context={"lang": "en_US"})
    return ids[0] if ids else None


def finde_nach_name(cl, modell: str, name: str):
    ids = cl.kw(modell, "search", [[["name", "=", name]]], limit=1)
    return ids[0] if ids else None


def lade_homepage() -> str:
    pfad = os.path.join(HERE, "website_homepage_o18.html")
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Schritt 1: Anhang (vor Seite 17, weil die URL die Anhang-id enthaelt)
# ---------------------------------------------------------------------------
def schritt_anhang(o11, o18cl, lauf: Lauf) -> dict:
    anhang = o11["anhang"]
    name = anhang["name"]
    daten = anhang["datas"]
    roh = base64.b64decode(daten)
    vorhanden = o18cl.kw("ir.attachment", "search_read", [[["name", "=", name]]],
                         fields=["id", "checksum", "file_size", "public"])
    treffer = None
    for a in vorhanden:
        if a["file_size"] == len(roh):
            treffer = a
            break
    if treffer:
        lauf.zeile("anhang", "vorhanden: id %s %r (%d Byte)" % (treffer["id"], name, treffer["file_size"]))
        lauf.zaehle("anhang", "vorhanden")
        return {"id": treffer["id"], "name": name, "vorher": treffer["id"]}
    if not lauf.schreiben:
        lauf.zeile("anhang", "neu anzulegen: %r (%d Byte, oeffentlich)" % (name, len(roh)))
        lauf.zaehle("anhang", "neu_geplant")
        return {"id": None, "name": name, "vorher": ANHANG_ID}
    neu = eins(o18cl.kw("ir.attachment", "create", [[{
        "name": name, "datas": daten, "mimetype": anhang.get("mimetype") or "image/png",
        "public": True, "res_model": False, "res_id": 0,
    }]]))
    lauf.zeile("anhang", "angelegt: id %s %r" % (neu, name))
    lauf.zaehle("anhang", "neu")
    return {"id": neu, "name": name, "vorher": ANHANG_ID}


# ---------------------------------------------------------------------------
# Schritt 2: Seiten
# ---------------------------------------------------------------------------
def schritt_seiten(o11, o18cl, lauf: Lauf, anhang: dict, website_id: int) -> dict:
    seiten11 = {p["id"]: p for p in o11["seiten"]}
    ergebnis = {}
    for o11_id, ziel in SEITEN.items():
        quelle = seiten11[o11_id]
        if ziel.get("arch") == "homepage":
            arch = lade_homepage()
            bericht = {"hinweis": "Startseite gestalterisch neu (E1), Inhalt aus Odoo 11"}
        else:
            arch, bericht = markup.konvertiere(quelle["arch"])
        # Bildverweis auf den migrierten Anhang umschreiben
        if anhang.get("id"):
            arch = arch.replace("/web/image/%s/" % ANHANG_ID, "/web/image/%s/" % anhang["id"])
        elif not lauf.schreiben:
            arch = arch.replace("/web/image/%s/" % ANHANG_ID, "/web/image/<neu>/")

        page_id = finde_seite(o18cl, ziel["key"], ziel["url"],
                              nur_key=bool(ziel.get("homepage")))
        werte = {
            "name": ziel["name"],
            "url": ziel["url"],
            "is_published": bool(quelle["website_published"]),
            "website_indexed": bool(quelle["website_indexed"]),
            "website_id": website_id,
        }
        if page_id:
            aktuell = o18cl.kw("website.page", "read", [[page_id], ["name", "url", "is_published",
                                                                     "website_indexed", "view_id",
                                                                     "website_id"]])[0]
            vid = aktuell["view_id"][0]
            arch_ist = o18cl.kw("ir.ui.view", "read", [[vid], ["arch_db"]])[0]["arch_db"] or ""
            gleich = (normalisiere(arch_ist) == normalisiere(arch))
            if lauf.schreiben:
                if not gleich:
                    o18cl.kw("ir.ui.view", "write", [[vid], {"arch_db": arch}])
                o18cl.kw("website.page", "write", [[page_id], werte])
                # key nach dem Namen setzen (write auf name wuerde den Key neu ableiten)
                if finde_view(o18cl, ziel["key"]) is None:
                    o18cl.kw("ir.ui.view", "write", [[vid], {"key": ziel["key"]}])
            lauf.zeile("seiten", "id %2d %-38s %-42s %s%s" % (
                o11_id, ziel["name"], ziel["url"],
                "unveraendert" if gleich else "Inhalt aktualisiert",
                "" if quelle["website_published"] else " (nicht veroeffentlicht)"))
            lauf.zaehle("seiten", "vorhanden")
            if not gleich:
                lauf.zaehle("seiten", "arch_aktualisiert")
            ergebnis[o11_id] = page_id
        else:
            if lauf.schreiben:
                vid = finde_view(o18cl, ziel["key"])
                if vid:
                    # Rest eines abgebrochenen Laufs: vorhandene View weiterverwenden
                    o18cl.kw("ir.ui.view", "write", [[vid], {"arch_db": arch, "name": ziel["name"],
                                                             "website_id": website_id}])
                else:
                    vid = o18cl.kw("ir.ui.view", "create", [[{
                        "name": ziel["name"], "key": ziel["key"], "type": "qweb",
                        "website_id": website_id, "arch_db": arch,
                    }]])
                    vid = vid[0] if isinstance(vid, list) else vid
                page_id = o18cl.kw("website.page", "create", [[dict(werte, view_id=vid)]])
                page_id = page_id[0] if isinstance(page_id, list) else page_id
                lauf.zeile("seiten", "id %2d %-38s %-42s angelegt (page %s, view %s)%s" % (
                    o11_id, ziel["name"], ziel["url"], page_id, vid,
                    "" if quelle["website_published"] else " (nicht veroeffentlicht)"))
                lauf.zaehle("seiten", "neu")
            else:
                lauf.zeile("seiten", "id %2d %-38s %-42s neu anzulegen%s" % (
                    o11_id, ziel["name"], ziel["url"],
                    "" if quelle["website_published"] else " (nicht veroeffentlicht)"))
                lauf.zaehle("seiten", "neu_geplant")
            ergebnis[o11_id] = page_id
        lauf.zahlen.setdefault("seiten_bericht", {})[str(o11_id)] = bericht
    return ergebnis


# ---------------------------------------------------------------------------
# Schritt 3: Menues
# ---------------------------------------------------------------------------
def schritt_menues(o11, o18cl, lauf: Lauf, seiten: dict, website_id: int) -> None:
    website = o18cl.kw("website", "read", [[website_id], ["menu_id"]])[0]
    wurzel = website["menu_id"][0] if website["menu_id"] else None
    if wurzel is None:
        raise RuntimeError("Website %s hat kein Wurzelmenue" % website_id)

    aktuelle = o18cl.kw("website.menu", "search_read", [[["parent_id", "=", wurzel]]],
                        fields=["id", "name", "url", "sequence", "page_id"], order="sequence,id")
    nach_url = {}
    for m in aktuelle:
        nach_url.setdefault(m["url"], []).append(m)

    soll = []
    for o11_id, name, url, seite, seq in MENUES:
        page_id = seiten.get(seite) if seite else None
        if seite and not page_id:
            # Teillauf (--nur menues) oder Reihenfolge: Zielseite selbst aufloesen,
            # damit die Menue-Seiten-Verknuepfung nicht verloren geht (Sichtbarkeit!)
            ziel = SEITEN.get(seite)
            if ziel:
                page_id = finde_seite(o18cl, ziel["key"], ziel["url"],
                                      nur_key=bool(ziel.get("homepage")))
        soll.append((url, name, seq, page_id))

    # Wurzel umbenennen
    if lauf.schreiben:
        for sprache in (None, "de_DE", "en_US"):
            ctx = {"lang": sprache} if sprache else None
            o18cl.kw("website.menu", "write", [[wurzel], {"name": WURZEL_NAME}], **({"context": ctx} if ctx else {}))
    lauf.zeile("menues", "Wurzelmenue %s heisst kuenftig %r (Odoo 11)" % (wurzel, WURZEL_NAME))

    benutzt = set()
    for url, name, seq, page_id in soll:
        kandidaten = [m for m in nach_url.get(url, []) if m["id"] not in benutzt]
        if kandidaten:
            m = kandidaten[0]
            benutzt.add(m["id"])
            werte = {"name": name, "sequence": seq, "url": url, "page_id": page_id or False}
            if lauf.schreiben:
                o18cl.kw("website.menu", "write", [[m["id"]], werte])
                # Name auch in der Anzeigesprache setzen: der alte de_DE-Slot
                # ("Veranstaltungen") bleibt sonst stehen (Menue-Falle Session 114)
                o18cl.kw("website.menu", "write", [[m["id"]], werte],
                         context={"lang": "de_DE"})
                o18cl.kw("website.menu", "write", [[m["id"]], werte],
                         context={"lang": "en_US"})
            lauf.zeile("menues", "%2d %-38s %-42s vorhanden (id %s)" % (seq, name, url, m["id"]))
            lauf.zaehle("menues", "vorhanden")
            continue
        if lauf.schreiben:
            neu = eins(o18cl.kw("website.menu", "create", [[{
                "name": name, "url": url, "sequence": seq, "parent_id": wurzel,
                "page_id": page_id or False, "website_id": website_id, "new_window": False,
            }]]))
            for sprache in ("de_DE", "en_US"):
                o18cl.kw("website.menu", "write", [[neu], {"name": name}],
                         context={"lang": sprache})
            lauf.zeile("menues", "%2d %-38s %-42s angelegt (id %s)" % (seq, name, url, neu))
            lauf.zaehle("menues", "neu")
        else:
            lauf.zeile("menues", "%2d %-38s %-42s neu anzulegen" % (seq, name, url))
            lauf.zaehle("menues", "neu_geplant")

    # ueberzaehlige Demo-Punkte unter der Wurzel entfernen (E14)
    for m in aktuelle:
        if m["id"] in benutzt:
            continue
        lauf.zeile("menues", "Demo-Punkt entfernen: %r (%s, id %s)" % (m["name"], m["url"], m["id"]))
        if lauf.schreiben:
            o18cl.kw("website.menu", "unlink", [[m["id"]]])
        lauf.zaehle("menues", "demo_entfernt")


# ---------------------------------------------------------------------------
# Schritt 4: Einstellungen (E11)
# ---------------------------------------------------------------------------
def schritt_einstellungen(o11, o18cl, lauf: Lauf, website_id: int) -> None:
    w11 = o11["website"]
    w18 = o18cl.kw("website", "read", [[website_id], ["name", "domain", "social_twitter",
                                                      "favicon", "crm_default_team_id",
                                                      "logo"]])[0]
    werte = {}
    if w18["name"] != w11["name"]:
        werte["name"] = w11["name"]
    if (w18["social_twitter"] or "") != (w11["social_twitter"] or ""):
        werte["social_twitter"] = w11["social_twitter"] or False
    if w11.get("favicon") and (w18.get("favicon") or "") != w11["favicon"]:
        werte["favicon"] = w11["favicon"]
    # Kopf-Logo: Odoo 11 zeigt das Unternehmenslogo (res.company 1). Ohne
    # website.logo rendert Odoo 18 ein kaputtes Bild im Kopf.
    if o11.get("unternehmenslogo") and (w18.get("logo") or "") != o11["unternehmenslogo"]:
        werte["logo"] = o11["unternehmenslogo"]

    # CRM-Standardteam: Odoo 11 "Vertriebskanäle (Intern)" existiert in Odoo 18 (id 5 lokal).
    team = finde_team(o18cl, "Vertriebskanäle (Intern)")
    if team and (w18["crm_default_team_id"] or [None])[0] != team:
        werte["crm_default_team_id"] = team
    # Odoo 11 hat zusaetzlich salesteam_id ("Webseite"); dieses Feld gibt es in
    # Odoo 18 nicht mehr (nur crm_default_team_id) - dokumentiert, kein Ersatzwert.

    if werte:
        kurz = {}
        for k, v in werte.items():
            if k in ("favicon", "logo") and isinstance(v, str):
                kurz[k] = "<%d Zeichen>" % len(v)
            else:
                kurz[k] = v
        lauf.zeile("einstellungen", "setzen: %s" % json.dumps(kurz, ensure_ascii=False))
        if lauf.schreiben:
            o18cl.kw("website", "write", [[website_id], werte])
        lauf.zaehle("einstellungen", "geaendert", len(werte))
    else:
        lauf.zeile("einstellungen", "keine Aenderung noetig")
    lauf.zeile("einstellungen", "Domain bleibt %r (Produktivdomain = externer Konfigurationspunkt, E11)"
               % w18["domain"])


# ---------------------------------------------------------------------------
# Schritt 5: Demo-Daten (E14)
# ---------------------------------------------------------------------------
def schritt_demo(o11, o18cl, lauf: Lauf, website_id: int) -> None:
    # 5a) doppelte Startseite: die vom Konfigurator kopierte, an die Website
    #     gebundene Seite wird entfernt; die Odoo-Standard-Startseite (Moduldaten,
    #     wuerde beim Upgrade zurueckkehren) wird aus dem Pfad "/" genommen.
    pages = o18cl.kw("website.page", "search_read", [[["url", "=", "/"]]],
                     fields=["id", "name", "key", "view_id", "website_id"], order="id")
    unsere_key = SEITEN[1]["key"]
    for p in pages:
        if p["key"] == unsere_key:
            continue
        if p["website_id"]:
            lauf.zeile("demo", "doppelte Startseite entfernen: page %s (view %s, %r, Website %s)"
                       % (p["id"], p["view_id"][0], p["name"], p["website_id"][1]))
            if lauf.schreiben:
                o18cl.kw("website.page", "unlink", [[p["id"]]])
            lauf.zaehle("demo", "seite_entfernt")
        else:
            lauf.zeile("demo", "Odoo-Standard-Startseite %s (view %s) auf %r legen und "
                               "unveroeffentlicht lassen - Moduldaten, loeschen waere nicht dauerhaft"
                       % (p["id"], p["view_id"][0], "/homepage-vorlage"))
            if lauf.schreiben:
                o18cl.kw("website.page", "write", [[p["id"]], {
                    "url": "/homepage-vorlage", "is_published": False,
                    "name": "Homepage-Vorlage (Odoo-Standard)"}])
            lauf.zaehle("demo", "standardseite_entkoppelt")

    # 5b) zweites Wurzelmenue (Demo) entfernen.
    #     ACHTUNG: `website.main_menu` ist Odoo-Standarddaten (uebergeordnetes Menue fuer
    #     neue Websites) und kann nicht geloescht werden; seine Kinder werden NICHT
    #     angefasst, weil website.menu.unlink beim Loeschen eines Master-Kindes
    #     zusaetzlich Website-Menues mit gleicher URL entfernt.
    w = o18cl.kw("website", "read", [[website_id], ["menu_id"]])[0]
    wurzel = w["menu_id"][0]
    md = o18cl.kw("ir.model.data", "search_read",
                  [[["module", "=", "website"], ["name", "=", "main_menu"]], ["res_id"]])
    master = md[0]["res_id"] if md else None
    alle = o18cl.kw("website.menu", "search_read", [[["parent_id", "=", False]]],
                    fields=["id", "name"], order="id")
    for m in alle:
        if m["id"] == wurzel:
            continue
        if m["id"] == master:
            lauf.zeile("demo", "Wurzelmenue %r (id %s) ist Odoo-Standarddaten (website.main_menu) "
                               "und bleibt als Vorlage fuer neue Websites erhalten"
                       % (m["name"], m["id"]))
            lauf.zaehle("demo", "standard_wurzelmenue")
            continue
        lauf.zeile("demo", "Demo-Wurzelmenue entfernen: %r (id %s)" % (m["name"], m["id"]))
        if lauf.schreiben:
            o18cl.kw("website.menu", "unlink", [[m["id"]]])
        lauf.zaehle("demo", "wurzelmenue_entfernt")

    # 5c) Demo-Besucher und Demo-Seitenansichten
    for modell, schluessel in (("website.visitor", "besucher_entfernt"),
                               ("website.track", "seitenansichten_entfernt")):
        ids = o18cl.kw(modell, "search", [[]])
        if ids:
            lauf.zeile("demo", "%s entfernen: %d Datensaetze %s" % (modell, len(ids), ids))
            if lauf.schreiben:
                o18cl.kw(modell, "unlink", [ids])
            lauf.zaehle("demo", schluessel, len(ids))


# ---------------------------------------------------------------------------
# Schritt 6: Link-Tracker (E9)
# ---------------------------------------------------------------------------
def schritt_tracker(o11, o18cl, lauf: Lauf) -> None:
    # Kampagnen. Im Trockenlauf werden Platzhalter je NAME vergeben, damit die
    # Eindeutigkeitsgruppen (siehe unten) in beiden Laeufen gleich berechnet werden.
    k_map = {}
    vorhanden = {c["name"]: c["id"] for c in
                 o18cl.kw("utm.campaign", "search_read", [[]], fields=["id", "name"], order="id")}
    for c in o11["kampagnen"]:
        if c["name"] in vorhanden and not isinstance(vorhanden[c["name"]], str):
            k_map[c["id"]] = vorhanden[c["name"]]
            lauf.zaehle("tracker", "kampagne_vorhanden")
        else:
            lauf.zeile("tracker", "Kampagne anlegen: %r" % c["name"])
            if lauf.schreiben:
                neu = eins(o18cl.kw("utm.campaign", "create", [[{"name": c["name"]}]]))
                vorhanden[c["name"]] = neu
                k_map[c["id"]] = neu
            else:
                vorhanden.setdefault(c["name"], "neu:%s" % c["name"])
                k_map[c["id"]] = vorhanden[c["name"]]
            lauf.zaehle("tracker", "kampagne_neu")

    # Medien (Odoo 18 hat umbenannt)
    m_map = {}
    medien18 = {m["name"]: m["id"] for m in
                o18cl.kw("utm.medium", "search_read", [[]], fields=["id", "name"], order="id")}
    for m in o11["medien"]:
        name = m["name"]
        ziel = name if name in medien18 else MEDIUM_MAP.get(name)
        if ziel and ziel in medien18:
            m_map[m["id"]] = medien18[ziel]
            lauf.zaehle("tracker", "medium_abgebildet")
        else:
            lauf.zeile("tracker", "Medium anlegen: %r (kein Odoo-18-Gegenstueck)" % name)
            if lauf.schreiben:
                neu = eins(o18cl.kw("utm.medium", "create", [[{"name": name}]]))
                medien18[name] = neu
                m_map[m["id"]] = neu
            else:
                m_map[m["id"]] = "neu:medium:%s" % name
            lauf.zaehle("tracker", "medium_neu")

    # Quellen
    q_map = {}
    quellen18 = {q["name"]: q["id"] for q in
                 o18cl.kw("utm.source", "search_read", [[]], fields=["id", "name"], order="id", limit=5000)}
    for q in o11["quellen"]:
        if q["name"] in quellen18:
            q_map[q["id"]] = quellen18[q["name"]]
            lauf.zaehle("tracker", "quelle_vorhanden")
        else:
            if lauf.schreiben:
                neu = eins(o18cl.kw("utm.source", "create", [[{"name": q["name"]}]]))
                quellen18[q["name"]] = neu
                q_map[q["id"]] = neu
            else:
                q_map[q["id"]] = "neu:quelle:%s" % q["name"]
            lauf.zaehle("tracker", "quelle_neu")

    # Tracker ueber den Kurz-URL-Code zuordnen (stabiler Schluessel)
    code_zu_link = {}
    for r in o18cl.kw("link.tracker.code", "search_read", [[], ["code", "link_id"]], limit=5000):
        code_zu_link[r["code"]] = r["link_id"][0]

    def zielwerte(t):
        return {
            "url": t["url"],
            "title": t["title"] or t["url"],
            "campaign_id": k_map.get((t["campaign_id"] or [0])[0]),
            "medium_id": m_map.get((t["medium_id"] or [0])[0]),
            "source_id": q_map.get((t["source_id"] or [0])[0]),
        }

    # Odoo 18 verlangt Eindeutigkeit von (url, kampagne, medium, quelle, label).
    # Odoo 11 erlaubte Dubletten (ein Kurzlink je Mailing). Gruppiert wird nach den
    # GEMAPPTEN Odoo-18-Werten - nur so ist die Regel stabil und nachvollziehbar.
    gruppen = {}
    for t in o11["tracker"]:
        z = zielwerte(t)
        schluessel = (z["url"], z["campaign_id"], z["medium_id"], z["source_id"])
        gruppen.setdefault(schluessel, []).append(t["id"])
    label_fuer = {}
    for schluessel, ids in gruppen.items():
        for i, tid in enumerate(sorted(ids)):
            if i:
                label_fuer[tid] = "Odoo-11-Link %s" % tid
    lauf.zeile("tracker", "%d Tracker in Odoo 11, davon %d mit technischer Kennung im "
                          "Feld Bezeichnung (Eindeutigkeit), %d ohne"
               % (len(o11["tracker"]), len(label_fuer), len(o11["tracker"]) - len(label_fuer)))

    # Klicks je Link (Odoo 18 rechnet count aus den Klick-Datensaetzen)
    klicks_je_link = {}
    for k in o11["klicks"]:
        lid = k["link_id"][0] if k["link_id"] else None
        if lid:
            klicks_je_link.setdefault(lid, []).append(k["create_date"])

    # bereits vorhandene Klick-Datensaetze je Link in Odoo 18 (1 Abfrage statt 837)
    klicks18 = {}
    for r in o18cl.kw("link.tracker.click", "search_read", [[], ["link_id"]], limit=20000):
        if r["link_id"]:
            klicks18[r["link_id"][0]] = klicks18.get(r["link_id"][0], 0) + 1

    def klicks_nachziehen(t, link_id):
        """Klickzahlen: je Klick ein Datensatz ohne IP-Adresse und ohne Mailbezug."""
        soll = t["count"] or 0
        ist = klicks18.get(link_id, 0) if link_id else 0
        fehlen = max(0, soll - ist)
        if fehlen:
            daten = (klicks_je_link.get(t["id"]) or [])[:fehlen]
            neue = []
            for i in range(fehlen):
                w = {"link_id": link_id}
                if i < len(daten) and daten[i]:
                    w["create_date"] = daten[i]
                neue.append(w)
            if lauf.schreiben and link_id:
                o18cl.kw("link.tracker.click", "create", [neue])
            lauf.zaehle("tracker", "klicks_neu", fehlen)
        lauf.zaehle("tracker", "klicks_soll", soll)

    # Phase 1: bereits vorhandene Tracker aktualisieren (Zuordnung ueber den Code).
    # Ein write prueft die Eindeutigkeit nur fuer den geschriebenen Datensatz,
    # deshalb gibt es hier keinen Konflikt mit noch nicht umbenannten Nachbarn.
    offene = []
    for t in o11["tracker"]:
        link_id = code_zu_link.get(t["code"])
        if not link_id:
            offene.append(t)
            continue
        vals = zielwerte(t)
        vals["label"] = label_fuer.get(t["id"]) or False
        lauf.zaehle("tracker", "vorhanden")
        if lauf.schreiben:
            o18cl.kw("link.tracker", "write", [[link_id], vals])
        klicks_nachziehen(t, link_id)

    # Phase 2: fehlende Tracker anlegen (Reihenfolge = Odoo-11-id, damit die
    # Label-Regel reproduzierbar bleibt).
    for t in offene:
        vals = zielwerte(t)
        vals["label"] = label_fuer.get(t["id"]) or False
        if not lauf.schreiben:
            lauf.zaehle("tracker", "neu_geplant")
            klicks_nachziehen(t, None)
            continue
        try:
            link_id = eins(o18cl.kw("link.tracker", "create", [[vals]]))
        except RuntimeError as err:
            if "eindeutig" not in str(err):
                raise
            # Sicherheitsnetz: Kombination doch belegt -> technische Kennung setzen
            vals["label"] = "Odoo-11-Link %s" % t["id"]
            link_id = eins(o18cl.kw("link.tracker", "create", [[vals]]))
            lauf.zaehle("tracker", "label_sicherheitsnetz")
        # historischen Kurz-URL-Code setzen (Kurz-URLs bleiben gleich)
        codes = o18cl.kw("link.tracker.code", "search", [[["link_id", "=", link_id]]])
        if codes:
            o18cl.kw("link.tracker.code", "write", [[codes[0]], {"code": t["code"]}])
        else:
            o18cl.kw("link.tracker.code", "create", [[{"code": t["code"], "link_id": link_id}]])
        code_zu_link[t["code"]] = link_id
        lauf.zaehle("tracker", "neu")
        klicks_nachziehen(t, link_id)

    # Stichprobe Kurz-URLs
    for muster in ("wFy",):
        ids = o18cl.kw("link.tracker.code", "search", [[["code", "=", muster]]])
        if ids:
            info = o18cl.kw("link.tracker.code", "read", [ids, ["code", "link_id"]])[0]
            tracker = o18cl.kw("link.tracker", "read", [[info["link_id"][0]],
                                                        ["url", "count", "short_url"]])[0]
            lauf.zeile("tracker", "Stichprobe Code %s -> %s (Klicks %s, Kurz-URL %s)"
                       % (muster, tracker["url"], tracker["count"], tracker["short_url"]))


# ---------------------------------------------------------------------------
# Abnahme (read-only)
# ---------------------------------------------------------------------------
def abnahme(o11, o18cl, instanz: str) -> dict:
    p11 = o11["seiten"]
    auswahl = {p["id"] for p in p11} & set(SEITEN)
    ergebnis = {}
    seiten18 = o18cl.kw("website.page", "search_read", [[]],
                        fields=["id", "name", "url", "key", "is_published", "website_id"],
                        order="id")
    menues18 = o18cl.kw("website.menu", "search_read", [[]],
                        fields=["id", "name", "url", "parent_id", "sequence"], order="sequence,id",
                        context={"lang": "de_DE"})
    tracker18 = o18cl.kw("link.tracker", "search_read", [[]], fields=["count"], limit=5000)
    ergebnis.update({
        "instanz": instanz,
        "o11_seiten": len(p11),
        "o11_uebernommen": len(auswahl),
        "o18_seiten": len(seiten18),
        "o18_seiten_liste": [(p["id"], p["name"], p["url"], p["is_published"]) for p in seiten18],
        "o11_menues": len(o11["menues"]),
        "o18_menues": len(menues18),
        "o18_menues_liste": [(m["sequence"], m["name"], m["url"]) for m in menues18],
        "o11_tracker": len(o11["tracker"]),
        "o11_klicksumme": sum(t["count"] for t in o11["tracker"]),
        "o18_tracker": len(tracker18),
        "o18_klicksumme": sum(t["count"] for t in tracker18),
        "o18_klickdatensaetze": o18cl.kw("link.tracker.click", "search_count", [[]]),
    })
    return ergebnis


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--schreiben", action="store_true", help="ohne dieses Flag nur Trockenlauf")
    ap.add_argument("--nur", help="Komma-Liste von Schritten (%s)" % ", ".join(SCHRITTE))
    ap.add_argument("--abnahme", action="store_true", help="nur Abnahmezaehlung")
    ap.add_argument("--json")
    args = ap.parse_args()

    schritte = [s.strip() for s in args.nur.split(",")] if args.nur else SCHRITTE
    for s in schritte:
        if s not in SCHRITTE:
            ap.error("unbekannter Schritt %r" % s)

    o11cl = client.o11()
    o18cl = Schreibschutz(client.o18(args.instanz), args.schreiben)
    lauf = Lauf(args.schreiben)

    print("=== Website-Migration %s (%s) ===" % (
        args.instanz, "SCHREIBEN" if args.schreiben else "TROCKENLAUF"))
    o11 = lade_o11(o11cl)
    o18 = lade_o18(o18cl)
    website_id = o18["website"]["id"]

    print("Odoo 11: %d Seiten (%d veroeffentlicht), %d Menues, %d Tracker, %d Klicks"
          % (len(o11["seiten"]), sum(1 for p in o11["seiten"] if p["website_published"]),
             len(o11["menues"]), len(o11["tracker"]), sum(t["count"] for t in o11["tracker"])))
    print("Odoo 18: %d Seiten, %d Menues, %d Tracker, %d Klicks, %d Besucher, %d Seitenansichten"
          % (len(o18["seiten"]), len(o18["menues"]), o18["tracker"], o18["klicks"],
             o18["visitors"], o18["tracks"]))

    # Befund Formulare und Medien (Auftrag: Formulare + tatsaechlich verwendete Medien)
    auswahl = [p for p in o11["seiten"] if p["id"] in SEITEN]
    formulare = sum(p["arch"].count("<form") for p in auswahl)
    base64_bilder = sum(p["arch"].count("data:image/") for p in auswahl)
    web_bilder = sum(p["arch"].count("/web/image/") for p in auswahl)
    print("Odoo 11 (uebernommene Seiten): %d Formulare, %d Base64-Bilder, %d /web/image-Verweise"
          % (formulare, base64_bilder, web_bilder))
    if formulare == 0:
        print("  -> Odoo 11 hat auf keiner Website-Seite ein Formular; das Kontaktformular "
              "entsteht in Odoo 18 ueber die Standardseite /contactus (website_crm -> crm.lead).")

    if args.abnahme:
        print(json.dumps(abnahme(o11cl, o18cl, args.instanz), ensure_ascii=False, indent=1))
        return 0

    anhang = {"id": ANHANG_ID, "name": o11["anhang"]["name"]}
    if "anhang" in schritte:
        print("\n-- Anhang --")
        anhang = schritt_anhang(o11, o18cl, lauf)
    elif "seiten" in schritte:
        # Anhang immer aufloesen, sonst schreibt der Seiten-Schritt die alte
        # Odoo-11-Anhang-id in die Bild-URL zurueck (nicht idempotent).
        anhang = schritt_anhang(o11, o18cl, lauf)
    if "demo" in schritte:
        print("\n-- Demo-Daten (vor den Seiten: gibt den Pfad / frei) --")
        schritt_demo(o11, o18cl, lauf, website_id)
    seiten = {}
    if "seiten" in schritte:
        print("\n-- Seiten --")
        seiten = schritt_seiten(o11, o18cl, lauf, anhang, website_id)
    if "menues" in schritte:
        print("\n-- Menues --")
        schritt_menues(o11, o18cl, lauf, seiten, website_id)
    if "einstellungen" in schritte:
        print("\n-- Einstellungen --")
        schritt_einstellungen(o11, o18cl, lauf, website_id)
    if "tracker" in schritte:
        print("\n-- Link-Tracker --")
        schritt_tracker(o11, o18cl, lauf)

    print("\n=== Summe (%s) ===" % ("Schreiblauf" if args.schreiben else "Trockenlauf"))
    print(json.dumps(lauf.zahlen, ensure_ascii=False, indent=1, sort_keys=True))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"zahlen": lauf.zahlen, "o11": {k: v for k, v in o11.items()
                                                      if k not in ("seiten", "anhang")}},
                      fh, ensure_ascii=False, indent=1, default=str)
        print("JSON:", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
