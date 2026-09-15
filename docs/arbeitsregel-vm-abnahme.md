# Verbindliche Arbeitsregel: VM = Test- und Abnahmeumgebung

**Gültig ab 15.09.2026 (Session 97) für das gesamte Odoo-18-Migrationsprojekt.**
Sie gilt automatisch für jeden weiteren Bereich, ohne dass Anna sie erneut nennen muss.

## Die Regel im Wortlaut (Anna)

> Die VM unter https://k001959vsx.ipax.at ist die maßgebliche Test- und Abnahmeumgebung.
> Die lokale Odoo-18-Installation darf weiterhin für Entwicklung, Analyse und Vorabtests verwendet werden.
> Ein Punkt gilt aber erst dann als wirklich umgesetzt bzw. abgeschlossen, wenn die Änderung:
> 1. auf der VM deployed ist,
> 2. in der VM-Datenbank `odoo18_test` geladen/aktiviert wurde,
> 3. direkt gegen https://k001959vsx.ipax.at geprüft wurde,
> 4. dort im echten Browser sichtbar bzw. funktional bestätigt wurde.
>
> Wenn ein Modul geändert wurde, reicht ein Git-Pull auf der VM nicht aus: immer prüfen, ob ein gezieltes
> Modul-Upgrade bzw. eine andere notwendige Aktivierung auf der VM erforderlich ist.
> Bei UI-/View-Änderungen: nicht nur XML/DOM/RPC prüfen, sondern die tatsächlich aktive View und die
> sichtbare Darstellung auf der VM kontrollieren.
> Lokal = Entwicklungsumgebung. VM = verbindliche Test-/Abnahmeumgebung.

## Kurzform für jede Aufgabe

| Umgebung | Rolle | Was dort erlaubt/erforderlich ist |
|---|---|---|
| `C:\Odoo-Test` + `http://localhost:8069` | **Entwicklung** | Entwickeln, analysieren, vorab testen. Kein Abnahmenachweis. |
| `https://k001959vsx.ipax.at` (`/opt/odoo18`, DB `odoo18_test`) | **Test und Abnahme** | Deployen, laden/aktivieren, dort prüfen, im Browser bestätigen. **Nur hier zählt „erledigt".** |

## Abnahme-Checkliste (in dieser Reihenfolge abzuarbeiten)

1. **Deploy:** Branch/`main` auf die VM bringen (`git pull --ff-only`), Container neu starten, damit Manifeste
   und Python neu geladen werden.
2. **Aktivierung:** Modul gezielt upgraden (**niemals** `-u all`): `scripts/upgrade_modules.py --instanz vm --update-list --module <modul>`.
   Nachsehen, ob die DB-Version wirklich der Repo-Version entspricht.
   Reine DB-/Konfigurationsschritte (z. B. Übersetzungs-Slots, Basisdaten, Einstellungen) zusätzlich per RPC auf der VM ausführen.
3. **Prüfung gegen die VM:** Verifikationsskript mit `--instanz vm` laufen lassen (nicht nur `lokal`).
4. **Browser-Bestätigung auf der VM:** echten Browser gegen https://k001959vsx.ipax.at rendern
   (`scripts/browser_form_layout.py --instanz vm`) und die sichtbare Darstellung/Position/Funktion bewerten.
   XML, DOM-Zählung oder RPC allein sind **kein** Abnahmenachweis.
5. **Dokumentation, Commit, Push, PR, Merge** wie bisher.
6. **VM auf den finalen `main`-Stand bringen** und dort **abschließend** verifizieren
   (`git rev-parse HEAD` auf der VM == `main` lokal == GitHub; Verifikation erneut gegen die VM).

## Werkzeug

`python scripts/vm_abnahme_check.py` prüft automatisch:

- Erreichbarkeit der VM (`/web/login` antwortet),
- VM-Git-Stand gegen den lokalen `main`-Stand,
- für alle im Repo geänderten Module: Repo-Version gegen **VM-installierte** Version → listet auf,
  welche Module auf der VM noch ein gezieltes Upgrade brauchen,
- Gesamtzahl der Module, bei denen VM-DB und Repo abweichen.

Rückgabewert: `0` = VM ist auf dem Stand, `1` = auf der VM ist noch etwas zu tun (Upgrade/Nachziehen).

## Konsequenzen für die Berichterstattung

- „Erledigt" wird **nur** mit VM-Nachweis gesagt (VM-Commit, im Modul sichtbare Version, Prüfskript-Ergebnis gegen die VM,
  Browser-Bestätigung auf der VM).
- Wenn nur lokal geprüft wurde, heißt es ausdrücklich **„lokal vorbereitet, VM-Abnahme offen"**.
- Jeder Abschlussbericht nennt beide Umgebungen getrennt: lokal (Entwicklung) und VM (Abnahme).

## Verwandte Regeln (unverändert gültig)

- Nur Struktur vorbereiten, keine Odoo-11-Produktivdaten migrieren.
- Keine Korrekturen/Reparaturen ohne ausdrückliche Freigabe; read-only zuerst.
- Kein `-u all`, keine Modul-Upgrades über den freigegebenen Umfang hinaus, keine Datenmigration.
- `main` nie direkt beschreiben; Arbeitsbranch → Push → PR → Merge (kein Force-Push, kein Rebase).
- Keine Zugangsdaten, Rohdaten oder Backups im Repo.
- **„Vorhanden" ist nicht „erledigt":** je Punkt auch prüfen, ob er sichtbar, an der richtigen Position
  und mit gleicher fachlicher Funktion/Bedienlogik vorhanden ist.
