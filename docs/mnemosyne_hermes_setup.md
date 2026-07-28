# Mnemosyne Hermes Setup

Installationsdatum: 27. Juli 2026
Hermes-Version: v0.17.0 (2026.6.19)
Mnemosyne-Version: mnemosyne-hermes 0.5.0, mnemosyne-memory 3.14.0

## Installation

```bash
# 1. In Hermes' venv installieren
source ~/.hermes/hermes-agent/venv/bin/activate
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install mnemosyne-hermes

# 2. Plugin verlinken
mkdir -p ~/.hermes/plugins/mnemosyne
ln -sfn "$(python -c 'import pathlib, mnemosyne_hermes; print(pathlib.Path(mnemosyne_hermes.__file__).resolve().parent)')"/* ~/.hermes/plugins/mnemosyne/

# 3. Aktivieren
hermes config set memory.provider mnemosyne

# 4. Prüfen
hermes memory status
```

## Datenbank

- Pfad: `~/.hermes/mnemosyne/data/mnemosyne.db`
- Profil: `default`

## Nach Hermes-Update wiederherstellen

```bash
source ~/.hermes/hermes-agent/venv/bin/activate
python -m pip install mnemosyne-hermes
mkdir -p ~/.hermes/plugins/mnemosyne
ln -sfn "$(python -c 'import pathlib, mnemosyne_hermes; print(pathlib.Path(mnemosyne_hermes.__file__).resolve().parent)')"/* ~/.hermes/plugins/mnemosyne/
hermes config set memory.provider mnemosyne
hermes memory status
```

## Deinstallation

```bash
hermes memory off
# Neue Session starten
rm -rf ~/.hermes/plugins/mnemosyne/
source ~/.hermes/hermes-agent/venv/bin/activate
python -m pip uninstall mnemosyne-hermes mnemosyne-memory
```

Die Datenbank (`~/.hermes/mnemosyne/`) bleibt erhalten und kann manuell gelöscht werden.

## CLI-Befehle

```bash
source ~/.hermes/hermes-agent/venv/bin/activate
mnemosyne store "Inhalt" "source" "0.8"
mnemosyne recall "Suchbegriff"
mnemosyne stats
mnemosyne sleep       # Konsolidierung
mnemosyne backup /pfad/zum/backup/
mnemosyne restore backup.db.gz
mnemosyne verify      # Integritätsprüfung
```
