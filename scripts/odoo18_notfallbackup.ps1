<#
.SYNOPSIS
    Notfall-Backup fuer die lokale Odoo-18-Testumgebung (ITK).
    Erstellt pro Lauf einen Zeitstempel-Ordner mit pg_dump (custom-Format),
    Filestore-Kopie und backup_info.txt.

.DESCRIPTION
    - PostgreSQL-DB odoo18_test: logischer pg_dump im Container (--file),
      Restore-Eignung via 'pg_restore --list', dann docker cp auf den Host.
      Bewusst KEINE PowerShell-Pipeline fuer den Dump (Encoding-Korruption!).
    - Filestore: robocopy von C:\Odoo-Test\filestore\odoo18_test (Bind-Mount).
    - Metadaten: backup_info.txt mit Versionen, Git-Stand, Ergebnissen.
    - Validierung: pg_dump Exit 0, pg_restore --list Exit 0, Dump > 0 Bytes,
      Filestore vorhanden, Ziel beschreibbar. Fehler -> Log + Exit 1.
    - STRENG READ-ONLY gegen die Live-Umgebung: keine Container-Stops, kein
      Zugriff auf das Named Volume odoo18_pgdata, keine DB-Modifikation,
      keine Loeschungen am Datenbestand.

    Kompatibilitaet: Windows PowerShell 5.1 (keine PS7-only-Syntax).
    Docker-Native-Commands werden ausschliesslich ueber $LASTEXITCODE
    ausgewertet; harmlose stderr-Ausgaben gelten nicht als Fehler.

.PARAMETER BackupRoot
    Zielverzeichnis fuer Backups (Standard: C:\Odoo-Notfallbackup)

.PARAMETER DbContainer / OdooContainer
    Container-Namen laut docker-compose.yml (odoo18-db / odoo18)

.PARAMETER DbName / DbUser
    Datenbank und DB-User (postgres:16 Image, POSTGRES_USER=odoo)

.PARAMETER PgVolume
    Docker-Named-Volume der PostgreSQL-Daten (nur fuer die Metadaten)

.PARAMETER FilestoreSource
    Host-Pfad des Filestores (Bind-Mount ./filestore im Container)

.PARAMETER GitRepo
    Lokales Git-Repo fuer Branch/Commit (nur Lesen)

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File C:\Odoo-Test\scripts\odoo18_notfallbackup.ps1
#>
[CmdletBinding()]
param(
    [string]$BackupRoot      = 'C:\Odoo-Notfallbackup',
    [string]$DbContainer     = 'odoo18-db',
    [string]$OdooContainer   = 'odoo18',
    [string]$DbName          = 'odoo18_test',
    [string]$DbUser          = 'odoo',
    [string]$PgVolume        = 'odoo18_pgdata',
    [string]$FilestoreSource = 'C:\Odoo-Test\filestore\odoo18_test',
    [string]$GitRepo         = 'C:\Odoo-Test'
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- Lauf-Setup
# Kollisionsschutz: gleicher Zeitstempel (z.B. manueller Doppellauf in derselben
# Minute) erhaelt Suffix _2, _3, ... statt das vorherige Backup zu ueberschreiben.
$RunName    = Get-Date -Format 'yyyy-MM-dd_HHmm'
$RunDir     = Join-Path $BackupRoot $RunName
$collision  = 2
while (Test-Path -LiteralPath $RunDir) {
    $RunName = (Get-Date -Format 'yyyy-MM-dd_HHmm') + "_$collision"
    $RunDir  = Join-Path $BackupRoot $RunName
    $collision++
}
$LogDir     = Join-Path $BackupRoot 'logs'
$LogFile    = Join-Path $LogDir ("backup_" + $RunName + ".log")
$DumpName   = $DbName + '_' + $RunName + '.dump'          # Name im Container (/tmp)
$DumpTarget = Join-Path $RunDir ($DbName + '.dump')       # Ziel auf dem Host
$FsDestDir  = Join-Path $RunDir 'filestore'
$FsDest     = Join-Path $FsDestDir $DbName
$InfoFile   = Join-Path $RunDir 'backup_info.txt'

# Sammelpunkt fuer Validierungs-/Schrittfehler (nicht-destruktiv, nur Buchhaltung)
$script:Failures = New-Object System.Collections.ArrayList

function Write-Log {
    param([string]$Msg)
    $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HHmmss'), $Msg
    try { Add-Content -Path $LogFile -Value $line -Encoding UTF8 } catch { Write-Host $line }
}

function Add-Failure {
    param([string]$Msg)
    [void]$script:Failures.Add($Msg)
    Write-Log ("FEHLER: " + $Msg)
}

# Jeder docker-Aufruf wird danach ueber $LASTEXITCODE geprueft; stderr wird
# bewusst ignoriert (docker schreibt dort auch harmlose Meldungen hin).
function Invoke-DockerChecked {
    param([string]$StepName, [scriptblock]$Block)
    try {
        & $Block | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Add-Failure ("$StepName fehlgeschlagen (Exit-Code " + $LASTEXITCODE + ")")
            return $false
        }
        return $true
    } catch {
        Add-Failure ("${StepName}: Exception - " + $_.Exception.Message)
        return $false
    }
}

function Format-Bytes {
    param([int64]$Bytes)
    if ($Bytes -ge 1GB) { return ("{0:N2} GB" -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ("{0:N2} MB" -f ($Bytes / 1MB)) }
    return ("{0:N0} KB" -f ($Bytes / 1KB))
}

# ------------------------------------------------------------- Metadaten-Rohdaten
$script:OdooVersion   = 'n/a'
$script:PgVersion     = 'n/a'
$script:GitBranch     = 'n/a'
$script:GitCommit     = 'n/a'
$script:VolumeName    = $PgVolume

# ---------------------------------------------------------------- Ablauf
Write-Host ("Odoo 18 Notfallbackup - Lauf " + $RunName)

# 1) Zielverzeichnisse + Schreibbarkeits-Check (Backup-Ziel beschreibbar?)
try {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
} catch {
    Write-Host ("KRITISCH: BackupRoot nicht anlegbar/beschreibbar: " + $_.Exception.Message)
    exit 1
}
$probe = Join-Path $RunDir '.write_test'
try {
    Set-Content -Path $probe -Value 'probe' -Encoding ASCII
    Remove-Item -Path $probe -Force
    Write-Log "Schreibbarkeits-Check Backup-Ziel: OK"
} catch {
    Add-Failure ("Backup-Ziel nicht beschreibbar: " + $_.Exception.Message)
}

# 2) Metadaten sammeln (jeweils mit Fallback, Fehler sind nicht fatal)
try { $script:OdooVersion = (docker exec $OdooContainer python3 -c "from odoo.release import version; print(version)" 2>$null) } catch { }
try { $script:PgVersion   = (docker exec $DbContainer psql --version 2>$null) } catch { }
try { $script:GitBranch   = (git -C $GitRepo rev-parse --abbrev-ref HEAD 2>$null) } catch { }
try { $script:GitCommit   = (git -C $GitRepo rev-parse HEAD 2>$null) } catch { }
Write-Log ("Metadaten: Odoo=" + $script:OdooVersion + " | PG=" + $script:PgVersion + " | Git=" + $script:GitBranch + "@" + $script:GitCommit)

# 3) PostgreSQL-Dump (logisch, custom-Format, im Container erzeugt -> kein
#    Binary-Stream durch PowerShell; das Named Volume wird NIE angefasst)
$dumpOk = $true
if (-not (Invoke-DockerChecked -StepName 'pg_dump' -Block { docker exec $DbContainer pg_dump -U $DbUser --format=custom ("--file=/tmp/" + $DumpName) $DbName })) {
    $dumpOk = $false
}
# Restore-Eignung: pg_restore --list muss den Dump-Header lesen koennen
if ($dumpOk) {
    $toc = @(docker exec $DbContainer pg_restore --list ("/tmp/" + $DumpName) 2>$null)
    if ($LASTEXITCODE -eq 0) {
        Write-Log ("Restore-Eignung pg_restore --list: OK (" + $toc.Count + " TOC-Zeilen)")
    } else {
        Add-Failure 'pg_restore --list konnte den Dump nicht lesen (kein gueltiges Custom-Format)'
        $dumpOk = $false
    }
}
# Dump auf den Host holen
if ($dumpOk) {
    if (Invoke-DockerChecked -StepName 'docker cp (Dump)' -Block { docker cp ($DbContainer + ":/tmp/" + $DumpName) $DumpTarget }) {
        $dumpItem = Get-Item -Path $DumpTarget -ErrorAction SilentlyContinue
        if ($null -eq $dumpItem -or $dumpItem.Length -eq 0) {
            Add-Failure 'Dump-Datei fehlt oder ist 0 Bytes gross'
        } else {
            Write-Log ("Dump kopiert: " + $DumpTarget + " (" + $dumpItem.Length + " Bytes)")
        }
    }
}
# Temp-Datei im Container immer aufraeumen (nur /tmp des Containers, read-only gegen Volume)
docker exec $DbContainer rm -f ("/tmp/" + $DumpName) 2>$null | Out-Null

# 4) Filestore (Bind-Mount C:\Odoo-Test\filestore -> /var/lib/odoo/filestore).
#    Nur der Unterordner des DbName wird kopiert; robocopy Exit 0-7 = Erfolg.
if (Test-Path -LiteralPath $FilestoreSource) {
    New-Item -ItemType Directory -Path $FsDestDir -Force | Out-Null
    robocopy $FilestoreSource $FsDest /E /COPY:DAT /R:1 /W:1 /NFL /NDL /NP /NJH /NJS /XJ | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) {
        Add-Failure ("robocopy Filestore fehlgeschlagen (Exit " + $rc + ")")
    } else {
        Write-Log ("Filestore kopiert (robocopy Exit " + $rc + ")")
    }
} else {
    Add-Failure ("Filestore-Quelle fehlt: " + $FilestoreSource)
}

# 5) Abschliessende Validierung (Ganz-wichtig-Checkliste)
$dumpExists = (Test-Path -LiteralPath $DumpTarget)
$dumpSize   = 0
if ($dumpExists) { $dumpSize = (Get-Item -LiteralPath $DumpTarget).Length }
if (-not $dumpExists) { Add-Failure 'Validierung: Dump-Datei existiert nicht' }
if ($dumpExists -and $dumpSize -eq 0) { Add-Failure 'Validierung: Dump-Datei ist 0 Bytes gross' }
$fsExists  = (Test-Path -LiteralPath $FsDest)
if (-not $fsExists) { Add-Failure 'Validierung: Filestore-Verzeichnis fehlt' }

$fsCount = 0
$fsBytes = 0
if ($fsExists) {
    $fsFiles = @(Get-ChildItem -LiteralPath $FsDest -Recurse -File -ErrorAction SilentlyContinue)
    $fsCount = $fsFiles.Count
    $fsSum   = $fsFiles | Measure-Object -Property Length -Sum
    $fsBytes = if ($null -ne $fsSum) { [int64]$fsSum.Sum } else { 0 }
}

$ok = ($script:Failures.Count -eq 0)

# 6) backup_info.txt schreiben
$info = @()
$info += "Odoo-18-Notfallbackup - Lauf-Informationen"
$info += ("=" * 45)
$info += ("Datum/Uhrzeit:          " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$info += ("Datenbankname:          " + $DbName)
$info += ("Odoo-Version:           " + $script:OdooVersion)
$info += ("PostgreSQL-Version:     " + $script:PgVersion)
$info += ("Git-Branch:             " + $script:GitBranch)
$info += ("Git-Commit:             " + $script:GitCommit)
$info += ("Docker-Named-Volume:    " + $script:VolumeName)
$info += ("Backup-Verzeichnis:     " + $RunDir)
$info += ("Ergebnis:               " + $(if ($ok) { 'OK' } else { 'FEHLERHAFT' }))
$info += ("DB-Dump:                " + $DumpTarget + " (" + $dumpSize + " Bytes = " + (Format-Bytes $dumpSize) + ", pg_dump custom, pg_restore --list geprueft)")
$info += ("Filestore:              " + $FsDest + " (" + $fsCount + " Dateien, " + (Format-Bytes $fsBytes) + ")")
if (-not $ok) {
    $info += ""
    $info += "Aufgetretene Fehler:"
    foreach ($f in $script:Failures) { $info += ("  - " + $f) }
}
try { $info | Set-Content -Path $InfoFile -Encoding UTF8 } catch { Add-Failure ("backup_info.txt konnte nicht geschrieben werden: " + $_.Exception.Message) }

# 7) Log-Abschluss
if ($ok) {
    Write-Log ("Backup-Lauf ABGESCHLOSSEN (OK): " + $RunDir + " | Dump " + $dumpSize + " Bytes | Filestore " + $fsCount + " Dateien")
    Write-Host ("Backup OK -> " + $RunDir)
    Write-Host ("  DB-Dump:  " + $DumpTarget + " (" + $dumpSize + " Bytes)")
    Write-Host ("  Filestore: " + $fsCount + " Dateien in " + $FsDest)
    exit 0
} else {
    Write-Log ("Backup-Lauf FEHLGESCHLAGEN - Log: " + $LogFile)
    Write-Host ("Backup FEHLGESCHLAGEN - Details: " + $LogFile) -ForegroundColor Red
    Write-Host "Es wurde nichts an der Live-Umgebung veraendert (kein Stop, kein Volume-Zugriff, keine DB-Modifikation)."
    exit 1
}
