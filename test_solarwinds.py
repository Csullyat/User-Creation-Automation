# test_solarwinds.py
import json
import requests
from config import get_solarwinds_credentials, SOLARWINDS_BASE_URL

def fetch_single_ticket():
    """Fetch a single onboarding ticket from SolarWinds and display all its fields."""
    # Test credentials (these won't work but will show us the API structure)
    username = "test_user"
    password = "test_pass"
    
    # Get actual credentials
    username, password = get_solarwinds_credentials()
    
    # Query for a New Employee Setup ticket
    query_params = {
        "page": 1,
        "size": 1,
        "query": "request_type.name='New Employee Setup' AND custom_fields.'New Employee Name'='Carson Geddes' AND (status.name='New' OR status.name='In Progress' OR status.name='Pending')"
    }
    
    print("🔍 Fetching ticket from SolarWinds...")
    response = requests.get(
        f"{SOLARWINDS_BASE_URL}/requests",
        params=query_params,
        auth=(username, password)
    )
    
    if response.status_code == 200:
        tickets = response.json()
        if tickets:
            ticket = tickets[0]
            print("\n📋 Raw ticket data (formatted):")
            print(json.dumps(ticket, indent=2))
            
            print("\n🔍 Custom Fields:")
            custom_fields = ticket.get("custom_fields", {})
            for field_name, value in custom_fields.items():
                print(f"{field_name:>30}: {value}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    fetch_single_ticket()
