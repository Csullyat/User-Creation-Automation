# slack_integration.py
import requests
import json
from config import get_secret_from_1password

SLACK_CHANNEL = "codybot_notifications"

def get_slack_token() -> str:
    """Get the Slack bot token from 1Password."""
    from config import get_secret_from_1password_service_account, get_secret_from_1password
    try:
        # Try service account first, fallback to regular CLI
        return get_secret_from_1password_service_account("op://IT/slack-bot-token/password")
    except:
        print("Service account failed, falling back to regular 1Password CLI")
        return get_secret_from_1password("op://IT/slack-bot-token/password")

def send_slack_notification(user_name: str, work_email: str, title: str, ticket_number: str, ticket_id: str = None) -> bool:
    """Send a Slack notification about successful Okta user creation."""
    try:
        token = get_slack_token()
        
        # Use the ticket_id (incident ID) for the IT portal URL, not the ticket_number
        # Format: https://it.filevine.com/incidents/{ticket_id}-{user-name}-new-user-request
        user_slug = user_name.lower().replace(" ", "-")
        incident_id = ticket_id if ticket_id else ticket_number  # Fallback to ticket_number if no ticket_id
        ticket_url = f"https://it.filevine.com/incidents/{incident_id}-{user_slug}-new-user-request"
        
        # Create a nice formatted message
        message = {
            "channel": f"#{SLACK_CHANNEL}",
            "text": f" New Okta User Created",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": " Okta User Created Successfully"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Name:*\n{user_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Email:*\n{work_email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Title:*\n{title}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Ticket:*\n<{ticket_url}|#{ticket_number}>"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🎫 Ticket status updated to 'In Progress'"
                        }
                    ]
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=message,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print(f"📱 Slack notification sent for {user_name}")
                return True
            else:
                print(f" Slack API error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f" Slack HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f" Slack notification failed: {str(e)}")
        return False

def send_report_to_slack(report_title: str, report_content: str, report_type: str = "Daily") -> bool:
    """Send a report to the Slack channel."""
    try:
        token = get_slack_token()
        
        # Format the report for Slack (trim if too long)
        max_length = 3000  # Slack message limit consideration
        if len(report_content) > max_length:
            truncated_content = report_content[:max_length] + "\n... (report truncated due to length)"
        else:
            truncated_content = report_content
        
        # Create formatted message for reports
        message = {
            "channel": f"#{SLACK_CHANNEL}",
            "text": f"Okta Automation {report_type} Report",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Okta Automation {report_type} Report"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{truncated_content}```"
                    }
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=message,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print(f"Report sent to Slack: {report_type}")
                return True
            else:
                print(f"Slack API error sending report: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"Slack HTTP error sending report: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Failed to send report to Slack: {str(e)}")
        return False
