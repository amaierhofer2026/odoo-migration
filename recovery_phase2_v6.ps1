# ============================================================================
# PostgreSQL Recovery Phase 2 — v6
# Basis: recovery_diag.ps1 (funktionierend unter PS 5.1)
# ============================================================================
$ErrorActionPreference = "Stop"
$BaseDir = "C:\Odoo-Test"
$RecoveryDir = "$BaseDir\postgres_recovery"
$DefektDir = "$BaseDir\postgres_defekt_2026-08-10"
$BackupDir = "$BaseDir\backups"
$TempDir = $env:TEMP
$Timestamp = "2026-08-10"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHASE 2: PostgreSQL Recovery v6" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Frische Arbeitskopie
# ---------------------------------------------------------------------------
Write-Host "[1/6] Frische Arbeitskopie ..." -ForegroundColor Yellow
if (Test-Path $RecoveryDir) {
    Write-Host "  Loesche altes postgres_recovery"
    Remove-Item -Recurse -Force $RecoveryDir
}
Copy-Item -Recurse $DefektDir $RecoveryDir
$fc = @(Get-ChildItem -Recurse -File $RecoveryDir).Count
Write-Host "  OK: $fc Dateien" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. postmaster.pid entfernen (in der Kopie)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/6] postmaster.pid in Kopie entfernen ..." -ForegroundColor Yellow
$pidPath = "$RecoveryDir\postmaster.pid"
if (Test-Path $pidPath) {
    Remove-Item $pidPath -Force
    Write-Host "  OK: postmaster.pid geloescht" -ForegroundColor Green
} else {
    Write-Host "  OK: war nicht vorhanden" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 3. pg_resetwal -f (Shell-Script wie recovery_diag.ps1)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] pg_resetwal -f ..." -ForegroundColor Yellow

$resetScript = @'
#!/bin/sh
echo "=== chown postgres:postgres ==="
chown -R postgres:postgres /var/lib/postgresql/data 2>/dev/null
echo ""
echo "=== pg_resetwal -f ==="
su postgres -c "pg_resetwal -f /var/lib/postgresql/data" 2>&1
RC=$?
echo ""
echo "=== EXIT: $RC ==="
exit $RC
'@

$resetFile = "$TempDir\pg_reset.sh"
$resetScript -replace "`r`n", "`n" | Out-File -FilePath $resetFile -Encoding ASCII

$resetOutput = docker run --rm `
    -v "$RecoveryDir`:/var/lib/postgresql/data" `
    -v "${resetFile}:/tmp/pg_reset.sh:ro" `
    postgres:16 `
    sh /tmp/pg_reset.sh 2>&1

Remove-Item $resetFile -Force -ErrorAction SilentlyContinue

Write-Host "  Output:"
$resetOutput -split "`n" | ForEach-Object { Write-Host "    $_" }

if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: pg_resetwal Exit-Code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: pg_resetwal -f erfolgreich" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 4. Recovery-Container starten
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] PostgreSQL starten ..." -ForegroundColor Yellow

# Container nur stoppen wenn vorhanden
$existing = docker ps -a --filter "name=^/odoo18-db-recovery$" --format "{{.Names}}" 2>&1
if ($existing -eq "odoo18-db-recovery") {
    docker stop odoo18-db-recovery 2>&1 | Out-Null
    docker rm odoo18-db-recovery 2>&1 | Out-Null
    Write-Host "  Alten Container entfernt"
}

docker run -d `
    --name odoo18-db-recovery `
    -e POSTGRES_DB=postgres `
    -e POSTGRES_USER=odoo `
    -e POSTGRES_PASSWORD=*** `
    -v "$RecoveryDir`:/var/lib/postgresql/data" `
    postgres:16 2>&1 | Out-Null

Write-Host "  Warte auf PostgreSQL ..."
Start-Sleep -Seconds 5

$ready = $false
for ($i = 1; $i -le 12; $i++) {
    $check = docker exec odoo18-db-recovery pg_isready -U odoo 2>&1
    if ($check -match "accepting connections") {
        $ready = $true
        Write-Host "  OK: Bereit nach $i Versuchen" -ForegroundColor Green
        break
    }
    Write-Host "  Versuch $i/12: $check"
    Start-Sleep -Seconds 3
}

if (-not $ready) {
    Write-Host "  FEHLER: PostgreSQL nicht bereit!" -ForegroundColor Red
    docker logs --tail 20 odoo18-db-recovery
    docker stop odoo18-db-recovery 2>&1 | Out-Null
    docker rm odoo18-db-recovery 2>&1 | Out-Null
    exit 1
}

# ---------------------------------------------------------------------------
# 5. odoo18_test pruefen + pg_dump
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] odoo18_test pruefen + Dump ..." -ForegroundColor Yellow

# Datenbankliste
Write-Host "  Datenbanken:"
docker exec odoo18-db-recovery psql -U odoo -d postgres -t -c "\l" 2>&1

# odoo18_test?
$dbOk = docker exec odoo18-db-recovery psql -U odoo -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='odoo18_test'" 2>&1
if ($dbOk -notmatch "1") {
    Write-Host "  FEHLER: odoo18_test nicht gefunden!" -ForegroundColor Red
    docker stop odoo18-db-recovery 2>&1 | Out-Null
    docker rm odoo18-db-recovery 2>&1 | Out-Null
    exit 1
}
Write-Host "  OK: odoo18_test vorhanden" -ForegroundColor Green

# Backup-Verzeichnis
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# pg_dump
$DumpFile = "$BackupDir\odoo18_dump_rescued_$Timestamp.sql"
Write-Host "  pg_dump nach $DumpFile ..."
docker exec odoo18-db-recovery pg_dump -U odoo -d odoo18_test --no-owner --no-acl > "$DumpFile" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: pg_dump Exit-Code $LASTEXITCODE" -ForegroundColor Red
    docker stop odoo18-db-recovery 2>&1 | Out-Null
    docker rm odoo18-db-recovery 2>&1 | Out-Null
    exit 1
}

$dumpSize = (Get-Item "$DumpFile").Length
$dumpSizeMB = [math]::Round($dumpSize / 1MB, 1)
Write-Host "  OK: $dumpSizeMB MB" -ForegroundColor Green

# Erste Zeilen zeigen
Write-Host "  Erste 3 Zeilen:"
Get-Content "$DumpFile" -First 3 | ForEach-Object { Write-Host "    $_" }

# ---------------------------------------------------------------------------
# 6. Container stoppen
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Container stoppen ..." -ForegroundColor Yellow
docker stop odoo18-db-recovery 2>&1 | Out-Null
docker rm odoo18-db-recovery 2>&1 | Out-Null
Write-Host "  OK: Container entfernt" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Zusammenfassung
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RECOVERY PHASE 2 ABGESCHLOSSEN" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "pg_resetwal:    Erfolgreich" -ForegroundColor Green
Write-Host "PostgreSQL:     Lief" -ForegroundColor Green
Write-Host "odoo18_test:    Vorhanden" -ForegroundColor Green
Write-Host "pg_dump:        $DumpFile ($dumpSizeMB MB)" -ForegroundColor Green
Write-Host ""
Write-Host "Naechste Schritte (manuell oder per Folge-Script):" -ForegroundColor Yellow
Write-Host "  - Tabellen-Zaehlungen pruefen"
Write-Host "  - Filestore sichern"
Write-Host "  - Phase 3: Saubere DB + Dump importieren"
