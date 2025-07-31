# okta_batch_create.py

import json
import requests
from config import OKTA_ORG_URL, get_okta_token
from ticket_extractor import fetch_tickets, filter_onboarding_users
from solarwinds_integration import update_ticket_status_direct, add_ticket_comment_direct
from slack_integration import send_slack_notification


def build_okta_payload(user):
    """Construct an Okta‑compliant payload and return it with the work email."""
    parts = user["name"].strip().split()
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    work_email = f"{first_name.lower()}{last_name.lower()}@filevine.com"

    payload = {
        "profile": {
            "firstName": first_name,
            "lastName": last_name,
            "displayName": f"{first_name} {last_name}",
            "email": work_email,
            "login": work_email,
            "mobilePhone": user.get("phone", ""),
            "secondEmail": user.get("personal_email", ""),
            "streetAddress": user.get("streetAddress", ""),
            "city": user.get("city", ""),
            "state": user.get("state", "UT"),
            "zipCode": user.get("zipCode", ""),
            "countryCode": user.get("countryCode", "US"),
            "department": user.get("department", ""),
            "title": user.get("title", ""),
            "managerId": user.get("managerId", ""),
            "manager": user.get("manager_name", ""),
            "preferredLanguage": "en",
            "timezone": user.get("timezone", "America/Denver"),  # Use timezone from address parsing
            "organization": "Filevine",
            "swrole": "Requester",
            "primary": True
        }
    }
    return payload, work_email


def create_okta_user(payload, headers, work_email, ticket_id=None, ticket_number=None):
    """POST a single user to Okta and log the result."""
    url = f"{OKTA_ORG_URL}/api/v1/users?activate=true"
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code in (200, 201):
            print(f"✅ Created: {work_email}")
            
            # ONLY update ticket and send notifications if user creation was successful
            if ticket_id and ticket_number:
                try:
                    success = update_ticket_status_direct(ticket_id, ticket_number, "In Progress")
                    if success:
                        # Add a comment about the user creation
                        comment = "Okta User Account has been created."
                        add_ticket_comment_direct(ticket_id, ticket_number, comment)
                        
                        # Send Slack notification
                        user_name = f"{payload['profile']['firstName']} {payload['profile']['lastName']}"
                        user_title = payload['profile'].get('title', 'No Title')
                        send_slack_notification(user_name, work_email, user_title, ticket_number, ticket_id)
                        
                except Exception as e:
                    print(f"⚠️ Ticket update failed (user was created): {str(e)}")
                    
        elif response.status_code == 400 and "E0000001" in response.text:
            # E0000001 often indicates a duplicate or validation error
            print(f"⚠️ Already exists: {work_email}")
            # Do NOT update ticket for duplicates
        else:
            print(f"❌ Failed: {work_email} — {response.status_code}")
            # Do NOT update ticket for failures
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error creating {work_email}: {str(e)}")
        # Do NOT update ticket for network errors
    except Exception as e:
        print(f"❌ Unexpected error creating {work_email}: {str(e)}")
        # Do NOT update ticket for unexpected errors


def main(test_mode: bool = True):
    """Fetch tickets, parse users, and create them in Okta.

    If *test_mode* is True, only the first user is processed so you can
    validate the flow safely.
    """
    tickets = fetch_tickets()
    users = filter_onboarding_users(tickets)

    if not users:
        print("⚠️ No onboarding users found. Exiting.")
        return

    # Get Okta API token
    okta_token = get_okta_token()
    headers = {
        "Authorization": f"SSWS {okta_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    iterable = users[:1] if test_mode else users

    for user in iterable:
        # Preview before hitting the API
        print(f"\n🔍 Previewing user: {user['name']} — {user.get('title', '')}")
        payload, work_email = build_okta_payload(user)
        ticket_id = user.get('ticket_id')
        ticket_number = user.get('ticket_number')
        create_okta_user(payload, headers, work_email, ticket_id, ticket_number)


if __name__ == "__main__":
    # Production mode - process all pending users
    main(test_mode=False)