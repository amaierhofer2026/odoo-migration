"""B6 Mailvorlagen: Pruefung der ITK-Rechnungsvorlagen in Odoo 18 (lokal und VM).

Prueft: Vorhandensein, Felder, Berichtsanhang, gerenderter Betreff und Text an einer echten
Rechnung. Wird read-only ausgefuehrt (nur Rendern, kein Versand).

Aufruf:  python scripts/verify_b6_mailvorlagen.py --instanz lokal
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18

ERWARTET = {
    "itk_reports.mail_template_itk_invoice": "Rechnungsstellung: Allgemeine Rechnung",
    "itk_reports.mail_template_itk_invoice_abo": "Rechnungsstellung: Ihr Abonnement für help-amtsweg.gv.at",
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    lade_env()
    k = o18(a.instanz)
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("=== Instanz %s ===" % a.instanz)
    vorlagen = {}
    for xmlid, name in ERWARTET.items():
        modul, kurz = xmlid.split(".")
        treffer = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", kurz)],
                                                        ["res_id", "model"]])
        pruefe(bool(treffer) and treffer[0]["model"] == "mail.template",
               "Vorlage %s vorhanden" % xmlid)
        if not treffer:
            continue
        tid = treffer[0]["res_id"]
        daten = k.kw("mail.template", "read", [[tid], ["id", "name", "subject", "email_from", "lang",
                                                       "auto_delete", "model_id", "report_template_ids",
                                                       "body_html"]], context={"lang": "de_DE"})[0]
        vorlagen[xmlid] = daten
        print("    id=%s name=%s" % (daten["id"], daten["name"]))
        print("    Betreff : %s" % daten["subject"])
        print("    Absender: %s" % daten["email_from"])
        print("    Bericht : %s" % daten["report_template_ids"])
        pruefe(daten["name"] == name, "Beschriftung wie in Odoo 11 (%s)" % name[:40])
        modell_ids = k.kw("ir.model", "search_read", [[("model", "=", "account.move")], ["id", "model"]])
        pruefe(bool(modell_ids) and daten["model_id"] and daten["model_id"][0] == modell_ids[0]["id"],
               "Modell ist account.move")
        pruefe("office@it-kommunal.at" in (daten["email_from"] or ""), "Absender ITK-Office wie in Odoo 11")
        pruefe(bool(daten["report_template_ids"]), "ITK-Rechnung als Anhang hinterlegt")
        pruefe("Rechnung (Ref" in (daten["subject"] or ""), "Betreff wie in Odoo 11")
        pruefe("itk_reports/static/img/itk_pageheader.jpg" in (daten["body_html"] or ""),
               "ITK-Briefkopf im Text")
        pruefe("Sehr geehrte Damen und Herren" in (daten["body_html"] or ""), "Anrede wie in Odoo 11")
        if "abo" in xmlid:
            pruefe("Nutzungsgebühr für amtsweg.gv.at" in (daten["body_html"] or ""),
                   "Abonnement-Text wie in Odoo 11")
        else:
            pruefe("im Zusammenhang für unsere Leistungen oder Produkte" in (daten["body_html"] or ""),
                   "Allgemeiner Rechnungstext wie in Odoo 11")

    print("\n=== Rendern an einer echten Rechnung ===")
    belege = k.kw("account.move", "search_read", [[("move_type", "=", "out_invoice"), ("state", "=", "posted")],
                                                  ["id", "name"]], order="id desc", limit=1)
    pruefe(bool(belege), "gebuchte Ausgangsrechnung im Testbestand vorhanden")
    if belege:
        beleg = belege[0]
        print("    Beleg: %s %s" % (beleg["id"], beleg["name"]))
        for xmlid, daten in vorlagen.items():
            try:
                mid = k.kw("mail.template", "send_mail", [[daten["id"]], beleg["id"]],
                           force_send=False, raise_exception=False)
                print("    %-28s mail.mail id %s" % (xmlid.split(".")[-1], mid))
                mail = k.kw("mail.mail", "read", [[mid], ["subject", "body_html", "email_from",
                                                          "attachment_ids", "state"]])[0]
                betreff = mail.get("subject") or ""
                text = re.sub(r"<[^>]+>", " ", mail.get("body_html") or "")
                text = re.sub(r"\s+", " ", text).strip()
                print("        Betreff : %s" % betreff[:70])
                print("        Text    : %s" % text[:130])
                print("        Anhaenge: %s | Zustand: %s" % (mail.get("attachment_ids"), mail.get("state")))
                pruefe(beleg["name"] in betreff, "Belegnummer im gerenderten Betreff")
                pruefe("Sehr geehrte Damen und Herren" in text, "Anrede im gerenderten Text")
                pruefe("itk_pageheader" in (mail.get("body_html") or ""),
                       "Briefkopf mit absoluter Adresse im gerenderten Text")
                pruefe("martina.waiss@it-kommunal.at" in text, "Signatur wie in Odoo 11")
                pruefe(len(mail.get("attachment_ids") or []) >= 1, "ITK-Rechnung als PDF angehaengt")
            except Exception as ausnahme:
                pruefe(False, "Rendern von %s (%s)" % (xmlid, str(ausnahme)[:90]))

    print("\n=== Massenversand-Weg (mail.compose.message mit Vorlage) ===")
    if belege:
        try:
            kid = k.kw("mail.compose.message", "create", [[{
                "model": "account.move",
                "res_ids": [beleg["id"]],
                "template_id": vorlagen["itk_reports.mail_template_itk_invoice"]["id"],
                "composition_mode": "mass_mail",
            }]], context={"active_model": "account.move", "active_ids": [beleg["id"]], "lang": "de_DE"})
            kid = kid[0] if isinstance(kid, list) else kid
            werte = k.kw("mail.compose.message", "read", [[kid], ["subject", "body", "partner_ids",
                                                                   "email_from", "attachment_ids"]],
                         context={"active_model": "account.move", "active_ids": [beleg["id"]], "lang": "de_DE"})[0]
            print("    Betreff: %s" % (werte["subject"] or "")[:70])
            print("    Anhaenge: %s" % werte["attachment_ids"])
            pruefe(bool(werte["subject"]), "Composer uebernimmt den Betreff der Vorlage")
            pruefe(bool(werte["body"]), "Composer uebernimmt den Text der Vorlage")
        except Exception as ausnahme:
            pruefe(False, "Composer-Test (%s)" % str(ausnahme)[:120])

    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
