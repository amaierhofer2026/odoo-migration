# -*- coding: utf-8 -*-
"""CRM / Verkaufschancen: Migrationsskript Odoo 11 -> Odoo 18.

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer
(Session 145, 17.11.2026). Quelle: Odoo 11 Prod ``ITK_V1_a`` - ausschliesslich
lesend. Ziel: Odoo 18 (lokal oder VM).

Umfang (gemessen am 17.11.2026, read-only):
- crm.stage        9 Stufen
- crm.team         8 Vertriebskanaele
- crm.lead.tag    44 Stichwoerter
- crm.lost.reason  5 Ablehnungsgruende
- mail.activity.type 12 Typen (davon 5 ITK-eigene)
- crm.lead     6.994 Interessenten und Verkaufschancen (6.973 aktiv, 21 archiviert)
- mail.activity   32 offene Aktivitaeten auf Interessenten

Nicht migriert (dokumentiert, siehe docs/migration/crm_migration.md):
- Chatter (3.479 mail.message) und Anhaenge (204, 71 MB)
- utm.source (220) und utm.campaign (16): von keinem Vorgang referenziert
- kanban_state, opt_out, day_open, day_close: in Odoo 18 nicht vorhanden bzw. berechnet

Idempotenz: technisches Feld ``itk_o11_id`` (Modul itk_migration_keys) auf
crm.lead, crm.stage, crm.team, crm.tag, crm.lost.reason, utm.*, mail.activity.type.
Der Zielbestand wird IMMER mit ``active_test=False`` gelesen, sonst werden
archivierte Datensaetze bei jedem Lauf neu angelegt.

Datenschutz: Die Migration verarbeitet personenbezogene Daten zwischen Odoo 11 und
Odoo 18. Konsole, Mapping-Datei und Dokumentation enthalten nur Zaehlwerte, IDs und
Status - keine Namen, E-Mail-Adressen, Telefonnummern, Freitexte oder Adressen.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/crm_migration.py --instanz lokal
    python scripts/migration/crm_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
    python scripts/migration/crm_migration.py --instanz vm --mapping "%LOCALAPPDATA%\\Temp\\crm_mapping.json"
"""
from __future__ import annotations

import argparse
import html as _html
import json
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX11 = {"lang": "de_DE"}
CTX18 = {"lang": "de_DE"}
BATCH = 100

# ---------------------------------------------------------------------------
# Verbindliche Benutzerzuordnung (Freigabe Anna Maierhofer, Session 145)
# ---------------------------------------------------------------------------
# Schluessel: Odoo-11-Login (klein geschrieben). Wert: (Odoo-18-Login klein,
# Odoo-18-Anzeigename). Die Regel greift VOR dem Login-/Namensvergleich.
#
# "Maierhofer Anna" (Odoo 11) ist dieselbe reale Benutzerin wie das bestehende
# Odoo-18-Konto "Administrator" (Login anna.maierhofer@it-kommunal.at). In Odoo 18
# existiert zusaetzlich ein Konto "Maierhofer Anna" (Login Anna.maierhofer@...);
# dieses ist NICHT das Ziel. Das Administrator-Konto bleibt unveraendert
# (keine Umbenennung, keine Rechteaenderung, kein zweites Konto).
#
# "Breiteneder Lorenz" fuehrt in Odoo 11 den veralteten Login lorenz.galler@...;
# in Odoo 18 heisst das Konto lorenz.breiteneder@... (137 Vorgaenge).
BENUTZER_MAPPING = {
    "anna.maierhofer@it-kommunal.at": ("anna.maierhofer@it-kommunal.at", "Administrator"),
    "lorenz.galler@it-kommunal.at": ("lorenz.breiteneder@it-kommunal.at", "Breiteneder Lorenz"),
}

# Odoo-11-Benutzer ohne Entsprechung, die als minimale historische Struktur
# angelegt und sofort inaktiv gestellt werden (Sammel-/Funktionskonto).
# Wert: (Anzeigename, Login im Zielsystem)
HISTORISCHE_BENUTZER = {
    "martina.waiss@itkommunal.at": ("ACO-Market", "aco-market@it-kommunal.at"),
}

# Odoo-11-Felder, die Odoo 18 nicht mehr fuehrt oder selbst berechnet
NICHT_UEBERNOMMEN = ("kanban_state", "opt_out", "day_open", "day_close",
                     "date_action_last", "meeting_count", "sale_number", "sale_amount_total")

FELDER_LEAD = ["id", "name", "type", "active", "stage_id", "team_id", "user_id", "partner_id",
               "partner_name", "contact_name", "source_id", "campaign_id", "medium_id", "priority",
               "tag_ids", "lost_reason", "probability", "planned_revenue", "date_deadline",
               "date_closed", "date_open", "date_last_stage_update", "date_conversion",
               "create_date", "write_date", "create_uid", "write_uid", "description", "email_from",
               "phone", "mobile", "state_id", "country_id", "title", "function", "x_Anrede_Lead",
               "x_Lead_Quelle", "x_Produktinteresse", "x_lead_status", "company_id", "referred",
               "color", "street", "street2", "zip", "city", "website", "email_cc"]


class Schreibschutz:
    """Bricht jeden Schreibaufruf im Trockenlauf ab (Sicherheitsnetz)."""

    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben: bool):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


def text_nach_html(text):
    if not text:
        return False
    if "<p>" in text or "<br" in text or "<div" in text:
        return text
    vereinheitlicht = text.replace(chr(13) + chr(10), chr(10))
    zeilen = [z.strip() for z in vereinheitlicht.split(chr(10))]
    return "".join("<p>%s</p>" % _html.escape(z) if z else "<p><br></p>" for z in zeilen)


def m2o(wert):
    return wert[0] if isinstance(wert, (list, tuple)) and wert else None


def o11_laden(o11):
    """Liest den kompletten CRM-Bestand aus Odoo 11 (nur lesende Aufrufe)."""
    d = {}
    d["stages"] = o11.kw("crm.stage", "search_read",
                         [[], ["id", "name", "sequence", "probability", "fold", "on_change"]],
                         context=CTX11, order="sequence,id", limit=200)
    d["teams"] = o11.kw("crm.team", "search_read",
                        [[], ["id", "name", "use_leads", "use_opportunities", "user_id",
                              "active", "team_type"]],
                        context=dict(CTX11, active_test=False), order="id", limit=200)
    d["tags"] = o11.kw("crm.lead.tag", "search_read", [[], ["id", "name", "color"]],
                       context=CTX11, order="id", limit=500)
    d["lost"] = o11.kw("crm.lost.reason", "search_read", [[], ["id", "name", "active"]],
                       context=dict(CTX11, active_test=False), order="id", limit=100)
    d["sources"] = o11.kw("utm.source", "search_read", [[], ["id", "name"]],
                          context=CTX11, order="id", limit=1000)
    d["campaigns"] = o11.kw("utm.campaign", "search_read", [[], ["id", "name"]],
                            context=CTX11, order="id", limit=500)
    d["mediums"] = o11.kw("utm.medium", "search_read", [[], ["id", "name"]],
                          context=dict(CTX11, active_test=False), order="id", limit=100)
    d["activity_types"] = o11.kw("mail.activity.type", "search_read",
                                 [[], ["id", "name", "summary", "category"]],
                                 context=dict(CTX11, active_test=False), order="id", limit=200)
    d["states"] = o11.kw("res.country.state", "search_read",
                         [[("country_id.code", "=", "AT")], ["id", "name", "code"]],
                         context=CTX11, limit=100)
    d["titles"] = o11.kw("res.partner.title", "search_read", [[], ["id", "name"]],
                         context=CTX11, limit=200)
    d["countries"] = o11.kw("res.country", "search_read", [[], ["id", "code"]],
                            context=CTX11, limit=300)
    ids = o11.kw("crm.lead", "search", [[]], context=dict(CTX11, active_test=False))
    leads = []
    for i in range(0, len(ids), 500):
        leads += o11.kw("crm.lead", "read", [ids[i:i + 500], FELDER_LEAD],
                        context=dict(CTX11, active_test=False))
    d["leads"] = leads
    d["activities"] = o11.kw("mail.activity", "search_read",
                             [[("res_model", "=", "crm.lead")],
                              ["id", "res_id", "activity_type_id", "user_id", "date_deadline",
                               "summary", "note"]],
                             context=CTX11, order="date_deadline,id", limit=2000)
    return d


def ziel_laden(o18):
    """Liest den vorhandenen Odoo-18-Bestand inklusive archivierter Datensaetze."""
    ctx = {"lang": "de_DE", "active_test": False}

    def ids_map(modell, limit=20000):
        rows = o18.kw(modell, "search_read", [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]],
                      context=ctx, limit=limit)
        return {r["itk_o11_id"]: r["id"] for r in rows}

    d = {
        "lead": ids_map("crm.lead"),
        "stage": ids_map("crm.stage"),
        "team": ids_map("crm.team"),
        "tag": ids_map("crm.tag"),
        "lost": ids_map("crm.lost.reason"),
        "medium": ids_map("utm.medium"),
        "source": ids_map("utm.source"),
        "campaign": ids_map("utm.campaign"),
        "activity_type": ids_map("mail.activity.type"),
    }
    d["stage_name"] = {r["name"]: r["id"] for r in
                       o18.kw("crm.stage", "search_read", [[], ["id", "name"]], context=CTX18,
                              limit=200)}
    d["team_name"] = {r["name"]: r["id"] for r in
                      o18.kw("crm.team", "search_read", [[], ["id", "name"]], context=ctx,
                             limit=200)}
    d["tag_name"] = {}
    for r in o18.kw("crm.tag", "search_read", [[], ["id", "name"]], context=CTX18, limit=2000):
        d["tag_name"].setdefault(r["name"], []).append(r["id"])
    d["lost_name"] = {}
    for r in o18.kw("crm.lost.reason", "search_read", [[], ["id", "name"]], context=ctx,
                    limit=200):
        d["lost_name"].setdefault(r["name"], []).append(r["id"])
    d["medium_name"] = {r["name"]: r["id"] for r in
                        o18.kw("utm.medium", "search_read", [[], ["id", "name"]], context=ctx,
                               limit=200)}
    d["activity_type_name"] = {}
    for r in o18.kw("mail.activity.type", "search_read", [[], ["id", "name"]], context=ctx,
                    limit=300):
        d["activity_type_name"].setdefault(r["name"], []).append(r["id"])
    d["partner"] = ids_map("res.partner", limit=30000)
    d["state_name"] = {r["name"]: r["id"] for r in
                       o18.kw("res.country.state", "search_read",
                              [[("country_id.code", "=", "AT")], ["id", "name"]],
                              context=CTX18, limit=100)}
    d["title_name"] = {r["name"]: r["id"] for r in
                       o18.kw("res.partner.title", "search_read", [[], ["id", "name"]],
                              context=CTX18, limit=200)}
    d["country_code"] = {(r.get("code") or "").upper(): r["id"] for r in
                         o18.kw("res.country", "search_read", [[], ["id", "code"]],
                                context=CTX18, limit=300)}
    d["user_login"] = {}
    d["user_name"] = {}
    d["user_liste"] = o18.kw("res.users", "search_read", [[], ["id", "login", "name", "active"]],
                             context=ctx, limit=500)
    for u in d["user_liste"]:
        if u.get("login"):
            d["user_login"].setdefault(u["login"].lower(), u["id"])
        if u.get("name"):
            d["user_name"].setdefault(u["name"], u["id"])
    d["company_name"] = {r["name"]: r["id"] for r in
                         o18.kw("res.company", "search_read", [[], ["id", "name"]],
                                context=CTX18, limit=50)}
    return d


def _chatter_migrieren(o11, ziel, z, stat, fehler, schreiben):
    """Uebertraegt fachliche Chatter-Nachrichten (nur solche mit Text).

    Reine Systemmeldungen ohne Text (Stufenwechsel, "Interessent wurde erstellt",
    "Chance gewonnen") werden nicht uebertragen - sie tragen keinen fachlichen
    Inhalt und wuerden in Odoo 18 als leere Nachrichten erscheinen.
    """
    felder = ["id", "res_id", "body", "author_id", "email_from", "date", "message_type",
              "subtype_id", "is_internal", "subject"]
    msgs = o11.kw("mail.message", "search_read", [[("model", "=", "crm.lead")], felder],
                  context=CTX11, limit=10000)
    vorhanden = set()
    rows = ziel.kw("mail.message", "search_read",
                   [[["itk_o11_msg_id", "!=", False]], ["itk_o11_msg_id"]],
                   context={"lang": "de_DE", "active_test": False}, limit=30000)
    vorhanden = {r["itk_o11_msg_id"] for r in rows}
    st18 = {}
    for s in ziel.kw("mail.message.subtype", "search_read", [[], ["id", "name"]],
                     context=CTX18, limit=300):
        st18.setdefault(s["name"], s["id"])
    stat["chatter_gelesen"] = len(msgs)
    for m in msgs:
        if not (m.get("body") or "").strip():
            stat["chatter_system_ausgelassen"] += 1
            continue
        if m["id"] in vorhanden:
            stat["chatter_vorhanden"] += 1
            continue
        zid = z["lead"].get(m["res_id"])
        if not zid:
            stat["chatter_ohne_vorgang"] += 1
            continue
        if not schreiben:
            stat["chatter_geplant"] += 1
            continue
        vals = {
            "model": "crm.lead", "res_id": zid, "body": m["body"],
            "message_type": m["message_type"] or "comment",
            "email_from": m["email_from"] or False,
            "date": m["date"], "subject": m["subject"] or False,
            "is_internal": m.get("is_internal") or False,
            "itk_o11_msg_id": m["id"],
        }
        zp = z["partner"].get(m2o(m.get("author_id")))
        if zp:
            vals["author_id"] = zp
        sub = m["subtype_id"][1] if m["subtype_id"] else None
        if sub and st18.get(sub):
            vals["subtype_id"] = st18[sub]
        try:
            ziel.kw("mail.message", "create", [vals])
            stat["chatter_angelegt"] += 1
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"o11_id": "msg %s" % m["id"], "fehler": str(exc)[:200]})


def _anhaenge_migrieren(o11, ziel, z, stat, fehler, schreiben):
    """Uebertraegt die Anhaenge der CRM-Vorgaenge (fachliche Dokumente)."""
    atts = o11.kw("ir.attachment", "search_read",
                  [[("res_model", "=", "crm.lead")],
                   ["id", "name", "file_size", "mimetype", "res_id"]],
                  context=CTX11, limit=1000)
    rows = ziel.kw("ir.attachment", "search_read",
                   [[["itk_o11_att_id", "!=", False]], ["itk_o11_att_id"]],
                   context={"lang": "de_DE", "active_test": False}, limit=5000)
    vorhanden = {r["itk_o11_att_id"] for r in rows}
    stat["anhaenge_gelesen"] = len(atts)
    for a in atts:
        if a["id"] in vorhanden:
            stat["anhaenge_vorhanden"] += 1
            continue
        zid = z["lead"].get(a["res_id"])
        if not zid:
            stat["anhaenge_ohne_vorgang"] += 1
            continue
        if not schreiben:
            stat["anhaenge_geplant"] += 1
            continue
        try:
            daten = o11.kw("ir.attachment", "read", [[a["id"]], ["datas"]],
                           context=CTX11)[0]["datas"]
            ziel.kw("ir.attachment", "create", [{
                "name": a["name"], "datas": daten, "mimetype": a["mimetype"],
                "res_model": "crm.lead", "res_id": zid, "itk_o11_att_id": a["id"],
            }])
            stat["anhaenge_angelegt"] += 1
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"o11_id": "anhang %s" % a["id"], "fehler": str(exc)[:200]})


def _anlegen(ziel, posten, z, stat, fehler, mapping, batch):
    """Legt vorgemerkte Vorgaenge gebuendelt an (create_multi je Batch).

    Ein Batch kostet einen RPC-Aufruf; Einzelanlagen ueber VPN waeren rund 20-mal
    langsamer. Scheitert ein Batch, werden seine Datensaetze einzeln wiederholt,
    damit ein einzelner Fehler nicht 50 Vorgaenge mitreisst.
    """
    for i in range(0, len(posten), batch):
        teil = posten[i:i + batch]
        try:
            ids = ziel.kw("crm.lead", "create", [[v for _, v in teil]])
            if not isinstance(ids, list):
                ids = [ids]
            if len(ids) != len(teil):
                raise RuntimeError("Batch lieferte %d IDs fuer %d Datensaetze" % (len(ids), len(teil)))
        except Exception:  # noqa: BLE001
            ids = []
            for r, v in teil:
                try:
                    erg = ziel.kw("crm.lead", "create", [v])
                    ids.append(erg[0] if isinstance(erg, list) else erg)
                except Exception as exc:  # noqa: BLE001
                    stat["fehler"] += 1
                    fehler.append({"o11_id": r["id"], "fehler": str(exc)[:200]})
                    ids.append(None)
        for (r, v), nid in zip(teil, ids):
            if not nid:
                continue
            z["lead"][r["id"]] = nid
            stat["angelegt"] += 1
            mapping["vorgaenge"].append({"o11_id": r["id"], "o18_id": nid,
                                         "typ": v["type"], "status": "angelegt",
                                         "aktiv": r["active"]})


def _zeitstempel_nachziehen(ziel, o11_leads, uid_map, stat, fehler, block=300):
    """Setzt create_date/write_date auf den Odoo-11-Stand (technischer Importweg).

    Odoo 18 entfernt die Log-Access-Spalten in `_sanitize_vals`; weder create()
    noch write() koennen sie setzen. Eine temporaere Server-Action fuehrt deshalb
    ein gezieltes UPDATE je Datensatz aus. Es werden nur Abweichungen geschrieben,
    der Schritt ist damit idempotent.
    """
    soll = {r["id"]: r for r in o11_leads}
    ids = ziel.kw("crm.lead", "search_read", [[["itk_o11_id", "!=", False]],
                                              ["id", "itk_o11_id", "create_date", "write_date",
                                               "date_open", "create_uid", "write_uid"]],
                  context={"lang": "de_DE", "active_test": False}, limit=30000)
    zu_fix = []
    for r in ids:
        q = soll.get(r["itk_o11_id"])
        if not q:
            continue
        erwartet = (q["create_date"], q["write_date"], q["date_open"],
                    uid_map.get(m2o(q["create_uid"])), uid_map.get(m2o(q["write_uid"])))
        ist = ((r["create_date"] or "")[:19], (r["write_date"] or "")[:19],
               (r["date_open"] or "")[:19],
               (r["create_uid"][0] if r["create_uid"] else None),
               (r["write_uid"][0] if r["write_uid"] else None))
        soll_werte = ((erwartet[0] or "")[:19], (erwartet[1] or "")[:19],
                      (erwartet[2] or "")[:19], erwartet[3], erwartet[4])
        if ist != soll_werte:
            zu_fix.append([r["itk_o11_id"], erwartet[0] or None, erwartet[1] or None,
                           erwartet[2] or None, erwartet[3], erwartet[4]])
    print("  Zeitstempel: %d von %d Vorgaengen weichen ab" % (len(zu_fix), len(ids)), flush=True)
    if not zu_fix:
        return 0

    geschrieben = 0
    for i in range(0, len(zu_fix), block):
        teil = zu_fix[i:i + block]
        try:
            anzahl = ziel.kw("itk.migration.zeitstempel", "setze_zeitstempel",
                             ["crm.lead", teil], context={"lang": "de_DE"})
            geschrieben += anzahl or 0
        except Exception as exc:  # noqa: BLE001
            fehler.append({"o11_id": "zeitstempel", "fehler": str(exc)[:200]})
            stat["fehler"] += 1
    return geschrieben


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true",
                    help="Schreiblauf (Standard ist Trockenlauf)")
    ap.add_argument("--ich-habe-freigabe", action="store_true",
                    help="Bestaetigt die Freigabe durch Anna Maierhofer")
    ap.add_argument("--grenze", type=int, default=0, help="nur die ersten N Vorgaenge")
    ap.add_argument("--mapping", help="Pfad fuer den Mapping-Export (ausserhalb des Repos)")
    ap.add_argument("--stammdaten", default="ja", choices=["ja", "nein"],
                    help="Stammdaten (Stufen, Teams, Tags, Gruende) mitpflegen")
    ap.add_argument("--chatter", default="ja", choices=["ja", "nein"],
                    help="fachliche Chatter-Nachrichten uebertragen (Standard ja)")
    ap.add_argument("--anhaenge", default="ja", choices=["ja", "nein"],
                    help="Anhaenge uebertragen (Standard ja)")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== CRM-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    q = o11_laden(o11)
    print("Odoo 11 gelesen: %d Vorgaenge, %d Stufen, %d Teams, %d Stichwoerter, %d Gruende, "
          "%d Aktivitaeten" % (len(q["leads"]), len(q["stages"]), len(q["teams"]),
                               len(q["tags"]), len(q["lost"]), len(q["activities"])))
    z = ziel_laden(ziel)
    # Erlaubte Auswahlwerte der ITK-Felder: Odoo 11 enthaelt Altwerte, die in der
    # Auswahl nicht mehr definiert sind (z. B. x_Lead_Quelle 'web_iinform').
    f18 = ziel.kw("crm.lead", "fields_get", [[], ["selection"]], context=CTX18)
    erlaubt = {}
    for feld in ("x_Anrede_Lead", "x_Lead_Quelle", "x_Produktinteresse", "x_lead_status"):
        erlaubt[feld] = {wert for wert, _ in (f18.get(feld, {}).get("selection") or [])}
    lead_model_ids = ziel.kw("ir.model", "search", [[("model", "=", "crm.lead")]],
                             context=CTX18, limit=1)
    lead_model_id = lead_model_ids[0] if lead_model_ids else None

    stat = Counter()
    fehler = []
    sonderfaelle = []
    mapping = {"stammdaten": [], "vorgaenge": []}
    gelesen = len(q["leads"])

    # ---------------------------------------------------------------- Stammdaten
    if args.stammdaten == "ja":
        # Stufen: Odoo 18 fuehrt bereits die neun Stufen mit den Odoo-11-Namen.
        for s in q["stages"]:
            zid = z["stage"].get(s["id"]) or z["stage_name"].get(s["name"])
            if zid:
                stat["stufe_erkannt"] += 1
                mapping["stammdaten"].append({"art": "crm.stage", "o11_id": s["id"], "o18_id": zid})
                if args.ausfuehren and not z["stage"].get(s["id"]):
                    ziel.kw("crm.stage", "write", [[zid], {"itk_o11_id": s["id"]}])
            else:
                stat["stufe_fehlend"] += 1
                sonderfaelle.append({"art": "crm.stage", "o11_id": s["id"], "grund": "Stufe fehlt"})

        # Teams: "Suche / Liste" und "Webseite" legt das Modul-Setup an (itk_crm 18.0.1.6.0).
        for t in q["teams"]:
            zid = z["team"].get(t["id"]) or z["team_name"].get(t["name"])
            if zid:
                stat["team_erkannt"] += 1
                mapping["stammdaten"].append({"art": "crm.team", "o11_id": t["id"], "o18_id": zid})
                if args.ausfuehren and not z["team"].get(t["id"]):
                    ziel.kw("crm.team", "write", [[zid], {"itk_o11_id": t["id"]}])
            else:
                stat["team_fehlend"] += 1
                sonderfaelle.append({"art": "crm.team", "o11_id": t["id"], "grund": "Team fehlt"})

        # Stichwoerter: Zuordnung ausschliesslich ueber den Namen (Entscheidung Anna,
        # Session 89/R6). Gleichnamige Ziele gelten als Konflikt, es wird nichts angelegt.
        for t in q["tags"]:
            zid = z["tag"].get(t["id"])
            if not zid:
                treffer = z["tag_name"].get(t["name"], [])
                if len(treffer) == 1:
                    zid = treffer[0]
                elif len(treffer) > 1:
                    stat["tag_konflikt"] += 1
                    sonderfaelle.append({"art": "crm.tag", "o11_id": t["id"],
                                         "grund": "mehrere gleichnamige Ziele"})
                    continue
            if zid:
                stat["tag_erkannt"] += 1
                mapping["stammdaten"].append({"art": "crm.tag", "o11_id": t["id"], "o18_id": zid})
                if args.ausfuehren and not z["tag"].get(t["id"]):
                    ziel.kw("crm.tag", "write", [[zid], {"itk_o11_id": t["id"]}])
            elif args.ausfuehren:
                neu = ziel.kw("crm.tag", "create", [{"name": t["name"], "color": t["color"],
                                                     "itk_o11_id": t["id"]}])
                z["tag"][t["id"]] = neu
                z["tag_name"].setdefault(t["name"], []).append(neu)
                stat["tag_angelegt"] += 1
                mapping["stammdaten"].append({"art": "crm.tag", "o11_id": t["id"], "o18_id": neu})
            else:
                stat["tag_wuerde_angelegt"] += 1
                mapping["stammdaten"].append({"art": "crm.tag", "o11_id": t["id"],
                                              "o18_id": "trockenlauf"})

        for r in q["lost"]:
            zid = z["lost"].get(r["id"]) or (z["lost_name"].get(r["name"]) or [None])[0]
            if zid:
                stat["grund_erkannt"] += 1
                mapping["stammdaten"].append({"art": "crm.lost.reason", "o11_id": r["id"],
                                              "o18_id": zid})
            else:
                stat["grund_fehlend"] += 1
                sonderfaelle.append({"art": "crm.lost.reason", "o11_id": r["id"],
                                     "grund": "Ablehnungsgrund fehlt"})

        # Medien: nur die tatsaechlich verwendeten (Odoo 11 nutzt ausschliesslich "Website").
        benutzte_medien = {m2o(r["medium_id"]) for r in q["leads"] if r["medium_id"]}
        for med in q["mediums"]:
            if med["id"] not in benutzte_medien:
                continue
            zid = z["medium"].get(med["id"]) or z["medium_name"].get(med["name"])
            if zid:
                stat["medium_erkannt"] += 1
                mapping["stammdaten"].append({"art": "utm.medium", "o11_id": med["id"],
                                              "o18_id": zid})
            else:
                stat["medium_fehlend"] += 1
                sonderfaelle.append({"art": "utm.medium", "o11_id": med["id"],
                                     "grund": "Medium fehlt"})

        # Aktivitaetstypen: die fuenf ITK-Typen legt itk_crm 18.0.1.6.0 an.
        # Odoo 18 nennt den Standardtyp "To-Do", Odoo 11 "Zu erledigen".
        alias = {"Zu erledigen": "To-Do"}
        for a in q["activity_types"]:
            zid = z["activity_type"].get(a["id"])
            if not zid:
                treffer = z["activity_type_name"].get(alias.get(a["name"], a["name"]), [])
                zid = treffer[0] if len(treffer) == 1 else None
            if zid:
                stat["aktivitaetstyp_erkannt"] += 1
                mapping["stammdaten"].append({"art": "mail.activity.type", "o11_id": a["id"],
                                              "o18_id": zid})
                if args.ausfuehren and not z["activity_type"].get(a["id"]):
                    ziel.kw("mail.activity.type", "write", [[zid], {"itk_o11_id": a["id"]}])
            else:
                stat["aktivitaetstyp_fehlend"] += 1
                sonderfaelle.append({"art": "mail.activity.type", "o11_id": a["id"],
                                     "grund": "Typ fehlt"})

    # ------------------------------------------------------------ Vorgaenge
    leads = q["leads"][:args.grenze] if args.grenze else q["leads"]
    stage_map = dict(z["stage"])
    for s in q["stages"]:
        stage_map.setdefault(s["id"], z["stage_name"].get(s["name"]))
    team_map = dict(z["team"])
    for t in q["teams"]:
        team_map.setdefault(t["id"], z["team_name"].get(t["name"]))
    lost_map = dict(z["lost"])
    for r in q["lost"]:
        lost_map.setdefault(r["id"], (z["lost_name"].get(r["name"]) or [None])[0])
    medium_map = dict(z["medium"])
    for m in q["mediums"]:
        medium_map.setdefault(m["id"], z["medium_name"].get(m["name"]))
    state_map = {}
    for s in q["states"]:
        state_map[s["id"]] = z["state_name"].get(s["name"])
    land_map = {}
    for c in q["countries"]:
        zid = z["country_code"].get((c.get("code") or "").upper())
        if zid:
            land_map[c["id"]] = zid
    title_map = {}
    for t in q["titles"]:
        title_map[t["id"]] = z["title_name"].get(t["name"])

    def benutzer(uid):
        """Loest einen Odoo-11-Benutzer nach der verbindlichen Regel auf.

        Reihenfolge: explizite Regel (BENUTZER_MAPPING), Login, Anzeigename,
        historischer Benutzer (HISTORISCHE_BENUTZER). Nie ueber Datenbank-IDs.
        """
        if not uid:
            return None
        u = o11.kw("res.users", "read", [[uid], ["id", "login", "name"]], context=CTX11)
        if not u:
            return None
        u = u[0]
        login = (u.get("login") or "").lower()

        regel = BENUTZER_MAPPING.get(login)
        if regel:
            ziel_login, ziel_name = regel
            for k in z["user_liste"]:
                if (k.get("login") or "").lower() == ziel_login and k.get("name") == ziel_name:
                    stat["verkaeufer_ueber_regel"] += 1
                    return k["id"]
            for k in z["user_liste"]:
                if (k.get("login") or "").lower() == ziel_login:
                    stat["verkaeufer_ueber_regel"] += 1
                    return k["id"]
            stat["verkaeufer_regel_ohne_ziel"] += 1
            sonderfaelle.append({"art": "res.users", "o11_id": uid,
                                 "grund": "Ziel der Mappingregel fehlt (%s)" % ziel_login})

        zid = z["user_login"].get(login)
        if zid:
            stat["verkaeufer_ueber_login"] += 1
            return zid
        zid = z["user_name"].get(u.get("name"))
        if zid:
            stat["verkaeufer_ueber_name"] += 1
            return zid

        # kein Treffer: minimale historische Benutzerstruktur anlegen
        hist = HISTORISCHE_BENUTZER.get(login)
        if hist:
            anzeige, ziel_login = hist
            for k in z["user_liste"]:
                if (k.get("login") or "").lower() == ziel_login:
                    stat["verkaeufer_historisch_vorhanden"] += 1
                    return k["id"]
            if args.ausfuehren:
                try:
                    neu = ziel.kw("res.users", "create", [{
                        "name": anzeige, "login": ziel_login, "share": False,
                        "active": False,
                    }])
                    nid = neu[0] if isinstance(neu, list) else neu
                    ziel.kw("res.users", "write", [[nid], {"active": False}])
                    z["user_liste"].append({"id": nid, "login": ziel_login,
                                            "name": anzeige, "active": False})
                    z["user_login"].setdefault(ziel_login, nid)
                    z["user_name"].setdefault(anzeige, nid)
                    stat["verkaeufer_historisch_angelegt"] += 1
                    sonderfaelle.append({"art": "res.users", "o11_id": uid,
                                         "grund": "historischer Benutzer angelegt: %s" % anzeige})
                    return nid
                except Exception as exc:  # noqa: BLE001
                    fehler.append({"o11_id": "user %s" % uid, "fehler": str(exc)[:200]})
                    stat["fehler"] += 1
                    return None
            stat["verkaeufer_historisch_geplant"] += 1
            return None
        stat["verkaeufer_ohne_ziel"] += 1
        return None

    benutzer_cache = {}

    def benutzer_cached(uid):
        if not uid:
            return None
        if uid not in benutzer_cache:
            benutzer_cache[uid] = benutzer(uid)
        return benutzer_cache[uid]

    neu, aktualisiert, erkannt, uebersprungen = [], [], [], []
    ausstehend = []  # (o11-Datensatz, vals) fuer die Batch-Anlage
    for r in leads:
        stat["gelesen"] += 1
        vals = {
            "itk_o11_id": r["id"],
            "name": (r["name"] or "").strip() or False,
            "type": r["type"] or "lead",
            "priority": r["priority"] or "0",
            "probability": r["probability"] or 0.0,
            "expected_revenue": r["planned_revenue"] or 0.0,
            "partner_name": r["partner_name"] or False,
            "contact_name": r["contact_name"] or False,
            "email_from": r["email_from"] or False,
            "email_cc": r["email_cc"] or False,
            "phone": r["phone"] or False,
            "mobile": r["mobile"] or False,
            "function": r["function"] or False,
            "street": r["street"] or False,
            "street2": r["street2"] or False,
            "zip": r["zip"] or False,
            "city": r["city"] or False,
            "website": r["website"] or False,
            "referred": r["referred"] or False,
            "description": text_nach_html(r["description"]),
            "color": r["color"] or 0,
            "date_deadline": r["date_deadline"] or False,
            "date_open": r["date_open"] or False,
            "date_closed": r["date_closed"] or False,
            "date_conversion": r["date_conversion"] or False,
            "date_last_stage_update": r["date_last_stage_update"] or False,
            "active": r["active"],
        }
        for feld in ("x_Anrede_Lead", "x_Lead_Quelle", "x_Produktinteresse", "x_lead_status"):
            wert = r.get(feld) or False
            if wert and wert not in erlaubt[feld]:
                stat["auswahlwert_unbekannt"] += 1
                sonderfaelle.append({"art": "crm.lead", "o11_id": r["id"],
                                     "grund": "%s: Wert nicht in der Auswahl (%s)" % (feld, wert)})
                wert = False
            vals[feld] = wert
        # Beziehungen: nur setzen, wenn das Ziel eindeutig gemappt ist
        pid = m2o(r["partner_id"])
        if pid:
            zpid = z["partner"].get(pid)
            if zpid:
                vals["partner_id"] = zpid
            else:
                stat["partner_nicht_zugeordnet"] += 1
        sid = m2o(r["stage_id"])
        if sid and stage_map.get(sid):
            vals["stage_id"] = stage_map[sid]
        elif sid:
            stat["stufe_nicht_zugeordnet"] += 1
        tid = m2o(r["team_id"])
        if tid and team_map.get(tid):
            vals["team_id"] = team_map[tid]
        elif tid:
            stat["team_nicht_zugeordnet"] += 1
        uid = m2o(r["user_id"])
        if uid:
            zui = benutzer_cached(uid)
            if zui:
                vals["user_id"] = zui
            else:
                stat["verkaeufer_nicht_zugeordnet"] += 1
                sonderfaelle.append({"art": "crm.lead", "o11_id": r["id"],
                                     "grund": "Verkäufer fehlt in Odoo 18 (user %s)" % uid})
                # ausdruecklich leer: sonst setzt Odoo 18 den anlegenden Benutzer ein
                vals["user_id"] = False
        else:
            vals["user_id"] = False
        lid = m2o(r["lost_reason"])
        if lid and lost_map.get(lid):
            vals["lost_reason_id"] = lost_map[lid]
        mid = m2o(r["medium_id"])
        if mid and medium_map.get(mid):
            vals["medium_id"] = medium_map[mid]
        stid = m2o(r["state_id"])
        if stid:
            if state_map.get(stid):
                vals["state_id"] = state_map[stid]
            else:
                stat["bundesland_nicht_zugeordnet"] += 1
        coid = m2o(r["country_id"])
        if coid and land_map.get(coid):
            vals["country_id"] = land_map[coid]
        elif coid:
            stat["land_nicht_zugeordnet"] += 1
        ttid = m2o(r["title"])
        if ttid and title_map.get(ttid):
            vals["title"] = title_map[ttid]
        tids = [z["tag"].get(t) for t in (r["tag_ids"] or [])]
        tids = [t for t in tids if t and t > 0]
        vals["tag_ids"] = [(6, 0, tids)]
        vals["create_date"] = r["create_date"]
        vals["write_date"] = r["write_date"]
        cuid = benutzer_cached(m2o(r["create_uid"]))
        if cuid:
            vals["create_uid"] = cuid
        wuid = benutzer_cached(m2o(r["write_uid"]))
        if wuid:
            vals["write_uid"] = wuid

        zid = z["lead"].get(r["id"])
        if zid:
            erkannt.append(r["id"])
            stat["erkannt"] += 1
            if args.ausfuehren:
                # Vergleichsfelder = alles, was geschrieben wird, ohne die
                # Log-Access-Spalten (die kann das ORM nicht setzen). state_id
                # und die uebrigen Beziehungen muessen mitgelesen werden, sonst
                # meldet jeder Lauf dieselbe Abweichung.
                lesen = [f for f in vals
                         if f not in ("create_date", "write_date", "create_uid", "write_uid",
                                      "itk_o11_id")]
                ist = ziel.kw("crm.lead", "read", [[zid], lesen],
                              context={"lang": "de_DE", "active_test": False})[0]
                diff = {}
                beziehungen = ("stage_id", "user_id", "team_id", "partner_id", "lost_reason_id",
                               "medium_id", "state_id", "country_id", "title")
                for feld, wert in vals.items():
                    if feld in ("create_date", "write_date", "create_uid", "write_uid",
                                "itk_o11_id"):
                        continue
                    if feld == "tag_ids":
                        if sorted(ist.get("tag_ids") or []) != sorted(wert[0][2]):
                            diff[feld] = wert
                        continue
                    if feld == "website":
                        # Odoo 18 normalisiert die Adresse beim Speichern
                        # (ergaenzt http://). Der migrierte Wert bleibt stehen;
                        # kein Nachschreiben, sonst entsteht bei jedem Lauf eine
                        # Scheinabweichung samt neuem Bearbeitungsdatum.
                        continue
                    if feld == "description":
                        # HTML wird beim Speichern normalisiert; nur leere Ziele fuellen.
                        if not (ist.get("description") or "").strip() and wert:
                            diff[feld] = wert
                        continue
                    if feld in ("phone", "mobile"):
                        # Odoo 18 normalisiert Telefonnummern (phone_validation)
                        # und ergaenzt Rufnummern aus dem Kontakt. Der migrierte
                        # Wert bleibt stehen; kein Nachschreiben (sonst Schaukeln).
                        continue
                    if feld == "email_from":
                        # Odoo 18 leitet email_from bei gesetztem Kontakt neu ab
                        # (precompute). Nur leere Ziele fuellen, sonst schaukelt
                        # sich der Wert bei jedem Lauf hoch.
                        if not (ist.get("email_from") or "").strip() and wert:
                            diff[feld] = wert
                        continue
                    if feld in beziehungen:
                        # False und None sind derselbe Zustand "leer".
                        if (m2o(ist.get(feld)) or False) != (wert or False):
                            diff[feld] = wert
                        continue
                    if feld not in ist:
                        continue
                    soll = ist.get(feld)
                    if isinstance(soll, float) and isinstance(wert, float):
                        if abs(soll - wert) > 1e-4:
                            diff[feld] = wert
                    elif soll != wert and not (soll in (False, None, "") and wert in (False, None, "")):
                        diff[feld] = wert
                if diff:
                    for feld in diff:
                        stat["diff_" + feld] += 1
                    ziel.kw("crm.lead", "write", [[zid], diff])
                    stat["aktualisiert"] += 1
                else:
                    stat["uebersprungen"] += 1
            else:
                stat["uebersprungen"] += 1
            mapping["vorgaenge"].append({"o11_id": r["id"], "o18_id": zid, "typ": vals["type"],
                                         "status": "vorhanden", "aktiv": r["active"]})
            continue

        # Neuanlage: nur vormerken, die Anlage laeuft gebuendelt nach der Schleife
        stat["neu_geplant"] += 1
        if not r["active"]:
            stat["archiviert"] += 1
        if args.ausfuehren:
            ausstehend.append((r, vals))
            if len(ausstehend) >= BATCH:
                _anlegen(ziel, ausstehend, z, stat, fehler, mapping, BATCH)
                ausstehend = []
                print("  ... %d angelegt" % stat["angelegt"], flush=True)
        else:
            neu.append(r["id"])
            mapping["vorgaenge"].append({"o11_id": r["id"], "o18_id": "trockenlauf",
                                         "typ": vals["type"], "status": "würde angelegt",
                                         "aktiv": r["active"]})

    if args.ausfuehren and ausstehend:
        _anlegen(ziel, ausstehend, z, stat, fehler, mapping, BATCH)
        ausstehend = []

    # ------------------------------------------------- Erstell-/Bearbeitungsdatum
    # Odoo 18 verwirft create_date/write_date im ORM (_sanitize_vals entfernt
    # LOG_ACCESS_COLUMNS). Der echte Odoo-11-Stand wird deshalb ueber eine
    # temporaere Server-Action per SQL nachgezogen - technischer Importweg,
    # gleichermassen lokal und auf der VM, ohne DB-Zugangsdaten im Skript.
    if args.ausfuehren:
        uid_map = {u: benutzer_cached(u) for u in
                   {m2o(r["create_uid"]) for r in leads} | {m2o(r["write_uid"]) for r in leads}
                   if u}
        stat["zeitstempel_korrigiert"] = _zeitstempel_nachziehen(
            ziel, o11_leads=leads, uid_map=uid_map, stat=stat, fehler=fehler)

    # ------------------------------------------------------------ Aktivitaeten
    akt_neu = 0
    if args.ausfuehren:
        atype_map = dict(z["activity_type"])
        for a in q["activity_types"]:
            treffer = z["activity_type_name"].get({"Zu erledigen": "To-Do"}.get(a["name"], a["name"]), [])
            atype_map.setdefault(a["id"], treffer[0] if len(treffer) == 1 else None)
        # Idempotenz ueber den technischen Anker itk_o11_activity_id (die
        # Kombination Typ/Benutzer/Frist/Text ist nicht eindeutig: Odoo 18
        # speichert Summary und Notiz anders ab, dadurch wurden Aktivitaeten
        # bei jedem Lauf erneut angelegt).
        rows = ziel.kw("mail.activity", "search_read",
                       [[["itk_o11_activity_id", "!=", False]], ["itk_o11_activity_id"]],
                       context={"lang": "de_DE", "active_test": False}, limit=5000)
        vorhandene_akt = {r["itk_o11_activity_id"] for r in rows}
        for a in q["activities"]:
            lid = a["res_id"]
            zid = z["lead"].get(lid)
            if not zid:
                stat["aktivitaet_ohne_vorgang"] += 1
                continue
            if a["id"] in vorhandene_akt:
                stat["aktivitaet_vorhanden"] += 1
                continue
            typ = atype_map.get(m2o(a["activity_type_id"]))
            zui = benutzer_cached(m2o(a["user_id"]))
            if not typ:
                stat["aktivitaet_nicht_zugeordnet"] += 1
                continue
            try:
                ziel.kw("mail.activity", "create", [{
                    "res_model": "crm.lead", "res_model_id": lead_model_id,
                    "res_id": zid, "activity_type_id": typ,
                    "user_id": zui or z["user_name"].get("Administrator"),
                    "date_deadline": a["date_deadline"], "summary": a["summary"] or False,
                    "note": a["note"] or False,
                    "itk_o11_activity_id": a["id"],
                }])
            except Exception as exc:  # noqa: BLE001
                stat["fehler"] += 1
                fehler.append({"o11_id": "activity %s" % a["id"], "fehler": str(exc)[:200]})
                continue
            vorhandene_akt.add(a["id"])
            akt_neu += 1
            stat["aktivitaet_angelegt"] += 1

    # ------------------------------------------------------------ Chatter
    if args.chatter == "ja":
        _chatter_migrieren(o11, ziel, z, stat, fehler, args.ausfuehren)

    # ------------------------------------------------------------ Anhaenge
    if args.anhaenge == "ja":
        _anhaenge_migrieren(o11, ziel, z, stat, fehler, args.ausfuehren)

    # ------------------------------------------------------------ Abschluss
    if args.mapping:
        with open(args.mapping, "w", encoding="utf-8") as fh:
            json.dump(mapping, fh, ensure_ascii=False, indent=1)
        print("Mapping geschrieben: %s (%d Stammdaten, %d Vorgaenge)" % (
            args.mapping, len(mapping["stammdaten"]), len(mapping["vorgaenge"])))

    # Dublettenpruefung: je Odoo-11-ID darf es genau einen Zielsatz geben
    doppelt = 0
    if args.ausfuehren:
        rows = ziel.kw("crm.lead", "search_read", [[["itk_o11_id", "!=", False]],
                                                    ["id", "itk_o11_id"]],
                       context={"lang": "de_DE", "active_test": False}, limit=30000)
        zaehler = Counter(r["itk_o11_id"] for r in rows)
        doppelt = sum(v - 1 for v in zaehler.values() if v > 1)

    print()
    print("--- Zusammenfassung (%s) ---" % ("SCHREIBEN" if args.ausfuehren else "TROCKENLAUF"))
    print("gelesen ..................... %d" % gelesen)
    print("erkannt (bereits vorhanden) . %d" % stat["erkannt"])
    print("angelegt .................... %d" % stat["angelegt"])
    print("aktualisiert ................ %d" % stat["aktualisiert"])
    print("uebersprungen ............... %d" % stat["uebersprungen"])
    print("archiviert uebernommen ...... %d" % stat["archiviert"])
    print("nicht zuordenbar (Vorgaenge)  %d" % (
        stat["partner_nicht_zugeordnet"] + stat["stufe_nicht_zugeordnet"] +
        stat["team_nicht_zugeordnet"] + stat["verkaeufer_nicht_zugeordnet"] +
        stat["bundesland_nicht_zugeordnet"]))
    print("   davon Verkaeufer fehlt ... %d" % stat["verkaeufer_nicht_zugeordnet"])
    print("   davon Partner fehlt ...... %d" % stat["partner_nicht_zugeordnet"])
    print("   davon Stufe fehlt ........ %d" % stat["stufe_nicht_zugeordnet"])
    print("   davon Team fehlt ......... %d" % stat["team_nicht_zugeordnet"])
    print("Fehler ...................... %d" % stat["fehler"])
    print("Dubletten ................... %d" % doppelt)
    print("Aktivitaeten angelegt ....... %d" % akt_neu)
    print("Zeitstempel nachgezogen ..... %d" % stat.get("zeitstempel_korrigiert", 0))
    print("Verkaeufer: ueber Regel %d, Login %d, Name %d, historisch angelegt %d, "
          "ohne Ziel %d" % (stat["verkaeufer_ueber_regel"], stat["verkaeufer_ueber_login"],
                            stat["verkaeufer_ueber_name"], stat["verkaeufer_historisch_angelegt"],
                            stat["verkaeufer_ohne_ziel"]))
    print("Chatter: gelesen %d, Systemnachricht ausgelassen %d, angelegt %d, vorhanden %d, "
          "ohne Vorgang %d" % (stat["chatter_gelesen"], stat["chatter_system_ausgelassen"],
                               stat["chatter_angelegt"], stat["chatter_vorhanden"],
                               stat["chatter_ohne_vorgang"]))
    print("Anhaenge: gelesen %d, angelegt %d, vorhanden %d, ohne Vorgang %d"
          % (stat["anhaenge_gelesen"], stat["anhaenge_angelegt"], stat["anhaenge_vorhanden"],
             stat["anhaenge_ohne_vorgang"]))
    print("Stammdaten: Stufen %d erkannt / %d fehlend, Teams %d / %d, Stichwoerter %d erkannt, "
          "%d angelegt, %d Konflikt, Gruende %d / %d, Medien %d / %d, Aktivitaetstypen %d / %d" % (
              stat["stufe_erkannt"], stat["stufe_fehlend"], stat["team_erkannt"],
              stat["team_fehlend"], stat["tag_erkannt"], stat["tag_angelegt"],
              stat["tag_konflikt"], stat["grund_erkannt"], stat["grund_fehlend"],
              stat["medium_erkannt"], stat["medium_fehlend"],
              stat["aktivitaetstyp_erkannt"], stat["aktivitaetstyp_fehlend"]))
    abweichende = {k: v for k, v in stat.items() if k.startswith("diff_")}
    if abweichende:
        print("Abweichende Felder bei der Aktualisierung: %s" %
              ", ".join("%s=%d" % (k[5:], v) for k, v in sorted(abweichende.items())))
    if not args.ausfuehren:
        print("Wuerde anlegen: %d Vorgaenge (Trockenlauf, nichts geschrieben)" % len(neu))
    if fehler:
        print("Fehlerdetails (max 10):")
        for f in fehler[:10]:
            print("  o11 %s: %s" % (f["o11_id"], f["fehler"]))
    if sonderfaelle:
        print("Sonderfaelle: %d (Details in der Mapping-Datei/Doku)" % len(sonderfaelle))
    return 0 if stat["fehler"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
