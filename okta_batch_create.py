# okta_batch_create.py

import json
import requests
import logging
import os
from datetime import datetime
from config import OKTA_ORG_URL, get_okta_token
from ticket_extractor import fetch_tickets, filter_onboarding_users
from solarwinds_integration import update_ticket_status_direct, add_ticket_comment_direct
from slack_integration import send_slack_notification
from okta_groups import assign_user_to_groups, validate_group_mappings

# Configure logging
def setup_logging():
    """Set up logging to both file and console."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file with date
    log_file = os.path.join(log_dir, f"okta_automation_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    # Configure logging format
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Set up logging to both file and console
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()


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
            "timezone": user.get("timezone", "America/Denver"),  # Use timezone from address parsing
            "organization": "Filevine",
            "swrole": "Requester",
            "primary": True
        }
    }
    return payload, work_email


def create_okta_user(payload, headers, work_email, user_department=None, ticket_id=None, ticket_number=None):
    """POST a single user to Okta and log the result."""
    url = f"{OKTA_ORG_URL}/api/v1/users?activate=true"
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code in (200, 201):
            logger.info(f"SUCCESS: Created Okta user {work_email} (Ticket #{ticket_number})")
            print(f"Created: {work_email}")
            
            # Get the created user's ID from the response for group assignment
            created_user = response.json()
            user_id = created_user.get('id')
            
            # Assign user to groups based on department
            if user_id and user_department:
                group_assignment_success = assign_user_to_groups(user_id, user_department, headers)
                if group_assignment_success:
                    logger.info(f"Successfully assigned {work_email} to groups for department '{user_department}'")
                    print(f"Added to {user_department} groups")
                else:
                    logger.warning(f"Group assignment failed for {work_email}, department '{user_department}'")
                    print(f"Group assignment failed")
            elif user_department:
                logger.warning(f" User created but no user ID returned for group assignment: {work_email}")
            else:
                logger.info(f" No department specified for {work_email}, skipping group assignment")
            
            # ONLY update ticket and send notifications if user creation was successful
            if ticket_id and ticket_number:
                try:
                    success = update_ticket_status_direct(ticket_id, ticket_number, "In Progress")
                    if success:
                        logger.info(f" Updated ticket #{ticket_number} status to 'In Progress'")
                        
                        # Add a comment about the user creation
                        comment = "Okta User Account has been created."
                        add_ticket_comment_direct(ticket_id, ticket_number, comment)
                        logger.info(f" Added comment to ticket #{ticket_number}")
                        
                        # Send Slack notification
                        user_name = f"{payload['profile']['firstName']} {payload['profile']['lastName']}"
                        user_title = payload['profile'].get('title', 'No Title')
                        send_slack_notification(user_name, work_email, user_title, ticket_number, ticket_id)
                        logger.info(f" Slack notification sent for {user_name}")
                        
                except Exception as e:
                    logger.error(f" Post-creation tasks failed for {work_email} (Ticket #{ticket_number}): {str(e)}")
                    print(f" Ticket update failed (user was created): {str(e)}")
                    
        elif response.status_code == 400 and "E0000001" in response.text:
            # E0000001 often indicates a duplicate or validation error
            logger.warning(f" DUPLICATE: User {work_email} already exists (Ticket #{ticket_number})")
            print(f" Already exists: {work_email}")
            # Do NOT update ticket for duplicates
        else:
            logger.error(f" FAILED: User creation failed for {work_email} - Status {response.status_code} (Ticket #{ticket_number})")
            print(f" Failed: {work_email} — {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f" NETWORK ERROR: Failed to create {work_email} - {str(e)} (Ticket #{ticket_number})")
        print(f" Network error creating {work_email}: {str(e)}")
        # Do NOT update ticket for network errors
    except Exception as e:
        logger.error(f" UNEXPECTED ERROR: Failed to create {work_email} - {str(e)} (Ticket #{ticket_number})")
        print(f" Unexpected error creating {work_email}: {str(e)}")
        # Do NOT update ticket for unexpected errors


def main(test_mode: bool = True):
    """Fetch tickets, parse users, and create them in Okta.

    If *test_mode* is True, only the first user is processed so you can
    validate the flow safely.
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"OKTA AUTOMATION STARTED - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Get Okta credentials for validation
        logger.info("Retrieving Okta API credentials...")
        okta_token = get_okta_token()
        headers = {
            "Authorization": f"SSWS {okta_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Validate group mappings on startup
        logger.info("Validating department-to-group mappings...")
        validation_success = validate_group_mappings(headers)
        if not validation_success:
            logger.error("Group mapping validation failed. Check group IDs in configuration.")
            print("Group mapping validation failed. Check logs for details.")
            return
        else:
            logger.info("All group mappings validated successfully")
            print("Group mappings validated")
        
        # Fetch and filter tickets
        logger.info("Fetching tickets from SolarWinds Service Desk...")
        print("Fetching tickets from SolarWinds...")
        tickets = fetch_tickets()
        users = filter_onboarding_users(tickets)
        
        logger.info(f"Found {len(users)} onboarding users to process")
        print(f"Found {len(users)} users to process")

        if not users:
            logger.info("No onboarding users found. Exiting.")
            print("No users found. Exiting.")
            return

        # Process users
        iterable = users[:1] if test_mode else users
        mode_msg = "TEST MODE - Processing first user only" if test_mode else f"PRODUCTION MODE - Processing all {len(users)} users"
        logger.info(f"{mode_msg}")

        success_count = 0
        duplicate_count = 0
        error_count = 0

        for i, user in enumerate(iterable, 1):
            logger.info(f"Processing user {i}/{len(iterable)}: {user['name']} — {user.get('title', 'No Title')} (Ticket #{user.get('ticket_number')})")
            
            # Process user
            print(f"\nProcessing: {user['name']} ({user.get('title', 'No Title')})")
            payload, work_email = build_okta_payload(user)
            ticket_id = user.get('ticket_id')
            ticket_number = user.get('ticket_number')
            user_department = user.get('department')  # Extract department for group assignment
            
            # Track result for statistics
            try:
                result = create_okta_user(payload, headers, work_email, user_department, ticket_id, ticket_number)
                # We'll need to modify create_okta_user to return a status
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f" Error processing {user['name']}: {str(e)}")

        # Log summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info(f"AUTOMATION SUMMARY - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Successful creations: {success_count}")
        logger.info(f"Duplicates skipped: {duplicate_count}")
        logger.info(f"Errors encountered: {error_count}")
        logger.info(f"Total users processed: {len(iterable)}")
        logger.info("=" * 60)
        
        # Clean console summary
        print(f"\nAutomation Complete!")
        print(f"{success_count} users created successfully")
        if duplicate_count > 0:
            print(f"{duplicate_count} duplicates skipped")
        if error_count > 0:
            print(f"{error_count} errors encountered")
        print(f"Completed in {duration}")
        print("Check logs for detailed information")
        
    except Exception as e:
        logger.error(f" CRITICAL ERROR in main automation: {str(e)}", exc_info=True)
        print(f" Critical error: {str(e)}")
        raise


if __name__ == "__main__":
    # Production mode - process all pending users
    main(test_mode=False)
