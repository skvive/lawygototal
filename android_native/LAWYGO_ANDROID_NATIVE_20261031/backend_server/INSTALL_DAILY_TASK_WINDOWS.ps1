# Execute manually in PowerShell (current user). Does not send any email.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = (Get-Command python -ErrorAction Stop).Source
$script = Join-Path $root 'run_daily_editorial.py'
$action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`"" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At "07:10"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 25) -StartWhenAvailable
Register-ScheduledTask -TaskName "LAWYGO-Daily-Editorial" -Action $action -Trigger $trigger -Settings $settings -Description "LAWYGO RSS 수집·초안만 생성. 발송하지 않음" -Force
Write-Host "LAWYGO RSS 매일 07:10 로컬 시간 일정 등록 완료. 실제 뉴스 수집은 실행 PC가 온라인이어야 합니다."
