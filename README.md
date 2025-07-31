# Okta User Creator

Automated Okta user creation from SolarWinds Service Desk tickets. Creates users, updates tickets, and sends Slack notifications - all scheduled to run automatically.

## What It Does

1. **Fetches tickets** from SolarWinds Service Desk (Samanage API)
2. **Creates Okta users** with proper fields (`swrole="Requester"`, `primary=true`)
3. **Handles international addresses** with correct timezone mapping (Slovakia → Europe/Bratislava, Czech Republic → Europe/Prague)
4. **Formats phone numbers** for both US and international users
5. **Updates ticket status** to "In Progress" and adds creation comment
6. **Sends Slack notifications** with clickable ticket links

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

- `config.py` - Credentials & configuration
- `okta_batch_create.py` - Main automation script
- `ticket_extractor.py` - Ticket processing with address/timezone parsing
- `solarwinds_integration.py` - Ticket updates
- `slack_integration.py` - Notifications
- `get_credential.ps1` - Service account setup
- `setup_task_scheduler.ps1` - Task Scheduler configuration

## Features

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
