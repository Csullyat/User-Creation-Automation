# okta_batch_create.py

import requests
from config import OKTA_ORG_URL, get_okta_token
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
            "timezone": "America/Denver",
            "organization": "Filevine",
            "swrole": "Requester",
            "primary": True
        }
    }
    return payload, work_email


def create_okta_user(payload, headers, work_email):
    """POST a single user to Okta and log the result."""
    url = f"{OKTA_ORG_URL}/api/v1/users?activate=true"
    
    # Debug: Show zip code specifically
    zip_code = payload.get("profile", {}).get("zipCode", "")
    print(f"🏠 Zip code being sent: '{zip_code}'")
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code in (200, 201):
        print(f"✅ Created: {work_email}")
    elif response.status_code == 400 and "E0000001" in response.text:
        # E0000001 often indicates a duplicate or validation error
        print(f"⚠️ Already exists: {work_email}")
    else:
        print(f"❌ Failed: {work_email} — {response.status_code}")


def main():
    """Fetch tickets, parse users, and create them in Okta."""
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

    for user in users:
        # Preview before hitting the API
        print(f"\n🔍 Previewing user: {user['name']} — {user.get('title', '')}")
        payload, work_email = build_okta_payload(user)
        create_okta_user(payload, headers, work_email)


if __name__ == "__main__":
    main()