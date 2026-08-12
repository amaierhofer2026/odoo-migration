# ============================================================================
# Odoo 18 Disaster Recovery --- Phase 3A v8 (final)
# Clean Restore 29.07. + Odoo-Start (KEINE Modul-Upgrades)
# v8: final, ausgefuehrt am 11.08.2026 (Details: PROJECT_KNOWLEDGE.md Session 71)
# ============================================================================
$ErrorActionPreference = "Stop"
$BaseDir = "C:\Odoo-Test"
$BackupZip = "$BaseDir\backups\odoo18_backup_clean_2026-07-29_1248.zip"
$ComposeFile = "$BaseDir\docker-compose.yml"
$ComposeNew = "$BaseDir\docker-compose.phase3.yml"
$Timestamp = "2026-08-11"
$TempDir = $env:TEMP
$VolumeName = "odoo18_pgdata"
$DbName = "odoo18_test"
$DbUser = "odoo"
$DbPassword = "odoo"

# ============================================================================
# PREFLIGHT
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHASE 3A v7 --- Clean Restore 29.07." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. PowerShell
Write-Host "[1/10] PowerShell $($PSVersionTable.PSVersion)" -ForegroundColor Yellow
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "  FEHLER: PS 5.1+ erforderlich" -ForegroundColor Red
    exit 1
}

# 2. Backup ZIP
Write-Host "[2/10] Backup ZIP" -ForegroundColor Yellow
if (-not (Test-Path $BackupZip)) {
    Write-Host "  FEHLER: $BackupZip nicht gefunden" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: $BackupZip" -ForegroundColor Green

# 3. Docker
Write-Host "[3/10] Docker" -ForegroundColor Yellow
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
$dc = docker --version 2>&1; $dcExit = $LASTEXITCODE
$ErrorActionPreference = $oldEap
if ($dcExit -ne 0) {
    Write-Host "  FEHLER: Docker nicht verfuegbar" -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# 4. postgres:16 Image
Write-Host "[4/10] postgres:16 Image" -ForegroundColor Yellow
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
$img = docker images postgres:16 --format "{{.Tag}}" 2>&1; $imgExit = $LASTEXITCODE
$ErrorActionPreference = $oldEap
if ($imgExit -ne 0) {
    Write-Host "  FEHLER: postgres:16 nicht gefunden" -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# 5. Container-Status
Write-Host "[5/10] Container-Status" -ForegroundColor Yellow
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
$running = docker ps --format "{{.Names}}" 2>&1
$ErrorActionPreference = $oldEap
$odoos = @($running -split "`n" | Where-Object { $_ -match "odoo18" })
if ($odoos.Count -gt 0) {
    Write-Host "  FEHLER: Container laufen: $odoos" -ForegroundColor Red
    Write-Host "  Bitte: cd $BaseDir; docker compose stop" -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# 6. Named Volume
Write-Host "[6/10] Volume $VolumeName" -ForegroundColor Yellow
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
$vols = docker volume ls --format "{{.Name}}" 2>&1
$ErrorActionPreference = $oldEap
$filtered = $vols -split "`n" | Where-Object { $_ -eq $VolumeName }
$volExists = ($filtered).Count -gt 0
if ($volExists) {
    Write-Host "  HINWEIS: Existiert bereits --- wird nicht geleert" -ForegroundColor Yellow
} else {
    Write-Host "  OK: Wird neu erstellt" -ForegroundColor Green
}

# 7. compose-Dateien
Write-Host "[7/10] compose-Dateien" -ForegroundColor Yellow
if (-not (Test-Path $ComposeFile)) {
    Write-Host "  FEHLER: $ComposeFile fehlt" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $ComposeNew)) {
    Write-Host "  FEHLER: $ComposeNew fehlt" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: Beide vorhanden" -ForegroundColor Green

# 8. ZIP-Inhalt
Write-Host "[8/10] ZIP-Inhalt" -ForegroundColor Yellow
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($BackupZip)
$hasDump = $false
$hasFS = $false
foreach ($e in $zip.Entries) {
    if ($e.Name -eq "dump.sql") { $hasDump = $true }
    $normPath = $e.FullName.Replace('\', '/')
    if ($normPath -like "filestore/*" -and $e.Name -ne "") { $hasFS = $true }
}
$zip.Dispose()
if (-not $hasDump) { Write-Host "  FEHLER: dump.sql fehlt" -ForegroundColor Red; exit 1 }
if (-not $hasFS) { Write-Host "  FEHLER: filestore fehlt" -ForegroundColor Red; exit 1 }
Write-Host "  OK: dump.sql + filestore" -ForegroundColor Green

# 9. Geschuetzte Verzeichnisse
Write-Host "[9/10] Geschuetzte Verzeichnisse" -ForegroundColor Yellow
$p1 = "$BaseDir\postgres"
$p2 = "$BaseDir\postgres_defekt_2026-08-10"
$p3 = "$BaseDir\postgres_defekt_2026-07-29_114402"
$p4 = "$BaseDir\postgres_recovery"
if (Test-Path $p1) { Write-Host "  $p1 --- BLEIBT" -ForegroundColor Green }
if (Test-Path $p2) { Write-Host "  $p2 --- BLEIBT" -ForegroundColor Green }
if (Test-Path $p3) { Write-Host "  $p3 --- BLEIBT" -ForegroundColor Green }
if (Test-Path $p4) { Write-Host "  $p4 --- BLEIBT" -ForegroundColor Green }

# 10. Zusammenfassung
Write-Host "[10/10] Parameter" -ForegroundColor Yellow
Write-Host "  Quelle:      $BackupZip" -ForegroundColor White
Write-Host "  DB:          $DbName" -ForegroundColor White
Write-Host "  Volume:      $VolumeName" -ForegroundColor White
Write-Host "  compose-NEU: $ComposeNew" -ForegroundColor White
Write-Host ""

$antwort = Read-Host "Phase 3A jetzt starten? (ja/nein)"
if ($antwort -ne "ja") {
    Write-Host "ABBRUCH." -ForegroundColor Yellow
    exit 0
}

# ============================================================================
# SCHRITT 1: docker-compose.yml sichern
# ============================================================================
Write-Host ""
Write-Host "=== [1/10] compose sichern ===" -ForegroundColor Cyan
$composeBak = "$BaseDir\docker-compose.before_phase3_$Timestamp.yml"
Copy-Item $ComposeFile $composeBak
Write-Host "  OK: $composeBak" -ForegroundColor Green

# ============================================================================
# SCHRITT 2: docker-compose.phase3.yml -> docker-compose.yml
# ============================================================================
Write-Host ""
Write-Host "=== [2/10] compose aktivieren ===" -ForegroundColor Cyan
Copy-Item $ComposeNew $ComposeFile
Write-Host "  OK: $ComposeNew -> $ComposeFile" -ForegroundColor Green

# ============================================================================
# SCHRITT 3: Named Volume
# ============================================================================
Write-Host ""
Write-Host "=== [3/10] Volume $VolumeName ===" -ForegroundColor Cyan
if (-not $volExists) {
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    docker volume create $VolumeName 2>&1 | Out-Null
    $volExit = $LASTEXITCODE
    $ErrorActionPreference = $oldEap
    if ($volExit -ne 0) {
        Write-Host "  FEHLER: Volume-Erstellung" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK: Erstellt" -ForegroundColor Green
} else {
    # Volume existiert bereits (von abgebrochenem Lauf) --- kontrolliert entfernen
    # Sicherstellen dass kein Container das Volume nutzt
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $existC = docker ps -a --filter "name=^/odoo18-restore$" --format "{{.Names}}" 2>&1
    $ErrorActionPreference = $oldEap
    if ($existC -eq "odoo18-restore") {
        $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        docker stop odoo18-restore 2>&1 | Out-Null
        docker rm odoo18-restore 2>&1 | Out-Null
        $ErrorActionPreference = $oldEap
        Write-Host "  Alter Restore-Container entfernt"
    }
    # Volume loeschen und neu erstellen
    Write-Host "  Entferne altes Volume ..."
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    docker volume rm $VolumeName 2>&1 | Out-Null
    $rmExit = $LASTEXITCODE
    $ErrorActionPreference = $oldEap
    if ($rmExit -ne 0) {
        Write-Host "  FEHLER: Volume konnte nicht geloescht werden (Exit $rmExit)" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK: Altes Volume geloescht" -ForegroundColor Green
    # Frisch erstellen
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    docker volume create $VolumeName 2>&1 | Out-Null
    $crExit = $LASTEXITCODE
    $ErrorActionPreference = $oldEap
    if ($crExit -ne 0) {
        Write-Host "  FEHLER: Volume konnte nicht erstellt werden (Exit $crExit)" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK: Frisches Volume erstellt" -ForegroundColor Green
}

# ============================================================================
# SCHRITT 4: ZIP extrahieren
# ============================================================================
Write-Host ""
Write-Host "=== [4/10] ZIP extrahieren ===" -ForegroundColor Cyan
$extractDir = "$TempDir\odoo18_restore_$Timestamp"
if (Test-Path $extractDir) {
    Remove-Item -Recurse -Force $extractDir
}
[System.IO.Compression.ZipFile]::ExtractToDirectory($BackupZip, $extractDir)
$cnt = @(Get-ChildItem -Recurse -File $extractDir).Count
Write-Host "  OK: $cnt Dateien" -ForegroundColor Green
$fsCheck = "$extractDir\filestore"
if (-not (Test-Path $fsCheck)) {
    Write-Host "  FEHLER: filestore/ nicht im Extrakt" -ForegroundColor Red
    exit 1
}
Write-Host "  filestore/ vorhanden" -ForegroundColor Green

# ============================================================================
# SCHRITT 5: dump.sql UTF-16 -> UTF-8
# ============================================================================
Write-Host ""
Write-Host "=== [5/10] dump.sql konvertieren ===" -ForegroundColor Cyan
$dumpSrc = "$extractDir\dump.sql"
$dumpUtf8 = "$TempDir\odoo18_dump_$Timestamp.sql"
Write-Host "  Lese dump.sql (UTF-16 LE) ..."
$raw = Get-Content $dumpSrc -Encoding Unicode -Raw
$raw | Set-Content $dumpUtf8 -Encoding UTF8 -NoNewline
Write-Host "  OK: $dumpUtf8" -ForegroundColor Green

# ============================================================================
# SCHRITT 6: Filestore sichern + wiederherstellen
# ============================================================================
Write-Host ""
Write-Host "=== [6/10] Filestore ===" -ForegroundColor Cyan
$fsDir = "$BaseDir\filestore"
$fsBak = "$BaseDir\filestore_before_phase3_$Timestamp"
if (Test-Path $fsDir) {
    Move-Item $fsDir $fsBak
    Write-Host "  Gesichert: $fsBak" -ForegroundColor Green
}
$zipFS = "$extractDir\filestore"
Copy-Item -Recurse $zipFS $fsDir
$fsCnt = @(Get-ChildItem -Recurse -File $fsDir).Count
Write-Host "  OK: $fsCnt Dateien aus ZIP" -ForegroundColor Green

# ============================================================================
# SCHRITT 7: PG 16 im Volume initialisieren
# ============================================================================
Write-Host ""
Write-Host "=== [7/10] PG 16 im Volume ===" -ForegroundColor Cyan

# Shell-Script fuer DB-Erstellung + Import
$initScript = @'
#!/bin/sh
set -e
echo "=== pg_isready ==="
pg_isready -U odoo
echo ""
echo "=== CREATE DATABASE ==="
psql -U odoo -d postgres -t -c "CREATE DATABASE odoo18_test OWNER odoo" 2>&1 || true
echo ""
echo "=== IMPORT DUMP ==="
psql -U odoo -d odoo18_test -f /tmp/dump.sql 2>&1
RC=$?
echo ""
echo "=== TABLE COUNT ==="
psql -U odoo -d odoo18_test -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>&1
echo ""
echo "=== EXIT: $RC ==="
exit $RC
'@

$initFile = "$TempDir\pg_init.sh"
$initScript -replace "`r`n", "`n" | Out-File -FilePath $initFile -Encoding ASCII

Write-Host "  Starte postgres:16 ..."
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
docker run -d --name odoo18-restore -e POSTGRES_DB=postgres -e "POSTGRES_USER=$DbUser" -e "POSTGRES_PASSWORD=$DbPassword" -v "${VolumeName}:/var/lib/postgresql/data" postgres:16 2>&1 | Out-Null
$runExit = $LASTEXITCODE
$ErrorActionPreference = $oldEap
if ($runExit -ne 0) {
    Write-Host "  FEHLER: Container-Start" -ForegroundColor Red
    exit 1
}

Write-Host "  Warte auf pg_isready ..."
Start-Sleep -Seconds 5
$rdy = $false
for ($i = 1; $i -le 15; $i++) {
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $ck = docker exec odoo18-restore pg_isready -U $DbUser 2>&1
    $pgExit = $LASTEXITCODE
    $ErrorActionPreference = $oldEap
    if ($ck -match "accepting connections") {
        $rdy = $true
        Write-Host "  OK: Bereit nach $i Versuchen" -ForegroundColor Green
        break
    }
    Write-Host "  Versuch $i/15 ..."
    Start-Sleep -Seconds 3
}
if (-not $rdy) {
    Write-Host "  FEHLER: PostgreSQL nicht bereit" -ForegroundColor Red
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    docker logs --tail 30 odoo18-restore
    docker stop odoo18-restore 2>&1 | Out-Null
    docker rm odoo18-restore 2>&1 | Out-Null
    $ErrorActionPreference = $oldEap
    exit 1
}

# ============================================================================
# SCHRITT 8: Dump importieren
# ============================================================================
Write-Host ""
Write-Host "=== [8/10] Dump importieren ===" -ForegroundColor Cyan

Write-Host "  Kopiere Dump + Script in Container ..."

$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
docker cp "$dumpUtf8" odoo18-restore:/tmp/dump.sql 2>&1 | Out-Null
$cp1Exit = $LASTEXITCODE
docker cp "$initFile" odoo18-restore:/tmp/pg_init.sh 2>&1 | Out-Null
$cp2Exit = $LASTEXITCODE
$ErrorActionPreference = $oldEap

if ($cp1Exit -ne 0) {
    Write-Host "  FEHLER: docker cp dump.sql (Exit $cp1Exit)" -ForegroundColor Red
    docker stop odoo18-restore 2>&1 | Out-Null
    docker rm odoo18-restore 2>&1 | Out-Null
    exit 1
}
if ($cp2Exit -ne 0) {
    Write-Host "  FEHLER: docker cp pg_init.sh (Exit $cp2Exit)" -ForegroundColor Red
    docker stop odoo18-restore 2>&1 | Out-Null
    docker rm odoo18-restore 2>&1 | Out-Null
    exit 1
}
Write-Host "  OK: Dump + Script kopiert" -ForegroundColor Green

Write-Host "  Fuehre Import aus (kann Minuten dauern) ..."
$importLog = "$TempDir\odoo18_import_$Timestamp.txt"
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
docker exec odoo18-restore sh /tmp/pg_init.sh 2>&1 | Out-File $importLog -Encoding UTF8
$importExit = $LASTEXITCODE
$ErrorActionPreference = $oldEap

if ($importExit -ne 0) {
    Write-Host "  FEHLER: Import Exit-Code $importExit" -ForegroundColor Red
    Write-Host "  Letzte Zeilen Log:"
    Get-Content $importLog -Tail 20
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    docker stop odoo18-restore 2>&1 | Out-Null
    docker rm odoo18-restore 2>&1 | Out-Null
    $ErrorActionPreference = $oldEap
    exit 1
}

# ERROR/FATAL im Log checken
$errs = Select-String -Path $importLog -Pattern "ERROR:" -SimpleMatch 2>&1
$fatals = Select-String -Path $importLog -Pattern "FATAL:" -SimpleMatch 2>&1
if ($errs -or $fatals) {
    Write-Host "  WARNUNG: Fehler im Log:" -ForegroundColor Yellow
    $errCount = if ($errs) { $errs.Count } else { 0 }; if ($errs) { Write-Host "    ERRORs: $errCount" -ForegroundColor Yellow }
    $fatCount = if ($fatals) { $fatals.Count } else { 0 }; if ($fatals) { Write-Host "    FATALs: $fatCount" -ForegroundColor Yellow }
    Write-Host "  Vollstaendiges Log: $importLog" -ForegroundColor Yellow
} else {
    Write-Host "  OK: Keine ERROR/FATAL" -ForegroundColor Green
}

# Aufraeumen im Container
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
docker exec odoo18-restore rm /tmp/dump.sql /tmp/pg_init.sh 2>$null
$ErrorActionPreference = $oldEap
Remove-Item $initFile -Force -ErrorAction SilentlyContinue

# Tabellen anzeigen
Write-Host "  Letzte Zeilen Log:"
Get-Content $importLog -Tail 5

# ============================================================================
# SCHRITT 9: Restore-Container stoppen
# ============================================================================
Write-Host ""
Write-Host "=== [9/10] Restore-Container stoppen ===" -ForegroundColor Cyan
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
docker stop odoo18-restore 2>&1 | Out-Null
docker rm odoo18-restore 2>&1 | Out-Null
$ErrorActionPreference = $oldEap
Write-Host "  OK" -ForegroundColor Green

# ============================================================================
# SCHRITT 10: Odoo starten
# ============================================================================
Write-Host ""
Write-Host "=== [10/10] Odoo starten ===" -ForegroundColor Cyan

Push-Location $BaseDir
$oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
docker compose up -d 2>&1
$composeExit = $LASTEXITCODE
$ErrorActionPreference = $oldEap
Pop-Location

if ($composeExit -ne 0) {
    Write-Host "  FEHLER: docker compose up (Exit $composeExit)" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: Container gestartet" -ForegroundColor Green

Write-Host "  Warte auf Odoo (max 120s) ..."
$odoordy = $false
for ($i = 1; $i -le 24; $i++) {
    Start-Sleep -Seconds 5
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8069/web/login" -TimeoutSec 5 -UseBasicParsing
        if ($r.StatusCode -eq 200) {
            $odoordy = $true
            $elapsed = $i * 5; Write-Host "  OK: Odoo HTTP 200 nach ${elapsed}s" -ForegroundColor Green
            break
        }
    } catch {
        if ($i -le 3) { Write-Host "  Versuch $i/24 ..." }
    }
}

if (-not $odoordy) {
    Write-Host "  FEHLER: Odoo nicht erreichbar" -ForegroundColor Red
    $oldEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    docker logs --tail 20 odoo18-db
    docker logs --tail 20 odoo18
    $ErrorActionPreference = $oldEap
    exit 1
}

# ============================================================================
# ZUSAMMENFASSUNG
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHASE 3A ABGESCHLOSSEN" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Odoo:          http://localhost:8069" -ForegroundColor Green
Write-Host "Volume:        $VolumeName" -ForegroundColor Green
Write-Host "DB:            $DbName" -ForegroundColor Green
Write-Host "compose-Backup: $composeBak" -ForegroundColor Green
Write-Host "fs-Backup:     $fsBak" -ForegroundColor Green
Write-Host "Import-Log:    $importLog" -ForegroundColor Green
Write-Host ""
Write-Host "BITTE PRUEFEN:" -ForegroundColor Yellow
Write-Host "  1. Login: anna.maierhofer@it-kommunal.at / <Passwort aus scripts/test_migration_contacts.py>" -ForegroundColor Yellow
Write-Host "  2. Module installiert?" -ForegroundColor Yellow
Write-Host "  3. DB odoo18_test korrekt?" -ForegroundColor Yellow
Write-Host ""
Write-Host "Phase 3B (Modul-Upgrades) erst nach Freigabe!" -ForegroundColor Yellow
