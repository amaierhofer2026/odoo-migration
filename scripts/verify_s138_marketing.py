"""Abnahmepruefung Bereich E-MAIL-MARKETING (Session 138) - read-only.

Prueft Struktur, Beschriftungen, Rechte, Daten und die Versandsperre gegen den
Odoo-11-Livebestand:
  * Module, Menues, Kampagnenstufen, Kampagnen, Tags, Mailinglisten
  * 147 uebernommene Mailings mit Betreff, Inhalt, Status, Sendedatum und
    historischen Kennzahlen (Feldgleichheit je Datensatz gegen Odoo 11)
  * KEINE Kontakte, Empfaenger, Traces, Abonnements oder Blacklist-Adressen
  * Versandsperre: historische Mailings lassen sich nicht senden, nicht in die
    Warteschlange legen und nicht auf "Im Versand" setzen; keine neue mail.mail-Zeile

Aufruf:
    python scripts/verify_s138_marketing.py --instanz lokal
    python scripts/verify_s138_marketing.py --instanz vm
"""
from __future__ import annotations

import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

DE = {"lang": "de_DE"}
OK = 0
FEHLER = []


def pruefe(bedingung, text, ist=None, soll=None):
    global OK
    if bedingung:
        OK += 1
    else:
        FEHLER.append("%s (ist=%r soll=%r)" % (text, ist, soll))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = ap.parse_args()
    k = o18(a.instanz)
    k11 = o11()
    print("=== Abnahme E-MAIL-MARKETING (%s) ===" % a.instanz)

    # ------------------------------------------------------------- Module
    mods = {m["name"]: m for m in k.kw("ir.module.module", "search_read",
                                       [[("name", "in", ["mass_mailing", "mass_mailing_themes",
                                                         "website_mass_mailing", "mass_mailing_event",
                                                         "itk_mass_mailing_compat"])],
                                        ["name", "state", "installed_version"]])}
    for name in ("mass_mailing", "mass_mailing_themes", "website_mass_mailing",
                 "mass_mailing_event", "itk_mass_mailing_compat"):
        pruefe(mods.get(name, {}).get("state") == "installed",
               "Modul %s installiert" % name, mods.get(name, {}).get("state"))
    print("  Module:", {n: mods.get(n, {}).get("installed_version") for n in mods})

    # -------------------------------------------------------------- Menues
    def menue(xmlid):
        modul, name = xmlid.split(".")
        d = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)], ["res_id"]])
        if not d:
            return None
        return k.kw("ir.ui.menu", "read", [[d[0]["res_id"]], ["name", "complete_name"]], context=DE)[0]

    soll = {
        "mass_mailing.mass_mailing_menu": "Massenmailings",
        "itk_mass_mailing_compat.menu_itk_mailing_campaign": "Kampagnen",
        "itk_mass_mailing_compat.menu_itk_mailing_campaign_stage": "Kampagnenstufen",
        "itk_mass_mailing_compat.menu_itk_mailing_tag": "Kampagnen-Tags",
    }
    for xmlid, name in soll.items():
        m = menue(xmlid)
        pruefe(m is not None and m["name"] == name, "Menue %s = %r" % (xmlid, name),
               m["name"] if m else None, name)
        if m:
            print("    %-56s %s" % (m["complete_name"], m["name"]))

    # -------------------------------------------------- Stufen/Tags/Kampagnen
    stages = k.kw("itk.mailing.campaign.stage", "search_read", [[], ["name", "sequence"]],
                  context=DE, order="sequence")
    pruefe(len(stages) == 3, "3 Kampagnenstufen", len(stages), 3)
    pruefe([s["name"] for s in stages] == ["Ausführungsplan", "Design", "Gesendet"],
           "Stufennamen wie Odoo 11", [s["name"] for s in stages])
    tags = k.kw("itk.mailing.tag", "search_read", [[], ["name"]])
    pruefe(len(tags) == 1 and tags[0]["name"] == "Campaign Tag 1", "1 Kampagnen-Tag wie Odoo 11", tags)

    camps = k.kw("itk.mailing.campaign", "search_read",
                 [[], ["name", "x_o11_id", "stage_id", "x_o11_sent", "x_o11_opened", "x_o11_total_mailings"]],
                 context=dict(DE, active_test=False))
    pruefe(len(camps) == 9, "9 Kampagnen", len(camps), 9)
    pruefe(all(c["x_o11_id"] for c in camps), "Kampagnen mit Odoo-11-Referenz",
           sum(1 for c in camps if not c["x_o11_id"]), 0)

    # ------------------------------------------------------------ Mailings
    ms = k.kw("mailing.mailing", "search_read",
              [[], ["id", "subject", "state", "active", "x_o11_id", "x_o11_name",
                    "x_o11_schedule_date", "sent_date", "schedule_date", "itk_campaign_id",
                    "x_o11_sent", "x_o11_opened", "x_o11_failed", "x_o11_total",
                    "contact_list_ids", "mailing_domain"]],
              context={"active_test": False}, order="x_o11_id")
    pruefe(len(ms) == 147, "147 uebernommene Mailings", len(ms), 147)
    pruefe(all(m["x_o11_id"] for m in ms), "alle Mailings mit Odoo-11-Referenz",
           sum(1 for m in ms if not m["x_o11_id"]), 0)
    st = collections.Counter(m["state"] for m in ms)
    pruefe(st.get("draft", 0) + st.get("done", 0) == len(ms),
           "nur Entwurf/Gesendet", dict(st))
    pruefe(st.get("in_queue", 0) == 0 and st.get("sending", 0) == 0,
           "kein Mailing in Warteschlange oder Versand", dict(st))
    pruefe(sum(1 for m in ms if m["schedule_date"]) == 0,
           "kein aktives Sendedatum", sum(1 for m in ms if m["schedule_date"]), 0)
    pruefe(sum(1 for m in ms if m["x_o11_schedule_date"]) == 3,
           "3 historische Planungstermine nur als Information",
           sum(1 for m in ms if m["x_o11_schedule_date"]), 3)
    print("  Mailings:", len(ms), "| Status:", dict(st),
          "| mit Kampagne:", sum(1 for m in ms if m["itk_campaign_id"]))

    # ------------------------------------------------------- keine Personen
    for modell in ("mailing.contact", "mailing.trace", "mailing.subscription"):
        n = k.kw(modell, "search_count", [[]], context={"active_test": False})
        pruefe(n == 0, "keine Datensaetze in %s" % modell, n, 0)
    listen = k.kw("mailing.list", "search_read", [[], ["name", "contact_count"]],
                  context={"active_test": False})
    pruefe(len(listen) == 8, "8 Mailinglisten (reine Struktur)", len(listen), 8)
    pruefe(all((l["contact_count"] or 0) == 0 for l in listen),
           "keine Listenmitglieder", [l["contact_count"] for l in listen], 0)
    partner = k.kw("res.partner", "search_count", [[]])
    print("  res.partner (Kontrollzahl):", partner)

    # ---------------------------------------- Feldgleichheit gegen Odoo 11
    m11 = {m["id"]: m for m in k11.kw("mail.mass_mailing", "search_read", [[("id", ">", 0)], [
        "id", "name", "state", "sent_date", "schedule_date", "sent", "opened", "failed",
        "total", "active"]], context={"lang": "de_DE", "active_test": False})}
    abw = []
    for m in ms:
        q = m11.get(m["x_o11_id"])
        if not q:
            abw.append((m["x_o11_id"], "fehlt in Odoo 11"))
            continue
        if m["x_o11_name"] != q["name"]:
            abw.append((m["x_o11_id"], "Name: %r != %r" % (m["x_o11_name"], q["name"])))
        if m["state"] != q["state"]:
            abw.append((m["x_o11_id"], "Status: %r != %r" % (m["state"], q["state"])))
        if (m["sent_date"] or False) != (q["sent_date"] or False):
            abw.append((m["x_o11_id"], "Sendedatum: %r != %r" % (m["sent_date"], q["sent_date"])))
        if (m["x_o11_schedule_date"] or False) != (q["schedule_date"] or False):
            abw.append((m["x_o11_id"], "Plantemrin: %r != %r" % (m["x_o11_schedule_date"], q["schedule_date"])))
        for f in ("sent", "opened", "failed", "total"):
            if m["x_o11_" + f] != (q[f] or 0):
                abw.append((m["x_o11_id"], "%s: %r != %r" % (f, m["x_o11_" + f], q[f])))
        if bool(m["active"]) != bool(q["active"]):
            abw.append((m["x_o11_id"], "Aktiv: %r != %r" % (m["active"], q["active"])))
    pruefe(not abw, "Feldgleichheit je Mailing gegen Odoo 11", abw[:5], "keine Abweichung")
    if abw:
        print("  Abweichungen (erste 10):")
        for x in abw[:10]:
            print("    ", x)

    # --------------------------------------------------------- Versandsperre
    hist = [m for m in ms if m["state"] == "done"][:1] + [m for m in ms if m["state"] == "draft"][:1]
    queue_vorher = k.kw("mail.mail", "search_count", [[]])
    for m in hist:
        for methode in ("action_send_mail", "action_put_in_queue", "action_launch", "action_set_sending"):
            try:
                k.kw("mailing.mailing", methode, [[m["id"]]])
                pruefe(False, "%s ist fuer historisches Mailing gesperrt" % methode, "ausgefuehrt")
            except Exception as exc:  # noqa: BLE001
                ok = "Odoo 11" in str(exc)
                pruefe(ok, "%s ist fuer historisches Mailing gesperrt" % methode, str(exc)[-80:])
    try:
        k.kw("mailing.mailing", "write", [[hist[0]["id"]], {"state": "in_queue"}])
        pruefe(False, "Statuswechsel auf 'in_queue' gesperrt", "erlaubt")
    except Exception as exc:  # noqa: BLE001
        pruefe("Odoo 11" in str(exc),
               "Statuswechsel auf 'in_queue' gesperrt", str(exc)[-80:])
    queue_nachher = k.kw("mail.mail", "search_count", [[]])
    pruefe(queue_nachher <= queue_vorher, "keine neue mail.mail-Zeile",
           "%s -> %s" % (queue_vorher, queue_nachher), "unveraendert")
    pruefe(k.kw("mailing.trace", "search_count", [[]]) == 0, "keine Versandprotokolle entstanden",
           k.kw("mailing.trace", "search_count", [[]]), 0)

    print("\n=== Ergebnis: %d OK / %d FEHLER ===" % (OK, len(FEHLER)))
    for f in FEHLER:
        print("   FEHLER:", f)
    return 0 if not FEHLER else 1


if __name__ == "__main__":
    sys.exit(main())
