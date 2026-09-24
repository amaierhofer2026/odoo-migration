"""Kleines Werkzeug fuer Pull Requests per GitHub-REST-API (gh-CLI fehlt in dieser Umgebung).

Das Token wird aus der Git-Remote-URL gelesen (oder aus GITHUB_TOKEN in der .env) und nie
ausgegeben.

Aufruf:
    python scripts/github_pr.py status  [--nummer N]
    python scripts/github_pr.py anlegen --titel "..." --kopf BRANCH [--basis main] [--text-datei DATEI]
    python scripts/github_pr.py mergen  --nummer N [--methode merge|squash|rebase]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com/repos/amaierhofer2026/odoo-migration"


def token():
    env = os.path.join(REPO, ".env")
    if os.path.exists(env):
        for zeile in open(env, encoding="utf-8"):
            if zeile.startswith("GITHUB_TOKEN="):
                return zeile.split("=", 1)[1].strip().strip('"')
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO,
                         capture_output=True, text=True).stdout.strip()
    m = re.match(r"https://[^:]+:([^@]+)@", url)
    if not m:
        raise SystemExit("Kein Token gefunden (weder .env noch Remote-URL).")
    return m.group(1)


def ruf(pfad, payload=None, methode="GET", token_=None):
    req = urllib.request.Request(
        API + pfad,
        data=(json.dumps(payload).encode("utf-8") if payload is not None else None),
        method=methode,
        headers={"Authorization": "token " + (token_ or token()),
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as f:
            return f.status, json.load(f)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def zeige_status(d):
    if not isinstance(d, dict):
        print("  %s" % str(d)[:300])
        return
    print("  PR #%s  %s" % (d.get("number"), d.get("title")))
    print("  Zustand      : %s%s" % (d.get("state"), " (gemergt)" if d.get("merged") else ""))
    print("  mergebar     : mergeable=%s  mergeable_state=%s" % (d.get("mergeable"), d.get("mergeable_state")))
    kopf = d.get("head") or {}
    basis = d.get("base") or {}
    print("  Branch       : %s -> %s" % (kopf.get("ref"), basis.get("ref")))
    print("  Commits      : %s | Dateien: %s | +%s -%s" % (
        d.get("commits"), d.get("changed_files"), d.get("additions"), d.get("deletions")))
    if d.get("merge_commit_sha"):
        print("  Merge-Commit : %s" % d.get("merge_commit_sha"))
    print("  URL          : %s" % d.get("html_url"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("aktion", choices=["status", "anlegen", "mergen"])
    p.add_argument("--nummer", type=int)
    p.add_argument("--titel", default="")
    p.add_argument("--kopf", default="")
    p.add_argument("--basis", default="main")
    p.add_argument("--text", default="")
    p.add_argument("--text-datei", default="")
    p.add_argument("--methode", default="merge", choices=["merge", "squash", "rebase"])
    p.add_argument("--titel-extra", default="", help="Zusatz fuer die Merge-Commit-Zeile")
    a = p.parse_args()

    if a.aktion == "status":
        if a.nummer:
            s, d = ruf("/pulls/%d" % a.nummer)
        else:
            s, d = ruf("/pulls?state=open&per_page=10")
            if isinstance(d, list):
                for x in d:
                    zeige_status(x)
                    print()
                return 0
        print("HTTP %s" % s)
        zeige_status(d)
        return 0

    if a.aktion == "anlegen":
        if not a.titel or not a.kopf:
            raise SystemExit("--titel und --kopf sind noetig.")
        text = a.text
        if a.text_datei:
            text = open(a.text_datei, encoding="utf-8").read()
        s, d = ruf("/pulls", {"title": a.titel, "head": a.kopf, "base": a.basis, "body": text}, "POST")
        print("HTTP %s" % s)
        zeige_status(d)
        return 0 if s in (200, 201) else 1

    if not a.nummer:
        raise SystemExit("--nummer ist noetig.")
    s, d = ruf("/pulls/%d" % a.nummer)
    titel = (d.get("title") if isinstance(d, dict) else "") or ""
    if a.titel_extra:
        titel = a.titel_extra
    s, d = ruf("/pulls/%d/merge" % a.nummer,
               {"merge_method": a.methode, "commit_title": "Merge pull request #%d: %s" % (a.nummer, titel)},
               "PUT")
    print("HTTP %s" % s)
    print("  %s" % (d if not isinstance(d, dict) else json.dumps(d, indent=2)))
    return 0 if s == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
