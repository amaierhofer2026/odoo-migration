# -*- coding: utf-8 -*-
"""Valorisierung: Migrationsskript Odoo 11 -> Odoo 18.

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer
(Session 148, 19.11.2026). Quelle: Odoo 11 Prod ``ITK_V1_a`` - ausschliesslich
lesend. Ziel: Odoo 18 (lokal oder VM).

Umfang (frisch gemessen am 19.11.2026, read-only):
- itk_valorisierung.valorisierung   10 Hinweise (2019 bis 2026), alle mit Text
- account.invoice.valorisierung_id   4.216 Rechnungen mit Hinweis

Die zehn Hinweise existieren in Odoo 18 bereits als Modul-Daten
(``valorisierung_o11_1`` bis ``_10``, ``noupdate="1"``) - aber **ohne
Beschreibungstext**. Das Skript ergaenzt den Text, setzt den Anker
``itk_o11_id`` und zieht Erstell-/Bearbeitungsdatum nach. Es legt keinen Satz
neu an, solange die Modul-Daten vorhanden sind.

Rechnungsverknuepfung: Die Rechnungen selbst sind in Odoo 18 noch nicht migriert
(Bereich Abrechnung). Das Skript ordnet jede Odoo-18-Rechnung mit ``itk_o11_id``
zu, deren Odoo-11-Gegenstueck einen Hinweis traegt, und weist die offenen Faelle
aus. Es wird nichts geraten.

Idempotenz: Anker ``itk_o11_id`` (Modul itk_migration_keys), zusaetzlich die
XML-ID ``itk_valorisierung.valorisierung_o11_<id>`` und der Name als Fallback.

Datenschutz: Es werden keine personenbezogenen Inhalte ausgegeben. Die Texte der
Hinweise sind fachliche Stammdaten ohne Personenbezug.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/valorisierung_migration.py --instanz lokal
    python scripts/migration/valorisierung_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
    python scripts/migration/valorisierung_migration.py --instanz vm --mapping "%LOCALAPPDATA%\\Temp\\valo_mapping.json"
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

CTX11 = {"lang": "de_DE", "active_test": False}
CTX18 = {"lang": "de_DE", "active_test": False}
MODELL = "itk_valorisierung.valorisierung"

# Verbindliche Benutzerzuordnung (wie im CRM): Der Odoo-11-Benutzer "admin"
# (Anzeigename "Administrator") ist das bestehende Odoo-18-Konto "Administrator"
# mit Login anna.maierhofer@it-kommunal.at. Das Konto bleibt unveraendert.
BENUTZER_MAPPING = {
    "admin": "anna.maierhofer@it-kommunal.at",
}


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


def o11_laden(o11):
    d = {}
    d["saetze"] = o11.kw(MODELL, "search_read",
                         [[], ["id", "name", "description", "seq", "create_date", "write_date",
                               "create_uid", "write_uid"]],
                         context=CTX11, order="id", limit=500)
    d["nutzung"] = {}
    for g in o11.kw("account.invoice", "read_group",
                    [[["valorisierung_id", "!=", False]], ["valorisierung_id"],
                     ["valorisierung_id"]], context=CTX11):
        d["nutzung"][m2o(g.get("valorisierung_id"))] = g.get("valorisierung_id_count", 0)
    d["rechnungen_mit_hinweis"] = o11.kw("account.invoice", "search_count",
                                         [[["valorisierung_id", "!=", False]]], context=CTX11)
    d["rechnungen_gesamt"] = o11.kw("account.invoice", "search_count", [[]], context=CTX11)
    d["benutzer"] = {}
    for u in {m2o(r["create_uid"]) for r in d["saetze"]} | {m2o(r["write_uid"]) for r in d["saetze"]}:
        if u:
            info = o11.kw("res.users", "read", [[u], ["login", "name"]], context=CTX11)
            if info:
                d["benutzer"][u] = info[0]
    return d


def ziel_laden(o18):
    ctx = CTX18
    d = {"saetze": o18.kw(MODELL, "search_read",
                          [[], ["id", "itk_o11_id", "name", "description", "seq", "create_date",
                                "write_date", "create_uid"]], context=ctx, order="id", limit=500)}
    d["xmlid"] = {}
    for x in o18.kw("ir.model.data", "search_read",
                    [[["module", "=", "itk_valorisierung"], ["model", "=", MODELL]],
                     ["name", "res_id"]], limit=500):
        d["xmlid"][x["name"]] = x["res_id"]
    # Rechnungen sind in Odoo 18 noch nicht migriert; itk_migration_keys fuehrt den
    # Anker dort (noch) nicht. Das Skript prueft das Feld, statt es vorauszusetzen.
    d["rechnungen"] = {}
    d["rechnungen_anker"] = "itk_o11_id" in o18.kw("account.move", "fields_get", [[], ["type"]])
    if d["rechnungen_anker"]:
        ids = o18.kw("account.move", "search", [[["itk_o11_id", "!=", False]]], context=ctx,
                     limit=50000)
        for i in range(0, len(ids), 1000):
            for r in o18.kw("account.move", "read", [ids[i:i + 1000], ["id", "itk_o11_id",
                                                                       "valorisierung_id"]],
                            context=ctx):
                d["rechnungen"][r["itk_o11_id"]] = r
    d["user_login"] = {}
    d["user_name"] = {}
    for u in o18.kw("res.users", "search_read", [[], ["id", "login", "name"]], context=ctx,
                    limit=500):
        if u.get("login"):
            d["user_login"].setdefault(u["login"].lower(), u["id"])
        if u.get("name"):
            d["user_name"].setdefault(u["name"], u["id"])
    return d


def rechnungen_nachziehen(o11, ziel, ausfuehren, stat, fehler, sonderfaelle, mapping):
    """Nachlauf: Valorisierungs-Rechnungsbeziehungen aus Odoo 11 nachziehen.

    Verbindliche externe Abhaengigkeit: Die 4.216 Odoo-11-Rechnungen mit
    Valorisierungshinweis koennen erst zugeordnet werden, wenn der Bereich Abrechnung
    migriert ist und ``account.move`` den Anker ``itk_o11_id`` traegt. Dieser Nachlauf
    ist dafuer vorgesehen und mehrfach ausfuehrbar:

    1. liest alle Odoo-11-Rechnungen mit Hinweis (nur lesend),
    2. ermittelt die Odoo-18-Rechnung ueber ``account.move.itk_o11_id``,
    3. setzt ``valorisierung_id`` auf den Satz mit passendem ``itk_o11_id``,
    4. laesst bereits korrekte Beziehungen unveraendert (idempotent),
    5. meldet nicht zuordenbare Rechnungen einzeln (technische IDs, keine Inhalte),
    6. prueft danach Anzahl und Verteilung gegen Odoo 11.

    Der technische Testdatensatz "VAL-OK" (ohne ``itk_o11_id``) kann nie Ziel sein,
    weil das Ziel ausschliesslich ueber den Odoo-11-Anker bestimmt wird.
    """
    print("\n=== Nachlauf Rechnungsverknuepfung ===")
    anker_da = "itk_o11_id" in ziel.kw("account.move", "fields_get",
                                       [[], ["type"]])
    if not anker_da:
        print("  account.move fuehrt noch keinen Anker itk_o11_id - der Bereich "
              "Abrechnung ist nicht migriert.")
        print("  Offen: %d Rechnungsverknuepfungen. Nach der Abrechnungsmigration "
              "diesen Lauf mit --nachlauf-rechnungen erneut starten."
              % stat.get("rechnungen_mit_hinweis", 0))
        stat["rechnung_offen"] = stat.get("rechnungen_mit_hinweis", 0)
        sonderfaelle.append({"art": "rechnung_nachlauf",
                             "grund": "Anker itk_o11_id auf account.move fehlt",
                             "offen": stat.get("rechnung_offen")})
        return

    # 1) Odoo 11: Rechnungen mit Hinweis lesen (nur lesend)
    ids11 = o11.kw("account.invoice", "search", [[["valorisierung_id", "!=", False]]],
                   context=CTX11, limit=200000)
    bezug11 = {}
    for i in range(0, len(ids11), 1000):
        for r in o11.kw("account.invoice", "read",
                        [ids11[i:i + 1000], ["id", "valorisierung_id"]], context=CTX11):
            bezug11[r["id"]] = m2o(r["valorisierung_id"])
    print("  Odoo 11: %d Rechnungen mit Hinweis" % len(bezug11))

    # 2) Zielsaetze je Odoo-11-Id
    ziel_valo = {}
    for v in ziel.kw(MODELL, "search_read", [[["itk_o11_id", "!=", False]],
                                            ["id", "itk_o11_id"]], context=CTX18, limit=1000):
        ziel_valo[v["itk_o11_id"]] = v["id"]

    # 3) Odoo 18: Rechnungen mit Anker
    ids18 = ziel.kw("account.move", "search", [[["itk_o11_id", "!=", False]]],
                    context=CTX18, limit=200000)
    rechnung18 = {}
    for i in range(0, len(ids18), 1000):
        for r in ziel.kw("account.move", "read",
                         [ids18[i:i + 1000], ["id", "itk_o11_id", "valorisierung_id"]],
                         context=CTX18):
            rechnung18[r["itk_o11_id"]] = r
    print("  Odoo 18: %d Rechnungen mit Anker" % len(rechnung18))

    # 4) Zuordnung bestimmen
    setzen = {}          # ziel_valorisierung -> [move_ids]
    korrigieren = {}
    korrekt = nicht_zuordenbar = ohne_zielsatz = 0
    beispiele = []
    for o11_id, valo11 in bezug11.items():
        r = rechnung18.get(o11_id)
        if not r:
            nicht_zuordenbar += 1
            if len(beispiele) < 20:
                beispiele.append(o11_id)
            continue
        zv = ziel_valo.get(valo11)
        if not zv:
            ohne_zielsatz += 1
            continue
        ist = m2o(r.get("valorisierung_id"))
        if ist == zv:
            korrekt += 1
            continue
        setzen.setdefault(zv, []).append(r["id"])
        if ist:
            korrigieren[zv] = korrigieren.get(zv, 0) + 1

    zu_setzen = sum(len(v) for v in setzen.values())
    print("  bereits korrekt: %d | zu setzen: %d (davon Korrektur: %d) | "
          "nicht zuordenbar: %d | ohne Zielhinweis: %d"
          % (korrekt, zu_setzen, sum(korrigieren.values()), nicht_zuordenbar, ohne_zielsatz))
    stat["rechnung_korrekt"] = korrekt
    stat["rechnung_zu_setzen"] = zu_setzen
    stat["rechnung_korrigiert"] = sum(korrigieren.values())
    stat["rechnung_nicht_zuordenbar"] = nicht_zuordenbar
    stat["rechnung_ohne_zielsatz"] = ohne_zielsatz

    if nicht_zuordenbar:
        sonderfaelle.append({"art": "rechnung_nicht_zuordenbar",
                             "anzahl": nicht_zuordenbar,
                             "o11_ids_beispiele": beispiele})
        print("  Nicht zuordenbar (keine Odoo-18-Rechnung mit diesem Anker): %d, "
              "technische Beispiele: %s" % (nicht_zuordenbar, beispiele[:5]))
    if ohne_zielsatz:
        sonderfaelle.append({"art": "rechnung_ohne_zielsatz", "anzahl": ohne_zielsatz})
        print("  Ohne Zielhinweis in Odoo 18 (Hinweis nicht migriert): %d" % ohne_zielsatz)

    # 5) Schreiben (nur geaenderte Beziehungen)
    if ausfuehren and zu_setzen:
        for zv, moves in setzen.items():
            for i in range(0, len(moves), 500):
                try:
                    ziel.kw("account.move", "write",
                            [moves[i:i + 500], {"valorisierung_id": zv}], context=CTX18)
                    stat["rechnung_gesetzt"] += len(moves[i:i + 500])
                except Exception as exc:  # noqa: BLE001
                    stat["fehler"] += 1
                    fehler.append({"art": "rechnung_write", "valorisierung": ziel_valo.get(zv),
                                   "anzahl": len(moves[i:i + 500]), "fehler": str(exc)[:300]})
        print("  gesetzt: %d Rechnungsbeziehungen" % stat["rechnung_gesetzt"])
    elif zu_setzen:
        print("  Trockenlauf: %d Beziehungen wuerden gesetzt." % zu_setzen)

    # 6) Nachpruefung gegen Odoo 11 (Anzahl und Verteilung)
    if not ausfuehren:
        print("  --- Nachpruefung uebersprungen (Trockenlauf schreibt nichts) ---")
        stat["rechnung_abweichungen"] = 0
        return
    print("  --- Nachpruefung ---")
    soll_verteilung = Counter()
    for o11_id, valo11 in bezug11.items():
        if o11_id in rechnung18:
            soll_verteilung[ziel_valo.get(valo11)] += 1
    ist_verteilung = Counter()
    ids_mit_anker = ziel.kw("account.move", "search", [[["itk_o11_id", "!=", False]]],
                            context=CTX18, limit=200000)
    for i in range(0, len(ids_mit_anker), 2000):
        for g in ziel.kw("account.move", "read_group",
                         [[["id", "in", ids_mit_anker[i:i + 2000]],
                           ["valorisierung_id", "!=", False]],
                          ["valorisierung_id"], ["valorisierung_id"]], context=CTX18):
            ist_verteilung[m2o(g.get("valorisierung_id"))] += g.get("valorisierung_id_count", 0)
    abweichungen = []
    for vz, soll in soll_verteilung.items():
        ist = ist_verteilung.get(vz, 0)
        if ist != soll:
            abweichungen.append({"valorisierung": vz, "soll": soll, "ist": ist})
    stat["rechnung_abweichungen"] = len(abweichungen)
    print("  Verteilung: %d Hinweise betroffen, %d Abweichungen"
          % (len(soll_verteilung), len(abweichungen)))
    for a in abweichungen[:10]:
        print("    Hinweis %s: soll %d, ist %d" % (a["valorisierung"], a["soll"], a["ist"]))
    if abweichungen:
        sonderfaelle.append({"art": "rechnung_verteilung", "abweichungen": abweichungen[:20]})
    mapping["rechnungen_nachlauf"] = {
        "o11_mit_hinweis": len(bezug11), "o18_mit_anker": len(rechnung18),
        "korrekt": korrekt, "zu_setzen": zu_setzen, "nicht_zuordenbar": nicht_zuordenbar,
        "ohne_zielsatz": ohne_zielsatz, "abweichungen": abweichungen[:20],
        "o11_ids_nicht_zuordenbar": beispiele}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true",
                    help="Schreiblauf (Standard ist Trockenlauf)")
    ap.add_argument("--ich-habe-freigabe", action="store_true",
                    help="Bestaetigt die Freigabe durch Anna Maierhofer")
    ap.add_argument("--nachlauf-rechnungen", action="store_true",
                    help="Nachlauf der Rechnungsverknuepfungen (nach der "
                         "Abrechnungsmigration; erwartet itk_o11_id auf account.move)")
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
    print("=== Valorisierungs-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    q = o11_laden(o11)
    print("Odoo 11 gelesen: %d Hinweise, %d von %d Rechnungen mit Hinweis"
          % (len(q["saetze"]), q["rechnungen_mit_hinweis"], q["rechnungen_gesamt"]))
    z = ziel_laden(ziel)
    print("  Zielbestand: %d Hinweise, %d Rechnungen mit Migrationsanker%s"
          % (len(z["saetze"]), len(z["rechnungen"]),
             "" if z["rechnungen_anker"] else " (account.move fuehrt keinen Anker)"))

    stat = Counter()
    fehler = []
    sonderfaelle = []
    mapping = {"saetze": [], "rechnungen": [], "sonderfaelle": []}

    def ziel_id(s):
        """Zuordnung: Anker, XML-ID, dann Name (getrimmt, eindeutig)."""
        for x in z["saetze"]:
            if x.get("itk_o11_id") == s["id"]:
                return x["id"], "anker"
        xid = z["xmlid"].get("valorisierung_o11_%d" % s["id"])
        if xid:
            return xid, "xmlid"
        name = (s["name"] or "").strip()
        treffer = [x["id"] for x in z["saetze"] if (x["name"] or "").strip() == name]
        if len(treffer) == 1:
            return treffer[0], "name"
        return None, "offen"

    # ------------------------------------------------------------------ Saetze
    print("\n--- Valorisierungshinweise ---")
    posten = []
    for s in q["saetze"]:
        zid, quelle = ziel_id(s)
        if not zid:
            stat["nicht_zuordenbar"] += 1
            sonderfaelle.append({"art": "valorisierung", "o11_id": s["id"],
                                 "grund": "kein Ziel (Name/XML-ID)"})
            print("  O11 %2d: NICHT ZUORDENBAR (%s)" % (s["id"], (s["name"] or "")[:40]))
            continue
        ist = next(x for x in z["saetze"] if x["id"] == zid)
        vals = {"description": s["description"] or False, "seq": s["seq"] or 0,
                "itk_o11_id": s["id"]}
        abweichend = {}
        if (ist.get("description") or "") != (s["description"] or ""):
            abweichend["description"] = True
        if (ist.get("seq") or 0) != (s["seq"] or 0):
            abweichend["seq"] = True
        if ist.get("itk_o11_id") != s["id"]:
            abweichend["itk_o11_id"] = True
        if not abweichend:
            stat["uebersprungen"] += 1
        else:
            posten.append((s, zid, vals, abweichend))
            stat["zu_aktualisieren"] += 1
        mapping["saetze"].append({"o11_id": s["id"], "o18_id": zid, "quelle": quelle,
                                  "name": (s["name"] or "").strip()[:40],
                                  "text_laenge": len(s["description"] or ""),
                                  "status": "aktuell" if not abweichend else "anzupassen",
                                  "felder": sorted(abweichend)})
        print("  O11 %2d -> O18 %2d (%s): %s"
              % (s["id"], zid, quelle,
                 "aktuell" if not abweichend else "Text/Anker ergaenzen"))

    if args.ausfuehren and posten:
        for s, zid, vals, abweichend in posten:
            try:
                ziel.kw(MODELL, "write", [[zid], {k: v for k, v in vals.items()
                                                  if k in abweichend}])
                stat["aktualisiert"] += 1
            except Exception as exc:  # noqa: BLE001
                stat["fehler"] += 1
                fehler.append({"o11_id": s["id"], "fehler": str(exc)[:300]})
    elif not args.ausfuehren:
        for s, zid, vals, abweichend in posten:
            stat["wuerde_aktualisieren"] += 1

    # -------------------------------------------------- Testdatensatz pruefen
    ohne_anker = [x for x in z["saetze"]
                  if not x.get("itk_o11_id") and x["id"] not in
                  {v for k, v in z["xmlid"].items() if k.startswith("valorisierung_o11_")}]
    for x in ohne_anker:
        # Tatsaechliche Nutzung zaehlen - unabhaengig vom Migrationsanker, denn die
        # Odoo-18-Rechnungen stammen derzeit aus der Abrechnungsrunde.
        genutzt = ziel.kw("account.move", "search_count",
                          [[["valorisierung_id", "=", x["id"]]]], context=CTX18)
        stat["satz_ohne_o11"] += 1
        sonderfaelle.append({"art": "valorisierung", "o18_id": x["id"],
                             "name": x["name"], "grund": "kein Odoo-11-Gegenstueck",
                             "rechnungen": genutzt})
        print("  Hinweis: Odoo-18-Satz %d '%s' ohne Odoo-11-Gegenstueck, von %d Rechnung(en) "
              "verwendet - nicht geloescht" % (x["id"], x["name"], genutzt))

    # ------------------------------------------------------ Rechnungsbezug
    print("\n--- Rechnungsverknuepfung ---")
    stat["rechnungen_mit_hinweis"] = q["rechnungen_mit_hinweis"]
    if args.nachlauf_rechnungen:
        rechnungen_nachziehen(o11, ziel, args.ausfuehren, stat, fehler, sonderfaelle, mapping)
    else:
        offen = 0
        for o11_id, r in z["rechnungen"].items():
            if o11_id in q["nutzung"]:
                if m2o(r.get("valorisierung_id")):
                    stat["rechnung_verbunden"] += 1
                else:
                    offen += 1
        offen += q["rechnungen_mit_hinweis"] - sum(
            1 for o11_id in z["rechnungen"] if o11_id in q["nutzung"])
        stat["rechnung_offen"] = offen
        print("  Odoo 11: %d Rechnungen mit Hinweis; Odoo 18: %d migrierte Rechnungen, "
              "%d davon verbunden, %d offen" % (q["rechnungen_mit_hinweis"],
                                                len(z["rechnungen"]),
                                                stat["rechnung_verbunden"], offen))
        if offen:
            print("  OFFENE EXTERNE ABHAENGIGKEIT: Rechnungen sind nicht migriert. "
                  "Nachlauf mit --nachlauf-rechnungen (siehe Doku Abschnitt 14).")
            sonderfaelle.append({"art": "rechnung", "grund": "Rechnungen nicht migriert",
                                 "offen": offen})

    # ------------------------------------------------------------ Zeitstempel
    if args.ausfuehren:
        print("\n--- Zeitstempel ---")
        ids = ziel.kw(MODELL, "search", [[["itk_o11_id", "!=", False]]], context=CTX18,
                      limit=500)
        soll = {s["id"]: s for s in q["saetze"]}
        zeilen = []
        for r in ziel.kw(MODELL, "read", [ids, ["id", "itk_o11_id", "create_date", "write_date",
                                                "create_uid"]], context=CTX18):
            s = soll.get(r["itk_o11_id"])
            if not s:
                continue
            uid_q = q["benutzer"].get(m2o(s["create_uid"])) or {}
            login = (uid_q.get("login") or "").lower()
            if login in BENUTZER_MAPPING:
                ziel_uid = z["user_login"].get(BENUTZER_MAPPING[login])
            else:
                ziel_uid = (z["user_login"].get(login)
                            or z["user_name"].get(uid_q.get("name")))
            # write_date mitpruefen: sonst bleiben fremde Schreibzugriffe unentdeckt.
            if ((r["create_date"] or "")[:19] != (s["create_date"] or "")[:19]
                    or (r["write_date"] or "")[:19] != (s["write_date"] or "")[:19]
                    or (ziel_uid and m2o(r["create_uid"]) != ziel_uid)):
                zeilen.append([r["id"], (s["create_date"] or "")[:19],
                               (s["write_date"] or "")[:19], None, ziel_uid,
                               ziel_uid])
        if zeilen:
            try:
                stat["zeitstempel"] = ziel.kw("itk.migration.zeitstempel", "setze_zeitstempel",
                                              [MODELL, zeilen], context=CTX18,
                                              spalte="id") or 0
            except Exception as exc:  # noqa: BLE001
                stat["fehler"] += 1
                fehler.append({"o11_id": "zeitstempel", "fehler": str(exc)[:300]})
        print("  %d Zeilen nachgezogen" % stat["zeitstempel"])

    # ------------------------------------------------------------- Abschluss
    if args.mapping:
        mapping["sonderfaelle"] = sonderfaelle
        with open(args.mapping, "w", encoding="utf-8") as fh:
            json.dump(mapping, fh, ensure_ascii=False, indent=1)
        print("\nMapping geschrieben: %s (%d Saetze)" % (args.mapping, len(mapping["saetze"])))

    doppelt = 0
    if args.ausfuehren:
        rows = ziel.kw(MODELL, "search_read", [[["itk_o11_id", "!=", False]],
                                              ["id", "itk_o11_id"]], context=CTX18, limit=1000)
        zaehler = Counter(r["itk_o11_id"] for r in rows)
        doppelt = sum(v - 1 for v in zaehler.values() if v > 1)
        stat["bestand_nachher"] = ziel.kw(MODELL, "search_count", [[]], context=CTX18)

    print()
    print("--- Zusammenfassung (%s) ---" % ("SCHREIBEN" if args.ausfuehren else "TROCKENLAUF"))
    print("gelesen ..................... %d" % len(q["saetze"]))
    print("angelegt .................... %d" % stat["angelegt"])
    print("aktualisiert ................ %d" % stat["aktualisiert"])
    print("uebersprungen ............... %d" % stat["uebersprungen"])
    print("archiviert .................. %d" % stat["archiviert"])
    print("nicht zuordenbar ............ %d" % stat["nicht_zuordenbar"])
    print("Fehler ...................... %d" % stat["fehler"])
    print("Dubletten ................... %d" % doppelt)
    if not args.ausfuehren:
        print("wuerde aktualisieren ........ %d" % stat["wuerde_aktualisieren"])
    print("Rechnungen mit Hinweis (O11)  %d, in Odoo 18 offen: %d"
          % (q["rechnungen_mit_hinweis"], stat["rechnung_offen"]))
    if args.nachlauf_rechnungen:
        print("Nachlauf: korrekt/gesetzt/nicht zuordenbar %d / %d / %d, "
              "Verteilungsabweichungen %d"
              % (stat["rechnung_korrekt"], stat["rechnung_gesetzt"],
                 stat["rechnung_nicht_zuordenbar"], stat["rechnung_abweichungen"]))
    if args.ausfuehren:
        print("Bestand nachher ............. %d Hinweise" % stat["bestand_nachher"])
    if fehler:
        print("Fehlerdetails (max 10):")
        for f in fehler[:10]:
            print("  O11 %s: %s" % (f["o11_id"], f["fehler"]))
    if sonderfaelle:
        print("Sonderfaelle: %d (Details in der Mapping-Datei/Doku)" % len(sonderfaelle))
    return 0 if stat["fehler"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
