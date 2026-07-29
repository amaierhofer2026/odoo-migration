# Odoo 18 Clean Backup: Dump + Filestore
# Creates a fresh backup of the currently working state

$OdooPath = "C:\Odoo-Test"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$BackupName = "odoo18_backup_clean_$Timestamp"
$BackupDir = "$OdooPath\backups\$BackupName"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Odoo 18: Clean Backup" -ForegroundColor Cyan
Write-Host "  $BackupName" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Set-Location $OdooPath

# Create backup directory
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
New-Item -ItemType Directory -Force -Path "$BackupDir\filestore" | Out-Null

# ============================================================
# 1. SQL Dump
# ============================================================
Write-Host ""
Write-Host "[1] Creating SQL dump..." -ForegroundColor Yellow
$DumpFile = "$BackupDir\dump.sql"
docker exec odoo18-db pg_dump -U odoo -d odoo18_test --no-owner --no-acl > $DumpFile 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: pg_dump failed!" -ForegroundColor Red
    Write-Host (Get-Content $DumpFile)
    exit 1
}

$dumpSizeMB = [math]::Round((Get-Item $DumpFile).Length / 1MB, 1)
Write-Host ("  Done: {0} MB" -f $dumpSizeMB)

# ============================================================
# 2. Filestore
# ============================================================
Write-Host ""
Write-Host "[2] Copying Filestore..." -ForegroundColor Yellow
docker cp odoo18:/var/lib/odoo/filestore/odoo18_test/. "$BackupDir\filestore" 2>&1

$filestoreCount = (Get-ChildItem -Path "$BackupDir\filestore" -Directory).Count
Write-Host ("  Done: {0} directories" -f $filestoreCount)

# ============================================================
# 3. Manifest
# ============================================================
Write-Host ""
Write-Host "[3] Writing manifest..." -ForegroundColor Yellow
$manifest = @"
{
  "created": "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
  "type": "clean_backup",
  "dump_size_mb": $dumpSizeMB,
  "filestore_dirs": $filestoreCount,
  "odoo_version": "18.0",
  "postgres_version": "16",
  "source": "odoo18-db:odoo18_test + odoo18:/var/lib/odoo/filestore/odoo18_test"
}
"@
$manifest | Out-File -FilePath "$BackupDir\manifest.json" -Encoding UTF8
Write-Host "  Done."

# ============================================================
# 4. Package as ZIP
# ============================================================
Write-Host ""
Write-Host "[4] Creating ZIP archive..." -ForegroundColor Yellow
$ZipFile = "$OdooPath\backups\$BackupName.zip"
Compress-Archive -Path "$BackupDir\*" -DestinationPath $ZipFile -Force

$zipSizeMB = [math]::Round((Get-Item $ZipFile).Length / 1MB, 1)
Write-Host ("  Done: {0} MB" -f $zipSizeMB)

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  BACKUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Directory: $BackupDir" -ForegroundColor White
Write-Host "  Archive:   $ZipFile" -ForegroundColor White
Write-Host ""
Write-Host ("  SQL dump:  {0} MB" -f $dumpSizeMB) -ForegroundColor White
Write-Host ("  Filestore: {0} directories" -f $filestoreCount) -ForegroundColor White
Write-Host ("  ZIP:       {0} MB" -f $zipSizeMB) -ForegroundColor White
