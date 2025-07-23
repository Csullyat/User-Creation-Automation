# ticket_extractor.py

import requests
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 🔐 Secure token and API setup
SWS_API_TOKEN = "Y29keWF0a2luc29uQGZpbGV2aW5lLmNvbQ==:eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoxMTc4Nzg1MCwiZ2VuZXJhdGVkX2F0IjoiMjAyNS0wNy0xOCAyMTo1MToyNyJ9.7EFirhIy120PdDHPnzSiFGB5EV9lvKs-85Ec4yEKkcfVvcI4dZw6l4WqfGNjqlS_76PqrSWbvHOoMFhkQLQpTw:VVM="
BASE_URL = "https://api.samanage.com"
HEADERS = {
    "X-Samanage-Authorization": f"Bearer {SWS_API_TOKEN}",
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
    out = {
        "ticket_number": ticket.get("number"),
        "ticket_state": ticket.get("state"),
        "ticket_created": ticket.get("created_at")
    }
    for f in ticket.get("custom_fields_values", []):
        label = f.get("name", "").strip()
        val = f.get("value", "").strip()

        if label == "New Employee Name": out["name"] = val
        elif label == "New Employee Personal Email Address": out["personal_email"] = val
        elif label == "New Employee Title": out["title"] = val
        elif label == "New Employee Department": out["department"] = val
        elif label == "New Employee Mailing Address": out["address"] = val
        elif label == "New Employee Phone Number": out["phone"] = val
        elif label == "Start Date": out["start_date"] = f.get("raw_value", val)
        elif label == "Laptop Style": out["laptop"] = val
        elif label == "Reports to":
            mgr = f.get("user", {})
            out["manager_name"] = mgr.get("name", "")
            out["manager_email"] = mgr.get("email", "")

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
