# Okta User Creator

Automated Okta user creation from SolarWinds Service Desk tickets. Creates users, updates tickets, and sends Slack notifications - all scheduled to run automatically.

## What It Does

1. **Fetches tickets** from SolarWinds Service Desk (Samanage API)
2. **Creates Okta users** with proper fields (`swrole="Requester"`, `primary=true`)
3. **Assigns users to groups** automatically based on department from ticket
4. **Handles international addresses** with correct timezone mapping (Slovakia → Europe/Bratislava, Czech Republic → Europe/Prague)
5. **Formats phone numbers** for both US and international users
6. **Updates ticket status** to "In Progress" and adds creation comment
7. **Sends Slack notifications** with clickable ticket links

## Setup

### Prerequisites
- Python 3.7+
- 1Password CLI with Service Account (for unattended operation)
- API access: Okta, SolarWinds/Samanage, Slack

### Install
```bash
pip install requests
```

### Configure Credentials
For unattended operation, use 1Password Service Account:
1. Create service account token in 1Password
2. Store token in Windows Credential Manager:
   ```powershell
   .\get_credential.ps1
   ```

**1Password vault items needed:**
- `op://IT/okta-api-token/password` - Okta API token
- `op://IT/samanage-api-token/password` - Samanage API token  
- `op://IT/slack-bot-token/password` - Slack bot token

### Configure URLs
Update `config.py`:
- `OKTA_ORG_URL` - Your Okta org URL
- `SAMANAGE_BASE_URL` - Samanage API URL

Update `slack_integration.py`:
- `SLACK_CHANNEL` - Your notification channel

### Configure Group Assignments
Set up automatic group assignment based on department:

1. **Get your Okta group IDs:**
   ```bash
   python get_okta_groups.py
   ```

2. **Update department mappings in `config.py`:**
   - Replace `REPLACE_WITH_*_GROUP_ID` with actual Okta group IDs
   - Maps SolarWinds departments to Okta groups automatically

**Supported Department Mappings:**
- Customer Success → Customer Success group
- Administrative → Administrative group  
- AE - Account Executives → Account Executive group
- IT → IT group
- HR → HR group
- Finance → Finance group
- Security → Security group
- Chat Support → Support Team group
- Legal → Legal group
- Product → Product group
- Account Manager → Account Management group
- Sales Operations → Sales group
- Research & Development → Product group
- SDR - Sales Development Reps → Sales group
- Marketing → Marketing group

## Run

### Manual
```bash
python okta_batch_create.py
```

### Automated (Recommended)
Set up Windows Task Scheduler for 3x daily execution:
```powershell
.\setup_task_scheduler.ps1
```

**Schedule:** 10:00 AM, 2:00 PM, 5:00 PM daily

## Files

- `config.py` - Credentials & configuration with department-to-group mappings
- `okta_batch_create.py` - Main automation script with comprehensive logging
- `okta_groups.py` - Automatic group assignment based on department
- `ticket_extractor.py` - Ticket processing with address/timezone parsing
- `solarwinds_integration.py` - Ticket updates
- `slack_integration.py` - Notifications
- `log_reporter.py` - Generate daily/weekly/monthly reports for management
- `send_reports.py` - Send reports to Slack automatically
- `get_okta_groups.py` - Helper to fetch group IDs for configuration
- `get_credential.ps1` - Service account setup
- `setup_task_scheduler.ps1` - Task Scheduler configuration
- `setup_report_scheduler.ps1` - Automatic Slack reporting setup

## Logging & Reports

### Automatic Logging
The system automatically logs all activities to `logs/okta_automation_YYYY-MM-DD.log`:
-  **Successful user creations** with ticket numbers and group assignments
-  **Group assignments** by department with success/failure status
-  **Duplicate users** and validation issues
-  **Errors** with detailed error messages
-  **Performance metrics** and runtime statistics

### Management Reports
Generate reports for your boss with `log_reporter.py`:

```bash
python log_reporter.py
```

### Automatic Slack Reports
Set up automatic report delivery to your Slack channel:

```powershell
.\setup_report_scheduler.ps1
```

**Automated Schedule:**
- **Daily Report:** Every day at 5:00 PM
- **Weekly Report:** Mondays at 8:00 AM  
- **Monthly Report:** 1st of each month at 8:00 AM (ONLY on the 1st, not daily)

**Manual Slack Reports:**
```bash
python send_reports.py daily     # Send today's report
python send_reports.py weekly    # Send 7-day summary
python send_reports.py monthly   # Send monthly analysis
```

All reports are sent to the same Slack channel (`#codybot_notifications`) where user creation notifications appear.

**Available Reports:**
- **Daily Report** - Today's activity summary
- **Weekly Report** - Last 7 days overview
- **Monthly Report** - Comprehensive monthly analysis with trends
- **Year-to-Date** - Annual summary for performance reviews

**Monthly Report Features:**
-  Executive summary with key metrics
-  Performance trends and success rates
-  Busiest days and peak activity periods
-  Error analysis and troubleshooting insights
-  Working day vs. weekend activity breakdown
-  Action items and recommendations

## Features

### Automatic Group Assignment
- **Department-based:** Users automatically added to Okta groups based on SolarWinds department field
- **Flexible mapping:** Supports variations like "CS - Customer Success" and "AE - Account Executives"
- **Validation:** Group IDs validated on startup to catch configuration errors
- **Comprehensive logging:** All group assignments logged for audit purposes

### Address Support
- **US addresses:** Standard format with state and 5-digit ZIP
- **European addresses:** Slovakia, Czech Republic with proper IANA timezones
- **Automatic timezone mapping:** Country detection sets correct timezone

### Phone Formatting
- **US numbers:** `555-123-4567`
- **US with country code:** `1-555-123-4567`
- **International:** `421-948-873-023` (Slovakia format)

## Troubleshooting

**1Password prompts for authentication?**
- Ensure Service Account token is stored in Windows Credential Manager
- Run `.\get_credential.ps1` to configure unattended access

**Task Scheduler fails?**  
- Use full Python executable path
- Set working directory to project folder
- Verify Service Account credentials

**No Slack notifications?**
- Check bot token permissions
- Ensure bot is invited to notification channel
- Verify SLACK_CHANNEL setting

**Wrong timezone for international users?**
- Check address format in ticket (should include country name)
- Supported: "Slovakia", "Czech Republic", "Czechia"
