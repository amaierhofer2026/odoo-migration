"""Produktivstart-Konfiguration Helpdesk (Odoo 18) - Werte aus Odoo 11.

Legt an bzw. richtet ein, was in docs/o11-o18-helpdesk-produktivstart.md
dokumentiert und von Anna freigegeben wurde:
  - Team "IT-Kommunal Support" (SLA aktiv, im Portal sichtbar, E-Mail-Alias)
  - SLA "Standard SLA Support ITK Produkte" (48 h, 4 Odoo-11-Kategorien,
    Zielstufe Geschlossen/Behoben, on Hold pausiert die Zeit)
  - Test-SLA (Testdatensatz) entfernen
  - Prioritaeten, Kategorien, Unterkategorien gegen Odoo 11 pruefen
  - Team fuer das oeffentliche Formular setzen
Keine Ticketdaten, keine Odoo-11-Tickets.

Aufruf: python scripts/helpdesk_produktivstart.py [--instanz lokal|vm] [--pruefen]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
from _o11o18_client import o18  # noqa: E402

# Odoo-11-Bezeichnungen (read-only erhoben)
TEAM_NAME = "IT-Kommunal Support"
SLA_NAME = "Standard SLA Support ITK Produkte"
SLA_KATEGORIEN = [
    "amtsweg.gv.at (Formulare & Postfächer)",
    "Amtssignatur (Sendhybrid Client)",
    "E-Learning (Städtebund Academy)",
    "Verwaltungsmanager (MAYAN EDMS)",
]
PRIORITAETEN = [
    ("Niedrig", "#ffff00"),
    ("Mittel", "#ffbf00"),
    ("Hoch", "#ff0000"),
    ("Angebotsanforderung", "#58acfa"),
]
KATEGORIEN = [
    "Acta Nova",
    "Amtssignatur (Sendhybrid Client)",
    "amtsweg.gv.at (Formulare & Postfächer)",
    "Anonymisierungsportal",
    "Communex (vormals Intrakommuna)",
    "E-Learning (Städtebund Academy)",
    "Gemeindecloud/Verwaltungscloud",
    "Gemeindeverordnungen Kärnten & amtstafel.at",
    "Hinweisportal",
    "IFG-Portal",
    "IFG-Verfahren",
    "Kommunaler KI-Assistent",
    "opendesk",
    "Public Management Expert*Innen-Netzwerk",
    "Sonstiges",
    "Vertragsmanagement",
    "Verwaltungsmanager (MAYAN EDMS)",
]
UNTERKATEGORIEN = [
    "Allgemeine Anfrage (Support)",
    "Störung/Fehler melden",
    "Angebot anfordern",
    "Individuelle Formularerstellung und Deployment",
    "Als Administrator anmelden",
    "Verordnung löschen",
    "allgemeiner Support",
    "Zugangsdaten vergessen",
]


def suche(c, modell, domain, limit=0, fields=None):
    return c.kw(modell, "search_read", [domain], fields=fields or [], limit=limit)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", default="lokal")
    p.add_argument("--pruefen", action="store_true", help="nur pruefen, nichts schreiben")
    a = p.parse_args()
    c = o18(a.instanz)
    bericht = []

    def melde(text):
        print(text)
        bericht.append(text)

    # ---------- 0. Bestand vorher ----------
    vor_tickets = c.kw("helpdesk.ticket", "search_count", [[]])
    vor_sla = c.kw("helpdesk.sla", "search_count", [[]])
    melde("Bestand vorher: Tickets %d, SLA-Datensaetze %d" % (vor_tickets, vor_sla))

    # ---------- 1. Kanaele pruefen ----------
    kanaele = suche(c, "helpdesk.ticket.channel", [], fields=["id", "name", "active"])
    namen = sorted(k["name"] for k in kanaele)
    melde("Kanaele: %s" % ", ".join(namen))
    email_kanal = next((k["id"] for k in kanaele if k["name"] == "Email"), False)
    if not email_kanal:
        melde("  WARNUNG: Kanal 'Email' fehlt")

    # ---------- 2. Team ----------
    teams = suche(c, "helpdesk.ticket.team", [],
                  fields=["id", "name", "use_sla", "show_in_portal", "alias_id", "alias_name"])
    team = teams[0] if teams else None
    if not team:
        melde("FEHLER: kein Helpdesk-Team vorhanden")
        return
    melde("Team vorher: %s (SLA %s, Portal %s, Alias %s)" % (
        team["name"], team["use_sla"], team["show_in_portal"], team["alias_name"]))
    if not a.pruefen:
        # Alias 'help' ist der vorhandene, vorgesehene Alias (vom Modul angelegt).
        alias = suche(c, "mail.alias", [["alias_name", "=", "help"]], limit=1,
                      fields=["id", "alias_name", "alias_defaults", "alias_contact"])
        daten = {"name": TEAM_NAME, "use_sla": True, "show_in_portal": True}
        if alias:
            daten["alias_id"] = alias[0]["id"]
            daten["alias_name"] = alias[0]["alias_name"]
        c.kw("helpdesk.ticket.team", "write", [[team["id"]], daten])
        if alias:
            vorgaben = {"team_id": team["id"]}
            if email_kanal:
                vorgaben["channel_id"] = email_kanal
            c.kw("mail.alias", "write", [[alias[0]["id"]], {"alias_defaults": str(vorgaben),
                                                            "alias_contact": "everyone"}])
    team_neu = suche(c, "helpdesk.ticket.team", [["id", "=", team["id"]]],
                     fields=["name", "use_sla", "show_in_portal", "alias_name", "alias_id"])[0]
    melde("Team nachher: %s (SLA %s, Portal %s, Alias %s)" % (
        team_neu["name"], team_neu["use_sla"], team_neu["show_in_portal"], team_neu["alias_name"]))

    # ---------- 3. Stufen ----------
    stufen = suche(c, "helpdesk.ticket.stage", [], fields=["id", "name", "sequence", "fold", "active"])
    stufen.sort(key=lambda s: s["id"])
    melde("Stufen: %s" % " | ".join("%s(%s)" % (s["name"], s["id"]) for s in stufen))
    offen = next((s for s in stufen if s["name"] == "Geschlossen/Behoben"), None)
    hold = next((s for s in stufen if s["name"].lower() == "on hold"), None)
    if not offen or not hold:
        melde("FEHLER: Stufe 'Geschlossen/Behoben' oder 'on Hold' fehlt")
        return

    # ---------- 4. SLA ----------
    sla_alt = suche(c, "helpdesk.sla", [], fields=["id", "name", "hours", "days", "team_ids",
                                                   "category_ids", "stage_id", "ignore_stage_ids"])
    for s in sla_alt:
        melde("SLA vorhanden: %s (%s h, Zielstufe %s)" % (s["name"], s["hours"], s["stage_id"]))
    kat_ids = [k["id"] for k in suche(c, "helpdesk.ticket.category", [["name", "in", SLA_KATEGORIEN]],
                                      fields=["id", "name"])]
    fehlend = [n for n in SLA_KATEGORIEN
               if n not in [k["name"] for k in suche(c, "helpdesk.ticket.category",
                                                     [["name", "in", SLA_KATEGORIEN]], fields=["name"])]]
    if fehlend:
        melde("  WARNUNG: Kategorien fehlen, SLA wird ohne sie angelegt: %s" % fehlend)
    if not a.pruefen:
        for s in sla_alt:
            if s["name"] != SLA_NAME:
                c.kw("helpdesk.sla", "unlink", [[s["id"]]])
                melde("  Test-SLA entfernt: %s" % s["name"])
        daten = {
            "name": SLA_NAME,
            "team_ids": [(6, 0, [team["id"]])],
            "category_ids": [(6, 0, kat_ids)],
            "stage_id": offen["id"],
            "ignore_stage_ids": [(6, 0, [hold["id"]])],
            "hours": 48,
            "days": 0,
        }
        neu = suche(c, "helpdesk.sla", [["name", "=", SLA_NAME]], limit=1, fields=["id"])
        if neu:
            c.kw("helpdesk.sla", "write", [[neu[0]["id"]], daten])
            melde("  SLA aktualisiert: %s" % SLA_NAME)
        else:
            c.kw("helpdesk.sla", "create", [daten])
            melde("  SLA angelegt: %s" % SLA_NAME)
    sla = suche(c, "helpdesk.sla", [], fields=["name", "hours", "days", "team_ids", "category_ids",
                                               "stage_id", "ignore_stage_ids"])
    for s in sla:
        melde("SLA jetzt: %s | %.0f h | Kategorien %s | Zielstufe %s | pausiert bei %s" % (
            s["name"], s["hours"], s["category_ids"], s["stage_id"], s["ignore_stage_ids"]))

    # ---------- 5. Prioritaeten ----------
    prio = suche(c, "itk.helpdesk.priority", [], fields=["id", "name", "color", "sequence"])
    for name, farbe in PRIORITAETEN:
        treffer = [p for p in prio if p["name"] == name]
        if not treffer:
            melde("  WARNUNG: Prioritaet fehlt: %s" % name)
        elif (treffer[0]["color"] or "").lower() != farbe.lower():
            if not a.pruefen:
                c.kw("itk.helpdesk.priority", "write", [[treffer[0]["id"]], {"color": farbe}])
            melde("  Prioritaet %s: Farbe %s -> %s" % (name, treffer[0]["color"], farbe))
    melde("Prioritaeten: %s" % " | ".join("%s=%s" % (p["name"], p["color"])
                                          for p in suche(c, "itk.helpdesk.priority", [],
                                                         fields=["name", "color"])))

    # ---------- 6. Kategorien und Unterkategorien ----------
    kat = [k["name"] for k in suche(c, "helpdesk.ticket.category", [["parent_id", "=", False]],
                                    fields=["name"])]
    unter = [k["name"] for k in suche(c, "helpdesk.ticket.category", [["parent_id", "!=", False]],
                                      fields=["name"])]
    melde("Kategorien: %d vorhanden, %d in Odoo 11 -> fehlend: %s" % (
        len(kat), len(KATEGORIEN), sorted(set(KATEGORIEN) - set(kat)) or "keine"))
    melde("Unterkategorien: %d / %d" % (len(unter), len(UNTERKATEGORIEN)))
    melde("Odoo-11-Hauptkategorien nicht mehr vorhanden: %s" % (
        sorted(set(kat) - set(KATEGORIEN)) or "keine"))

    # ---------- 7. Einstellungen und externe Werte ----------
    einst = suche(c, "ir.config_parameter", [["key", "like", "helpdesk"]], fields=["key", "value"])
    for e in einst:
        melde("Einstellung %s = %s" % (e["key"], e["value"]))
    for schluessel in ("mail.catchall.domain", "mail.default.from",
                       "recaptcha_public_key", "recaptcha_private_key"):
        r = suche(c, "ir.config_parameter", [["key", "=", schluessel]], limit=1, fields=["value"])
        melde("  %-24s %s" % (schluessel, (r[0]["value"] if r and r[0]["value"] else "(nicht gesetzt)")))
    melde("Bestand nachher: Tickets %d, SLA-Datensaetze %d" % (
        c.kw("helpdesk.ticket", "search_count", [[]]), c.kw("helpdesk.sla", "search_count", [[]])))


if __name__ == "__main__":
    main()
