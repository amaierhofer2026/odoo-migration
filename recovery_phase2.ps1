# ============================================================================
# odoo18 PostgreSQL Recovery Script — Phase 2
# Datum: 10.08.2026
# Vorsicht: Arbeitet NUR auf Kopie C:\Odoo-Test\postgres_recovery
# Original C:\Odoo-Test\postgres bleibt UNVERÄNDERT
# ============================================================================

$ErrorActionPreference = "Stop"
$BaseDir = "C:\Odoo-Test"
$RecoveryDir = "$BaseDir\postgres_recovery"
$DefektDir = "$BaseDir\postgres_defekt_2026-08-10"
$BackupDir = "$BaseDir\backups"
$Timestamp = "2026-08-10"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 2: PostgreSQL Recovery" -ForegroundColor Cyan
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
$tableCheck = docker exec odoo18-db-recovery psql -U odoo -d odoo18_test -t -c "
SELECT 'ir_model_data: ' || count(*) FROM ir_model_data;
SELECT 'res_users: ' || count(*) FROM res_users;
SELECT 'res_partner: ' || count(*) FROM res_partner;
SELECT 'ir_module_module: ' || count(*) FROM ir_module_module;
SELECT 'crm_lead: ' || count(*) FROM crm_lead;
SELECT 'crm_team: ' || count(*) FROM crm_team;
SELECT 'ir_ui_view: ' || count(*) FROM ir_ui_view;
SELECT 'ir_ui_menu: ' || count(*) FROM ir_ui_menu;
SELECT 'ir_attachment: ' || count(*) FROM ir_attachment;
" 2>&1
Write-Host "  $tableCheck"

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
Write-Host "BITTE PRUEFEN: Ist die Dump-Groesse ($dumpSizeMB MB) plausibel?" -ForegroundColor Yellow
Write-Host "Zum Vergleich: Letztes sauberes Backup vom 29.07. war 6.7 MB als ZIP." -ForegroundColor Yellow
Write-Host ""
Write-Host "Sobald bestaetigt: Phase 3 starten (neue saubere DB, Dump importieren)." -ForegroundColor White
