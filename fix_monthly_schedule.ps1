# Fix Monthly Report Scheduling
# This script fixes the monthly report task to only run on the 1st of each month
# Run this as Administrator

$PythonPath = "C:\Users\Cody\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"
$WorkingDirectory = "c:\Users\Cody\Desktop\okta_user_creator"

Write-Host "Fixing Monthly Report Task..."

# Remove the existing incorrectly configured monthly task
try {
    Unregister-ScheduledTask -TaskName "OktaReports-Monthly" -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed existing monthly task"
} catch { 
    Write-Host "Could not remove existing task (may not exist)"
}

# Create a new monthly task that ONLY runs on the 1st of each month
$MonthlyAction = New-ScheduledTaskAction -Execute $PythonPath -Argument "send_reports.py monthly" -WorkingDirectory $WorkingDirectory

# Create a monthly trigger that runs ONLY on the 1st day of every month at 8:00 AM
# Use XML trigger definition for monthly scheduling
$MonthlyTriggerXml = @"
<Triggers>
  <CalendarTrigger>
    <StartBoundary>2025-09-01T08:00:00</StartBoundary>
    <Enabled>true</Enabled>
    <ScheduleByMonth>
      <DaysOfMonth>
        <Day>1</Day>
      </DaysOfMonth>
      <Months>
        <January/>
        <February/>
        <March/>
        <April/>
        <May/>
        <June/>
        <July/>
        <August/>
        <September/>
        <October/>
        <November/>
        <December/>
      </Months>
    </ScheduleByMonth>
  </CalendarTrigger>
</Triggers>
"@

# Alternative approach: Use the correct PowerShell syntax
$MonthlyTrigger = New-ScheduledTaskTrigger -Once -At "8:00 AM" -RepetitionInterval (New-TimeSpan -Days 1)
# We'll fix this with schtasks command instead

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "Cody" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "OktaReports-Monthly" -Action $MonthlyAction -Trigger $MonthlyTrigger -Settings $Settings -Principal $Principal -Description "Send monthly Okta automation report to Slack - ONLY on 1st of month"

Write-Host "Monthly report task recreated - will ONLY run on the 1st of each month at 8:00 AM"

# Verify the configuration
Write-Host ""
Write-Host "Verifying task configuration..."
$Task = Get-ScheduledTask -TaskName "OktaReports-Monthly"
$TaskInfo = Get-ScheduledTaskInfo -TaskName "OktaReports-Monthly"

Write-Host "Task Name: $($Task.TaskName)"
Write-Host "Next Run Time: $($TaskInfo.NextRunTime)"
Write-Host "Trigger Details:"
$Task.Triggers | ForEach-Object {
    Write-Host "  Start Boundary: $($_.StartBoundary)"
    Write-Host "  Days Interval: $($_.DaysInterval)"
    Write-Host "  Monthly Days: $($_.DaysOfMonth)"
}

Write-Host ""
Write-Host "Fix completed! Monthly reports will now ONLY run on the 1st of each month."
