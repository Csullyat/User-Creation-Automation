# okta_batch_create.py

import requests
from config import OKTA_API_TOKEN, OKTA_ORG_URL, getApiToken
from ticket_extractor import fetch_tickets, filter_onboarding_users


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
            "email": work_email,
            "login": work_email,
            "mobilePhone": user.get("phone", ""),
            "department": user.get("department", ""),
            "title": user.get("title", "")
        }
    }
    return payload, work_email


def create_okta_user(payload, headers, work_email):
    """POST a single user to Okta and log the result."""
    url = f"{OKTA_ORG_URL}/api/v1/users?activate=true"
    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code in (200, 201):
        print(f"✅ Created: {work_email}")
    elif response.status_code == 400 and "E0000001" in response.text:
        # E0000001 often indicates a duplicate or validation error
        print(f"⚠️ Already exists or invalid: {work_email}")
    else:
        print(f"❌ Failed: {work_email} — {response.status_code}")
        print(response.text)


def main(test_mode: bool = True):

    getApiToken()

    """Fetch tickets, parse users, and create them in Okta.

    If *test_mode* is True, only the first user is processed so you can
    validate the flow safely.
    """
    tickets = fetch_tickets()
    users = filter_onboarding_users(tickets)

    if not users:
        print("⚠️ No onboarding users found. Exiting.")
        return

    headers = {
        "Authorization": f"SSWS {OKTA_API_TOKEN}",
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