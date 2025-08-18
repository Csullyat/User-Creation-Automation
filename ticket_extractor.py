# ticket_extractor.py

import requests
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Imports and API configuration
from config import get_samanage_token

logger = logging.getLogger(__name__)

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

    # Only log to file, not console
    logger.debug(f"📡 Fetching page {page}...")
    resp = requests.get(f"{BASE_URL}/incidents.json", headers=HEADERS, params=params)

    if resp.status_code != 200:
        print(f" Error on page {page}: {resp.status_code}: {resp.text}")
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
                print(f" Thread error: {e}")

    print(f"Total tickets fetched: {len(all_tickets)}")
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
            "ticket_id": ticket.get("id"),
            "ticket_number": ticket.get("number"),
            "ticket_state": ticket.get("state", "Unknown"),
            "ticket_created": ticket.get("created_at", "Unknown"),
            "preferredLanguage": "en",
            "organization": "Filevine",
            "swrole": "Requester",
            "primary": True,
            "timezone": "America/Denver",
            "countryCode": "US"
        }

        # Track required fields to ensure they're all present
        required_fields = {"name", "title", "department"}
        found_fields = set()


        # If name wasn't found in custom fields, try ticket name
        if "name" not in found_fields:
            ticket_name = ticket.get("name", "").split(" - ")[0].strip()
            if ticket_name:
                out["name"] = ticket_name
                found_fields.add("name")

        # Validate required fields
        missing_fields = required_fields - found_fields
        if missing_fields:
            return {}

        # Validate required address fields
        required_address_fields = ["streetAddress", "city", "state", "zipCode", "countryCode"]
        missing_address = [f for f in required_address_fields if not out.get(f)]
        if missing_address:
            logger.warning(f"Ticket {out.get('ticket_number')} missing address fields: {', '.join(missing_address)}. Skipping user creation.")
            return {}

        # Calculate timezone from state and countryCode
        us_state_timezones = {
            "CT": "America/New_York", "DE": "America/New_York", "FL": "America/New_York",
            "GA": "America/New_York", "IN": "America/New_York", "KY": "America/New_York",
            "MA": "America/New_York", "MD": "America/New_York", "ME": "America/New_York",
            "MI": "America/New_York", "NC": "America/New_York", "NH": "America/New_York",
            "NJ": "America/New_York", "NY": "America/New_York", "OH": "America/New_York",
            "PA": "America/New_York", "RI": "America/New_York", "SC": "America/New_York",
            "TN": "America/New_York", "VA": "America/New_York", "VT": "America/New_York",
            "WV": "America/New_York",
            "AL": "America/Chicago", "AR": "America/Chicago", "IA": "America/Chicago",
            "IL": "America/Chicago", "KS": "America/Chicago", "LA": "America/Chicago",
            "MN": "America/Chicago", "MO": "America/Chicago", "MS": "America/Chicago",
            "ND": "America/Chicago", "NE": "America/Chicago", "OK": "America/Chicago",
            "SD": "America/Chicago", "TX": "America/Chicago", "WI": "America/Chicago",
            "CO": "America/Denver", "ID": "America/Denver", "MT": "America/Denver",
            "NM": "America/Denver", "UT": "America/Denver", "WY": "America/Denver",
            "AZ": "America/Phoenix",
            "CA": "America/Los_Angeles", "NV": "America/Los_Angeles",
            "OR": "America/Los_Angeles", "WA": "America/Los_Angeles",
            "AK": "America/Anchorage", "HI": "America/Honolulu"
        }
        if out.get("countryCode", "US") == "US":
            state = out.get("state", "UT")
            out["timezone"] = us_state_timezones.get(state, "America/Denver")
        elif out.get("countryCode") == "SK":
            out["timezone"] = "Europe/Bratislava"
        elif out.get("countryCode") == "CZ":
            out["timezone"] = "Europe/Prague"
        else:
            out["timezone"] = "America/Denver"  # Default fallback

        return out
    except Exception as e:
        print(f" Critical error parsing ticket {ticket.get('number', 'Unknown')}: {str(e)}")
        return {}

        return out
    except Exception as e:
        print(f" Critical error parsing ticket {ticket.get('number', 'Unknown')}: {str(e)}")
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
                print(f" Parse error: {e}")

    print(f"\nFinal parsed onboarding users: {len(users)} of {len(tickets)} tickets")
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
        print(f" Script error: {e}")
