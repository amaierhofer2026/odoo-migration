# ============================================================================
# odoo18 PostgreSQL Recovery Script — Phase 2 (v2)
# PowerShell 5.1 kompatibel — kein && / || / PS7-Syntax
# Datum: 10.08.2026
# ============================================================================
# SICHERHEIT:
# - Arbeitet NUR auf Kopie C:\Odoo-Test\postgres_recovery
# - C:\Odoo-Test\postgres und postgres_defekt_2026-08-10 bleiben UNVERAENDERT
# - Preflight-Modus ZUERST — erst bei Erfolg wird Phase 2 gestartet
# ============================================================================

$ErrorActionPreference = "Stop"
$BaseDir = "C:\Odoo-Test"
$RecoveryDir = "$BaseDir\postgres_recovery"
$DefektDir = "$BaseDir\postgres_defekt_2026-08-10"
$BackupDir = "$BaseDir\backups"
$Timestamp = "2026-08-10"

# ============================================================================
# PREFLIGHT — nur Prüfungen, keine Änderungen
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PREFLIGHT-CHECK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. PowerShell version
Write-Host "[Preflight 1/7] PowerShell-Version ..." -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
Write-Host "  Major: $($psVersion.Major), Minor: $($psVersion.Minor)"
if ($psVersion.Major -lt 5) {
    Write-Host "  FEHLER: PowerShell 5.1 oder neuer erforderlich!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# 2. Defekt-Verzeichnis existiert
Write-Host "[Preflight 2/7] Defekt-Verzeichnis: $DefektDir ..." -ForegroundColor Yellow
if (-not (Test-Path $DefektDir)) {
    Write-Host "  FEHLER: $DefektDir existiert nicht!" -ForegroundColor Red
    exit 1
}
$defektFiles = (Get-ChildItem -Recurse -File $DefektDir -ErrorAction SilentlyContinue).Count
if ($defektFiles -lt 10000) {
    Write-Host "  WARNUNG: Nur $defektFiles Dateien — erwartet ~15200" -ForegroundColor Yellow
}
Write-Host "  OK: $defektFiles Dateien" -ForegroundColor Green

# 3. Recovery-Verzeichnis darf ueberschrieben werden
Write-Host "[Preflight 3/7] Recovery-Ziel: $RecoveryDir ..." -ForegroundColor Yellow
if (Test-Path $RecoveryDir) {
    Write-Host "  Bereits vorhanden — wird vor Recovery geloescht."
}
Write-Host "  OK: Kann gefahrlos erstellt werden" -ForegroundColor Green

# 4. Original postgres NICHT anfassen
Write-Host "[Preflight 4/7] Original postgres/ ..." -ForegroundColor Yellow
$pgDir = "$BaseDir\postgres"
if (Test-Path $pgDir) {
    $pgFiles = (Get-ChildItem -Recurse -File $pgDir -ErrorAction SilentlyContinue).Count
    Write-Host "  OK: $pgFiles Dateien — wird NICHT veraendert" -ForegroundColor Green
} else {
    Write-Host "  WARNUNG: $pgDir existiert nicht" -ForegroundColor Yellow
}

# 5. Docker verfuegbar
Write-Host "[Preflight 5/7] Docker ..." -ForegroundColor Yellow
$dockerCheck = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: Docker nicht verfuegbar!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: $dockerCheck" -ForegroundColor Green

# 6. PostgreSQL-16-Image
Write-Host "[Preflight 6/7] postgres:16 Image ..." -ForegroundColor Yellow
$imgCheck = docker images postgres:16 --format "{{.Tag}}" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: postgres:16 Image nicht gefunden!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: postgres:16 vorhanden" -ForegroundColor Green

# 7. Odoo-Container gestoppt
Write-Host "[Preflight 7/7] Container-Status ..." -ForegroundColor Yellow
$running = docker ps --format "{{.Names}}" 2>&1
$odoos = @($running -split "`n" | Where-Object { $_ -match "odoo18" })
if ($odoos.Count -gt 0) {
    Write-Host "  WARNUNG: Container laufen noch: $odoos" -ForegroundColor Yellow
    Write-Host "  Bitte vorher stoppen: docker compose stop" -ForegroundColor Yellow
    Write-Host "  Preflight fortsetzen, aber Phase 2 wird NICHT automatisch starten." -ForegroundColor Yellow
} else {
    Write-Host "  OK: Keine Odoo-Container aktiv" -ForegroundColor Green
}

# Stelle sicher dass backup-Verzeichnis existiert
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# ============================================================================
# Preflight abgeschlossen — Frage stellen
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PREFLIGHT ABGESCHLOSSEN" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Phase 2 wird:" -ForegroundColor White
Write-Host "  1. $RecoveryDir aus $DefektDir kopieren"
Write-Host "  2. pg_resetwal -f auf der KOPIE ausfuehren"
Write-Host "  3. Temporaren Recovery-Container starten"
Write-Host "  4. odoo18_test pruefen + Tabellen zaehlen"
Write-Host "  5. pg_dump nach backups\odoo18_dump_rescued_$Timestamp.sql"
Write-Host "  6. Filestore sichern"
Write-Host "  7. Recovery-Container stoppen"
Write-Host ""
Write-Host "WICHTIG: $BaseDir\postgres und $DefektDir bleiben UNVERAENDERT." -ForegroundColor Yellow
Write-Host ""

$antwort = Read-Host "Phase 2 jetzt starten? (ja/nein)"
if ($antwort -ne "ja") {
    Write-Host "ABBRUCH durch Benutzer." -ForegroundColor Yellow
    exit 0
}

# ============================================================================
# PHASE 2 — RECOVERY
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHASE 2: PostgreSQL Recovery" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Schritt 1: Arbeitskopie erstellen
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[1/7] Arbeitskopie erstellen ..." -ForegroundColor Yellow

if (Test-Path $RecoveryDir) {
    Write-Host "  Loesche alte Recovery-Kopie: $RecoveryDir"
    Remove-Item -Recurse -Force $RecoveryDir
}

Write-Host "  Kopiere: $DefektDir --> $RecoveryDir"
Copy-Item -Recurse $DefektDir $RecoveryDir

$fileCount = (Get-ChildItem -Recurse -File $RecoveryDir).Count
Write-Host "  OK: $fileCount Dateien kopiert" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Schritt 2: pg_resetwal ausfuehren
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/7] pg_resetwal -f auf Recovery-Kopie ..." -ForegroundColor Yellow

$resetOutput = docker run --rm `
    -v "$RecoveryDir`:/var/lib/postgresql/data" `
    postgres:16 `
    pg_resetwal -f /var/lib/postgresql/data 2>&1

Write-Host "  pg_resetwal Output:"
Write-Host "  $resetOutput"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  FEHLER: pg_resetwal mit Exit-Code $LASTEXITCODE fehlgeschlagen!" -ForegroundColor Red
    Write-Host "  ABBRUCH — keine weiteren Schritte." -ForegroundColor Red
    exit 1
}
Write-Host "  OK: pg_resetwal erfolgreich" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Schritt 3: PostgreSQL Recovery-Container starten
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/7] PostgreSQL Recovery-Container starten ..." -ForegroundColor Yellow

# Stoppe ggf. alten Recovery-Container
docker stop odoo18-db-recovery 2>$null
docker rm odoo18-db-recovery 2>$null

docker run -d `
    --name odoo18-db-recovery `
    -e POSTGRES_DB=postgres `
    -e POSTGRES_USER=odoo `
    -e POSTGRES_PASSWORD=odoo `
    -v "$RecoveryDir`:/var/lib/postgresql/data" `
    postgres:16 2>&1

Write-Host "  Container gestartet, warte auf PostgreSQL..."
Start-Sleep -Seconds 5

# Pruefe ob PostgreSQL bereit ist
$maxAttempts = 10
$ready = $false
for ($i = 1; $i -le $maxAttempts; $i++) {
    $check = docker exec odoo18-db-recovery pg_isready -U odoo 2>&1
    if ($check -match "accepting connections") {
        $ready = $true
        break
    }
    Write-Host "  Versuch $i/$maxAttempts ... $check"
    Start-Sleep -Seconds 3
}

if (-not $ready) {
    Write-Host ""
    Write-Host "  FEHLER: PostgreSQL nicht bereit nach $maxAttempts Versuchen!" -ForegroundColor Red
    Write-Host "  Logs:" -ForegroundColor Red
    docker logs --tail 30 odoo18-db-recovery
    Write-Host "  ABBRUCH." -ForegroundColor Red
    docker stop odoo18-db-recovery
    exit 1
}
Write-Host "  OK: PostgreSQL ist bereit" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Schritt 4: Datenbanken pruefen
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/7] Datenbanken pruefen ..." -ForegroundColor Yellow

$dbs = docker exec odoo18-db-recovery psql -U odoo -d postgres -t -c "\l" 2>&1
Write-Host "  Datenbanken:"
Write-Host "  $dbs"

# Pruefe ob odoo18_test existiert
$dbCheck = docker exec odoo18-db-recovery psql -U odoo -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='odoo18_test'" 2>&1
if ($dbCheck -notmatch "1") {
    Write-Host "  FEHLER: Datenbank 'odoo18_test' NICHT gefunden!" -ForegroundColor Red
    docker stop odoo18-db-recovery
    exit 1
}
Write-Host "  OK: odoo18_test existiert" -ForegroundColor Green

# Zeige wichtige Tabellen-Zaehlungen
Write-Host ""
Write-Host "  Wichtige Tabellen:" -ForegroundColor Yellow

$sqlQueries = @(
    "SELECT 'ir_model_data: ' || count(*) FROM ir_model_data;",
    "SELECT 'res_users: ' || count(*) FROM res_users;",
    "SELECT 'res_partner: ' || count(*) FROM res_partner;",
    "SELECT 'ir_module_module: ' || count(*) FROM ir_module_module;",
    "SELECT 'crm_lead: ' || count(*) FROM crm_lead;",
    "SELECT 'crm_team: ' || count(*) FROM crm_team;",
    "SELECT 'ir_ui_view: ' || count(*) FROM ir_ui_view;",
    "SELECT 'ir_ui_menu: ' || count(*) FROM ir_ui_menu;",
    "SELECT 'ir_attachment: ' || count(*) FROM ir_attachment;"
)

foreach ($query in $sqlQueries) {
    $result = docker exec odoo18-db-recovery psql -U odoo -d odoo18_test -t -c $query 2>&1
    Write-Host "  $result"
}

# ---------------------------------------------------------------------------
# Schritt 5: SQL-Dump erstellen
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/7] SQL-Dump erstellen ..." -ForegroundColor Yellow

$DumpFile = "$BackupDir\odoo18_dump_rescued_$Timestamp.sql"

docker exec odoo18-db-recovery pg_dump -U odoo -d odoo18_test --no-owner --no-acl > "$DumpFile" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: pg_dump mit Exit-Code $LASTEXITCODE fehlgeschlagen!" -ForegroundColor Red
    docker stop odoo18-db-recovery
    exit 1
}

$dumpSize = (Get-Item "$DumpFile").Length
$dumpSizeMB = [math]::Round($dumpSize / 1MB, 1)
Write-Host "  OK: Dump erstellt: $DumpFile ($dumpSizeMB MB)" -ForegroundColor Green

# Pruefe ersten Zeilen des Dumps
Write-Host "  Erste 5 Zeilen:"
Get-Content "$DumpFile" -First 5 | ForEach-Object { Write-Host "    $_" }

# ---------------------------------------------------------------------------
# Schritt 6: Filestore sichern
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/7] Filestore sichern ..." -ForegroundColor Yellow

$FilestoreSource = "$BaseDir\filestore"
$FilestoreBackup = "$BackupDir\filestore_rescued_$Timestamp"

if (Test-Path $FilestoreBackup) {
    Remove-Item -Recurse -Force $FilestoreBackup
}

# Filestore ist ein Bind-Mount (./filestore:/var/lib/odoo/filestore)
# Da Odoo-Container gestoppt ist, ist der aktuelle Filestore auf Disk
Copy-Item -Recurse $FilestoreSource $FilestoreBackup

$fsFileCount = (Get-ChildItem -Recurse -File $FilestoreBackup).Count
$fsSize = [math]::Round((Get-ChildItem -Recurse -File $FilestoreBackup | Measure-Object Length -Sum).Sum / 1KB, 0)
Write-Host "  OK: $fsFileCount Dateien ($fsSize KB) gesichert nach $FilestoreBackup" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Schritt 7: Recovery-Container stoppen
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[7/7] Recovery-Container stoppen ..." -ForegroundColor Yellow

docker stop odoo18-db-recovery
docker rm odoo18-db-recovery
Write-Host "  OK: Container gestoppt und entfernt" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Zusammenfassung
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RECOVERY PHASE 2 ABGESCHLOSSEN" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ergebnisse:" -ForegroundColor White
Write-Host "  pg_resetwal:      Erfolgreich"
Write-Host "  PostgreSQL-Start:  Erfolgreich"
Write-Host "  odoo18_test:      Vorhanden"
Write-Host "  SQL-Dump:         $DumpFile ($dumpSizeMB MB)"
Write-Host "  Filestore-Backup: $FilestoreBackup ($fsFileCount Dateien)"
Write-Host ""
Write-Host "Zum Vergleich: Letztes sauberes Backup vom 29.07. war 6.7 MB als ZIP." -ForegroundColor Yellow
Write-Host ""
Write-Host "BITTE DIE OBIGEN TABELLEN-ZAEHLUNGEN PRUEFEN." -ForegroundColor Yellow
Write-Host "Sobald bestaetigt: Phase 3 starten (neue saubere DB, Dump importieren)." -ForegroundColor White
