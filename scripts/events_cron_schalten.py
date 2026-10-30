"""Cron "Event: Mail Scheduler" ein- oder ausschalten.

Der Bereich Events ist ohne Kontakt- und Teilnehmerdaten migriert; der
Mailversand aus Veranstaltungs-Mailplanern ist deshalb stillgelegt.
Dieses Skript schaltet den Cron gezielt und protokolliert den Zustand.

Aufruf:
    python scripts/events_cron_schalten.py --instanz lokal               # Zustand zeigen
    python scripts/events_cron_schalten.py --instanz lokal --aktiv       # einschalten
    python scripts/events_cron_schalten.py --instanz lokal --inaktiv     # ausschalten
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

DE = {"lang": "de_DE"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--aktiv", action="store_true")
    ap.add_argument("--inaktiv", action="store_true")
    a = ap.parse_args()
    k = o18(a.instanz)
    crons = k.kw("ir.cron", "search_read",
                 [[("name", "ilike", "Mail Scheduler")], ["name", "active", "nextcall"]],
                 context={"active_test": False})
    if not crons:
        sys.exit("FEHLER: Cron 'Event: Mail Scheduler' nicht gefunden")
    c = crons[0]
    print("%s: %s | aktiv=%s | nextcall=%s" % (a.instanz, c["name"], c["active"], c["nextcall"]))
    ziel = True if a.aktiv else (False if a.inaktiv else None)
    if ziel is None:
        return 0
    k.kw("ir.cron", "write", [[c["id"]], {"active": ziel}])
    neu = k.kw("ir.cron", "read", [[c["id"]], ["active"]], context={"active_test": False})[0]
    print("  -> aktiv=%s" % neu["active"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
