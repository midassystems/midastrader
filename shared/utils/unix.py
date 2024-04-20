import pytz
from datetime import datetime, timezone

from datetime import datetime, timezone
import pytz

def iso_to_unix(timestamp_str: str):
    try:
        # Try to parse the timestamp with timezone information
        dt = datetime.fromisoformat(timestamp_str)
    except ValueError:
        # If no timezone is specified, assume UTC
        dt = datetime.fromisoformat(timestamp_str + 'Z').replace(tzinfo=timezone.utc)

    # Convert to Unix timestamp (seconds since the epoch)
    unix_timestamp = int(dt.timestamp())
    return unix_timestamp

def unix_to_iso(unix_timestamp: int, tz_info='UTC'):
    # Convert Unix timestamp to datetime object in UTC
    dt_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)

    # Check if a specific timezone is requested
    if tz_info != 'UTC':
        tz = pytz.timezone(tz_info)
        dt_tz = dt_utc.astimezone(tz)
        return dt_tz.isoformat()
    else:
        return dt_utc.isoformat()





# def convert_to_unix(timestamp: str):
#     # Parse the timestamp string to a datetime object
#     dt = datetime.fromisoformat(timestamp)
    
#     # Assume the timestamp is in UTC for conversion
#     dt = dt.replace(tzinfo=timezone.utc)
    
#     # Convert to Unix timestamp (seconds since the epoch)
#     unix_timestamp = int(dt.timestamp())
    
#     return unix_timestamp

# def unix_to_iso(unix_timestamp: int):
#     # Convert Unix timestamp to datetime object in UTC
#     dt_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    
#     # Return the datetime in ISO 8601 format
#     return dt_utc.isoformat()

# def unix_to_est(unix_timestamp: int):
#     # Convert Unix timestamp to datetime object in UTC
#     dt_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    
#     # Convert UTC datetime to Eastern Standard Time
#     eastern = pytz.timezone('US/Eastern')
#     dt_est = dt_utc.astimezone(eastern)
    
#     # Return the datetime in ISO 8601 format for EST
#     return dt_est.isoformat()