from datetime import datetime, timezone

def convert_to_unix(timestamp: str):
    # Parse the timestamp string to a datetime object
    dt = datetime.fromisoformat(timestamp)
    
    # Assume the timestamp is in UTC for conversion
    dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to Unix timestamp (seconds since the epoch)
    unix_timestamp = int(dt.timestamp())
    
    return unix_timestamp