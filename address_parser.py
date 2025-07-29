"""Address parsing utilities for ticket extractor."""

def extract_apartment_info(parts: list) -> tuple[str, list]:
    """Extract apartment information from address parts."""
    apt_indicators = {'apt', 'apartment', 'unit', '#', 'suite', 'ste'}
    apt_info = None
    remaining_parts = []
    skip_next = False

    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue

        part_lower = part.lower()
        
        # Check if this part is an apartment indicator
        if part_lower in apt_indicators:
            if i + 1 < len(parts):
                apt_info = f"Apt {parts[i + 1]}"
                skip_next = True
            continue
        
        # Check for combined apartment indicators like "#123" or "Apt123"
        for indicator in apt_indicators:
            if part_lower.startswith(indicator):
                apt_num = part_lower[len(indicator):].strip()
                if apt_num:
                    apt_info = f"Apt {apt_num}"
                    break
                elif i + 1 < len(parts):
                    apt_info = f"Apt {parts[i + 1]}"
                    skip_next = True
                    break
        
        # If this part wasn't used for apartment info, keep it
        if not skip_next and not apt_info:
            remaining_parts.append(part)
            
    return apt_info, remaining_parts

def parse_slc_address(address: str) -> dict:
    """Parse a Salt Lake City style address (e.g., '123 E 400 S Apt 512')."""
    print(f"DEBUG: Raw address input: '{address}'")
    parts = address.split()
    result = {"apt": None, "zip": None}
    
    # First find the core street part (up through second direction)
    directions = {'N', 'S', 'E', 'W'}
    street_end = 0
    directions_found = 0
    
    # Step through parts to find the end of the street portion
    for i, part in enumerate(parts):
        if part.upper() in directions:
            directions_found += 1
            if directions_found == 2:
                street_end = i + 1
                break
    
    # Extract street portion
    if street_end > 0:
        result["street"] = ' '.join(parts[:street_end])
        remaining_parts = parts[street_end:]
        
        # Extract apartment information
        apt_info, remaining_parts = extract_apartment_info(remaining_parts)
        if apt_info:
            result["apt"] = apt_info
                
        # Look for ZIP code in remaining parts
        for part in remaining_parts:
            if part.isdigit() and len(part) == 5:
                result["zip"] = part
                break
    
    # Build return value with proper format
    result["city"] = "Salt Lake City"
    result["state"] = "UT"
    result["zipCode"] = result["zip"] if result["zip"] else "84111"  # Default downtown SLC
    
    # Build the final street address
    street_addr = result["street"]
    if result["apt"]:
        street_addr = f"{street_addr} {result['apt']}"
    result["streetAddress"] = street_addr.strip()
    
    # Remove temporary fields
    del result["street"]
    del result["apt"]
    del result["zip"]
    
    return result

def parse_standard_address(address: str) -> dict:
    """Parse a standard format address (e.g., '123 Main St, Apt 4B, Salt Lake City, UT 84111')."""
    result = {}
    
    # Split on commas first
    parts = [p.strip() for p in address.split(',')]
    
    if len(parts) < 2:
        raise ValueError(f"Invalid address format: {address}")
        
    # First part is always street address
    street_parts = parts[0].split()
    if not street_parts:
        raise ValueError(f"No street address found in: {address}")
        
    # Extract any apartment information from street address
    apt_info, street_parts = extract_apartment_info(street_parts)
    street_addr = ' '.join(street_parts)
    if apt_info:
        street_addr = f"{street_addr} {apt_info}"
    result["streetAddress"] = street_addr
    
    # Handle the remaining parts
    remaining_parts = parts[1:]
    
    # Check if next part is an apartment (if we didn't find one in street address)
    if not apt_info and len(remaining_parts) > 0:
        next_part = remaining_parts[0].strip()
        if any(indicator in next_part.lower() for indicator in ['apt', 'unit', '#', 'suite']):
            # This part is an apartment, add it to street address
            result["streetAddress"] = f"{street_addr} {next_part}"
            remaining_parts = remaining_parts[1:]
    
    # Last part should contain state and ZIP
    if not remaining_parts:
        raise ValueError(f"Missing city/state/ZIP in address: {address}")
        
    # City is the next part (or next-to-last if we have multiple parts)
    if len(remaining_parts) >= 2:
        result["city"] = remaining_parts[-2].strip()
        
        # Parse state and ZIP from last part
        state_zip = remaining_parts[-1].strip().split()
        if len(state_zip) >= 2:
            result["state"] = state_zip[0].upper()
            zip_code = state_zip[-1]
            if zip_code.isdigit() and len(zip_code) == 5:
                result["zipCode"] = zip_code
            else:
                raise ValueError(f"Invalid ZIP code in address: {zip_code}")
        else:
            raise ValueError(f"Missing state or ZIP in: {remaining_parts[-1]}")
    else:
        raise ValueError(f"Incomplete address format: {address}")
    
    return result
