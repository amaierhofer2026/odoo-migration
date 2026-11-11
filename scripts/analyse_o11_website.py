"""Bereich WEBSITE / WEBINHALTE: read-only Bestandsaufnahme Odoo 11 gegen Odoo 18.

Aufruf:
    python scripts/analyse_o11_website.py                 # Uebersicht beide Seiten
    python scripts/analyse_o11_website.py --json datei.json
    python scripts/analyse_o11_website.py --seiten-arch   # Seiteninhalte nach HTML/CSV

Schreibt NICHTS: nur search_read / read / fields_get gegen die drei Instanzen.
Odoo 11 Prod wird ausschliesslich lesend benutzt.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _o11o18_client as client  # noqa: E402

DE = {"lang": "de_DE"}
MODULE = ["website", "website_form", "website_links", "website_rating", "website_blog",
          "website_forum", "website_slides", "website_sale", "website_crm", "website_mail",
          "website_mass_mailing", "website_event", "website_support", "website_partner",
          "website_odoo_debranding", "website_cookie_notice", "survey", "survey_crm",
          "website_legal_page", "website_livechat", "website_hr_recruitment"]


def sichtbarer_text(arch: str) -> str:
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", arch, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def module(cl) -> dict:
    rows = cl.kw("ir.module.module", "search_read",
                 [[["name", "in", MODULE]], ["name", "state", "installed_version", "shortdesc"]])
    return {r["name"]: {"state": r["state"], "version": r.get("installed_version"),
                        "shortdesc": r.get("shortdesc")} for r in rows}


def seiten(cl) -> list:
    pgs = cl.kw("website.page", "search_read", [[]],
                fields=["id", "name", "url", "view_id", "website_published", "website_indexed",
                        "key", "is_homepage", "website_meta_title", "website_meta_description"],
                order="id")
    if not pgs:
        return []
    vids = [p["view_id"][0] for p in pgs if p["view_id"]]
    arch = {v["id"]: (v["arch_db"] or "") for v in
            cl.kw("ir.ui.view", "read", [vids, ["arch_db"]])}
    for p in pgs:
        a = arch.get(p["view_id"][0] if p["view_id"] else 0, "")
        txt = sichtbarer_text(a)
        hs = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", a, flags=re.S)
        p.update({
            "arch_zeichen": len(a),
            "text_zeichen": len(txt),
            "ueberschriften": len(hs),
            "faq_aufklapper": a.count("data-toggle") + a.count("data-bs-toggle"),
            "base64_bilder": len(re.findall(r"data:image/[a-z]+;base64,", a)),
            "web_image_verweise": sorted(set(re.findall(r"/web/image/([^\"'\s)]+)", a))),
            "bootstrap3": {
                "col_offset": len(re.findall(r"col-(?:md|sm|xs|lg)-offset-\d", a)),
                "jumbotron": len(re.findall(r"\bjumbotron\b", a)),
                "pull": len(re.findall(r"\bpull-(?:left|right)\b", a)),
                "panel": len(re.findall(r"\bpanel(?:-body|-heading|-group|-title|-collapse)?\b", a)),
                "fa_icon": len(re.findall(r"\bfa-[a-z]", a)),
            },
            "escaped": {"nbsp": a.count("&amp;nbsp;"), "amp": a.count("&amp;amp;")},
            "snippets": sorted(set(re.findall(r"\b(s_[a-z_]+)", a))),
        })
    return pgs


def menues(cl) -> list:
    return cl.kw("website.menu", "search_read", [[]],
                 fields=["id", "name", "url", "parent_id", "sequence", "page_id", "new_window"],
                 order="sequence,id", context=DE)


def website_satz(cl) -> dict:
    ws = cl.kw("website", "search_read", [[]],
               fields=["name", "domain", "default_lang_id", "language_ids", "social_twitter",
                       "social_facebook", "social_linkedin", "social_youtube", "social_github",
                       "social_instagram", "google_analytics_key", "crm_default_team_id",
                       "company_id", "cdn_activated"])
    return ws[0] if ws else {}


def zaehler(cl) -> dict:
    out = {}
    for mod, feld in (("link.tracker", "count"), ("rating.rating", None), ("survey.survey", None),
                      ("event.event", None), ("product.template", None), ("ir.attachment", None),
                      ("website.redirect", None), ("website.menu", None), ("website.page", None)):
        try:
            out[mod] = cl.kw(mod, "search_count", [[]])
        except Exception as exc:  # Modell existiert auf dieser Instanz nicht
            out[mod] = "ERR: %s" % str(exc)[:60]
    if isinstance(out.get("link.tracker"), int) and out["link.tracker"]:
        try:
            out["link.tracker.klicks"] = sum(t["count"] for t in
                                             cl.kw("link.tracker", "search_read", [[], ["count"]]))
        except Exception:
            pass
    try:
        out["event.event.veroeffentlicht"] = cl.kw("event.event", "search_count",
                                                   [[["website_published", "=", True]]])
    except Exception:
        pass
    try:
        out["product.template.veroeffentlicht"] = cl.kw("product.template", "search_count",
                                                        [[["website_published", "=", True]]])
    except Exception:
        pass
    return out


def rechte(cl) -> dict:
    out = {"gruppen": [], "acl": [], "rules": []}
    for g in cl.kw("res.groups", "search_read", [[["category_id.name", "ilike", "Website"]],
                                                 ["name", "full_name", "category_id"]], context=DE):
        n = cl.kw("res.users", "search_count", [[["groups_id", "in", [g["id"]]], ["active", "=", True]]])
        out["gruppen"].append({"id": g["id"], "name": g["full_name"], "aktive_benutzer": n})
    for a in cl.kw("ir.model.access", "search_read",
                   [[["model_id.model", "in", ["website.page", "website.menu", "link.tracker"]]],
                    ["name", "model_id", "group_id", "perm_read", "perm_write", "perm_create",
                     "perm_unlink"]]):
        out["acl"].append(a)
    try:
        for r in cl.kw("ir.rule", "search_read", [[["model_id.model", "like", "website"]],
                                                  ["name", "model_id", "groups", "domain_force"]]):
            out["rules"].append(r)
    except Exception:
        pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--seiten-arch", help="HTML-Inhalte der Seiten in dieses Verzeichnis schreiben")
    args = ap.parse_args()

    daten = {}
    for name, inst in (("o11", "o11"), ("lokal", "lokal"), ("vm", "vm")):
        cl = client.o11() if inst == "o11" else client.o18(inst)
        daten[name] = {"website": website_satz(cl), "module": module(cl), "seiten": seiten(cl),
                       "menues": menues(cl), "zaehler": zaehler(cl), "rechte": rechte(cl)}
        print("=== %s ===" % name.upper())
        print("Website:", daten[name]["website"].get("name"), "| Domain:",
              daten[name]["website"].get("domain"))
        print("Seiten:", len(daten[name]["seiten"]), "| Menues:", len(daten[name]["menues"]))
        for m, v in sorted(daten[name]["module"].items()):
            print("  %-24s %-12s %s" % (m, v["state"], v["version"]))
        print("Zaehler:", json.dumps(daten[name]["zaehler"], ensure_ascii=False))
        print("Gruppen:", [(g["name"], g["aktive_benutzer"]) for g in daten[name]["rechte"]["gruppen"]])
        print()

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
        print("JSON geschrieben:", args.json)

    if args.seiten_arch:
        os.makedirs(args.seiten_arch, exist_ok=True)
        cl = client.o11()
        for p in daten["o11"]["seiten"]:
            arch = cl.kw("ir.ui.view", "read", [[p["view_id"][0]], ["arch_db"]])[0]["arch_db"] or ""
            pfad = os.path.join(args.seiten_arch, "o11_seite_%03d.html" % p["id"])
            with open(pfad, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(arch)
            print("geschrieben:", pfad, len(arch), "Zeichen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
