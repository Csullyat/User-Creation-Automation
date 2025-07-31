#!/usr/bin/env python3
"""
Okta Group Management
Handles automatic assignment of users to groups based on department.
"""

import requests
import logging
from typing import List, Dict
from config import OKTA_ORG_URL, get_okta_token, get_groups_for_department

logger = logging.getLogger(__name__)

def assign_user_to_groups(user_id: str, department: str, headers: Dict[str, str]) -> bool:
    """Assign a user to appropriate groups based on their department."""
    try:
        # Get group IDs for the department
        group_ids = get_groups_for_department(department)
        
        if not group_ids:
            logger.warning(f"No groups found for department: {department}")
            return False
        
        success_count = 0
        total_groups = len(group_ids)
        
        for group_id in group_ids:
            try:
                # Add user to group
                url = f"{OKTA_ORG_URL}/api/v1/groups/{group_id}/users/{user_id}"
                response = requests.put(url, headers=headers, timeout=30)
                
                if response.status_code in (200, 204):
                    logger.info(f"Added user {user_id} to group {group_id}")
                    success_count += 1
                elif response.status_code == 409:
                    # User is already in the group
                    logger.info(f"User {user_id} already in group {group_id}")
                    success_count += 1
                else:
                    logger.error(f"Failed to add user {user_id} to group {group_id}: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error adding user {user_id} to group {group_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error adding user {user_id} to group {group_id}: {str(e)}")
        
        # Return True if we successfully added to at least one group
        success_rate = success_count / total_groups if total_groups > 0 else 0
        
        if success_count == total_groups:
            logger.info(f"Successfully assigned user {user_id} to all {total_groups} groups for department '{department}'")
            return True
        elif success_count > 0:
            logger.warning(f"Partially assigned user {user_id} to {success_count}/{total_groups} groups for department '{department}'")
            return True
        else:
            logger.error(f"Failed to assign user {user_id} to any groups for department '{department}'")
            return False
            
    except Exception as e:
        logger.error(f"Critical error in group assignment for user {user_id}, department '{department}': {str(e)}")
        return False

def get_user_groups(user_id: str, headers: Dict[str, str]) -> List[Dict]:
    """Get all groups a user is currently assigned to."""
    try:
        url = f"{OKTA_ORG_URL}/api/v1/users/{user_id}/groups"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            groups = response.json()
            logger.info(f"Retrieved {len(groups)} groups for user {user_id}")
            return groups
        else:
            logger.error(f"Failed to get groups for user {user_id}: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting groups for user {user_id}: {str(e)}")
        return []

def get_group_info(group_id: str, headers: Dict[str, str]) -> Dict:
    """Get information about a specific group."""
    try:
        url = f"{OKTA_ORG_URL}/api/v1/groups/{group_id}"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            group_info = response.json()
            return group_info
        else:
            logger.error(f"Failed to get group info for {group_id}: {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting group info for {group_id}: {str(e)}")
        return {}

def list_all_groups(headers: Dict[str, str]) -> List[Dict]:
    """List all groups in the Okta org (for setup/configuration purposes)."""
    try:
        url = f"{OKTA_ORG_URL}/api/v1/groups"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            groups = response.json()
            logger.info(f"Retrieved {len(groups)} total groups from Okta")
            return groups
        else:
            logger.error(f"Failed to list groups: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error listing groups: {str(e)}")
        return []

def validate_group_mappings(headers: Dict[str, str]) -> bool:
    """Validate that all group IDs in the mapping exist in Okta."""
    from config import DEPARTMENT_GROUP_MAPPING
    
    invalid_count = 0
    total_count = len(DEPARTMENT_GROUP_MAPPING)
    
    for department, group_id in DEPARTMENT_GROUP_MAPPING.items():
        group_info = get_group_info(group_id, headers)
        if group_info:
            # Only log to file, not console
            logger.debug(f"Group mapping valid: {department} → {group_info.get('profile', {}).get('name', group_id)}")
        else:
            invalid_count += 1
            logger.error(f"Invalid group mapping: {department} → {group_id} (group not found)")
    
    if invalid_count == 0:
        logger.info(f"All {total_count} group mappings validated successfully")
        return True
    else:
        logger.error(f"{invalid_count} invalid group mappings found")
        return False
