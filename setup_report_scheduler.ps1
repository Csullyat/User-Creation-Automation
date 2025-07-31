# PowerShell script to create scheduled tasks for automatic report sending
# Run this as Administrator to set up automatic Slack reporting

$PythonPath = "C:\Users\Cody\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"
$ScriptPath = "send_reports.py"
$WorkingDirectory = "c:\Users\Cody\Desktop\okta_user_creator"

Write-Host "Setting up Okta Automation Report Tasks..."

# Daily Report Task - Runs every day at 5:00 PM
try {
    Unregister-ScheduledTask -TaskName "OktaReports-Daily" -Confirm:$false -ErrorAction SilentlyContinue
} catch { }

$DailyAction = New-ScheduledTaskAction -Execute $PythonPath -Argument "send_reports.py daily" -WorkingDirectory $WorkingDirectory
$DailyTrigger = New-ScheduledTaskTrigger -Daily -At "5:00 PM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "Cody" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "OktaReports-Daily" -Action $DailyAction -Trigger $DailyTrigger -Settings $Settings -Principal $Principal -Description "Send daily Okta automation report to Slack"

Write-Host "Daily report task created (5:00 PM daily)"

# Weekly Report Task - Runs every Monday at 8:00 AM
try {
    Unregister-ScheduledTask -TaskName "OktaReports-Weekly" -Confirm:$false -ErrorAction SilentlyContinue
} catch { }

$WeeklyAction = New-ScheduledTaskAction -Execute $PythonPath -Argument "send_reports.py weekly" -WorkingDirectory $WorkingDirectory
$WeeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "8:00 AM"

Register-ScheduledTask -TaskName "OktaReports-Weekly" -Action $WeeklyAction -Trigger $WeeklyTrigger -Settings $Settings -Principal $Principal -Description "Send weekly Okta automation report to Slack"

Write-Host "Weekly report task created (Mondays at 8:00 AM)"

# Monthly Report Task - Runs on the 1st of every month at 8:00 AM
try {
    Unregister-ScheduledTask -TaskName "OktaReports-Monthly" -Confirm:$false -ErrorAction SilentlyContinue
} catch { }

$MonthlyAction = New-ScheduledTaskAction -Execute $PythonPath -Argument "send_reports.py monthly" -WorkingDirectory $WorkingDirectory
# Create a monthly trigger that runs on the 1st day of every month
$MonthlyTrigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At "8:00 AM"

Register-ScheduledTask -TaskName "OktaReports-Monthly" -Action $MonthlyAction -Trigger $MonthlyTrigger -Settings $Settings -Principal $Principal -Description "Send monthly Okta automation report to Slack"

Write-Host "Monthly report task created (1st of month at 8:00 AM)"

Write-Host ""
Write-Host "Report scheduling completed!"
Write-Host "Scheduled Tasks Created:"
Write-Host "- OktaReports-Daily: Daily at 5:00 PM"
Write-Host "- OktaReports-Weekly: Mondays at 8:00 AM" 
Write-Host "- OktaReports-Monthly: 1st of month at 8:00 AM"
Write-Host ""
Write-Host "All reports will be sent to the #codybot_notifications Slack channel"
Write-Host ""
Write-Host "To test manually:"
Write-Host "python send_reports.py daily"
Write-Host "python send_reports.py weekly"
Write-Host "python send_reports.py monthly"
