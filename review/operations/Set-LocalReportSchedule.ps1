$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$python = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Programs\Python\Python312\pythonw.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Expected Windows Python 3.12 runner is missing.' }

$ops = Get-ScheduledTask -TaskName 'WMM GOV RADAR Unified Operations'
if ($ops.Actions.Count -ne 1 -or $ops.Actions[0].Arguments -notmatch 'govradar-operations\\run_ops\.py') {
    throw 'Existing report task action mismatch.'
}
$reportTimes = @('08:20','11:20','15:20','19:20')
$opsTriggers = $reportTimes | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $_ }
Set-ScheduledTask -TaskName $ops.TaskName -Trigger $opsTriggers | Out-Null

$prophecy = Get-ScheduledTask -TaskName 'WMM-Prophecy-YouTube-Daily'
$prophecyArg = '-X utf8 "' + (Join-Path $PSScriptRoot 'prophecy_watch.py') + '"'
if ($prophecy.Actions.Count -ne 1 -or
    ($prophecy.Actions[0].Arguments -notmatch 'prophecy_daily_run\.py' -and $prophecy.Actions[0].Arguments -ne $prophecyArg)) {
    throw 'Existing video watcher action mismatch.'
}
$hourly = 0..23 | ForEach-Object {
    New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes(10))
}
$prophecyAction = New-ScheduledTaskAction -Execute $python -Argument $prophecyArg -WorkingDirectory $workspace
Set-ScheduledTask -TaskName $prophecy.TaskName -Trigger $hourly -Action $prophecyAction | Out-Null

$name = 'WMM GOV RADAR Public Cyber Notices'
$publicArg = '-X utf8 "' + (Join-Path $PSScriptRoot 'public_notices.py') + '"'
$old = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($old -and ($old.Actions.Count -ne 1 -or $old.Actions[0].Arguments -ne $publicArg)) {
    throw 'Existing advisory task action mismatch.'
}
if (!$old) {
    $start = [datetime]::Today.AddMinutes(5)
    $daily = New-ScheduledTaskTrigger -Daily -At $start
    $repeat = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 1)
    $daily.Repetition = $repeat.Repetition
    $act = New-ScheduledTaskAction -Execute $python -Argument $publicArg -WorkingDirectory $workspace
    $identity = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
    Register-ScheduledTask -TaskName $name -Action $act -Trigger $daily -Principal $identity -Settings $settings -Description 'Checks official public defensive security advisories. Collects notice titles, dates and source links.' | Out-Null
}

Start-ScheduledTask -TaskName $name
Start-ScheduledTask -TaskName $prophecy.TaskName
$observed = foreach ($taskName in @($ops.TaskName, $prophecy.TaskName, $name)) {
    $task = Get-ScheduledTask -TaskName $taskName
    $info = $task | Get-ScheduledTaskInfo
    [pscustomobject]@{
        name = $taskName
        triggerCount = @($task.Triggers).Count
        interval = $task.Triggers[0].Repetition.Interval
        displayTimes = if ($taskName -eq $ops.TaskName) { @($task.Triggers.StartBoundary) }
        next = $info.NextRunTime
        state = [string]$task.State
    }
}
ConvertTo-Json -InputObject @($observed) -Depth 4 -Compress
