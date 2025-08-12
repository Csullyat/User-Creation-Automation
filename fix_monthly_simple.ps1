# Fix Monthly Report Scheduling - Simple Version
# This script fixes the monthly report task to only run on the 1st of each month
# Run this as Administrator

$PythonPath = "C:\Users\Cody\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"
$WorkingDirectory = "c:\Users\Cody\Desktop\okta_user_creator"

Write-Host "Fixing Monthly Report Task..."

# Remove the existing incorrectly configured monthly task
try {
    schtasks /delete /tn "OktaReports-Monthly" /f
    Write-Host "Removed existing monthly task"
} catch { 
    Write-Host "Could not remove existing task (may not exist)"
}

# Create a new monthly task using schtasks command
# This will run ONLY on the 1st day of each month at 8:00 AM
$Command = "schtasks /create /tn `"OktaReports-Monthly`" /tr `"$PythonPath send_reports.py monthly`" /sc monthly /d 1 /st 08:00 /sd 09/01/2025 /f"

Write-Host "Creating new monthly task with command:"
Write-Host $Command

# Execute the schtasks command
Invoke-Expression $Command

Write-Host ""
Write-Host "Monthly report task recreated - will ONLY run on the 1st of each month at 8:00 AM"

# Verify the configuration
Write-Host ""
Write-Host "Verifying task configuration..."
schtasks /query /tn "OktaReports-Monthly" /fo list

Write-Host ""
Write-Host "Fix completed! Monthly reports will now ONLY run on the 1st of each month."
