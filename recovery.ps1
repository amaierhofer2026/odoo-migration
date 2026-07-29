# Odoo 18 Recovery Script v3
# Wiederherstellung der Odoo-18-Testumgebung aus SQL-Dump vom 24.07.2026
# Erstellt: 29.07.2026
# v3: ASCII-only, keine Sonderzeichen, UTF-8 BOM, idempotent

$OdooPath = "C:\Odoo-Test"
$BackupPath = "$OdooPath\BACKUP-2026-07-29"
$DumpFile = "$BackupPath\extracted\dump.sql"
$FilestoreSource = "$BackupPath\extracted\filestore"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

# ============================================================
# Hilfsfunktionen
# ============================================================

function Write-Step {
    param([string]$Msg)
    Write-Host ""
    Write-Host $Msg -ForegroundColor Yellow
}

function Write-Ok {
    param([string]$Msg)
    Write-Host ("  " + $Msg) -ForegroundColor Green
}

function Write-Warn {
    param([string]$Msg)
    Write-Host ("  WARNUNG: " + $Msg) -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Msg)
    Write-Host ("  FEHLER: " + $Msg) -ForegroundColor Red
}

# Docker command wrapper: captures stderr without aborting, checks LASTEXITCODE
function Invoke-Docker {
    param(
        [string]$Description,
        [ScriptBlock]$Command
    )
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Command 2>&1 | ForEach-Object { Write-Host ("    [docker] " + $_) }
        $ok = ($LASTEXITCODE -eq 0)
        if (-not $ok) {
            Write-Err ($Description + " fehlgeschlagen (Exitcode " + $LASTEXITCODE + ")")
        }
        return $ok
    } finally {
        $ErrorActionPreference = $oldEAP
    }
}

# Check if a Docker container is running
function Test-ContainerRunning {
    param([string]$Name)
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $result = docker ps --format "{{.Names}}" 2>$null | Where-Object { $_ -eq $Name }
    $ErrorActionPreference = $oldEAP
    return ($null -ne $result)
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Odoo 18 Recovery Script v3" -ForegroundColor Cyan
Write-Host "  Restore from dump 2026-07-24" -ForegroundColor Cyan
Write-Host "  Idempotent - skips completed steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ============================================================
# SCHRITT 0: Checks
# ============================================================
Write-Step "[SCHRITT 0] Checks"

if (-not (Test-Path $OdooPath)) {
    Write-Err ("Path not found: " + $OdooPath)
    exit 1
}
if (-not (Test-Path $DumpFile)) {
    Write-Err ("Dump file not found: " + $DumpFile)
    exit 1
}

$DumpSize = (Get-Item $DumpFile).Length
$DumpSizeMB = [math]::Round($DumpSize / 1MB, 1)
Write-Ok ("Dump file: $DumpFile ({0} MB)" -f $DumpSizeMB)
Write-Ok ("Odoo path: $OdooPath")
Set-Location $OdooPath

# ============================================================
# SCHRITT 1: Stop containers (only if running)
# ============================================================
Write-Step "[SCHRITT 1] Stop Docker containers"

$OdooRunning = Test-ContainerRunning "odoo18"
$DbRunning = Test-ContainerRunning "odoo18-db"

if ($OdooRunning -or $DbRunning) {
    Write-Host "  Containers are running - stopping..." -ForegroundColor Cyan
    $ok = Invoke-Docker -Description "docker compose down" -Command { docker compose down }
    if (-not $ok) {
        Write-Warn "docker compose down failed. Trying individual stop..."
        if ($OdooRunning) {
            docker stop odoo18 2>$null
        }
        if ($DbRunning) {
            docker stop odoo18-db 2>$null
        }
    }
    Write-Ok "Containers stopped."
} else {
    Write-Ok "Containers already stopped - skipping."
}

# ============================================================
# SCHRITT 2: Rename damaged postgres data (do NOT delete!)
# ============================================================
Write-Step "[SCHRITT 2] Save damaged PostgreSQL data"

$PostgresPath = "$OdooPath\postgres"
if (Test-Path $PostgresPath) {
    if (Test-Path "$PostgresPath\base") {
        $DefektDir = "postgres_defekt_" + $Timestamp
        Rename-Item $PostgresPath $DefektDir
        Write-Ok ("Damaged postgres renamed to: " + $DefektDir)
    } else {
        Write-Warn "postgres folder exists but has no base/ directory. Already replaced?"
    }
} else {
    Write-Ok "No postgres folder - already renamed or new."
}

$ExistingDefekt = Get-ChildItem $OdooPath -Directory | Where-Object { $_.Name -like "postgres_defekt_*" }
if ($ExistingDefekt) {
    Write-Ok ("Existing safety copy: " + $ExistingDefekt.Name)
}

# ============================================================
# SCHRITT 3: Prepare filestore
# ============================================================
Write-Step "[SCHRITT 3] Prepare filestore"

$FilestorePath = "$OdooPath\filestore"
$FilestoreDbPath = "$FilestorePath\odoo18_test"

$ExistingFilestore = (Get-ChildItem -Recurse -File $FilestoreDbPath -ErrorAction SilentlyContinue | Measure-Object).Count
if ($ExistingFilestore -gt 0) {
    Write-Ok ("{0} filestore files already present - skipping." -f $ExistingFilestore)
} else {
    if (Test-Path $FilestoreDbPath) {
        $oldTotal = (Get-ChildItem -Recurse -File $FilestorePath -ErrorAction SilentlyContinue | Measure-Object).Count
        if ($oldTotal -gt 0) {
            $FilestoreAlt = "filestore_alt_" + $Timestamp
            Rename-Item $FilestorePath $FilestoreAlt
            Write-Ok ("Old filestore renamed to: " + $FilestoreAlt)
        }
    }

    New-Item -ItemType Directory -Force -Path $FilestoreDbPath | Out-Null

    if (Test-Path $FilestoreSource) {
        Copy-Item -Recurse ($FilestoreSource + "\*") ($FilestoreDbPath + "\") -Force
        $FilestoreCount = (Get-ChildItem -Recurse -File $FilestoreDbPath | Measure-Object).Count
        Write-Ok ("{0} filestore files restored from backup." -f $FilestoreCount)
    } else {
        Write-Warn "No filestore backup source found."
    }
}

# ============================================================
# SCHRITT 4: Start fresh PostgreSQL
# ============================================================
Write-Step "[SCHRITT 4] Start PostgreSQL container"

$DbRunning = Test-ContainerRunning "odoo18-db"
if (-not $DbRunning) {
    $ok = Invoke-Docker -Description "docker compose up -d db" -Command { docker compose up -d db }
    if (-not $ok) {
        Write-Err "Cannot start PostgreSQL container!"
        exit 1
    }
} else {
    Write-Ok "PostgreSQL container already running."
}

# Wait for PostgreSQL to be ready
Write-Host "  Waiting for PostgreSQL..." -ForegroundColor Cyan
$Ready = $false
for ($i = 0; $i -lt 30; $i++) {
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $result = docker exec odoo18-db pg_isready -U odoo 2>&1
    $ErrorActionPreference = $oldEAP
    if ($result -match "accepting connections") {
        $Ready = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $Ready) {
    Write-Err "PostgreSQL did not become ready in time!"
    docker compose logs db 2>&1 | Select-Object -Last 20
    exit 1
}
Write-Ok "PostgreSQL is ready."

# ============================================================
# SCHRITT 5: Create database odoo18_test
# ============================================================
Write-Step "[SCHRITT 5] Database odoo18_test"

$oldEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$dbCheck = docker exec odoo18-db psql -U odoo -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='odoo18_test'" 2>&1
$ErrorActionPreference = $oldEAP

$DumpAlreadyRestored = $false

if ($dbCheck -match "1") {
    Write-Ok "Database odoo18_test already exists."
    
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $tableResult = docker exec odoo18-db psql -U odoo -d odoo18_test -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>&1
    $ErrorActionPreference = $oldEAP
    
    $tableCount = $tableResult.Trim()
    $tableCountInt = 0
    try { $tableCountInt = [int]$tableCount } catch { $tableCountInt = 0 }
    
    if ($tableCountInt -gt 100) {
        Write-Ok ("Database already has {0} tables - dump was already restored." -f $tableCountInt)
        $DumpAlreadyRestored = $true
    } else {
        Write-Warn ("Database exists but only has {0} tables - recreating." -f $tableCountInt)
        $oldEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        docker exec odoo18-db psql -U odoo -d postgres -c "DROP DATABASE odoo18_test WITH (FORCE);" 2>&1 | Out-Null
        docker exec odoo18-db psql -U odoo -d postgres -c "CREATE DATABASE odoo18_test OWNER odoo;" 2>&1 | Out-Null
        $ErrorActionPreference = $oldEAP
        Write-Ok "Database odoo18_test recreated."
    }
} else {
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    docker exec odoo18-db psql -U odoo -d postgres -c "CREATE DATABASE odoo18_test OWNER odoo;" 2>&1 | Out-Null
    $ErrorActionPreference = $oldEAP
    Write-Ok "Database odoo18_test created."
}

# ============================================================
# SCHRITT 6: Restore SQL dump (only if not already done)
# ============================================================
Write-Step "[SCHRITT 6] Restore SQL dump"

if ($DumpAlreadyRestored) {
    Write-Ok "Dump already restored (detected in step 5) - skipping."
} else {
    $DumpSizeMB = [math]::Round((Get-Item $DumpFile).Length / 1MB, 1)
    Write-Host ("  Restoring dump.sql ({0} MB, may take several minutes)..." -f $DumpSizeMB) -ForegroundColor Cyan
    
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    
    $RestoreOutput = Get-Content $DumpFile | docker exec -i odoo18-db psql -U odoo -d odoo18_test 2>&1
    
    $ErrorActionPreference = $oldEAP
    
    $Errors = $RestoreOutput | Where-Object { $_ -match "ERROR:" }
    $Warnings = $RestoreOutput | Where-Object { $_ -match "WARNING:" }
    
    if ($Errors) {
        Write-Host "  Errors during restore:" -ForegroundColor Red
        $Errors | Select-Object -First 20 | ForEach-Object { Write-Err $_ }
        
        $CriticalErrors = $Errors | Where-Object { $_ -notmatch "already exists" }
        if (-not $CriticalErrors) {
            Write-Ok "Only 'already exists' messages - dump was probably already applied."
        }
    } else {
        Write-Ok "SQL dump restored successfully."
    }
    
    if ($Warnings) {
        Write-Warn "Warnings during restore:"
        $Warnings | Select-Object -First 5 | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor Yellow }
    }
}

# ============================================================
# SCHRITT 7: Start Odoo container
# ============================================================
Write-Step "[SCHRITT 7] Start Odoo container"

$OdooRunning = Test-ContainerRunning "odoo18"
if (-not $OdooRunning) {
    $ok = Invoke-Docker -Description "docker compose up -d odoo" -Command { docker compose up -d odoo }
    if (-not $ok) {
        Write-Err "Cannot start Odoo container!"
        exit 1
    }
} else {
    Write-Ok "Odoo container already running."
}

# Wait for Odoo to be ready
Write-Host "  Waiting for Odoo (may take up to 3 minutes on first start)..." -ForegroundColor Cyan
$OdooReady = $false
for ($i = 0; $i -lt 90; $i++) {
    try {
        $oldEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $response = Invoke-WebRequest -Uri "http://localhost:8069/web/login" -UseBasicParsing -TimeoutSec 3 2>$null
        $ErrorActionPreference = $oldEAP
        if ($response.StatusCode -eq 200) {
            $OdooReady = $true
            break
        }
    } catch {
        # Not ready yet
    }
    if ($i -eq 10) {
        Write-Host "    ... Odoo is initializing the database (slow on first run) ..." -ForegroundColor Cyan
    }
    if ($i -gt 0 -and $i % 30 -eq 0) {
        Write-Host ("    ... still starting (" + $i + " s)") -ForegroundColor Cyan
    }
    Start-Sleep -Seconds 2
}

if (-not $OdooReady) {
    Write-Warn "Odoo is not responding on http://localhost:8069"
    Write-Host "  Last Odoo logs:" -ForegroundColor Yellow
    docker compose logs odoo 2>&1 | Select-Object -Last 30
} else {
    Write-Ok "Odoo is ready at http://localhost:8069"
}

# ============================================================
# SCHRITT 8: Check logs for errors
# ============================================================
Write-Step "[SCHRITT 8] Check logs for errors"

# PostgreSQL
$PgLogs = docker compose logs db 2>&1 | Select-Object -Last 50
$PgErrors = $PgLogs | Where-Object { $_ -match "could not open|ERROR|FATAL|PANIC" }
if ($PgErrors) {
    Write-Err "PostgreSQL errors found:"
    $PgErrors | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor Red }
} else {
    Write-Ok "No PostgreSQL errors ('could not open' etc.) in logs."
}

# Odoo
$OdooLogs = docker compose logs odoo 2>&1 | Select-Object -Last 50
$OdooErrors = $OdooLogs | Where-Object { $_ -match "ERROR|CRITICAL|Traceback" }
if ($OdooErrors) {
    Write-Warn "Odoo errors in logs:"
    $OdooErrors | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor Yellow }
} else {
    Write-Ok "No Odoo errors in logs."
}

# ============================================================
# FINISH
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESTORE COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Data source: SQL dump from 2026-07-24" -ForegroundColor White
Write-Host "Database: odoo18_test" -ForegroundColor White
Write-Host "Odoo: http://localhost:8069" -ForegroundColor White
Write-Host ""
Write-Host "Safety copies:" -ForegroundColor White
$DefektDirs = Get-ChildItem $OdooPath -Directory | Where-Object { $_.Name -like "postgres_defekt_*" }
foreach ($d in $DefektDirs) {
    Write-Host ("  Damaged PostgreSQL: " + $OdooPath + "\" + $d.Name) -ForegroundColor DarkGray
}
Write-Host ("  Full backup: " + $BackupPath) -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Open http://localhost:8069 and verify login" -ForegroundColor White
Write-Host "  2. Check: contacts, subscriptions, helpdesk, OCA modules" -ForegroundColor White
Write-Host "  3. Update code from git: cd C:\Odoo-Test; git checkout main; git pull" -ForegroundColor White
Write-Host "  4. If needed: docker compose restart" -ForegroundColor White
Write-Host ""
