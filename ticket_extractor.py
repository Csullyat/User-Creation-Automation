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
    """Parse an address string into components, supporting both US and European formats."""
    result = {"streetAddress": "", "city": "", "state": "UT", "zipCode": "", "countryCode": "US"}
    
    if not address:
        return result
    
    # Country name to ISO code mapping with timezones
    country_mapping = {
        "Slovakia": {"code": "SK", "timezone": "Europe/Bratislava"},
        "Czech Republic": {"code": "CZ", "timezone": "Europe/Prague"}, 
        "Czechia": {"code": "CZ", "timezone": "Europe/Prague"},
        "United States": {"code": "US", "timezone": "America/Denver"},
        "USA": {"code": "US", "timezone": "America/Denver"},
        "US": {"code": "US", "timezone": "America/Denver"}
    }
    
    # Split by commas
    parts = [p.strip() for p in address.split(',')]
    
    if len(parts) >= 3:
        # Check if this looks like a European address (has a country at the end)
        last_part = parts[-1].strip()
        country_info = country_mapping.get(last_part)
        is_european = country_info is not None and last_part not in ["US", "USA", "United States"]
        
        if is_european:
            # European format: "Street, Postal Code City, Country"
            result["streetAddress"] = parts[0].strip()
            result["countryCode"] = country_info["code"]
            result["timezone"] = country_info["timezone"]
            result["state"] = ""  # European addresses don't use state
            
            # Parse "Postal Code City" from the middle part
            if len(parts) >= 2:
                postal_city = parts[1].strip()
                # Look for postal code pattern (digits with optional space)
                import re
                # Match postal codes like "821 06", "94911", "949 11"
                postal_match = re.match(r'^(\d{3}\s?\d{2,3})\s+(.+)$', postal_city)
                if postal_match:
                    result["zipCode"] = postal_match.group(1).strip()
                    result["city"] = postal_match.group(2).strip()
                else:
                    # Fallback: assume last word(s) are city, first are postal
                    tokens = postal_city.split()
                    if len(tokens) >= 2:
                        # Find where postal code ends (first non-digit token)
                        postal_tokens = []
                        city_tokens = []
                        found_city_start = False
                        
                        for token in tokens:
                            if not found_city_start and (token.isdigit() or (len(token) <= 3 and token.isdigit())):
                                postal_tokens.append(token)
                            else:
                                found_city_start = True
                                city_tokens.append(token)
                        
                        if postal_tokens and city_tokens:
                            result["zipCode"] = " ".join(postal_tokens)
                            result["city"] = " ".join(city_tokens)
                        else:
                            result["city"] = postal_city  # Fallback
        else:
            # US format: handle existing logic
            us_country_info = country_mapping.get("US")
            if us_country_info:
                result["timezone"] = us_country_info["timezone"]
            
            # Handle apartment in street address (combine first two parts if second looks like apt)
            apt_keywords = ["Apt", "Apartment", "Unit", "Suite", "Ste", "#"]
            if len(parts) > 3 and any(parts[1].strip().startswith(k) for k in apt_keywords):
                result["streetAddress"] = f"{parts[0]} {parts[1]}".strip()
                result["city"] = parts[2]
                state_zip = parts[3]
            else:
                result["streetAddress"] = parts[0]
                result["city"] = parts[1]
                state_zip = parts[2]
            
            # Extract state and zip from last part
            tokens = state_zip.split()
            for token in tokens:
                if len(token) == 2 and token.isalpha():
                    result["state"] = token.upper()
                elif len(token) == 5 and token.isdigit():
                    result["zipCode"] = token
    
    return result

def format_phone(phone: str) -> str:
    """Format phone numbers with proper dashes for both US and international numbers."""
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 10:
        # US format: 555-123-4567
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        # US format with country code: 1-555-123-4567
        return f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    elif len(digits) == 12:
        # International format (like Slovakia +421): 421-948-873-023
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:9]}-{digits[9:]}"
    elif len(digits) >= 10:
        # Generic international format - insert dashes every 3 digits after country code
        # Assume first 1-3 digits are country code, rest in groups of 3
        if len(digits) <= 13:
            # For numbers 10-13 digits, try to format reasonably
            if len(digits) == 11:
                return f"{digits[:2]}-{digits[2:5]}-{digits[5:8]}-{digits[8:]}"
            elif len(digits) == 13:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:9]}-{digits[9:]}"
    
    # If we can't format it nicely, return original
    return phone
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

def fetch_tickets(per_page: int = 100, max_pages: int = 20, workers: int = 30) -> List[Dict]:
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
            "ticket_id": ticket.get("id"),  # Add ticket ID for direct updates
            "ticket_number": ticket.get("number"),
            "ticket_state": ticket.get("state", "Unknown"),
            "ticket_created": ticket.get("created_at", "Unknown"),
            "preferredLanguage": "en",  # Set English as preferred language for all users
            "organization": "Filevine",  # Set organization for all users
            "swrole": "Requester",  # Set to 'Requester' for Okta dropdown
            "primary": True,  # Always set to true as requested
            "timezone": "America/Denver",  # Default timezone - will be overridden by address parsing
            "countryCode": "US"  # Default country code - will be overridden by address parsing
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
                    # Format phone for Okta output
                    phone = format_phone(val)
                    if phone:
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
            # print(f"⚠️ Ticket {out['ticket_number']} missing required fields: {', '.join(missing_fields)}")
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
