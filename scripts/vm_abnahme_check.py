#!/usr/bin/env python3
"""VM-Abnahme-Prüfung (verbindliche Arbeitsregel seit 15.09.2026, Session 97).

Die VM https://k001959vsx.ipax.at ist die maßgebliche Test- und Abnahmeumgebung.
Ein Git-Pull allein genügt NICHT: Moduländerungen brauchen ein gezieltes Upgrade in der
VM-Datenbank odoo18_test. Dieses Skript prüft genau das und sagt, was noch fehlt.

Geprüft wird (read-only, keine Änderungen):
  1. Erreichbarkeit der VM (Login-Seite antwortet)
  2. Git-Stand der VM gegen den lokalen main-Stand (per SSH-Helfer %TEMP%/vm_exec.py)
  3. Für alle im Repo geänderten Module: Repo-Version vs. auf der VM installierte Version
  4. Gesamtzahl der Module, bei denen VM-DB und Repo-Version abweichen

Aufruf:
    python scripts/vm_abnahme_check.py                 # Standardprüfung
    python scripts/vm_abnahme_check.py --seit <commit> # Änderungen seit diesem Commit prüfen
    python scripts/vm_abnahme_check.py --modul itk_base_setup [--modul ...]
    python scripts/vm_abnahme_check.py --ohne-ssh      # ohne Git-Prüfung der VM

Rückgabewert: 0 = VM auf dem Stand, 1 = auf der VM ist noch etwas zu tun.
"""
import argparse, ast, json, os, re, subprocess, sys, urllib.request, http.cookiejar

VM_URL = "https://k001959vsx.ipax.at"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lade_env():
    env = {}
    pfad = os.path.join(REPO, ".env")
    if os.path.exists(pfad):
        for zeile in open(pfad, encoding="utf-8"):
            if "=" in zeile and not zeile.strip().startswith("#"):
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def git(*args):
    try:
        r = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True, timeout=60)
        return r.stdout.strip()
    except Exception as e:
        return ""


def repo_modulversionen():
    """{modulname: version} aus allen __manifest__.py im Repo."""
    versionen = {}
    for basis, _, dateien in os.walk(os.path.join(REPO, "addons")):
        if "__manifest__.py" in dateien:
            pfad = os.path.join(basis, "__manifest__.py")
            try:
                daten = ast.literal_eval(open(pfad, encoding="utf-8").read())
                if isinstance(daten, dict) and daten.get("name"):
                    versionen[os.path.basename(basis)] = str(daten.get("version", ""))
            except Exception:
                pass
    return versionen


def vm_git_stand():
    helfer = os.path.join(os.environ.get("TEMP", ""), "vm_exec.py")
    if not os.path.exists(helfer):
        return None, "SSH-Helfer %TEMP%/vm_exec.py nicht vorhanden"
    try:
        r = subprocess.run([sys.executable, helfer, "cd /opt/odoo18 && git rev-parse HEAD && git status --porcelain | wc -l"],
                           capture_output=True, text=True, timeout=180)
        head, schmutz = None, None
        for z in (r.stdout or "").splitlines():
            z = z.strip()
            if re.fullmatch(r"[0-9a-f]{7,40}", z) and head is None:
                head = z
            elif re.fullmatch(r"\d+", z):
                schmutz = z
        if head:
            return head, (schmutz or "?")
        return None, (r.stdout or "").strip()[:200] or "keine Ausgabe"
    except Exception as e:
        return None, str(e)[:200]


class RPC:
    def __init__(self, db, user, pwd):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        r = urllib.request.Request(VM_URL + "/web/session/authenticate",
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                    "params": {"db": db, "login": user, "password": pwd}}).encode(),
                                   headers={"Content-Type": "application/json"})
        with self.op.open(r, timeout=120) as f:
            self.auth = json.loads(f.read().decode())

    def kw(self, model, method, args, context=None, **extra):
        k = {"context": context} if context else {}
        k.update(extra)
        r = urllib.request.Request(VM_URL + "/web/dataset/call_kw",
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                    "params": {"model": model, "method": method, "args": args, "kwargs": k}}).encode(),
                                   headers={"Content-Type": "application/json"})
        with self.op.open(r, timeout=180) as f:
            o = json.loads(f.read().decode())
        if "error" in o:
            raise RuntimeError(json.dumps(o["error"])[:300])
        return o["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seit", help="nur Änderungen seit diesem Commit prüfen (Default: VM-HEAD)")
    ap.add_argument("--modul", action="append", default=[], help="einzelne Module prüfen (mehrfach möglich)")
    ap.add_argument("--ohne-ssh", action="store_true", help="Git-Stand der VM nicht prüfen")
    a = ap.parse_args()

    env = lade_env()
    fehler = []
    print("=== VM-Abnahmeprüfung", VM_URL, "===")

    # 1. Erreichbarkeit
    try:
        r = urllib.request.urlopen(VM_URL + "/web/login", timeout=30)
        print("1) Erreichbarkeit   : HTTP %s (Login-Seite antwortet)" % r.status)
    except Exception as e:
        print("1) Erreichbarkeit   : FEHLER %s" % str(e)[:120])
        return 1

    # 2. Git-Stand der VM
    lokal_head = git("rev-parse", "HEAD")
    vm_head = None
    if not a.ohne_ssh:
        vm_head, info = vm_git_stand()
        if vm_head:
            gleich = vm_head == lokal_head
            print("2) Git-Stand        : lokal %s | VM %s %s" % (lokal_head[:7], vm_head[:7],
                                                                  "(identisch)" if gleich else "<- ABWEICHUNG"))
            if not gleich:
                fehler.append("VM-Git-Stand weicht vom lokalen main ab (VM: %s, lokal: %s)" % (vm_head[:7], lokal_head[:7]))
            if info and info.strip() != "0":
                print("   VM-Arbeitsbaum   : nicht sauber (%s geänderte Dateien)" % info.strip())
        else:
            print("2) Git-Stand        : nicht geprüft (%s)" % info)

    # 3. Geänderte Module + Versionsvergleich
    versionen = repo_modulversionen()
    geaendert = set(a.modul)
    if not a.modul:
        basis = a.seit or vm_head or lokal_head
        diff = git("diff", "--name-only", "%s..%s" % (basis, lokal_head), "--", "addons/")
        for zeile in diff.splitlines():
            teile = zeile.split("/")
            if len(teile) > 1 and teile[0] == "addons":
                geaendert.add(teile[1])
    if not geaendert:
        print("3) Geänderte Module : keine (kein Unterschied im addons/-Baum)")

    try:
        rpc = RPC(env.get("ODOO18_DB", "odoo18_test"), env["ODOO18_USER"], env["ODOO18_PWD"])
        uid = rpc.auth.get("result", {}).get("uid")
        print("   VM-Anmeldung     : OK (uid %s)" % uid)
    except Exception as e:
        print("   VM-Anmeldung     : FEHLER %s" % str(e)[:160])
        return 1

    offen = []
    if geaendert:
        satz = rpc.kw("ir.module.module", "search_read",
                      [[["name", "in", sorted(geaendert)]], ["name", "installed_version", "state"]])
        gefunden = {s["name"]: s for s in satz}
        for mod in sorted(geaendert):
            soll = versionen.get(mod, "?")
            ist_daten = gefunden.get(mod)
            if not ist_daten:
                print("   %-28s im Repo, auf der VM NICHT installiert" % mod)
                offen.append(mod)
                continue
            ist = ist_daten["installed_version"] or "-"
            status = "OK" if ist == soll else "UPGRADE NÖTIG auf der VM"
            print("   %-28s Repo %-14s VM %-14s %s" % (mod, soll, ist, status))
            if ist != soll:
                offen.append(mod)

    # 4. Gesamtabweichungen (Information)
    alle = rpc.kw("ir.module.module", "search_read", [[["state", "=", "installed"]], ["name", "installed_version"]])
    abweichungen = [m["name"] for m in alle if m["name"] in versionen and (m["installed_version"] or "") != versionen[m["name"]]]
    print("4) VM-DB vs. Repo  : %d von %d installierten Repo-Modulen mit abweichender Version (%s)"
          % (len(abweichungen), len(set(m["name"] for m in alle) & set(versionen)),
             ", ".join(abweichungen[:6]) + ("..." if len(abweichungen) > 6 else "") if abweichungen else "-"))

    if offen:
        print("\nERGEBNIS: NICHT abgenommen - auf der VM gezielt upgraden: %s" % ", ".join(offen))
        print("Befehl: python scripts/upgrade_modules.py --instanz vm --update-list --module %s" % " --module ".join(offen))
        fehler.append("Module ohne VM-Upgrade: " + ", ".join(offen))
    if fehler:
        print("\nERGEBNIS: VM-Abnahme noch offen.")
        for f in fehler:
            print("   -", f)
        return 1
    print("\nERGEBNIS: VM ist auf dem Stand (Git + Modulversionen).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
