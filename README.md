# Okta User Creator

Automated Okta user creation from SolarWinds Service Desk tickets. Creates users, updates tickets, and sends Slack notifications - all scheduled to run daily.

## What It Does

1. **Fetches tickets** from SolarWinds Service Desk (Samanage API)
2. **Creates Okta users** with proper fields (\swrole="Requester"\, \primary=true\)
3. **Updates ticket status** to "In Progress" and adds creation comment
4. **Sends Slack notifications** with clickable ticket links

## Setup

### Prerequisites
- Python 3.7+
- 1Password CLI 
- API access: Okta, SolarWinds/Samanage, Slack

### Install
\\\ash
pip install requests
\\\

### Configure Credentials
Store these in 1Password:
- \op://IT/okta-api-token/password\ - Okta API token
- \op://IT/samanage-api-token/password\ - Samanage API token  
- \op://IT/slack-bot-token/password\ - Slack bot token

### Set URLs
Update \config.py\:
- \OKTA_ORG_URL\ - Your Okta org URL
- \SAMANAGE_BASE_URL\ - Samanage API URL

Update \slack_integration.py\:
- \SLACK_CHANNEL\ - Your notification channel

## Run

### Manual
\\\ash
python okta_batch_create.py
\\\

### Automated (Recommended)
Windows Task Scheduler:
1. **Program:** \python\
2. **Arguments:** \okta_batch_create.py\ 
3. **Start in:** \C:\path\to\okta_user_creator\
4. **Schedule:** Daily at 5:00 PM

## Files

- \config.py\ - Credentials & configuration
- \okta_batch_create.py\ - Main automation script
- \	icket_extractor.py\ - Ticket processing
- \solarwinds_integration.py\ - Ticket updates
- \slack_integration.py\ - Notifications

## Troubleshooting

**1Password prompts for auth?**
- Use Service Account for unattended operation

**Task Scheduler fails?**  
- Use full Python path, set working directory

**No Slack notifications?**
- Check bot permissions and channel invite
