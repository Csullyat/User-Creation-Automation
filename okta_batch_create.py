# okta_batch_create.py

import json
import requests
from config import OKTA_ORG_URL, get_okta_token
from ticket_extractor import fetch_tickets, filter_onboarding_users


def build_okta_payload(user):
    """Construct an Okta‑compliant payload and return it with the work email."""
    parts = user["name"].strip().split()
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    work_email = f"{first_name.lower()}{last_name.lower()}@filevine.com"

    # Format phone number as xxx-xxx-xxxx
    phone = user.get("phone", "")
    if phone:
        # Strip to just digits
        phone_digits = ''.join(filter(str.isdigit, phone))
        if len(phone_digits) >= 10:
            # Format as xxx-xxx-xxxx
            phone = f"{phone_digits[-10:-7]}-{phone_digits[-7:-4]}-{phone_digits[-4:]}"

    # Get manager name parts (already in "lastname, firstname" format from ticket_extractor)
    manager = user.get("manager_name", "")

    payload = {
        "profile": {
            "firstName": first_name,
            "lastName": last_name,
            "displayName": f"{first_name} {last_name}",
            "email": work_email,
            "login": work_email,
            "mobilePhone": phone,
            "secondEmail": user.get("personal_email", ""),
            "streetAddress": user.get("streetAddress", ""),  # This includes apartment number
            "city": user.get("city", ""),
            "state": user.get("state", "UT"),  # Default to UT
            "zipCode": user.get("zipCode", ""),
            "countryCode": "US",  # Default to US
            "department": user.get("department", ""),
            "title": user.get("title", ""),
            "managerId": user.get("manager_email", ""),  # Using manager's email as ID
            "manager": manager,  # Already formatted as "lastname, firstname"
            "preferredLanguage": "en",
            "timezone": "America/Denver",  # Default timezone for Utah
            "organization": "Filevine",
            "swRole": "Requester",
            "primary": "false"
        }
    }
    return payload, work_email


def create_okta_user(payload, headers, work_email):
    """POST a single user to Okta and log the result."""
    url = f"{OKTA_ORG_URL}/api/v1/users?activate=true"
    print("\n📋 Sending to Okta:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"\n🔍 Response from Okta ({response.status_code}):")
    print(response.text)

    if response.status_code in (200, 201):
        print(f"✅ Created: {work_email}")
    elif response.status_code == 400 and "E0000001" in response.text:
        # E0000001 often indicates a duplicate or validation error
        print(f"⚠️ Already exists or invalid: {work_email}")
    else:
        print(f"❌ Failed: {work_email} — {response.status_code}")


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
        create_okta_user(payload, headers, work_email)


if __name__ == "__main__":
    # Set test_mode=False once you've validated everything works.
    main(test_mode=True)