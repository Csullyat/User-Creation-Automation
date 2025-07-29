# ticket_extractor.py

import requests
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Imports and API configuration
from config import get_samanage_token

BASE_URL = "https://api.samanage.com"
# Get the token once at module level
HEADERS = {
    "X-Samanage-Authorization": f"Bearer {get_samanage_token()}",
    "Accept": "application/vnd.samanage.v2.1+json"
}

# Onboarding catalog item ID and state IDs from filtered view
CATALOG_ITEM_ID = 1198997
STATE_IDS = [
    827236, 827237, 827238, 827239, 827240,
    868561, 912210, 918367, 925284,
    1214303, 1303729, 1388495
]
# States that represent "open" lifecycle statuses
ACTIVE_STATES = {"New", "Assigned", "Auto-Assigned"}

def parse_address(address: str) -> Dict[str, str]:
    """Parse an address string into components, handling apartments correctly."""
    result = {
        "streetAddress": "",
        "city": "",
        "state": "",
        "zipCode": "",
        "countryCode": "US"  # Default to US
    }
    
    if not address:
        return result
        
    # Split by commas for parts (street, city, state zip)
    parts = [p.strip() for p in address.split(',')]
    
    if len(parts) >= 2:
        # Handle street address and apartment
        street = parts[0]
        # Look for apartment indicators
        apt_indicators = ['apt', 'apartment', '#', 'unit', 'ste', 'suite']
        
        # First try to find apartment number with common formats
        apt_num = None
        street_parts = street.lower().split()
        for i, part in enumerate(street_parts):
            if part in apt_indicators and i + 1 < len(street_parts):
                apt_num = street_parts[i + 1]
                # Remove apartment parts from street
                street = ' '.join(street_parts[:i] + street_parts[i+2:])
                break
            elif part.startswith('#'):
                apt_num = part[1:]
                # Remove apartment part from street
                street = ' '.join(street_parts[:i] + street_parts[i+1:])
                break
        
        # Clean up street address
        result["streetAddress"] = street.strip()
        if apt_num:
            result["streetAddress"] = f"{result['streetAddress']} #{apt_num}"
            
        # City
        result["city"] = parts[1].strip()
        
        # Handle state and zip if present
        if len(parts) > 2:
            state_zip = parts[2].strip().split()
            if len(state_zip) >= 2:
                result["state"] = state_zip[0].upper()
                result["zipCode"] = state_zip[-1]
                
    return result

def fetch_page(page: int, per_page: int) -> List[Dict]:
    params = {
        "per_page": per_page,
        "page": page,
        "catalog_item_id": CATALOG_ITEM_ID,
    }
    for sid in STATE_IDS:
        params.setdefault("state_id[]", []).append(sid)

    print(f"📡 Fetching page {page}...")
    resp = requests.get(f"{BASE_URL}/incidents.json", headers=HEADERS, params=params)

    if resp.status_code != 200:
        print(f"❌ Error on page {page}: {resp.status_code}: {resp.text}")
        return []

    return resp.json()

def fetch_tickets(per_page: int = 100, max_pages: int = 60, workers: int = 30) -> List[Dict]:
    all_tickets = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_page, page, per_page) for page in range(1, max_pages + 1)]
        for future in as_completed(futures):
            try:
                incidents = future.result()
                all_tickets.extend(incidents)
            except Exception as e:
                print(f"⚠️ Thread error: {e}")

    print(f"🧾 Total tickets fetched: {len(all_tickets)}")
    return all_tickets

def parse_ticket(ticket: Dict) -> Dict:
    """Parse a ticket with validation and error handling."""
    try:
        # Validate ticket has minimum required fields
        if not isinstance(ticket, dict):
            raise ValueError(f"Invalid ticket format: expected dict, got {type(ticket)}")
        
        if not ticket.get("number"):
            raise ValueError("Ticket is missing required field: number")
            
        out = {
            "ticket_number": ticket.get("number"),
            "ticket_state": ticket.get("state", "Unknown"),
            "ticket_created": ticket.get("created_at", "Unknown"),
            "preferredLanguage": "en",  # Set English as preferred language for all users
            "organization": "Filevine",  # Set organization for all users
            "swRole": 1,  # 1 for Requester (0 would be Administrator)
            "primary": False,  # Always set to false as requested
            "timezone": "America/Denver",  # Default timezone for Filevine
            "countryCode": "US"  # Default country code
        }
        
        # Track required fields to ensure they're all present
        required_fields = {"name", "title", "department"}
        found_fields = set()
        
        for f in ticket.get("custom_fields_values", []):
            try:
                label = f.get("name", "").strip()
                val = f.get("value", "").strip()
                
                if not val:
                    continue

                if label == "New Employee Name":
                    out["name"] = val
                    found_fields.add("name")
                elif label == "New Employee Personal Email Address":
                    if "@" not in val:
                        print(f"⚠️ Invalid email format for ticket {out['ticket_number']}: {val}")
                    else:
                        out["personal_email"] = val
                elif label == "New Employee Title":
                    out["title"] = val
                    found_fields.add("title")
                elif label == "New Employee Department":
                    out["department"] = val
                    found_fields.add("department")
                elif label == "New Employee Phone Number":
                    # Strip any non-digit characters from phone
                    phone = ''.join(filter(str.isdigit, val))
                    if len(phone) >= 10:  # Ensure we have at least a full phone number
                        out["phone"] = phone
                elif label == "Start Date":
                    out["start_date"] = f.get("raw_value", val)
                elif label == "Reports to":
                    try:
                        mgr = f.get("user", {})
                        if not mgr:
                            continue
                            
                        manager_name = mgr.get("name", "")
                        if not manager_name:
                            continue
                            
                        # Split manager name into parts for Okta format
                        mgr_name_parts = manager_name.split()
                        if len(mgr_name_parts) < 2:
                            print(f"⚠️ Invalid manager name format for ticket {out['ticket_number']}: {manager_name}")
                            continue
                            
                        mgr_first_name = mgr_name_parts[0]
                        mgr_last_name = " ".join(mgr_name_parts[1:])
                        
                        out["managerId"] = mgr.get("email", "")
                        out["manager_name"] = f"{mgr_last_name}, {mgr_first_name}"
                        out["manager_email"] = mgr.get("email", "")
                    except Exception as e:
                        print(f"⚠️ Error parsing manager info for ticket {out['ticket_number']}: {e}")
                elif label == "New Employee Mailing Address":
                    try:
                        # Parse address with our new function
                        address_parts = parse_address(val)
                        out.update(address_parts)
                    except Exception as e:
                        print(f"⚠️ Error parsing address for ticket {out['ticket_number']}: {e}")
            except Exception as e:
                print(f"⚠️ Error parsing field {label} for ticket {out['ticket_number']}: {e}")
                continue

        # If name wasn't found in custom fields, try ticket name
        if "name" not in found_fields:
            ticket_name = ticket.get("name", "").split(" - ")[0].strip()
            if ticket_name:
                out["name"] = ticket_name
                found_fields.add("name")

        # Validate required fields
        missing_fields = required_fields - found_fields
        if missing_fields:
            print(f"⚠️ Ticket {out['ticket_number']} missing required fields: {', '.join(missing_fields)}")
            return {}  # Return empty dict for invalid tickets

        return out
    except Exception as e:
        print(f"❌ Critical error parsing ticket {ticket.get('number', 'Unknown')}: {str(e)}")
        return {}

    if "name" not in out:
        out["name"] = ticket.get("name", "").split(" - ")[0].strip()

    return out

def filter_onboarding_users(tickets: List[Dict]) -> List[Dict]:
    def should_parse(t: Dict) -> bool:
        return t.get("state") in ACTIVE_STATES

    filtered = [t for t in tickets if should_parse(t)]

    users = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(parse_ticket, t): t for t in filtered}
        for future in as_completed(futures):
            try:
                u = future.result()
                if u and "title" in u and "department" in u:
                    users.append(u)
            except Exception as e:
                print(f"⚠️ Parse error: {e}")

    print(f"\n🎯 Final parsed onboarding users: {len(users)} of {len(tickets)} tickets")
    return users

def print_users(users: List[Dict]):
    for i, u in enumerate(users, 1):
        print(f"\n--- User #{i} ---")
        print(f"Ticket #: {u.get('ticket_number')} | Created: {u.get('ticket_created')} | State: {u.get('ticket_state')}")
        for k, v in u.items():
            if k not in ("ticket_number", "ticket_state", "ticket_created"):
                print(f"{k:>16}: {v}")

if __name__ == "__main__":
    try:
        tickets = fetch_tickets()
        users = filter_onboarding_users(tickets)
        print_users(users)
    except Exception as e:
        print(f"❌ Script error: {e}")
