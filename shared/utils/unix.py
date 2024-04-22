import pytz
from datetime import datetime, timezone

def iso_to_unix(timestamp_str: str):
    """Converts ISO to UNIX in nanoseconds."""
    try:
        # Try to parse the timestamp with timezone information
        dt = datetime.fromisoformat(timestamp_str)
    except ValueError:
        # If no timezone is specified, assume UTC
        dt = datetime.fromisoformat(timestamp_str + 'Z').replace(tzinfo=timezone.utc)

    # Convert to Unix timestamp (seconds since the epoch, with nanoseconds)
    unix_timestamp = int(dt.timestamp() * 1e9)
    return unix_timestamp

def unix_to_iso(unix_timestamp: int, tz_info='UTC'):
    """Converts UNIX in nanoseconds to ISO assuming UNIX in nanoseconds"""
    # Convert Unix timestamp to datetime object in UTC
    dt_utc = datetime.fromtimestamp(unix_timestamp  / 1e9, tz=timezone.utc)

    # Check if a specific timezone is requested
    if tz_info != 'UTC':
        tz = pytz.timezone(tz_info)
        dt_tz = dt_utc.astimezone(tz)
        return dt_tz.isoformat()
    else:
        return dt_utc.isoformat()
