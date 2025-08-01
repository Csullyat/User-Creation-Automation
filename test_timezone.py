#!/usr/bin/env python3
"""Test timezone parsing for different states"""

from ticket_extractor import parse_address

# Test addresses for each timezone
test_addresses = [
    ("632 Wantoot Blvd, Charleston, SC, 29407", "South Carolina - Eastern"),
    ("3133 Arezzo Dr, San Luis Obispo, CA 93401", "California - Pacific"),
    ("123 Main St, Dallas, TX 75201", "Texas - Central"),
    ("456 Mountain View, Denver, CO 80202", "Colorado - Mountain"),
    ("789 Pike St, Seattle, WA 98101", "Washington - Pacific"),
    ("321 Peachtree St, Atlanta, GA 30309", "Georgia - Eastern"),
    ("654 LaSalle St, Chicago, IL 60601", "Illinois - Central"),
    ("987 Broadway, New York, NY 10001", "New York - Eastern"),
]

print("Testing timezone assignments by state:\n")

for address, description in test_addresses:
    result = parse_address(address)
    print(f"{description}:")
    print(f"  Address: {address}")
    print(f"  State: {result['state']}")
    print(f"  Timezone: {result['timezone']}")
    print()

# Summary of expected timezones
print("Expected timezone mappings:")
print("- SC (South Carolina): America/New_York (Eastern)")
print("- CA (California): America/Los_Angeles (Pacific)")
print("- TX (Texas): America/Chicago (Central)")
print("- CO (Colorado): America/Denver (Mountain)")
print("- WA (Washington): America/Los_Angeles (Pacific)")
print("- GA (Georgia): America/New_York (Eastern)")
print("- IL (Illinois): America/Chicago (Central)")
print("- NY (New York): America/New_York (Eastern)")
