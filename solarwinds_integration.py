# solarwinds_integration.py
import requests
from config import get_solarwinds_credentials, SAMANAGE_BASE_URL

def get_solarwinds_headers():
    """Get headers for SolarWinds Service Desk API."""
    token, _ = get_solarwinds_credentials()
    return {
        "X-Samanage-Authorization": f"Bearer {token}",
        "Accept": "application/vnd.samanage.v2.1+json",
        "Content-Type": "application/json"
    }

def update_ticket_status_direct(ticket_id: str, ticket_number: str, new_status: str = "In Progress") -> bool:
    """Update a ticket status using the ticket ID directly (no search needed)."""
    try:
        headers = get_solarwinds_headers()
        
        # Update the ticket status directly using the ID
        update_data = {
            "incident": {
                "state": new_status
            }
        }
        
        print(f"Updating ticket {ticket_number} to '{new_status}'...")
        
        update_response = requests.put(
            f"{SAMANAGE_BASE_URL}/incidents/{ticket_id}.json",
            json=update_data,
            headers=headers,
            timeout=30
        )
        
        if update_response.status_code in (200, 204):
            print(f" Updated ticket {ticket_number} status to '{new_status}'")
            return True
        else:
            print(f" Failed to update ticket {ticket_number}: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
    except Exception as e:
        print(f" Error updating ticket {ticket_number}: {str(e)}")
        return False

def add_ticket_comment_direct(ticket_id: str, ticket_number: str, comment: str) -> bool:
    """Add a comment to a ticket using the ticket ID directly (no search needed)."""
    try:
        headers = get_solarwinds_headers()
        
        # Add comment directly using the ID
        comment_data = {
            "comment": {
                "body": comment,
                "is_private": False
            }
        }
        
        comment_response = requests.post(
            f"{SAMANAGE_BASE_URL}/incidents/{ticket_id}/comments.json",
            json=comment_data,
            headers=headers,
            timeout=30
        )
        
        if comment_response.status_code in (200, 201):
            print(f"Added comment to ticket {ticket_number}")
            return True
        else:
            print(f" Failed to add comment to ticket {ticket_number}")
            return False
            
    except Exception as e:
        print(f" Error adding comment to ticket {ticket_number}: {str(e)}")
        return False
