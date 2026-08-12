# ============================================================================
# PostgreSQL Recovery DIAGNOSTIC — Dry-Run ONLY (keine Aenderungen!)
# Prueft: User, Mount, PG_VERSION, pg_resetwal -n
# ============================================================================
$ErrorActionPreference = "Stop"
$BaseDir = "C:\Odoo-Test"
$RecoveryDir = "$BaseDir\postgres_recovery"
$DefektDir = "$BaseDir\postgres_defekt_2026-08-10"
$TempDir = $env:TEMP

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DIAGNOSE: pg_resetwal Dry-Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Frische Kopie erstellen
# ---------------------------------------------------------------------------
Write-Host "[1/4] Frische Arbeitskopie ..." -ForegroundColor Yellow
if (Test-Path $RecoveryDir) {
    Write-Host "  Loesche altes postgres_recovery"
    Remove-Item -Recurse -Force $RecoveryDir
}
Copy-Item -Recurse $DefektDir $RecoveryDir
$fc = @(Get-ChildItem -Recurse -File $RecoveryDir).Count
Write-Host "  OK: $fc Dateien" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Shell-Script fuer Container-Diagnose schreiben
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] Diagnose-Shellscript erstellen ..." -ForegroundColor Yellow

# @' ... '@ = PowerShell Here-String (single-quoted, KEINE Variablen-Expansion)
$diagScript = @'
#!/bin/sh
echo "=== whoami ==="
whoami
echo ""
echo "=== id ==="
id
echo ""
echo "=== ls -la /var/lib/postgresql/data/ ==="
ls -la /var/lib/postgresql/data/
echo ""
echo "=== PG_VERSION ==="
cat /var/lib/postgresql/data/PG_VERSION
echo ""
echo "=== postmaster.pid entfernen (Crash-Lockdatei) ==="
rm -f /var/lib/postgresql/data/postmaster.pid
echo "  entfernt (falls vorhanden)"
echo ""
echo "=== pg_resetwal -n (DRY RUN) ==="
chown -R postgres:postgres /var/lib/postgresql/data 2>/dev/null
su postgres -c "pg_resetwal -n /var/lib/postgresql/data" 2>&1
echo ""
echo "=== DONE (keine Aenderungen am WAL) ==="
'@

$diagFile = "$TempDir\pg_diag.sh"
$diagScript -replace "`r`n", "`n" | Out-File -FilePath $diagFile -Encoding ASCII
Write-Host "  OK: $diagFile" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 3. Container starten mit Shell-Script
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] Diagnose-Container starten ..." -ForegroundColor Yellow

# Container nur stoppen/loeschen wenn vorhanden (sonst ErrorActionPreference=Stop crasht)
$existingRecovery = docker ps -a --filter "name=^/odoo18-db-recovery$" --format "{{.Names}}" 2>&1
if ($existingRecovery -eq "odoo18-db-recovery") {
    docker stop odoo18-db-recovery 2>&1 | Out-Null
    docker rm odoo18-db-recovery 2>&1 | Out-Null
    Write-Host "  Alten Recovery-Container gestoppt und entfernt"
}

$diagOutput = docker run --rm `
    --name odoo18-db-recovery `
    -v "$RecoveryDir`:/var/lib/postgresql/data" `
    -v "${diagFile}:/tmp/pg_diag.sh:ro" `
    postgres:16 `
    sh /tmp/pg_diag.sh 2>&1

Write-Host "  Container-Output:"
Write-Host "  ----------------------------------------"
$diagOutput -split "`n" | ForEach-Object { Write-Host "  $_" }
Write-Host "  ----------------------------------------"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  FEHLER: Exit-Code $LASTEXITCODE" -ForegroundColor Red
}

# ---------------------------------------------------------------------------
# 4. Aufraeumen
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] Aufraeumen ..." -ForegroundColor Yellow
Remove-Item $diagFile -Force -ErrorAction SilentlyContinue
Write-Host "  Temp-Datei geloescht"
Write-Host ""
Write-Host "HINWEIS: postgres_recovery wurde durch chown veraendert." -ForegroundColor Yellow
Write-Host "Vor dem echten Recovery wird es FRISCH aus DefektDir kopiert." -ForegroundColor Yellow
