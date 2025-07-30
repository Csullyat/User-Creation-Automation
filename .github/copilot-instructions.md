# Copilot Instructions for Okta User Creator

## Project Overview
- This project automates Okta user creation based on onboarding tickets from SolarWinds Service Desk (Samanage).
- The workflow: fetch tickets → parse user info → create Okta user → update ticket status/comment → send Slack notification.
- All secrets (API tokens) are retrieved via 1Password CLI, with plans to migrate to 1Password Service Accounts for unattended automation.

## Key Components
- `config.py`: Centralized config and secret management. All API tokens are fetched using 1Password CLI (`op read`).
- `okta_batch_create.py`: Main orchestration script. Handles ticket fetching, user creation, ticket updates, and Slack notifications. Entry point for automation.
- `ticket_extractor.py`: Fetches and parses onboarding tickets. Extracts user data and ticket IDs for direct updates.
- `solarwinds_integration.py`: Updates ticket status and adds comments using direct API calls (no search needed if ticket ID is known).
- `slack_integration.py`: Sends Slack notifications to a configured channel when a user is created.
- `README.md`: Setup, usage, and workflow documentation. Always reference for environment and credential setup.

## Patterns & Conventions
- **Secrets:** Always use `get_secret_from_1password()` for API tokens. Do not hardcode secrets.
- **User Creation:** Okta payloads must include custom fields: `swrole="Requester"`, `primary=True`.
- **Ticket Updates:** Use direct update functions with both `ticket_id` and `ticket_number` to avoid duplicate API searches.
- **Slack Notifications:** Use the incident ID (`ticket_id`) for ticket URLs in Slack messages, not the ticket number.
- **Error Handling:** Only update tickets and send notifications if Okta user creation is successful. Do not update for duplicates or failures.
- **Test Mode:** The main script supports `test_mode` for safe validation. Production runs set `test_mode=False`.
- **Automation:** Designed for Windows Task Scheduler. Script must be run via Python executable, not directly as a `.py` file.

## Integration Points
- **Okta:** Uses Okta API for user creation. Requires org URL and API token.
- **SolarWinds/Samanage:** Uses API for ticket fetching and updates. Requires API token.
- **Slack:** Sends notifications using Slack API and bot token.
- **1Password:** CLI used for secret retrieval. Service Account integration recommended for unattended runs.

## Example Workflow
1. Fetch tickets from Samanage API.
2. Parse onboarding users and extract user/ticket data.
3. For each user:
   - Build Okta payload
   - Create Okta user
   - If successful: update ticket status, add comment, send Slack notification
4. Log all actions and errors to console (optionally to file).

## Troubleshooting
- If the script prompts for 1Password fingerprint, migrate to Service Account for unattended automation.
- If Task Scheduler fails, ensure Python executable is used and working directory is set correctly.
- For missing Slack notifications, check bot token and channel invite.

## References
- See `README.md` for setup and environment details.
- All code follows the patterns described above. Reference key files for implementation details.

---

**Feedback:** If any section is unclear or missing, please specify which workflow or integration needs more detail.
