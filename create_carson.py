# create_carson.py
from typing import Dict, List
import json
import requests
from config import OKTA_ORG_URL, get_okta_token, get_samanage_token
from okta_batch_create import build_okta_payload, create_okta_user

BASE_URL = "https://api.samanage.com"

def get_headers():
    """Get headers for Samanage API."""
    token = get_samanage_token()
    return {
        "X-Samanage-Authorization": f"Bearer {token}",
        "Accept": "application/vnd.samanage.v2.1+json",
        "Content-Type": "application/json"
    }

def get_carson_ticket() -> Dict:
    """Fetch only Carson's ticket."""
    params = {
        "page": 1,
        "per_page": 1,
        "catalog_item_id": 1198997,  # Onboarding catalog item
        "name": "Carson Geddes"  # Exact name match
    }
    
    print("🔍 Fetching Carson's ticket...")
    resp = requests.get(f"{BASE_URL}/incidents.json", headers=get_headers(), params=params)
    
    if resp.status_code != 200:
        print(f"❌ Error: {resp.status_code}: {resp.text}")
        return None
        
    tickets = resp.json()
    print("DEBUG Response:", json.dumps(tickets, indent=2))
    if not tickets:
        print("❌ No ticket found for Carson")
        return None
        
    # Double check it's ticket #59907
    ticket = tickets[0]
    if str(ticket.get("number")) != "59907":
        print("❌ Wrong ticket found")
        return None
        
    return ticket

def main():
    """Create only Carson's Okta account."""
    ticket = get_carson_ticket()
    if not ticket:
        return
        
    # Preview the ticket first
    print("\n🔍 Found ticket:")
    print(f"Name: {ticket.get('name')}")
    print(f"State: {ticket.get('state')}")
    print(f"Created: {ticket.get('created_at')}")
    
    confirm = input("\n⚠️ Create Carson's Okta account? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
        
    # Create the account
    payload, work_email = build_okta_payload(ticket)
    headers = {
        "Authorization": f"SSWS {get_okta_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    create_okta_user(payload, headers, work_email)

if __name__ == "__main__":
    main()
