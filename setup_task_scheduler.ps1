# PowerShell script to create the Okta User Creator scheduled task
# Run this as Administrator

$TaskName = "OktaUserCreator"
$PythonPath = "C:\Users\Cody\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"
$ScriptPath = "okta_batch_create.py"
$WorkingDirectory = "c:\Users\Cody\Desktop\okta_user_creator"

# Delete existing task if it exists
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Deleted existing task: $TaskName"
} catch {
    Write-Host "No existing task to delete"
}

# Create the action (what to run)
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $WorkingDirectory

# Create multiple triggers (three times a day: 10 AM, 2 PM, 5 PM)
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "10:00 AM"
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "2:00 PM" 
$Trigger3 = New-ScheduledTaskTrigger -Daily -At "5:00 PM"
$Triggers = @($Trigger1, $Trigger2, $Trigger3)

# Create the settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create the principal (run as current user with highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId "Cody" -LogonType Interactive -RunLevel Highest

# Register the task with multiple triggers
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Triggers -Settings $Settings -Principal $Principal -Description "Automated Okta user creation from SolarWinds tickets - runs 3x daily"

Write-Host "✅ Task created successfully!"
Write-Host "Task Name: $TaskName"
Write-Host "Schedule: Daily at 10:00 AM, 2:00 PM, and 5:00 PM"
Write-Host "Command: $PythonPath $ScriptPath"
Write-Host "Working Directory: $WorkingDirectory"
Write-Host ""
Write-Host "To test the task manually, run:"
Write-Host "Start-ScheduledTask -TaskName '$TaskName'"
