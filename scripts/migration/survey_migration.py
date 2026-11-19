# -*- coding: utf-8 -*-
"""Umfragen / Survey: Migrationsskript Odoo 11 -> Odoo 18.

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer
(Session 146, 18.11.2026). Quelle: Odoo 11 Prod ``ITK_V1_a`` - ausschliesslich
lesend. Ziel: Odoo 18 (lokal oder VM).

Umfang (frisch gemessen am 18.11.2026, read-only):
- survey.survey          2 Umfragen (1 Testumfrage "Entwurf", 1 offene Umfrage)
- survey.page            2 Seiten  -> Odoo 18: survey.question mit is_page=True
- survey.question        2 Fragen  (1x simple_choice, 1x textbox)
- survey.label           2 Antwortvorgaben (ja/nein) -> survey.question.answer
- survey.user_input     72 Teilnahmen (71 abgeschlossen, 1 neu/leer)
- survey.user_input_line 71 Antworten (alle Freitext)

Nicht uebertragen (dokumentiert in docs/o11-o18-vergleich-survey.md):
- survey.stage (Entwurf/In Bearbeitung/Geschlossen/Dauerhaft): Odoo 18 fuehrt kein
  Stufenmodell. Regel: O11 "Geschlossen" entspricht "archiviert"; alle anderen Stufen
  bleiben aktiv. Beide vorhandenen Umfragen sind offen, es geht kein Datensatz verloren.
- user_input.type ('manually'): in Odoo 18 kein Feld mehr.
- survey.mail.compose.message ("Umfrage senden") und survey_crm-Versandaktion:
  nicht mehr benoetigt (Entscheidung Projekt, siehe PROJECT_KNOWLEDGE).
- quizz_score: Odoo 18 berechnet die Punkte aus den Antworten (beide Umfragen sind
  ohne Bewertung, scoring_type = no_scoring).

Idempotenz: technisches Feld ``itk_o11_id`` (Modul itk_migration_keys) auf
survey.survey, survey.question, survey.question.answer, survey.user_input und
survey.user_input.line. Der Zielbestand wird IMMER mit ``active_test=False``
gelesen, sonst werden archivierte Datensaetze bei jedem Lauf neu angelegt.

Datenschutz: Die Antworten enthalten Freitexte von Teilnehmern. Konsole,
Mapping-Datei und Dokumentation enthalten nur Zaehlwerte, IDs, Laengen und
Status - keine Antwortinhalte, Namen oder E-Mail-Adressen. Die Antworttexte
werden ausschliesslich zwischen Odoo 11 und Odoo 18 uebertragen.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/survey_migration.py --instanz lokal
    python scripts/migration/survey_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
    python scripts/migration/survey_migration.py --instanz vm --mapping "%LOCALAPPDATA%\\Temp\\survey_mapping.json"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX11 = {"lang": "de_DE"}
CTX18 = {"lang": "de_DE"}
CTX18_ALLE = {"lang": "de_DE", "active_test": False}
BATCH = 100

# Odoo-11-Fragetyp -> Odoo-18-Fragetyp. Die uebrigen Typen heissen gleich.
FRAGETYP = {
    "textbox": "text_box",
    "simple_choice": "simple_choice",
    "multiple_choice": "multiple_choice",
    "numerical_box": "numerical_box",
    "date": "date",
    "datetime": "datetime",
    "matrix": "matrix",
    "scale": "scale",
}

# Odoo-11-Antworttyp -> Odoo-18-Antworttyp (survey.user_input.line)
ANTWORTTYP = {
    "text": "text_box",
    "free_text": "text_box",
    "suggestion": "suggestion",
    "number": "numerical_box",
    "numerical_box": "numerical_box",
    "date": "date",
    "datetime": "datetime",
}

# Odoo-11-Stufe -> Zielzustand. Odoo 18 kennt keine Stufen; "Geschlossen" wird
# zu "archiviert", alles andere bleibt aktiv. Kein Statusfeld wird nachgebaut.
STUFE_GESCHLOSSEN = "Closed"


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


def m2o(wert):
    return wert[0] if isinstance(wert, (list, tuple)) and wert else None


def _gleich(a, b):
    """Vergleich fuer die Idempotenzpruefung; False/None und '' gelten gleich."""
    if a in (False, None, "") and b in (False, None, ""):
        return True
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a or 0) - float(b or 0)) < 0.0001
        except (TypeError, ValueError):
            return False
    return a == b


# ---------------------------------------------------------------------------
# Quelle lesen (ausschliesslich lesend)
# ---------------------------------------------------------------------------
def o11_laden(o11):
    d = {}
    d["stages"] = o11.kw("survey.stage", "search_read",
                         [[], ["id", "name", "sequence", "closed", "fold"]],
                         context=CTX11, order="sequence,id", limit=50)
    d["surveys"] = o11.kw("survey.survey", "search_read",
                          [[], ["id", "title", "description", "active", "stage_id", "quizz_mode",
                                "auth_required", "users_can_go_back", "is_closed", "color",
                                "email_template_id", "thank_you_message", "create_date",
                                "write_date", "create_uid", "write_uid"]],
                          context=CTX11_ALLE(), order="id", limit=500)
    d["pages"] = o11.kw("survey.page", "search_read",
                        [[], ["id", "title", "description", "survey_id", "sequence",
                              "create_date", "write_date", "create_uid", "write_uid"]],
                        context=CTX11, order="survey_id,sequence,id", limit=1000)
    d["questions"] = o11.kw("survey.question", "search_read",
                            [[], ["id", "question", "description", "page_id", "survey_id", "type",
                                  "sequence", "constr_mandatory", "constr_error_msg",
                                  "comments_allowed", "comments_message", "comment_count_as_answer",
                                  "validation_required", "validation_error_msg",
                                  "validation_min_float_value", "validation_max_float_value",
                                  "validation_min_date", "validation_max_date",
                                  "validation_length_min", "validation_length_max",
                                  "validation_email", "matrix_subtype",
                                  "create_date", "write_date", "create_uid", "write_uid"]],
                            context=CTX11, order="survey_id,sequence,id", limit=2000)
    d["labels"] = o11.kw("survey.label", "search_read",
                         [[], ["id", "value", "question_id", "question_id_2", "sequence",
                               "quizz_mark", "create_date", "write_date", "create_uid",
                               "write_uid"]],
                         context=CTX11, order="question_id,sequence,id", limit=2000)
    d["inputs"] = o11.kw("survey.user_input", "search_read",
                         [[], ["id", "survey_id", "state", "token", "email", "partner_id",
                               "test_entry", "quizz_score", "date_create", "deadline",
                               "last_displayed_page_id", "type", "create_date", "write_date",
                               "create_uid", "write_uid"]],
                         context=CTX11_ALLE(), order="id", limit=20000)
    d["lines"] = o11.kw("survey.user_input_line", "search_read",
                        [[], ["id", "user_input_id", "survey_id", "question_id", "page_id",
                              "answer_type", "skipped", "quizz_mark", "value_text",
                              "value_free_text", "value_number", "value_date", "value_suggested",
                              "value_suggested_row", "date_create", "create_date", "write_date",
                              "create_uid", "write_uid"]],
                        context=CTX11, order="user_input_id,id", limit=50000)
    return d


def CTX11_ALLE():
    return {"lang": "de_DE", "active_test": False}


# ---------------------------------------------------------------------------
# Zielbestand lesen
# ---------------------------------------------------------------------------
def ziel_laden(o18):
    ctx = CTX18_ALLE

    def ids_map(modell, zusatz=None):
        dom = [["itk_o11_id", "!=", False]]
        if zusatz:
            dom = [["itk_o11_id", "!=", False]] + zusatz
        ids = o18.kw(modell, "search", [dom], context=ctx, limit=50000)
        erg = {}
        for i in range(0, len(ids), 2000):
            for r in o18.kw(modell, "read", [ids[i:i + 2000], ["id", "itk_o11_id"]], context=ctx):
                if r.get("itk_o11_id"):
                    erg[r["itk_o11_id"]] = r["id"]
        return erg

    d = {
        "survey": ids_map("survey.survey"),
        # Seiten (O11 survey.page) und Fragen (O11 survey.question) tragen in Odoo 11
        # ueberlappende IDs (Seite 1 und Frage 1). Sie werden deshalb getrennt
        # gefuehrt und ueber is_page unterschieden - sonst ueberschreiben sie sich.
        "page": ids_map("survey.question", [["is_page", "=", True]]),
        "question": ids_map("survey.question", [["is_page", "=", False]]),
        "answer": ids_map("survey.question.answer"),
        "input": ids_map("survey.user_input"),
        "line": ids_map("survey.user_input.line"),
    }
    d["bestand"] = {
        m: o18.kw(m, "search_count", [[]], context=ctx)
        for m in ("survey.survey", "survey.question", "survey.question.answer",
                  "survey.user_input", "survey.user_input.line")
    }
    d["survey_ohne_anker"] = o18.kw("survey.survey", "search_read",
                                    [[["itk_o11_id", "=", False]], ["id", "title"]],
                                    context=ctx, limit=50)
    d["partner"] = {}
    pids = o18.kw("res.partner", "search", [[["itk_o11_id", "!=", False]]], context=ctx,
                  limit=30000)
    for i in range(0, len(pids), 2000):
        for r in o18.kw("res.partner", "read", [pids[i:i + 2000], ["id", "itk_o11_id"]],
                        context=ctx):
            if r.get("itk_o11_id"):
                d["partner"][r["itk_o11_id"]] = r["id"]
    d["user_login"] = {}
    d["user_name"] = {}
    for u in o18.kw("res.users", "search_read", [[], ["id", "login", "name"]], context=ctx,
                    limit=500):
        if u.get("login"):
            d["user_login"].setdefault(u["login"].lower(), u["id"])
        if u.get("name"):
            d["user_name"].setdefault(u["name"], u["id"])
    return d


# ---------------------------------------------------------------------------
# Satzbau je Modell
# ---------------------------------------------------------------------------
def survey_vals(s, stage_geschlossen, seiten_vorhanden):
    """Baut die Zielwerte einer Umfrage."""
    vals = {
        "title": s["title"] or "",
        "description": s["description"] or False,
        "active": bool(s["active"]) and not stage_geschlossen,
        "survey_type": "survey",
        "access_mode": "token" if s["auth_required"] else "public",
        "users_login_required": bool(s["auth_required"]),
        "users_can_go_back": bool(s["users_can_go_back"]),
        "scoring_type": "scoring_with_answers" if s["quizz_mode"] else "no_scoring",
        "questions_selection": "all",
        "questions_layout": "page_per_section" if seiten_vorhanden else "one_page",
        "color": s["color"] or 0,
        "itk_o11_id": s["id"],
    }
    return vals


def frage_vals(q, ziel_survey, ziel_page, ist_seite=False):
    typ = "text_box" if ist_seite else FRAGETYP.get(q.get("type") or "", "char_box")
    vals = {
        "survey_id": ziel_survey,
        "title": (q.get("title") or q.get("question") or ""),
        "sequence": q.get("sequence") or 0,
        "description": q.get("description") or False,
        "itk_o11_id": q["id"],
    }
    if ist_seite:
        vals["is_page"] = True
        return vals
    vals.update({
        "is_page": False,
        "question_type": typ,
        "page_id": ziel_page or False,
        "constr_mandatory": bool(q.get("constr_mandatory")),
        "constr_error_msg": q.get("constr_error_msg") or False,
        "comments_allowed": bool(q.get("comments_allowed")),
        "comments_message": q.get("comments_message") or False,
        "comment_count_as_answer": bool(q.get("comment_count_as_answer")),
        "validation_required": bool(q.get("validation_required")),
        "validation_error_msg": q.get("validation_error_msg") or False,
        "validation_email": bool(q.get("validation_email")),
        "validation_length_min": q.get("validation_length_min") or 0,
        "validation_length_max": q.get("validation_length_max") or 0,
        "matrix_subtype": q.get("matrix_subtype") or "simple",
    })
    typ11 = q.get("type") or ""
    if typ11 in ("textbox", "char_box"):
        pass
    elif typ11 in ("simple_choice", "multiple_choice", "matrix"):
        pass
    elif typ11 in ("numerical_box", "scale"):
        vals["validation_min_float_value"] = q.get("validation_min_float_value") or 0.0
        vals["validation_max_float_value"] = q.get("validation_max_float_value") or 0.0
    elif typ11 in ("date", "datetime"):
        vals["validation_min_date"] = q.get("validation_min_date") or False
        vals["validation_max_date"] = q.get("validation_max_date") or False
    return vals


def antwort_vals(l, ziel_frage, ziel_matrix):
    return {
        "question_id": ziel_frage,
        "matrix_question_id": ziel_matrix or False,
        "value": l["value"] or "",
        "sequence": l["sequence"] or 0,
        "answer_score": l["quizz_mark"] or 0.0,
        "itk_o11_id": l["id"],
    }


def input_vals(i, ziel_survey, ziel_page, ziel_partner, ende):
    return {
        "survey_id": ziel_survey,
        "state": "done" if i["state"] == "done" else "new",
        "test_entry": bool(i["test_entry"]),
        "access_token": i["token"] or False,
        "email": i["email"] or False,
        "partner_id": ziel_partner or False,
        "start_datetime": i["date_create"] or False,
        "end_datetime": ende or False,
        "deadline": i["deadline"] or False,
        "last_displayed_page_id": ziel_page or False,
        "itk_o11_id": i["id"],
    }


def zeile_vals(z, ziel_input, ziel_frage, ziel_page, ziel_antwort, ziel_matrix):
    typ = ANTWORTTYP.get(z["answer_type"] or "", False)
    vals = {
        "user_input_id": ziel_input,
        "question_id": ziel_frage,
        "page_id": ziel_page or False,
        "skipped": bool(z["skipped"]),
        "answer_type": typ,
        "answer_score": z["quizz_mark"] or 0.0,
        "itk_o11_id": z["id"],
    }
    if typ == "text_box":
        vals["value_text_box"] = z["value_text"] or z["value_free_text"] or False
    elif typ == "suggestion":
        vals["suggested_answer_id"] = ziel_antwort or False
        vals["matrix_row_id"] = ziel_matrix or False
    elif typ == "numerical_box":
        vals["value_numerical_box"] = z["value_number"] or 0.0
    elif typ in ("date", "datetime"):
        vals["value_date"] = z["value_date"] or False
    return vals


# ---------------------------------------------------------------------------
# Schreiben
# ---------------------------------------------------------------------------
def _anlegen(ziel, modell, posten, stat, fehler, schluessel, mapping, art):
    """Legt Datensaetze gebuendelt an; bei Batch-Fehler einzeln wiederholen."""
    neu = 0
    for i in range(0, len(posten), BATCH):
        teil = posten[i:i + BATCH]
        try:
            ids = ziel.kw(modell, "create", [[v for _, v in teil]])
            if not isinstance(ids, list):
                ids = [ids]
            if len(ids) != len(teil):
                raise RuntimeError("Batch lieferte %d IDs fuer %d Datensaetze"
                                   % (len(ids), len(teil)))
        except Exception:  # noqa: BLE001
            ids = []
            for r, v in teil:
                try:
                    erg = ziel.kw(modell, "create", [[v]])
                    ids.append(erg[0] if isinstance(erg, list) else erg)
                except Exception as exc:  # noqa: BLE001
                    stat["fehler"] += 1
                    fehler.append({"art": art, "o11_id": r["id"], "fehler": str(exc)[:300]})
                    ids.append(None)
        for (r, v), nid in zip(teil, ids):
            if not nid:
                continue
            schluessel[r["id"]] = nid
            stat["angelegt"] += 1
            neu += 1
            mapping["daten"].append({"art": art, "o11_id": r["id"], "o18_id": nid,
                                     "status": "angelegt"})
    return neu


def _frage_anlegen(ziel, sid, vals, ist_seite, stat, fehler, schluessel, mapping, art):
    """Legt Seite oder Frage ueber die O2M ``question_and_page_ids`` an.

    ``survey.question.create`` ist in Odoo 18.0.3.7 OHNE ``@api.model_create_multi``
    definiert. Der JSON-RPC Aufruf ``create`` scheitert deshalb mit
    ``TypeError: create() missing 1 required positional argument: 'vals_list'``
    (Produktfehler im Modul survey, nicht in diesem Skript). Die Umfrage-Maske
    legt Fragen und Seiten ebenfalls ueber die O2M an - dieser Weg funktioniert
    und wird hier verwendet. Anschliessend wird die neue ID ueber den Anker
    gelesen.
    """
    try:
        ziel.kw("survey.survey", "write", [[sid], {"question_and_page_ids": [(0, 0, vals)]}])
    except Exception as exc:  # noqa: BLE001
        stat["fehler"] += 1
        fehler.append({"art": art, "o11_id": vals["itk_o11_id"], "fehler": str(exc)[:300]})
        return None
    ids = ziel.kw("survey.question", "search",
                  [[["itk_o11_id", "=", vals["itk_o11_id"]], ["is_page", "=", bool(ist_seite)]]],
                  context=CTX18_ALLE, limit=1)
    if not ids:
        stat["fehler"] += 1
        fehler.append({"art": art, "o11_id": vals["itk_o11_id"],
                       "fehler": "nach dem Anlegen nicht auffindbar"})
        return None
    # Odoo verwirft beim Anlegen ueber die O2M je nach Instanz das Feld ``page_id``
    # (und setzt bei Seiten eine eigene Sequenz). Beides wird deshalb nach dem
    # Anlegen ausdruecklich gesetzt - sonst haengen Fragen ohne Abschnitt in der
    # Umfrage und die oeffentliche Seite zeigt sie nicht an.
    nachziehen = {"sequence": vals.get("sequence") or 0}
    if not ist_seite:
        nachziehen["page_id"] = vals.get("page_id") or False
    try:
        ziel.kw("survey.question", "write", [[ids[0]], nachziehen])
    except Exception as exc:  # noqa: BLE001
        stat["fehler"] += 1
        fehler.append({"art": art, "o11_id": vals["itk_o11_id"],
                       "fehler": "Abschnitt/Reihenfolge nicht setzbar: %s" % str(exc)[:200]})
    schluessel[vals["itk_o11_id"]] = ids[0]
    stat["angelegt"] += 1
    mapping["daten"].append({"art": art, "o11_id": vals["itk_o11_id"], "o18_id": ids[0],
                             "status": "angelegt"})
    return ids[0]


def _pflegen(ziel, modell, posten, ist_cache, stat, fehler, schluessel, mapping, art,
             vergleichsfelder):
    """Aktualisiert vorhandene Datensaetze, wenn Zielwerte abweichen."""
    for o11_id, zid, vals in posten:
        if not zid:
            continue
        ist = ist_cache.get(zid) or {}
        abweichend = {}
        for feld in vergleichsfelder:
            # Many2one kommt aus read() als [id, name] zurueck - verglichen wird die ID.
            ist_wert = ist.get(feld)
            if isinstance(ist_wert, (list, tuple)):
                ist_wert = m2o(ist_wert)
            if not _gleich(ist_wert, vals.get(feld)):
                abweichend[feld] = (ist_wert, vals.get(feld))
        if not abweichend:
            stat["uebersprungen"] += 1
            continue
        try:
            ziel.kw(modell, "write", [[zid], {k: v for k, v in vals.items()
                                              if k in abweichend and k != "itk_o11_id"}])
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"art": art, "o11_id": o11_id, "fehler": str(exc)[:300]})
            continue
        stat["aktualisiert"] += 1
        for feld in abweichend:
            stat["diff_" + feld] += 1
        mapping["daten"].append({"art": art, "o11_id": o11_id, "o18_id": zid,
                                 "status": "aktualisiert",
                                 "felder": sorted(abweichend)})


def _planen(z, modell, o11_id, zid, stat):
    """Trockenlauf: geplante Datensaetze als negativen Platzhalter vormerken.

    Ohne Platzhalter wuerden Seiten, Fragen, Teilnahmen und Antworten im
    Trockenlauf als "nicht zuordenbar" gezaehlt, obwohl sie im Schreiblauf
    ueber die neu angelegte Umfrage aufgeloest werden.
    """
    if zid:
        return zid
    z[modell][o11_id] = -o11_id
    stat["geplant"] += 1
    return -o11_id


def _ist_laden(o18, modell, ids, felder):
    ids = [i for i in ids if i]
    erg = {}
    for i in range(0, len(ids), 200):
        for r in o18.kw(modell, "read", [ids[i:i + 200], ["id"] + felder],
                        context=CTX18_ALLE):
            erg[r["id"]] = r
    return erg


def _zeitstempel(ziel, modell, quelle, uid_map, stat, fehler, seite=None):
    """Setzt create_date/write_date/create_uid/write_uid auf den Odoo-11-Stand.

    ``seite`` grenzt bei survey.question auf Seiten (True) oder Fragen (False) ein,
    weil Odoo-11-Seiten und -Fragen ueberlappende IDs haben.
    """
    dom = [["itk_o11_id", "!=", False]]
    if seite is not None:
        dom.append(["is_page", "=", bool(seite)])
    ids = ziel.kw(modell, "search", [dom], context=CTX18_ALLE, limit=50000)
    if not ids:
        return 0
    zeilen = []
    for i in range(0, len(ids), 500):
        for r in ziel.kw(modell, "read", [ids[i:i + 500],
                                          ["id", "itk_o11_id", "create_date", "write_date",
                                           "create_uid", "write_uid"]], context=CTX18_ALLE):
            q = quelle.get(r["itk_o11_id"])
            if not q:
                continue
            soll = ((q["create_date"] or "")[:19], (q["write_date"] or "")[:19],
                    uid_map.get(m2o(q["create_uid"])), uid_map.get(m2o(q["write_uid"])))
            ist = ((r["create_date"] or "")[:19], (r["write_date"] or "")[:19],
                   m2o(r["create_uid"]), m2o(r["write_uid"]))
            # Odoo setzt beim Anlegen den ausfuehrenden Benutzer; nur abweichende
            # Datums- oder Benutzerwerte werden nachgezogen.
            if ist[0] != soll[0] or ist[1] != soll[1] or (soll[2] and ist[2] != soll[2]) \
                    or (soll[3] and ist[3] != soll[3]):
                zeilen.append([r["id"], soll[0] or None, soll[1] or None, None,
                               soll[2], soll[3]])
    if not zeilen:
        return 0
    geschrieben = 0
    for i in range(0, len(zeilen), 300):
        try:
            geschrieben += ziel.kw("itk.migration.zeitstempel", "setze_zeitstempel",
                                   [modell, zeilen[i:i + 300]], context=CTX18,
                                   spalte="id") or 0
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"art": "zeitstempel %s" % modell, "o11_id": "-",
                           "fehler": str(exc)[:300]})
    return geschrieben


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true",
                    help="Schreiblauf (Standard ist Trockenlauf)")
    ap.add_argument("--ich-habe-freigabe", action="store_true",
                    help="Bestaetigt die Freigabe durch Anna Maierhofer")
    ap.add_argument("--grenze", type=int, default=0, help="nur die ersten N Teilnahmen")
    ap.add_argument("--mapping", help="Pfad fuer den Mapping-Export (ausserhalb des Repos)")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2
    if os.environ.get("ITK_STACKDUMP"):
        import faulthandler
        faulthandler.dump_traceback_later(120, repeat=True)

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== Survey-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    q = o11_laden(o11)
    print("Odoo 11 gelesen: %d Umfragen, %d Seiten, %d Fragen, %d Antwortvorgaben, "
          "%d Teilnahmen, %d Antworten" % (
              len(q["surveys"]), len(q["pages"]), len(q["questions"]), len(q["labels"]),
              len(q["inputs"]), len(q["lines"])))
    print("  lade Zielbestand ...", flush=True)
    z = ziel_laden(ziel)
    print("  Zielbestand: %s" % ", ".join("%s %d" % (k, v)
                                         for k, v in sorted(z["bestand"].items())), flush=True)
    if z["survey_ohne_anker"]:
        print("  HINWEIS: %d Umfrage(n) ohne Migrationsanker bereits im Ziel vorhanden: %s"
              % (len(z["survey_ohne_anker"]),
                 ", ".join(str(x["id"]) for x in z["survey_ohne_anker"])))

    stat = Counter()
    fehler = []
    sonderfaelle = []
    mapping = {"umfragen": [], "daten": [], "sonderfaelle": []}
    geschlossen = {s["id"] for s in q["stages"] if s["closed"]}
    stufe_je_survey = {s["id"]: m2o(s["stage_id"]) for s in q["surveys"]}
    seiten_je_survey = Counter(m2o(p["survey_id"]) for p in q["pages"])
    fragen_seite = {q_["id"]: m2o(q_["page_id"]) for q_ in q["questions"]}
    antworten_je_frage = Counter(m2o(l["question_id"]) for l in q["labels"])
    zeilen_je_input = Counter(m2o(z_["user_input_id"]) for z_ in q["lines"])

    # ------------------------------------------------------------------ Umfragen
    print("\n--- Umfragen ---")
    for s in q["surveys"]:
        geschlossen_s = stufe_je_survey.get(s["id"]) in geschlossen or bool(s["is_closed"])
        vals = survey_vals(s, geschlossen_s, seiten_je_survey.get(s["id"], 0) > 0)
        zid = z["survey"].get(s["id"])
        stufe = next((x["name"] for x in q["stages"] if x["id"] == stufe_je_survey.get(s["id"])),
                     "-")
        if geschlossen_s:
            stat["stufe_geschlossen_archiviert"] += 1
            sonderfaelle.append({"art": "survey.survey", "o11_id": s["id"],
                                 "grund": "Stufe %s -> archiviert" % stufe})
        if zid:
            stat["survey_vorhanden"] += 1
            mapping["umfragen"].append({"o11_id": s["id"], "o18_id": zid,
                                        "stufe_o11": stufe, "status": "vorhanden"})
        else:
            stat["survey_geplant"] += 1
            mapping["umfragen"].append({"o11_id": s["id"], "o18_id": "offen",
                                        "stufe_o11": stufe, "status": "anzulegen"})
        print("  O11 %s: Stufe %s -> %s, Umfrage %s"
              % (s["id"], stufe, "archiviert" if geschlossen_s else "aktiv",
                 "vorhanden" if zid else "wird angelegt"))

    if not args.ausfuehren:
        for s in q["surveys"]:
            _planen(z, "survey", s["id"], z["survey"].get(s["id"]), stat)
    if args.ausfuehren:
        neu, bestehend = [], []
        for s in q["surveys"]:
            geschlossen_s = stufe_je_survey.get(s["id"]) in geschlossen or bool(s["is_closed"])
            vals = survey_vals(s, geschlossen_s, seiten_je_survey.get(s["id"], 0) > 0)
            zid = z["survey"].get(s["id"])
            (bestehend if zid else neu).append((s, zid, vals))
        if neu:
            _anlegen(ziel, "survey.survey", [(r, v) for r, _, v in neu], stat, fehler,
                     z["survey"], mapping, "survey.survey")
        if bestehend:
            felder = ["title", "description", "active", "survey_type", "access_mode",
                      "users_login_required", "users_can_go_back", "scoring_type",
                      "questions_selection", "questions_layout", "color"]
            cache = _ist_laden(ziel, "survey.survey", [zid for _, zid, _ in bestehend], felder)
            # Fragen/Seiten entstehen erst danach - questions_layout wird zum Schluss gesetzt.
            _pflegen(ziel, "survey.survey",
                     [(r["id"], zid, {k: v for k, v in v_.items()
                                      if k in felder}) for r, zid, v_ in bestehend],
                     cache, stat, fehler, z["survey"], mapping, "survey.survey", felder)

    # --------------------------------------------------------------------- Seiten
    print("\n--- Seiten (Odoo 18: Frage mit is_page=True) ---")
    seiten_posten = []
    for p in q["pages"]:
        sid = z["survey"].get(m2o(p["survey_id"]))
        if not sid:
            stat["seite_ohne_umfrage"] += 1
            sonderfaelle.append({"art": "survey.page", "o11_id": p["id"],
                                 "grund": "Umfrage fehlt"})
            continue
        vals = frage_vals(p, sid, None, ist_seite=True)
        zid = z["page"].get(p["id"])
        seiten_posten.append((p, zid, vals))
    if not args.ausfuehren:
        for r, zid, v in seiten_posten:
            _planen(z, "page", r["id"], zid, stat)
    if args.ausfuehren:
        neu = [(r, v) for r, zid, v in seiten_posten if not zid]
        alt = [(r["id"], zid, v) for r, zid, v in seiten_posten if zid]
        for r, v in neu:
            _frage_anlegen(ziel, v["survey_id"], v, True, stat, fehler, z["page"], mapping,
                           "survey.page")
        if alt:
            felder = ["title", "sequence", "description", "is_page"]
            cache = _ist_laden(ziel, "survey.question", [zid for _, zid, _ in alt], felder)
            _pflegen(ziel, "survey.question", alt, cache, stat, fehler, z["page"],
                     mapping, "survey.page", felder)
    print("  %d Seiten, %d bereits vorhanden" % (
        len(seiten_posten), sum(1 for _, zid, _ in seiten_posten if zid and zid > 0)))

    # -------------------------------------------------------------------- Fragen
    print("\n--- Fragen ---")
    fragen_posten = []
    for f in q["questions"]:
        sid = z["survey"].get(m2o(f["survey_id"]))
        pid = z["page"].get(m2o(f["page_id"]))
        if not sid:
            stat["frage_ohne_umfrage"] += 1
            sonderfaelle.append({"art": "survey.question", "o11_id": f["id"],
                                 "grund": "Umfrage fehlt"})
            continue
        if m2o(f["page_id"]) and not pid:
            stat["frage_ohne_seite"] += 1
            sonderfaelle.append({"art": "survey.question", "o11_id": f["id"],
                                 "grund": "Seite fehlt"})
            continue
        if (f.get("type") or "") not in FRAGETYP:
            stat["fragetyp_unbekannt"] += 1
            sonderfaelle.append({"art": "survey.question", "o11_id": f["id"],
                                 "grund": "Fragetyp %s" % f.get("type")})
            continue
        vals = frage_vals(f, sid, pid)
        zid = z["question"].get(f["id"])
        fragen_posten.append((f, zid, vals))
    if not args.ausfuehren:
        for r, zid, v in fragen_posten:
            _planen(z, "question", r["id"], zid, stat)
    if args.ausfuehren:
        neu = [(r, v) for r, zid, v in fragen_posten if not zid]
        alt = [(r["id"], zid, v) for r, zid, v in fragen_posten if zid]
        for r, v in neu:
            _frage_anlegen(ziel, v["survey_id"], v, False, stat, fehler, z["question"], mapping,
                           "survey.question")
        if alt:
            felder = ["title", "sequence", "description", "is_page", "question_type", "page_id",
                      "constr_mandatory", "constr_error_msg", "comments_allowed",
                      "comments_message", "comment_count_as_answer", "validation_required",
                      "validation_error_msg", "validation_email", "validation_length_min",
                      "validation_length_max", "validation_min_float_value",
                      "validation_max_float_value", "validation_min_date", "validation_max_date"]
            cache = _ist_laden(ziel, "survey.question", [zid for _, zid, _ in alt], felder)
            _pflegen(ziel, "survey.question", alt, cache, stat, fehler, z["question"],
                     mapping, "survey.question", felder)
    typen = Counter(FRAGETYP.get(f["type"], f["type"]) for f, _, _ in fragen_posten)
    print("  %d Fragen: %s" % (len(fragen_posten),
                               ", ".join("%s=%d" % kv for kv in sorted(typen.items())) or "-"))

    # --------------------------------------------------------------- Antwortvorgaben
    print("\n--- Antwortvorgaben ---")
    antwort_posten = []
    for l in q["labels"]:
        fid = z["question"].get(m2o(l["question_id"]))
        mid = z["question"].get(m2o(l["question_id_2"])) if l["question_id_2"] else None
        if not fid:
            stat["antwort_ohne_frage"] += 1
            sonderfaelle.append({"art": "survey.label", "o11_id": l["id"],
                                 "grund": "Frage fehlt"})
            continue
        vals = antwort_vals(l, fid, mid)
        zid = z["answer"].get(l["id"])
        antwort_posten.append((l, zid, vals))
    if not args.ausfuehren:
        for r, zid, v in antwort_posten:
            _planen(z, "answer", r["id"], zid, stat)
    if args.ausfuehren:
        neu = [(r, v) for r, zid, v in antwort_posten if not zid]
        alt = [(r["id"], zid, v) for r, zid, v in antwort_posten if zid]
        if neu:
            _anlegen(ziel, "survey.question.answer", neu, stat, fehler, z["answer"], mapping,
                     "survey.label")
        if alt:
            felder = ["value", "sequence", "answer_score", "matrix_question_id", "question_id"]
            cache = _ist_laden(ziel, "survey.question.answer", [zid for _, zid, _ in alt], felder)
            _pflegen(ziel, "survey.question.answer", alt, cache, stat, fehler, z["answer"],
                     mapping, "survey.label", felder)
    print("  %d Antwortvorgaben, %d bereits vorhanden" % (
        len(antwort_posten), sum(1 for _, zid, _ in antwort_posten if zid and zid > 0)))

    # ---------------------------------------------------------------- Teilnahmen
    print("\n--- Teilnahmen ---")
    inputs = q["inputs"][:args.grenze] if args.grenze else q["inputs"]
    ende_je_input = {}
    for z_ in q["lines"]:
        iid = m2o(z_["user_input_id"])
        d = (z_["date_create"] or "")[:19]
        if d and (iid not in ende_je_input or d > ende_je_input[iid]):
            ende_je_input[iid] = d
    input_posten = []
    for i in inputs:
        sid = z["survey"].get(m2o(i["survey_id"]))
        if not sid:
            stat["input_ohne_umfrage"] += 1
            sonderfaelle.append({"art": "survey.user_input", "o11_id": i["id"],
                                 "grund": "Umfrage fehlt"})
            continue
        pid = z["page"].get(m2o(i["last_displayed_page_id"]))
        partner = z["partner"].get(m2o(i["partner_id"])) if i["partner_id"] else None
        if i["partner_id"] and not partner:
            stat["input_partner_fehlend"] += 1
            sonderfaelle.append({"art": "survey.user_input", "o11_id": i["id"],
                                 "grund": "Partner fehlt"})
        ende = ende_je_input.get(i["id"]) if i["state"] == "done" else None
        vals = input_vals(i, sid, pid, partner, ende)
        zid = z["input"].get(i["id"])
        input_posten.append((i, zid, vals))
    if not args.ausfuehren:
        for r, zid, v in input_posten:
            _planen(z, "input", r["id"], zid, stat)
    if args.ausfuehren:
        neu = [(r, v) for r, zid, v in input_posten if not zid]
        alt = [(r["id"], zid, v) for r, zid, v in input_posten if zid]
        if neu:
            _anlegen(ziel, "survey.user_input", neu, stat, fehler, z["input"], mapping,
                     "survey.user_input")
        if alt:
            felder = ["survey_id", "state", "test_entry", "access_token", "email", "partner_id",
                      "start_datetime", "end_datetime", "deadline", "last_displayed_page_id"]
            cache = _ist_laden(ziel, "survey.user_input", [zid for _, zid, _ in alt], felder)
            _pflegen(ziel, "survey.user_input", alt, cache, stat, fehler, z["input"], mapping,
                     "survey.user_input", felder)
    zustand = Counter(i["state"] for i, _, _ in input_posten)
    print("  %d Teilnahmen (%s), %d bereits vorhanden" % (
        len(input_posten), ", ".join("%s=%d" % kv for kv in sorted(zustand.items())),
        sum(1 for _, zid, _ in input_posten if zid and zid > 0)))

    # ---------------------------------------------------------------- Antworten
    print("\n--- Antworten ---")
    gueltige_inputs = {i["id"] for i in inputs}
    zeilen_posten = []
    for z_ in q["lines"]:
        iid = m2o(z_["user_input_id"])
        if iid not in gueltige_inputs:
            stat["zeile_ohne_teilnahme"] += 1
            continue
        zu = z["input"].get(iid)
        frage = z["question"].get(m2o(z_["question_id"]))
        page = z["page"].get(m2o(z_["page_id"]))
        antwort = z["answer"].get(m2o(z_["value_suggested"])) if z_["value_suggested"] else None
        # value_suggested_row ist eine Matrixzeile, also eine Antwortvorgabe (survey.label).
        matrix = z["answer"].get(m2o(z_["value_suggested_row"])) if z_["value_suggested_row"] \
            else None
        if not (zu and frage):
            stat["zeile_nicht_zugeordnet"] += 1
            sonderfaelle.append({"art": "survey.user_input_line", "o11_id": z_["id"],
                                 "grund": "Teilnahme oder Frage fehlt"})
            continue
        vals = zeile_vals(z_, zu, frage, page, antwort, matrix)
        zid = z["line"].get(z_["id"])
        zeilen_posten.append((z_, zid, vals))
    if not args.ausfuehren:
        for r, zid, v in zeilen_posten:
            _planen(z, "line", r["id"], zid, stat)
    if args.ausfuehren:
        neu = [(r, v) for r, zid, v in zeilen_posten if not zid]
        alt = [(r["id"], zid, v) for r, zid, v in zeilen_posten if zid]
        if neu:
            _anlegen(ziel, "survey.user_input.line", neu, stat, fehler, z["line"], mapping,
                     "survey.user_input_line")
        if alt:
            felder = ["user_input_id", "question_id", "page_id", "skipped", "answer_type",
                      "answer_score", "value_text_box", "suggested_answer_id", "matrix_row_id",
                      "value_numerical_box", "value_date"]
            cache = _ist_laden(ziel, "survey.user_input.line", [zid for _, zid, _ in alt], felder)
            _pflegen(ziel, "survey.user_input.line", alt, cache, stat, fehler, z["line"],
                     mapping, "survey.user_input_line", felder)
    print("  %d Antworten, %d bereits vorhanden" % (
        len(zeilen_posten), sum(1 for _, zid, _ in zeilen_posten if zid and zid > 0)))

    # ------------------------------------------------- Fragen ohne Antworten/leer
    for i, _, _ in input_posten:
        if zeilen_je_input.get(i["id"], 0) == 0:
            stat["teilnahme_ohne_antwort"] += 1
    for f, _, _ in fragen_posten:
        if antworten_je_frage.get(f["id"], 0) == 0 and FRAGETYP.get(f["type"]) in (
                "simple_choice", "multiple_choice", "matrix", "scale"):
            stat["frage_ohne_vorgabe"] += 1

    # -------------------------------------------------------------- Zeitstempel
    if args.ausfuehren:
        print("\n--- Zeitstempel (Erstellungs-/Bearbeitungsdatum) ---")
        uid_map = {}
        for u in {m2o(r["create_uid"]) for r in
                  q["surveys"] + q["pages"] + q["questions"] + q["labels"] + q["inputs"]
                  + q["lines"] if r.get("create_uid")} | \
                 {m2o(r["write_uid"]) for r in
                  q["surveys"] + q["pages"] + q["questions"] + q["labels"] + q["inputs"]
                  + q["lines"] if r.get("write_uid")}:
            if not u:
                continue
            daten = o11.kw("res.users", "read", [[u], ["login", "name"]], context=CTX11)
            if not daten:
                continue
            login = (daten[0].get("login") or "").lower()
            uid_map[u] = z["user_login"].get(login) or z["user_name"].get(daten[0].get("name"))
        # survey.question traegt Seiten UND Fragen - getrennt nach is_page, weil die
        # Odoo-11-IDs ueberlappen (Seite 1 und Frage 1).
        for modell, quelle, seite in (
                ("survey.survey", {r["id"]: r for r in q["surveys"]}, None),
                ("survey.question", {r["id"]: r for r in q["pages"]}, True),
                ("survey.question", {r["id"]: r for r in q["questions"]}, False),
                ("survey.question.answer", {r["id"]: r for r in q["labels"]}, None),
                ("survey.user_input", {r["id"]: r for r in q["inputs"]}, None),
                ("survey.user_input.line", {r["id"]: r for r in q["lines"]}, None)):
            anzahl = _zeitstempel(ziel, modell, quelle, uid_map, stat, fehler, seite)
            stat["zeitstempel_%s" % modell] = stat.get("zeitstempel_%s" % modell, 0) + anzahl
            print("  %-28s %s%d Zeilen nachgezogen"
                  % (modell, "" if seite is None else ("Seiten " if seite else "Fragen "), anzahl))

    # ------------------------------------------------------------------ Abschluss
    if args.mapping:
        mapping["sonderfaelle"] = sonderfaelle
        with open(args.mapping, "w", encoding="utf-8") as fh:
            json.dump(mapping, fh, ensure_ascii=False, indent=1)
        print("\nMapping geschrieben: %s (%d Umfragen, %d Datensaetze, %d Sonderfaelle)"
              % (args.mapping, len(mapping["umfragen"]), len(mapping["daten"]),
                 len(sonderfaelle)))

    doppelt = 0
    if args.ausfuehren:
        for modell in ("survey.survey", "survey.question", "survey.question.answer",
                       "survey.user_input", "survey.user_input.line"):
            felder = ["id", "itk_o11_id"]
            if modell == "survey.question":
                felder.append("is_page")
            rows = ziel.kw(modell, "search_read", [[["itk_o11_id", "!=", False]], felder],
                           context=CTX18_ALLE, limit=50000)
            # Seiten und Fragen haben eigene O11-IDs, die sich ueberlappen - der
            # Schluessel ist deshalb (is_page, itk_o11_id).
            schluessel = [(bool(r.get("is_page")), r["itk_o11_id"]) if modell == "survey.question"
                          else r["itk_o11_id"] for r in rows]
            zaehler = Counter(schluessel)
            doppelt += sum(v - 1 for v in zaehler.values() if v > 1)
        stat["bestand_nachher"] = {m: ziel.kw(m, "search_count", [[]], context=CTX18_ALLE)
                                  for m in ("survey.survey", "survey.question",
                                            "survey.question.answer", "survey.user_input",
                                            "survey.user_input.line")}

    print()
    print("--- Zusammenfassung (%s) ---" % ("SCHREIBEN" if args.ausfuehren else "TROCKENLAUF"))
    print("gelesen ..................... %d Umfragen, %d Seiten, %d Fragen, %d Vorgaben, "
          "%d Teilnahmen, %d Antworten" % (
              len(q["surveys"]), len(q["pages"]), len(q["questions"]), len(q["labels"]),
              len(inputs), len(q["lines"])))
    print("erkannt (bereits vorhanden) . %d" % stat["survey_vorhanden"])
    print("angelegt .................... %d" % stat["angelegt"])
    print("aktualisiert ................ %d" % stat["aktualisiert"])
    print("uebersprungen ............... %d" % stat["uebersprungen"])
    if not args.ausfuehren:
        print("wuerde anlegen .............. %d" % stat["geplant"])
    print("nicht zuordenbar ............ %d" % (
        stat["seite_ohne_umfrage"] + stat["frage_ohne_umfrage"] + stat["frage_ohne_seite"] +
        stat["antwort_ohne_frage"] + stat["input_ohne_umfrage"] + stat["input_partner_fehlend"] +
        stat["zeile_ohne_teilnahme"] + stat["zeile_nicht_zugeordnet"] +
        stat["fragetyp_unbekannt"]))
    print("Fehler ...................... %d" % stat["fehler"])
    print("Dubletten ................... %d" % doppelt)
    print("Stufe 'Geschlossen' -> archiviert: %d" % stat["stufe_geschlossen_archiviert"])
    print("Teilnahmen ohne Antwortzeile  %d (fachlich: angefangen, nicht beantwortet)"
          % stat["teilnahme_ohne_antwort"])
    print("Auswahlfragen ohne Vorgabe .. %d" % stat["frage_ohne_vorgabe"])
    if args.ausfuehren:
        print("Bestand nachher ............. %s" % ", ".join(
            "%s %d" % kv for kv in sorted(stat["bestand_nachher"].items())))
    abweichende = {k: v for k, v in stat.items() if k.startswith("diff_")}
    if abweichende:
        print("Abweichende Felder: %s" % ", ".join("%s=%d" % (k[5:], v)
                                                  for k, v in sorted(abweichende.items())))
    if fehler:
        print("Fehlerdetails (max 10):")
        for f in fehler[:10]:
            print("  %s o11 %s: %s" % (f["art"], f["o11_id"], f["fehler"]))
    if sonderfaelle:
        print("Sonderfaelle: %d (Details in der Mapping-Datei/Doku)" % len(sonderfaelle))
    return 0 if stat["fehler"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
