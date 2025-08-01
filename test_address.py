#!/usr/bin/env python3
from ticket_extractor import parse_address
import json

# Test various address formats
addresses = [
    '1035 Pink Lily Lane Richmond, TX 77406',  # Donny's format with comma
    '1035 Pink Lily Lane Richmond TX 77406',   # Donny's format without comma  
    '123 Main St, Anytown, CA 90210',          # Traditional 3-part
    '456 Oak Avenue Springfield IL 62701',     # Space-only format
]

for addr in addresses:
    print(f'Testing: {addr}')
    try:
        result = parse_address(addr)
        print(f'  Street: {result["streetAddress"]}')
        print(f'  City: {result["city"]}') 
        print(f'  State: {result["state"]}')
        print(f'  Zip: {result["zipCode"]}')
        print(f'  Timezone: {result["timezone"]}')
    except Exception as e:
        print(f'  ERROR: {e}')
    print()
