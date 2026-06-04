<#
.SYNOPSIS
  Register the odg-sorter daemon as a Windows Scheduled Task that runs at user logon.

.NOTES
  Run from an elevated PowerShell prompt. Re-run to update the trigger or action.
#>
param(
  [string]$TaskName = "odg-sorter daemon",
  [string]$PythonExe = (Get-Command python).Source
)

$ErrorActionPreference = "Stop"

$action = New-ScheduledTaskAction `
  -Execute $PythonExe `
  -Argument "-m odg_sorter daemon" `
  -WorkingDirectory "C:\ODG\repos\asset-management"

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal `
  -UserId $env:USERNAME `
  -LogonType Interactive

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -Principal $principal `
  -Force | Out-Null

Write-Host "Registered '$TaskName'. It will run at next logon. Start it now with:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
