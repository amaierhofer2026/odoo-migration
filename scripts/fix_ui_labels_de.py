#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ITK Abschnitt-1-Korrekturen (Freigabe Anna 02.09.2026, Session 81).
Setzt gezielte de_DE-Slots (Menues, Actions, Felder) per ORM-write mit lang-Context
(jsonb_set-Aequivalent) gegen die VM (https://k001959vsx.ipax.at, DB odoo18_test,
Credentials aus C:\Odoo-Test\.env ODOO18_*). Idempotent; nach jedem Restore aus einem
Backup VOR dem Fix erneut ausfuehren (bzw. beim naechsten Setup-Lauf).
Nur dokumentierte Stellen - keine globale Ersetzung.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Freigabe Anna 02.09.2026 - Gezielte de_DE-Label-Korrekturen (Menues, Actions, Felder) auf der VM.
Methode: ORM-write mit lang-Context (setzt genau einen jsonb-Slot). Referenz-Mechanik:
fehlende de_DE-Labels werden aus Pendant-Feldern (gleicher Feldname, andere Modelle) uebernommen,
wenn die en-Werte identisch sind. KEINE globale Ersetzung; nur ZIELmodelle/-menues/-actions.
Report: was geaendert / was offen (Klaerung noetig)."""
import json, os, urllib.request, http.cookiejar, sys

URL = "https://k001959vsx.ipax.at"
env = {}
for line in open(r"C:\Odoo-Test\.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
DB, LOGIN, PWD = env.get("ODOO18_DB", "odoo18_test"), env.get("ODOO18_USER", ""), env.get("ODOO18_PWD", "")
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def rpc(url, params, timeout=120):
    body = json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode())
    if "error" in resp:
        raise RuntimeError("RPC-Fehler: %s" % str(resp["error"])[:400])
    return resp.get("result")
res = rpc(URL + "/web/session/authenticate", {"db": DB, "login": LOGIN, "password": PWD})
uid = res.get("uid")
def exec_kw(model, method, args=None, kwargs=None, timeout=120):
    return rpc(URL + "/web/dataset/call_kw", {"model": model, "method": method,
               "args": args or [], "kwargs": kwargs or {}}, timeout=timeout)

LOG = []
def p(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)

# ---------------- MENUES (Ziel-de; nur wenn aktuell de == en, d.h. kein de_DE-Slot) ----------------
MENU_FIX = {  # id: (de, Klaerung? , Grund)
    736: "Alle Kunden", 737: "Aktuelle Kunden", 738: "Ehemalige Kunden", 739: "Zielkunden",
    740: "Alle Reseller", 891: "Support-Tickets", 601: "Alle Auftragszeilen",
    746: "Alle Tickets", 775: "SLA-Bericht", 757: "Zeiterfassung", 756: "Arbeit starten",
}
# Actions nach (aktueller en-Name) -> de; nur Module der Ziel-Liste (ir_model_data)
ACT_FIX = {
    "Actual customers": "Aktuelle Kunden", "All customers": "Alle Kunden",
    "Former Customers": "Ehemalige Kunden", "Target Customers": "Zielkunden",
    "All Resellers": "Alle Reseller",
    "Order Lines": "Auftragszeilen", "Support Tickets": "Support-Tickets",
    "Helpdesk Ticket": "Helpdesk-Ticket", "Helpdesk Tickets": "Helpdesk-Tickets",
    "SLA Report": "SLA-Bericht", "Start work": "Arbeit starten", "Timesheets": "Zeiterfassung",
    "Set Pricelist for Subscriptions": "Preisliste für Abonnements festlegen",
    "Update Multifactor for Subscriptionlines": "Multifaktor für Abo-Zeilen aktualisieren",
    "Update Population and Multifactor for Partners": "Einwohnerzahl und Faktor für Partner aktualisieren",
}
MODS_OF_INTEREST = ["itk_crm","itk_translation","itk_subscription","itk_product","itk_sale_management",
    "itk_valorisierung","itk_projectcategory","itk_base_setup","itk_third_party_setup","itk_reports",
    "itk_saleorder_lines","itk_multifactor","itk_automated_actions","itk_helpdesk_category_user",
    "itk_helpdesk_compat","helpdesk_mgmt","helpdesk_mgmt_project","helpdesk_mgmt_sla",
    "helpdesk_mgmt_timesheet","project_timesheet_time_control","server_action_mass_edit"]

def fix_menus():
    ids = list(MENU_FIX.keys())
    de_rows = exec_kw("ir.ui.menu", "read", [ids, ["id", "name"]], {"context": {"lang": "de_DE"}})
    en_rows = exec_kw("ir.ui.menu", "read", [ids, ["id", "name"]], {"context": {"lang": "en_US"}})
    enmap = {x["id"]: x["name"] for x in en_rows}
    for x in sorted(de_rows, key=lambda r: r["id"]):
        mid, de_now = x["id"], x["name"]
        if de_now == enmap.get(mid) and str(de_now) != str(MENU_FIX[mid]):
            exec_kw("ir.ui.menu", "write", [[mid], {"name": MENU_FIX[mid]}], {"context": {"lang": "de_DE"}})
            p("MENUE %s: %r -> %r" % (mid, de_now, MENU_FIX[mid]))
        else:
            p("MENUE %s (%r): uebersprungen (de vorhanden oder gleich)" % (mid, de_now))

def fix_actions():
    # Actions der Zielmodule mit de == en und Name in ACT_FIX
    imd = exec_kw("ir.model.data", "search_read",
                  [[["module", "in", MODS_OF_INTEREST], ["model", "=", "ir.actions.act_window"]],
                   ["res_id"]])
    aids = list({r["res_id"] for r in imd if r.get("res_id")})
    de_rows = exec_kw("ir.actions.act_window", "read", [aids, ["id", "name"]], {"context": {"lang": "de_DE"}})
    en_rows = exec_kw("ir.actions.act_window", "read", [aids, ["id", "name"]], {"context": {"lang": "en_US"}})
    enmap = {x["id"]: x["name"] for x in en_rows}
    for x in de_rows:
        nm = x["name"]
        if nm in ACT_FIX and nm == enmap.get(x["id"]):
            exec_kw("ir.actions.act_window", "write", [[x["id"]], {"name": ACT_FIX[nm]}], {"context": {"lang": "de_DE"}})
            p("ACTION %s: %r -> %r" % (x["id"], nm, ACT_FIX[nm]))

# ---------------- FELDER: Referenz-Mechanik + Sonderfaelle ----------------
# Zielmodelle je Gruppe mit Referenz-Quellmodellen (Reihenfolge = Prioritaet)
GROUPS = [
    (["sale.subscription", "sale.subscription.template", "sale.subscription.line", "sale.subscription.close.reason"],
     ["sale.order", "account.move", "product.template", "res.partner", "helpdesk.ticket"]),
    (["helpdesk.ticket", "helpdesk.ticket.stage", "helpdesk.ticket.team", "helpdesk.ticket.category",
      "helpdesk.ticket.tag", "helpdesk.ticket.channel", "helpdesk.ticket.duplicate.wizard", "helpdesk.sla",
      "helpdesk.ticket.sla", "helpdesk.ticket.timesheet", "helpdesk.stage", "helpdesk.team"],
     ["helpdesk.ticket", "res.partner", "crm.lead"]),
    (["project.project", "project.task", "project.milestone", "project.todo", "project.project.todo"],
     ["project.task", "project.project", "res.partner", "helpdesk.ticket"]),
    (["crm.lead", "crm.stage", "mail.activity", "mail.activity.type"],
     ["crm.lead", "helpdesk.ticket", "res.partner"]),
    (["account.analytic.line", "hr.timesheet.switch", "timesheets.analysis.report"],
     ["project.task", "account.move", "res.partner"]),
    (["product.template", "product.product"], ["sale.order", "product.template", "res.partner"]),
    (["account.move", "account.bank.statement.line", "sale.order", "sale.order.line"],
     ["sale.order", "account.move", "res.partner"]),
    (["res.config.settings", "res.company"], ["res.partner", "account.move"]),
    (["res.partner", "res.users"], ["res.partner", "sale.order"]),
]
ALL_TARGETS = sorted({m for g, _ in GROUPS for m in g})
print("Zielmodelle:", len(ALL_TARGETS))

# 1) Alle Feldzeilen der Zielmodelle lesen (de+en)
fld_de = exec_kw("ir.model.fields", "search_read",
                 [[["model", "in", ALL_TARGETS]], ["id", "model", "name", "field_description"]],
                 {"context": {"lang": "de_DE"}})
fld_en = exec_kw("ir.model.fields", "read", [[f["id"] for f in fld_de], ["field_description"]],
                 {"context": {"lang": "en_US"}})
enmap = {f["id"]: (f.get("field_description") or "") for f in fld_en}
rows = []
for f in fld_de:
    rows.append({"id": f["id"], "model": f["model"], "name": f["name"],
                 "de": (f.get("field_description") or ""), "en": enmap.get(f["id"], "")})
print("Feldzeilen Zielmodelle:", len(rows))

# 2) Referenz en->de je Feldname aus QUELLmodellen (nur wo de != en, d.h. echter de-Slot)
src_models = sorted({m for _, src in GROUPS for m in src})
ref = {}
q = exec_kw("ir.model.fields", "search_read",
            [[["model", "in", src_models]], ["id", "model", "name", "field_description"]],
            {"context": {"lang": "de_DE"}})
q_en = exec_kw("ir.model.fields", "read", [[f["id"] for f in q], ["field_description"]],
               {"context": {"lang": "en_US"}})
qen = {f["id"]: (f.get("field_description") or "") for f in q_en}
for f in q:
    d, e = (f.get("field_description") or ""), qen.get(f["id"], "")
    if d and d != e:
        ref.setdefault(f["name"], []).append((e, d, f["model"]))
print("Referenz-Feldnamen mit de-Slot:", len(ref))

# 3) Sonderfaelle (manuell, fachlich eindeutig) -> (model, name, de)
SPECIAL = {
    ("res.partner", "firstname"): "Vorname", ("res.partner", "lastname"): "Nachname",
    ("res.users", "firstname"): "Vorname", ("res.users", "lastname"): "Nachname",
    ("res.partner", "salutation"): "Anrede", ("res.users", "salutation"): "Anrede",
    ("res.partner", "austria_wiki_url"): "Österreich-Wiki-URL",
    ("res.users", "austria_wiki_url"): "Österreich-Wiki-URL",
    ("res.partner", "sales_as_final_customer_count"): "Anzahl Verkäufe als Endkunde",
    ("res.users", "sales_as_final_customer_count"): "Anzahl Verkäufe als Endkunde",
    ("product.template", "product_type_id"): "Produkttyp", ("product.product", "product_type_id"): "Produkttyp",
    ("product.template", "to_multiply_by_factor"): "Mit Faktor multiplizieren (pro 1.000)",
    ("product.product", "to_multiply_by_factor"): "Mit Faktor multiplizieren (pro 1.000)",
    ("product.template", "is_multi_factor_product"): "Mit Faktor multiplizieren (pro 1.000)",
    ("product.product", "is_multi_factor_product"): "Mit Faktor multiplizieren (pro 1.000)",
    ("product.template", "recurring_invoice"): "Abo-Produkt",
    ("product.product", "recurring_invoice"): "Abo-Produkt",
    ("product.template", "subscription_template_id"): "Abo-Vorlage",
    ("product.product", "subscription_template_id"): "Abo-Vorlage",
    ("sale.order", "administrative_contact_id"): "Verwaltungskontakt",
    ("sale.order", "technical_contact_id"): "Technischer Kontakt",
    ("sale.order", "sale_contact_id"): "Verkaufskontakt",
    ("sale.order", "final_customer_id"): "Endkunde",
    ("sale.order", "product_category_id"): "Produktkategorie",
    ("sale.order", "subscription_count"): "Anzahl Abonnements",
    ("sale.order", "subscription_management"): "Abo-Verwaltung",
    ("sale.order.line", "qty_multiplication_factor"): "Multiplikationsfaktor (pro 1.000)",
    ("account.move", "valorisierung_id"): "Valorisierungstext",
    ("account.bank.statement.line", "valorisierung_id"): "Valorisierungstext",
    ("account.move", "projectcategory_id"): "Projektkategorie",
    ("account.bank.statement.line", "projectcategory_id"): "Projektkategorie",
    ("helpdesk.ticket.category", "user_ids"): "Benutzer (Follower)",
    ("helpdesk.ticket", "allow_timesheet"): "Zeiterfassung erlauben",
    ("helpdesk.ticket.team", "allow_timesheet"): "Zeiterfassung erlauben",
    ("helpdesk.ticket", "planned_hours"): "Geplante Stunden",
    ("helpdesk.ticket", "remaining_hours"): "Verbleibende Stunden",
    ("helpdesk.ticket", "total_hours"): "Gesamtstunden",
    ("helpdesk.ticket", "last_timesheet_activity"): "Letzte Zeiterfassungsaktivität",
    ("helpdesk.ticket.team", "show_timesheet_portal"): "Zeiterfassung im Portal anzeigen",
    ("project.project", "ticket_count"): "Anzahl Tickets",
    ("project.project", "todo_ticket_count"): "Anzahl Tickets",
    ("project.project", "label_tickets"): "Tickets verwenden als",
    ("project.task", "ticket_count"): "Anzahl Tickets",
    ("project.task", "todo_ticket_count"): "Anzahl Tickets",
    ("project.task", "label_tickets"): "Tickets verwenden als",
    ("project.milestone", "helpdesk_ticket_count"): "Anzahl Helpdesk-Tickets",
    ("helpdesk.sla", "sla_deadline"): None,  # Platzhalter unbenutzt
    # sale.subscription / template - Kernfelder (fachlich eindeutig)
    ("sale.subscription", "date_start"): "Startdatum",
    ("sale.subscription", "date"): "Enddatum",
    ("sale.subscription", "recurring_next_date"): "Datum der nächsten Rechnung",
    ("sale.subscription", "recurring_interval"): "Wiederholen alle",
    ("sale.subscription", "recurring_rule_type"): "Wiederholung",
    ("sale.subscription", "recurring_total"): "Wiederkehrender Preis",
    ("sale.subscription", "recurring_monthly"): "Monatlicher wiederkehrender Umsatz",
    ("sale.subscription", "recurring_amount_total"): "Gesamt (wiederkehrend)",
    ("sale.subscription", "recurring_amount_tax"): "Steuern (wiederkehrend)",
    ("sale.subscription", "code"): "Referenz",
    ("sale.subscription", "end_of_contract_date"): "Vertragsenddatum",
    ("sale.subscription", "sale_order_id"): "Verkaufsauftrag",
    ("sale.subscription", "sale_order_confirmation_date"): "Datum des ersten Verkaufsauftrags",
    ("sale.subscription", "sale_order_count"): "Anzahl Verkaufsaufträge",
    ("sale.subscription", "invoice_count"): "Anzahl Rechnungen",
    ("sale.subscription", "uuid"): "Konto-UUID",
    ("sale.subscription", "website_url"): "Website-URL",
    ("sale.subscription", "payment_token_id"): "Zahlungstoken",
    ("sale.subscription", "analytic_account_id"): "Kostenstelle",
    ("sale.subscription", "company_id"): "Unternehmen",
    ("sale.subscription", "country_id"): "Land",
    ("sale.subscription", "industry_id"): "Branche",
    ("sale.subscription", "pricelist_id"): "Preisliste",
    ("sale.subscription", "currency_id"): "Währung",
    ("sale.subscription", "partner_id"): "Kunde",
    ("sale.subscription", "user_id"): "Verkäufer",
    ("sale.subscription", "display_name"): "Anzeigename",
    ("sale.subscription", "close_reason_id"): "Beendigungsgrund",
    ("sale.subscription", "template_id"): "Abo-Vorlage",
    ("sale.subscription", "recurring_invoice_line_ids"): "Rechnungszeilen",
    ("sale.subscription.template", "description"): "Allgemeine Geschäftsbedingungen",
    ("sale.subscription.template", "journal_id"): "Buchhaltungsjournal",
    ("sale.subscription.template", "user_closable"): "Vom Kunden kündbar",
    ("sale.subscription.template", "product_ids"): "Produkt",
    ("sale.subscription.template", "product_count"): "Produktanzahl",
    ("sale.subscription.template", "subscription_count"): "Anzahl Abonnements",
    # helpdesk SLA / Timesheet - fachlich eindeutig
    ("helpdesk.sla", "name"): "Name",
    ("helpdesk.ticket.sla", "deadline"): "Frist",
    ("helpdesk.ticket.sla", "expected_stage_id"): "Erwartete Stufe",
    ("helpdesk.ticket.sla", "consumed_time"): "Verbrauchte Zeit",
    ("helpdesk.ticket.sla", "expired"): "Abgelaufen",
    ("helpdesk.ticket.sla", "sla_id"): "SLA",
    ("helpdesk.ticket", "sla_deadline"): "SLA-Frist",
    ("helpdesk.ticket", "sla_expired"): "SLA abgelaufen",
    ("helpdesk.ticket", "sla_fits"): "SLA erfüllt",
    ("helpdesk.ticket", "team_sla"): "Team-SLA",
    ("helpdesk.ticket", "ticket_sla_ids"): "Ticket-SLAs",
    ("helpdesk.ticket", "sla_ids"): "Anwendbare SLAs",
    ("helpdesk.ticket", "progress"): "Fortschritt",
    ("helpdesk.ticket.team", "resource_calendar_id"): "Arbeitszeit",
    ("helpdesk.ticket.team", "use_sla"): "SLA verwenden",
    ("helpdesk.ticket.category", "complete_name"): "Vollständiger Name",
    ("helpdesk.ticket.category", "parent_id"): "Übergeordnete Kategorie",
    ("helpdesk.ticket.category", "child_id"): "Unterkategorien",
    ("helpdesk.ticket.category", "parent_path"): "Elternpfad",
    ("helpdesk.ticket.category", "show_in_portal"): "Im Portal anzeigen",
    ("helpdesk.ticket.team", "complete_name"): "Vollständiger Name",
    ("helpdesk.ticket.team", "parent_id"): "Übergeordnetes Team",
    ("helpdesk.ticket.team", "parent_path"): "Elternpfad",
    ("helpdesk.ticket.team", "show_in_portal"): "Im Portal anzeigen",
    ("helpdesk.ticket.team", "alias_name"): "Alias-Name",
    ("helpdesk.ticket.team", "alias_domain"): "Alias-Domain",
    ("helpdesk.ticket.team", "alias_email"): "Alias-E-Mail",
    ("helpdesk.ticket.duplicate.wizard", "duplicate_of_id"): "Duplikat von",
    ("helpdesk.ticket.duplicate.wizard", "target_stage_id"): "Zielstufe",
    ("helpdesk.ticket.stage", "close_from_portal"): "Im Portal schließbar",
    ("helpdesk.ticket.stage", "team_ids"): "Helpdesk-Teams",
    ("account.analytic.line", "date_time"): "Startzeit",
    ("account.analytic.line", "date_time_end"): "Endzeit",
    ("account.analytic.line", "show_time_control"): "Zeitkontrolle anzeigen",
    ("hr.timesheet.switch", "date_time"): "Startzeit",
    ("hr.timesheet.switch", "date_time_end"): "Endzeit",
    ("hr.timesheet.switch", "show_time_control"): "Zeitkontrolle anzeigen",
    ("hr.timesheet.switch", "running_timer_id"): "Laufender Timer",
    ("hr.timesheet.switch", "running_timer_start"): "Start des laufenden Timers",
    ("hr.timesheet.switch", "running_timer_duration"): "Bisherige Dauer",
    ("hr.timesheet.switch", "analytic_line_id"): "Ursprungszeile",
    ("hr.timesheet.switch", "name"): "Beschreibung",
    ("project.project", "ticket_ids"): "Tickets",
    ("project.task", "ticket_ids"): "Tickets",
    ("project.milestone", "helpdesk_ticket_ids"): "Helpdesk-Tickets",
    ("res.company", "helpdesk_mgmt_ticket_auto_assign"): "Tickets automatisch zuweisen",
    ("res.company", "helpdesk_mgmt_duplicate_tracking"): "Duplikat-Erkennung für Tickets aktivieren",
    ("res.company", "helpdesk_mgmt_duplicate_ticket_stage_id"): "Duplikat-Tickets in diese Stufe verschieben",
    ("res.company", "helpdesk_mgmt_portal_select_team"): "Team im Helpdesk-Portal auswählen",
    ("res.company", "helpdesk_mgmt_portal_team_id_required"): "Team-Feld im Helpdesk-Portal als Pflichtfeld",
    ("res.company", "helpdesk_mgmt_portal_select_category"): "Kategorie im Helpdesk-Portal auswählen",
    ("res.company", "helpdesk_mgmt_portal_category_id_required"): "Kategorie-Feld im Helpdesk-Portal als Pflichtfeld",
    ("res.config.settings", "helpdesk_mgmt_ticket_auto_assign"): "Tickets automatisch zuweisen",
    ("res.config.settings", "helpdesk_mgmt_duplicate_tracking"): "Duplikat-Erkennung für Tickets aktivieren",
    ("res.config.settings", "helpdesk_mgmt_duplicate_ticket_stage_id"): "Duplikat-Tickets in diese Stufe verschieben",
    ("res.config.settings", "helpdesk_mgmt_portal_select_team"): "Team im Helpdesk-Portal auswählen",
    ("res.config.settings", "helpdesk_mgmt_portal_team_id_required"): "Team-Feld im Helpdesk-Portal als Pflichtfeld",
    ("res.config.settings", "helpdesk_mgmt_portal_select_category"): "Kategorie im Helpdesk-Portal auswählen",
    ("res.config.settings", "helpdesk_mgmt_portal_category_id_required"): "Kategorie-Feld im Helpdesk-Portal als Pflichtfeld",
}
SPECIAL = {k: v for k, v in SPECIAL.items() if v}

def apply_de(fid, model, name, de_new, en_old):
    exec_kw("ir.model.fields", "write", [[fid], {"field_description": de_new}], {"context": {"lang": "de_DE"}})
    p("FELD %s.%s: %r -> %r" % (model, name, en_old, de_new))

changed, open_list = [], []
for r in rows:
    if r["de"] != r["en"]:
        continue  # de-Slot vorhanden oder anderes Label -> nicht anfassen
    target = SPECIAL.get((r["model"], r["name"]))
    if target:
        apply_de(r["id"], r["model"], r["name"], target, r["en"])
        changed.append((r["model"], r["name"], r["en"], target))
        continue
    # Referenz ueber Feldname (Quellmodelle der Gruppe)
    candidates = ref.get(r["name"], [])
    if not candidates:
        continue
    hit = None
    for (e, d, m) in candidates:
        if e == r["en"]:
            hit = (e, d)
            break
    if hit:
        apply_de(r["id"], r["model"], r["name"], hit[1], r["en"])
        changed.append((r["model"], r["name"], r["en"], hit[1]))
    else:
        open_list.append((r["model"], r["name"], r["en"]))

p("")
p("GEAENDERT: %d Felder" % len(changed))
p("")
p("OFFEN (kein de-Pendant gefunden, Klaerung noetig): %d" % len(open_list))
seen = set()
for (m, n, e) in open_list:
    if (n, e) in seen:
        continue
    seen.add((n, e))
    p("  %-28s %-34r" % (n, e))

open(os.path.join(os.environ.get("TEMP", "."), "fix_report.txt"), "w", encoding="utf-8").write("\n".join(LOG) + "\n")
print("Report -> fix_report.txt")
