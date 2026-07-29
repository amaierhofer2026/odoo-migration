# Odoo 18 Recovery v2: UTF-8 correct restore (DB + Filestore)
# Problem: Get-Content | docker exec pipeline mangled UTF-8 to Windows-1252
# Fix: docker cp + psql -f inside container (no Windows pipeline)

$OdooPath = "C:\Odoo-Test"
$BackupPath = "$OdooPath\BACKUP-2026-07-29"
$DumpFile = "$BackupPath\extracted\dump.sql"
$FilestoreSource = "$BackupPath\extracted\filestore"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Odoo 18: UTF-8 Correct Restore v2" -ForegroundColor Cyan
Write-Host "  DB + Filestore" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Set-Location $OdooPath

$dumpSizeMB = [math]::Round((Get-Item $DumpFile).Length / 1MB, 1)
$filestoreDirs = (Get-ChildItem -Path $FilestoreSource -Directory).Count
Write-Host ("Dump: {0} MB, Filestore: {1} directories" -f $dumpSizeMB, $filestoreDirs)

# ============================================================
# 1. Stop Odoo, ensure PostgreSQL is running
# ============================================================
Write-Host ""
Write-Host "[1] Stop Odoo container..." -ForegroundColor Yellow
docker stop odoo18 2>$null
docker rm odoo18 2>$null

# Ensure db container is running
$dbRunning = docker ps --format '{{.Names}}' | Select-String "odoo18-db"
if (-not $dbRunning) {
    Write-Host "  Starting db container..." -ForegroundColor Yellow
    docker compose up -d db 2>&1 | Out-Null
    Start-Sleep -Seconds 3
}
Write-Host "  Ready."

# ============================================================
# 2. Drop and recreate database with UTF8
# ============================================================
Write-Host ""
Write-Host "[2] Drop and recreate odoo18_test (UTF8)..." -ForegroundColor Yellow
docker exec odoo18-db psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS odoo18_test WITH (FORCE);" 2>&1 | ForEach-Object { Write-Host "    $_" }
docker exec odoo18-db psql -U odoo -d postgres -c "CREATE DATABASE odoo18_test OWNER odoo ENCODING 'UTF8';" 2>&1 | ForEach-Object { Write-Host "    $_" }
Write-Host "  Created."

# ============================================================
# 3. Copy dump into container and restore
# ============================================================
Write-Host ""
Write-Host "[3] Copy dump into container..." -ForegroundColor Yellow
docker cp "$DumpFile" odoo18-db:/tmp/dump.sql
Write-Host "  Copied."

Write-Host ""
Write-Host "[4] Restore dump (this may take several minutes)..." -ForegroundColor Yellow
$output = docker exec odoo18-db psql -U odoo -d odoo18_test -f /tmp/dump.sql 2>&1

# Count and categorize messages
$errors = $output | Where-Object { $_ -match "ERROR:" }
$warnings = $output | Where-Object { $_ -match "WARNING:" }
$critical = $errors | Where-Object {
    $_ -notmatch "transaction_timeout" -and
    $_ -notmatch "already exists" -and
    $_ -notmatch "does not exist"
}

if ($critical) {
    Write-Host "  CRITICAL errors:" -ForegroundColor Red
    $critical | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
} else {
    Write-Host "  Restore complete." -ForegroundColor Green
    if ($errors.Count -gt 0) {
        Write-Host ("  Non-critical messages: " + $errors.Count) -ForegroundColor DarkGray
    }
}
docker exec odoo18-db rm /tmp/dump.sql 2>$null

# ============================================================
# 4. Verify tables
# ============================================================
Write-Host ""
Write-Host "[5] Verify tables..." -ForegroundColor Yellow
$tableCount = docker exec odoo18-db psql -U odoo -d odoo18_test -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>&1
Write-Host ("  Tables: " + $tableCount.Trim())

# Check a few key tables
$contactCount = docker exec odoo18-db psql -U odoo -d odoo18_test -t -c "SELECT COUNT(*) FROM res_partner;" 2>&1
Write-Host ("  Contacts (res_partner): " + $contactCount.Trim())

# ============================================================
# 5. Restore Filestore
# ============================================================
Write-Host ""
Write-Host "[6] Restore Filestore..." -ForegroundColor Yellow
# Start odoo18 so the container exists
docker compose up -d odoo 2>&1 | Out-Null
Start-Sleep -Seconds 5

# Create filestore directory and copy files
docker exec odoo18 mkdir -p /var/lib/odoo/filestore/odoo18_test 2>$null
docker cp "$FilestoreSource\." odoo18:/tmp/filestore_restore 2>&1
docker exec odoo18 sh -c "cp -r /tmp/filestore_restore/* /var/lib/odoo/filestore/odoo18_test/ 2>/dev/null; rm -rf /tmp/filestore_restore" 2>&1 | Out-Null

$restoredCount = docker exec odoo18 sh -c "ls /var/lib/odoo/filestore/odoo18_test/ 2>/dev/null | wc -l" 2>&1
Write-Host ("  Filestore entries: " + $restoredCount.Trim())

# ============================================================
# 6. Restart Odoo and wait
# ============================================================
Write-Host ""
Write-Host "[7] Restart Odoo..." -ForegroundColor Yellow
docker restart odoo18 2>&1 | Out-Null
Write-Host "  Waiting for Odoo to initialize..."

for ($i = 0; $i -lt 120; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8069/web/login" -UseBasicParsing -TimeoutSec 3 2>$null
        if ($resp.StatusCode -eq 200) {
            Write-Host ("  Odoo ready after ~" + ($i*2) + " seconds.") -ForegroundColor Green
            break
        }
    } catch {}
    if ($i -eq 15) { Write-Host "  ... initializing database (this can take 1-2 minutes) ..." -ForegroundColor Cyan }
    Start-Sleep -Seconds 2
}

# ============================================================
# 7. Quick verification
# ============================================================
Write-Host ""
Write-Host "[8] Quick verification..." -ForegroundColor Yellow

# Check login page contains proper German text
try {
    $body = (Invoke-WebRequest -Uri "http://localhost:8069" -UseBasicParsing -TimeoutSec 5).Content
    if ($body -match "Nützliche Links" -or $body -match "nützliche") {
        Write-Host "  German characters: OK" -ForegroundColor Green
    } else {
        Write-Host "  German characters: CHECK MANUALLY" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Could not verify homepage." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DONE - DB + Filestore restored" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  http://localhost:8069" -ForegroundColor White
Write-Host ""
Write-Host "Manually verify:" -ForegroundColor White
Write-Host "  - Login works" -ForegroundColor White
Write-Host "  - German characters (Nutzliche Links, Uber uns)" -ForegroundColor White
Write-Host "  - Contacts, Subscriptions, Helpdesk tickets" -ForegroundColor White
Write-Host "  - Attachments / uploaded files" -ForegroundColor White
