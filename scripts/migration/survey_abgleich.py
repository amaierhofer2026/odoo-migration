# -*- coding: utf-8 -*-
"""Umfragen / Survey: Abgleich Odoo 11 gegen Odoo 18 (read-only, beide Seiten).

Prueft Mengen, Beziehungen, Statuswerte, Punkte, Datumsfelder und - ueber
Laenge und Pruefsumme, nicht ueber den Inhalt - die Antworttexte. Es werden
keine Antwortinhalte ausgegeben oder gespeichert.

Aufruf:
    python scripts/migration/survey_abgleich.py --instanz lokal
    python scripts/migration/survey_abgleich.py --instanz vm
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX11 = {"lang": "de_DE", "active_test": False}
CTX18 = {"lang": "de_DE", "active_test": False}


def m2o(w):
    return w[0] if isinstance(w, (list, tuple)) and w else None


def o11_lesen():
    c = client.o11()
    return {
        "surveys": c.kw("survey.survey", "search_read",
                        [[], ["id", "title", "active", "auth_required", "users_can_go_back",
                              "quizz_mode", "create_date", "write_date"]],
                        context=CTX11, order="id", limit=500),
        "pages": c.kw("survey.page", "search_read",
                      [[], ["id", "title", "survey_id", "sequence", "create_date", "write_date"]],
                      context=CTX11, order="id", limit=1000),
        "questions": c.kw("survey.question", "search_read",
                          [[], ["id", "question", "page_id", "survey_id", "type", "sequence",
                                "constr_mandatory", "constr_error_msg", "create_date",
                                "write_date"]],
                          context=CTX11, order="id", limit=2000),
        "labels": c.kw("survey.label", "search_read",
                       [[], ["id", "value", "question_id", "sequence", "quizz_mark",
                             "create_date", "write_date"]],
                       context=CTX11, order="id", limit=2000),
        "inputs": c.kw("survey.user_input", "search_read",
                       [[], ["id", "survey_id", "state", "token", "test_entry", "quizz_score",
                             "date_create", "deadline", "partner_id", "email", "create_date",
                             "write_date", "create_uid"]],
                       context=CTX11, order="id", limit=20000),
        "lines": c.kw("survey.user_input_line", "search_read",
                      [[], ["id", "user_input_id", "question_id", "page_id", "answer_type",
                            "skipped", "quizz_mark", "value_text", "value_suggested",
                            "value_suggested_row", "value_number", "value_date", "create_date"]],
                      context=CTX11, order="id", limit=50000),
    }


def o18_lesen(instanz):
    c = client.o18(instanz)
    return c, {
        "surveys": c.kw("survey.survey", "search_read",
                        [[["itk_o11_id", "!=", False]],
                         ["id", "itk_o11_id", "title", "active", "users_login_required",
                          "users_can_go_back", "scoring_type", "access_mode", "survey_type",
                          "create_date", "write_date", "create_uid"]],
                        context=CTX18, order="itk_o11_id", limit=500),
        "pages": c.kw("survey.question", "search_read",
                      [[["itk_o11_id", "!=", False], ["is_page", "=", True]],
                       ["id", "itk_o11_id", "title", "sequence", "survey_id", "create_date",
                        "write_date", "create_uid"]],
                      context=CTX18, order="itk_o11_id", limit=1000),
        "questions": c.kw("survey.question", "search_read",
                          [[["itk_o11_id", "!=", False], ["is_page", "=", False]],
                           ["id", "itk_o11_id", "title", "sequence", "page_id", "survey_id",
                            "question_type", "constr_mandatory", "constr_error_msg",
                            "create_date", "write_date", "create_uid"]],
                          context=CTX18, order="itk_o11_id", limit=2000),
        "labels": c.kw("survey.question.answer", "search_read",
                       [[["itk_o11_id", "!=", False]],
                        ["id", "itk_o11_id", "value", "sequence", "answer_score",
                         "question_id", "create_date", "write_date"]],
                       context=CTX18, order="itk_o11_id", limit=2000),
        "inputs": c.kw("survey.user_input", "search_read",
                       [[["itk_o11_id", "!=", False]],
                        ["id", "itk_o11_id", "survey_id", "state", "access_token", "test_entry",
                         "scoring_total", "start_datetime", "end_datetime", "deadline",
                         "partner_id", "email", "create_date", "write_date", "create_uid"]],
                       context=CTX18, order="itk_o11_id", limit=20000),
        "lines": c.kw("survey.user_input.line", "search_read",
                      [[["itk_o11_id", "!=", False]],
                       ["id", "itk_o11_id", "user_input_id", "question_id", "page_id",
                        "answer_type", "skipped", "answer_score", "value_text_box", "value_date",
                        "value_numerical_box", "suggested_answer_id", "create_date"]],
                      context=CTX18, order="itk_o11_id", limit=50000),
    }


def pruefe(name, soll, ist, ok_liste, fehler):
    if soll == ist:
        ok_liste.append(name)
    else:
        fehler.append("%s: Odoo 11 = %s, Odoo 18 = %s" % (name, soll, ist))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    args = ap.parse_args()

    print("=== Survey-Abgleich Odoo 11 <-> Odoo 18 (%s) ===" % args.instanz)
    a = o11_lesen()
    c18, b = o18_lesen(args.instanz)
    ok, fehler = [], []

    # ------------------------------------------------------------------ Mengen
    pruefe("Umfragen", len(a["surveys"]), len(b["surveys"]), ok, fehler)
    pruefe("Seiten", len(a["pages"]), len(b["pages"]), ok, fehler)
    pruefe("Fragen", len(a["questions"]), len(b["questions"]), ok, fehler)
    pruefe("Antwortvorgaben", len(a["labels"]), len(b["labels"]), ok, fehler)
    pruefe("Teilnahmen", len(a["inputs"]), len(b["inputs"]), ok, fehler)
    pruefe("Antworten", len(a["lines"]), len(b["lines"]), ok, fehler)

    # ------------------------------------------------------------- Statuswerte
    pruefe("Teilnahmen nach Status", dict(Counter(x["state"] for x in a["inputs"])),
           dict(Counter(x["state"] for x in b["inputs"])), ok, fehler)
    pruefe("Testteilnahmen", sum(1 for x in a["inputs"] if x["test_entry"]),
           sum(1 for x in b["inputs"] if x["test_entry"]), ok, fehler)
    pruefe("aktive Umfragen", sum(1 for x in a["surveys"] if x["active"]),
           sum(1 for x in b["surveys"] if x["active"]), ok, fehler)
    pruefe("Teilnahmen mit Partner", sum(1 for x in a["inputs"] if x["partner_id"]),
           sum(1 for x in b["inputs"] if x["partner_id"]), ok, fehler)
    pruefe("Teilnahmen mit E-Mail", sum(1 for x in a["inputs"] if x["email"]),
           sum(1 for x in b["inputs"] if x["email"]), ok, fehler)
    pruefe("Teilnahmen mit Frist", sum(1 for x in a["inputs"] if x["deadline"]),
           sum(1 for x in b["inputs"] if x["deadline"]), ok, fehler)
    pruefe("Antworten uebersprungen", sum(1 for x in a["lines"] if x["skipped"]),
           sum(1 for x in b["lines"] if x["skipped"]), ok, fehler)
    pruefe("Punkte summiert", round(sum(x["quizz_mark"] or 0 for x in a["lines"]), 2),
           round(sum(x["answer_score"] or 0 for x in b["lines"]), 2), ok, fehler)

    # --------------------------------------------------------------- Titel/Art
    for s in a["surveys"]:
        z = next((x for x in b["surveys"] if x["itk_o11_id"] == s["id"]), None)
        if not z:
            fehler.append("Umfrage O11 %s fehlt in Odoo 18" % s["id"])
            continue
        pruefe("Umfrage %s Titel" % s["id"], s["title"], z["title"], ok, fehler)
        pruefe("Umfrage %s aktiv" % s["id"], bool(s["active"]), bool(z["active"]), ok, fehler)
        pruefe("Umfrage %s Anmeldung" % s["id"], bool(s["auth_required"]),
               bool(z["users_login_required"]), ok, fehler)
        pruefe("Umfrage %s zurueck" % s["id"], bool(s["users_can_go_back"]),
               bool(z["users_can_go_back"]), ok, fehler)

    fragen_typ = {"textbox": "text_box", "simple_choice": "simple_choice",
                  "multiple_choice": "multiple_choice", "numerical_box": "numerical_box",
                  "date": "date", "datetime": "datetime", "matrix": "matrix"}
    for f in a["questions"]:
        z = next((x for x in b["questions"] if x["itk_o11_id"] == f["id"]), None)
        if not z:
            fehler.append("Frage O11 %s fehlt in Odoo 18" % f["id"])
            continue
        pruefe("Frage %s Typ" % f["id"], fragen_typ.get(f["type"]), z["question_type"], ok, fehler)
        pruefe("Frage %s Pflicht" % f["id"], bool(f["constr_mandatory"]),
               bool(z["constr_mandatory"]), ok, fehler)
        pruefe("Frage %s Fehlertext" % f["id"], f["constr_error_msg"],
               z["constr_error_msg"], ok, fehler)
        # Seite: O11-Seite -> O18-Abschnitt derselben Umfrage
        if f["page_id"]:
            seite18 = next((p for p in b["pages"] if p["id"] == m2o(z["page_id"])), None)
            pruefe("Frage %s Seite" % f["id"], m2o(f["page_id"]),
                   seite18["itk_o11_id"] if seite18 else None, ok, fehler)

    for p in a["pages"]:
        z = next((x for x in b["pages"] if x["itk_o11_id"] == p["id"]), None)
        if not z:
            fehler.append("Seite O11 %s fehlt in Odoo 18" % p["id"])
            continue
        pruefe("Seite %s Titel" % p["id"], p["title"], z["title"], ok, fehler)
        pruefe("Seite %s Reihenfolge" % p["id"], p["sequence"], z["sequence"], ok, fehler)

    for l in a["labels"]:
        z = next((x for x in b["labels"] if x["itk_o11_id"] == l["id"]), None)
        if not z:
            fehler.append("Antwortvorgabe O11 %s fehlt" % l["id"])
            continue
        pruefe("Vorgabe %s Wert" % l["id"], l["value"], z["value"], ok, fehler)
        pruefe("Vorgabe %s Punkte" % l["id"], l["quizz_mark"] or 0.0,
               z["answer_score"] or 0.0, ok, fehler)

    # -------------------------------------------------------------- Teilnahmen
    ins18 = {x["itk_o11_id"]: x for x in b["inputs"]}
    for i in a["inputs"]:
        z = ins18.get(i["id"])
        if not z:
            fehler.append("Teilnahme O11 %s fehlt" % i["id"])
            continue
        pruefe("Teilnahme %s Status" % i["id"], i["state"], z["state"], ok, fehler)
        pruefe("Teilnahme %s Token" % i["id"], i["token"], z["access_token"], ok, fehler)
        pruefe("Teilnahme %s Start" % i["id"], (i["date_create"] or "")[:19],
               (z["start_datetime"] or "")[:19], ok, fehler)
        pruefe("Teilnahme %s Erstellt-Datum" % i["id"], (i["create_date"] or "")[:19],
               (z["create_date"] or "")[:19], ok, fehler)

    # ----------------------------------------------------------------- Antworten
    zeilen18 = {x["itk_o11_id"]: x for x in b["lines"]}
    typ_map = {"text": "text_box", "suggestion": "suggestion", "number": "numerical_box",
               "date": "date"}
    inhalt_gleich = 0
    laenge_gleich = 0
    for z_ in a["lines"]:
        z = zeilen18.get(z_["id"])
        if not z:
            fehler.append("Antwort O11 %s fehlt" % z_["id"])
            continue
        pruefe("Antwort %s Typ" % z_["id"], typ_map.get(z_["answer_type"]),
               z["answer_type"], ok, fehler)
        soll_text = z_["value_text"] or ""
        ist_text = z["value_text_box"] or ""
        if len(soll_text) == len(ist_text):
            laenge_gleich += 1
        else:
            fehler.append("Antwort %s Laenge: %d != %d" % (z_["id"], len(soll_text), len(ist_text)))
        if hashlib.sha1(soll_text.encode("utf-8")).hexdigest() == \
                hashlib.sha1(ist_text.encode("utf-8")).hexdigest():
            inhalt_gleich += 1
        else:
            fehler.append("Antwort %s Inhalt weicht ab (Pruefsumme)" % z_["id"])
        # Beziehungen: Teilnahme und Frage muessen zur selben Umfrage gehoeren
        if m2o(z["user_input_id"]) != ins18[z_["user_input_id"][0]]["id"]:
            fehler.append("Antwort %s Teilnahme nicht verknuepft" % z_["id"])
    pruefe("Antworten Textlaenge gleich", len(a["lines"]), laenge_gleich, ok, fehler)
    pruefe("Antworten Inhalt gleich (Pruefsumme)", len(a["lines"]), inhalt_gleich, ok, fehler)

    # -------------------------------------------------- Beziehungen Umfrage->...
    for s in b["surveys"]:
        n_fragen = sum(1 for q in b["questions"] if m2o(q["survey_id"]) == s["id"])
        n_seiten = sum(1 for q in b["pages"] if m2o(q["survey_id"]) == s["id"])
        n_inputs = sum(1 for i in b["inputs"] if m2o(i["survey_id"]) == s["id"])
        print("  Umfrage O18 %s: %d Seiten, %d Fragen, %d Teilnahmen"
              % (s["id"], n_seiten, n_fragen, n_inputs))
        soll = sum(1 for i in a["inputs"] if m2o(i["survey_id"]) == s["itk_o11_id"])
        pruefe("Umfrage %s Teilnahmen" % s["itk_o11_id"], soll, n_inputs, ok, fehler)
        soll_q = sum(1 for q in a["questions"] if m2o(q["survey_id"]) == s["itk_o11_id"])
        pruefe("Umfrage %s Fragen" % s["itk_o11_id"], soll_q, n_fragen, ok, fehler)
        soll_p = sum(1 for p in a["pages"] if m2o(p["survey_id"]) == s["itk_o11_id"])
        pruefe("Umfrage %s Seiten" % s["itk_o11_id"], soll_p, n_seiten, ok, fehler)

    # Antworten je Frage / je Teilnahme
    for q in b["questions"]:
        soll = sum(1 for l in a["lines"] if m2o(l["question_id"]) == q["itk_o11_id"])
        ist = sum(1 for l in b["lines"] if m2o(l["question_id"]) == q["id"])
        pruefe("Frage %s Antworten" % q["itk_o11_id"], soll, ist, ok, fehler)

    # ------------------------------------------------------------- Datumsfelder
    soll_spanne = (min((x["create_date"] for x in a["inputs"]), default="")[:19],
                   max((x["create_date"] for x in a["inputs"]), default="")[:19])
    ist_spanne = (min((x["create_date"] for x in b["inputs"]), default="")[:19],
                  max((x["create_date"] for x in b["inputs"]), default="")[:19])
    pruefe("Teilnahmen Zeitspanne", soll_spanne, ist_spanne, ok, fehler)
    pruefe("Teilnahmen abgeschlossen mit Enddatum",
           sum(1 for x in a["inputs"] if x["state"] == "done"),
           sum(1 for x in b["inputs"] if x["state"] == "done" and x["end_datetime"]), ok, fehler)

    print()
    print("--- Ergebnis ---")
    print("Pruefungen OK ............... %d" % len(ok))
    print("Abweichungen ................ %d" % len(fehler))
    for f in fehler[:25]:
        print("  %s" % f)
    if len(fehler) > 25:
        print("  ... %d weitere" % (len(fehler) - 25))
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
