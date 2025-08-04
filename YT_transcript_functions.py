import re

def iso_duration_to_hms(duration_str):
    # Extract hours, minutes, seconds using regex
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    
    if not match:
        return "00:00:00"  # Return default if format is incorrect
    
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    # Format as HH:MM:SS
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Example
# duration_str = "PT251H14M42S"
# print(iso_duration_to_hms(duration_str))
