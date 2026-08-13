<#
.SYNOPSIS
    Registriert die beiden taeglichen Odoo-18-Notfallbackup-Tasks im
    Windows Task Scheduler (09:00 und 15:00 Uhr).

.DESCRIPTION
    Fuehrt odoo18_notfallbackup.ps1 taeglich um 09:00 und 15:00 aus.
    Laeuft als aktuell angemeldeter User (Docker Desktop benoetigt den
    interaktiven Kontext). Idempotent: -Force ersetzt bestehende Tasks.
#>
$scriptPath = 'C:\Odoo-Test\scripts\odoo18_notfallbackup.ps1'
$argument   = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $scriptPath + '"'

$action   = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argument
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew

$trigger09 = New-ScheduledTaskTrigger -Daily -At 09:00
$trigger15 = New-ScheduledTaskTrigger -Daily -At 15:00

Register-ScheduledTask -TaskName 'Odoo18 Notfallbackup 09-00' -Action $action -Trigger $trigger09 -Settings $settings `
    -Description 'Odoo-18-Notfallbackup (pg_dump + Filestore) taeglich 09:00' -Force | Out-Null
Register-ScheduledTask -TaskName 'Odoo18 Notfallbackup 15-00' -Action $action -Trigger $trigger15 -Settings $settings `
    -Description 'Odoo-18-Notfallbackup (pg_dump + Filestore) taeglich 15:00' -Force | Out-Null

Write-Output 'Tasks registriert:'
Get-ScheduledTask -TaskName 'Odoo18 Notfallbackup 09-00', 'Odoo18 Notfallbackup 15-00' |
    Select-Object TaskName, State |
    Format-Table -AutoSize | Out-String | Write-Output
