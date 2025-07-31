#!/usr/bin/env python3
"""
Helper script to fetch all Okta groups and their IDs for easy configuration.
Run this script to get the group IDs you need to update in config.py
"""

import requests
from config import get_okta_token, OKTA_ORG_URL

def get_all_okta_groups():
    """Fetch all Okta groups and display them for configuration."""
    
    try:
        # Get credentials
        print(" Getting Okta credentials...")
        okta_token = get_okta_token()
        
        headers = {
            "Authorization": f"SSWS {okta_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Get all groups
        print(" Fetching all Okta groups...")
        url = f"{OKTA_ORG_URL}/api/v1/groups"
        
        all_groups = []
        next_url = url
        
        while next_url:
            response = requests.get(next_url, headers=headers)
            response.raise_for_status()
            
            groups = response.json()
            all_groups.extend(groups)
            
            # Check for pagination
            link_header = response.headers.get('link', '')
            next_url = None
            if 'rel="next"' in link_header:
                # Parse next URL from link header
                for link in link_header.split(','):
                    if 'rel="next"' in link:
                        next_url = link.split('<')[1].split('>')[0]
                        break
        
        print(f"\n Found {len(all_groups)} groups in your Okta org\n")
        print("=" * 80)
        print("OKTA GROUPS - Copy the IDs you need for config.py")
        print("=" * 80)
        
        # Sort groups by name for easier reading
        all_groups.sort(key=lambda x: x['profile']['name'].lower())
        
        for group in all_groups:
            group_id = group['id']
            group_name = group['profile']['name']
            description = group['profile'].get('description', 'No description')
            
            print(f" {group_name}")
            print(f"   ID: {group_id}")
            print(f"   Description: {description}")
            print()
        
        print("=" * 80)
        print("SUGGESTED MAPPINGS FOR YOUR DEPARTMENTS")
        print("=" * 80)
        
        # Suggest mappings based on common group names
        departments_needed = [
            "Customer Success",
            "Administrative", 
            "Account Executive",
            "Implementations",
            "IT",
            "HR",
            "Finance",
            "Security",
            "Support Team",
            "Legal",
            "Product",
            "Account Management",
            "Sales",
            "Marketing"
        ]
        
        print(" Looking for groups that match your departments...")
        print()
        
        for dept in departments_needed:
            print(f" {dept}:")
            matches = []
            
            for group in all_groups:
                group_name = group['profile']['name']
                if dept.lower() in group_name.lower():
                    matches.append(f"    '{group_name}' -> {group['id']}")
            
            if matches:
                for match in matches:
                    print(match)
            else:
                print(f"   No obvious match found - check manually")
            print()
        
        print("=" * 80)
        print("NEXT STEPS:")
        print("1. Copy the group IDs above")
        print("2. Update config.py DEPARTMENT_GROUP_MAPPING")
        print("3. Replace REPLACE_WITH_*_GROUP_ID with actual IDs")
        print("4. Test with python okta_batch_create.py in test mode")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your Okta credentials are configured correctly.")

if __name__ == "__main__":
    get_all_okta_groups()
