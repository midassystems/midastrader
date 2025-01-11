import pytz
import pandas as pd
from datetime import datetime, timezone


def iso_to_unix(timestamp_str: str):
    """
    Convert an ISO 8601 formatted datetime string to a UNIX timestamp in nanoseconds.

    Parses the provided ISO 8601 datetime string. If no timezone is specified, UTC is assumed.
    The function returns the UNIX timestamp in nanoseconds since the epoch (1970-01-01 00:00:00 UTC).

    Args:
        timestamp_str (str): ISO 8601 formatted datetime string.

    Returns:
        int: UNIX timestamp in nanoseconds.

    Raises:
        ValueError: If the input string is not a valid ISO 8601 format.
    """
    try:
        # Try to parse the timestamp with timezone information
        dt = datetime.fromisoformat(timestamp_str)

        # If the datetime is naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        # If parsing fails, raise an error
        raise ValueError("Invalid ISO 8601 datetime format")

    # Convert to Unix timestamp in nanoseconds
    unix_timestamp = int(dt.timestamp() * 1e9)
    return unix_timestamp


def unix_to_iso(unix_timestamp: int, tz_info="UTC"):
    """
    Convert a UNIX timestamp in nanoseconds to an ISO 8601 formatted datetime string.

    The UNIX timestamp is converted to a UTC datetime object, then adjusted to the
    specified timezone if provided.

    Args:
        unix_timestamp (int): UNIX timestamp in nanoseconds since the epoch.
        tz_info (str, optional): Timezone name (e.g., 'UTC', 'America/New_York'). Defaults to 'UTC'.

    Returns:
        str: ISO 8601 formatted datetime string in the specified timezone.

    Raises:
        pytz.UnknownTimeZoneError: If the provided timezone name is invalid.
    """
    # Convert Unix timestamp to datetime object in UTC
    dt_utc = datetime.fromtimestamp(unix_timestamp / 1e9, tz=timezone.utc)

    # Check if a specific timezone is requested
    if tz_info != "UTC":
        tz = pytz.timezone(tz_info)
        dt_tz = dt_utc.astimezone(tz)
        return dt_tz.isoformat()
    else:
        return dt_utc.isoformat()


def unix_to_date(unix_timestamp: int, tz_info="UTC") -> datetime.date:
    """
    Converts a UNIX timestamp in nanoseconds to an ISO 8601 formatted date string, with an optional timezone.

    This function takes a UNIX timestamp in nanoseconds and converts it into a datetime object. The datetime
    is initially set in UTC. If a different timezone is specified, the datetime is converted to that timezone
    before formatting it into an ISO 8601 date string (YYYY-MM-DD).

    Parameters:
    - unix_timestamp (int): The UNIX timestamp in nanoseconds since the epoch.
    - tz_info (str): A string representing the timezone for the resulting ISO string. Defaults to 'UTC'.

    Returns:
    - str: An ISO 8601 formatted date string in the specified timezone (YYYY-MM-DD).
    """
    # Convert Unix timestamp to datetime object in UTC
    dt_utc = datetime.fromtimestamp(unix_timestamp / 1e9, tz=timezone.utc)

    # Check if a specific timezone is requested
    if tz_info != "UTC":
        tz = pytz.timezone(tz_info)
        dt_tz = dt_utc.astimezone(tz)
        return dt_tz.date()
    else:
        return dt_utc.date()


def _convert_timestamp(
    df: pd.DataFrame,
    column: str = "timestamp",
    tz_info: str = "UTC",
) -> None:
    """
    Convert a DataFrame column of UNIX timestamps to ISO 8601 formatted strings.

    Args:
        df (pd.DataFrame): The DataFrame containing the timestamp column.
        column (str, optional): The name of the column to convert. Defaults to 'timestamp'.
        tz_info (str, optional): Timezone name for conversion. Defaults to 'UTC'.

    Returns:
        None: Modifies the DataFrame in place.
    """
    df[column] = pd.to_datetime(
        df[column].map(lambda x: unix_to_iso(x, tz_info))
    )


def resample_timestamp(df: pd.DataFrame, interval: str = "D", tz_info="UTC"):
    """
    Resample a DataFrame with a UNIX timestamp index to a specified time interval.

    Args:
        df (pd.DataFrame): DataFrame with a UNIX timestamp index.
        interval (str, optional): Resampling interval (e.g., 'D' for daily, 'H' for hourly). Defaults to 'D'.
        tz_info (str, optional): Timezone name for conversion. Defaults to 'UTC'.

    Returns:
        pd.DataFrame: A resampled DataFrame with the specified frequency.
    """
    utc = True

    if tz_info != "UTC":
        utc = False

    # Convert index to readable datetime
    df.index = pd.to_datetime(
        df.index.map(lambda x: unix_to_iso(x, tz_info)), utc=utc
    )

    # Store original UNIX timestamps before resampling
    original_timestamps = df.index.to_series().resample(interval).last()
    original_timestamps.dropna(inplace=True)

    # Resample to daily frequency, using the last value of each day
    daily_df = df.resample(interval).last()

    # Optionally, fill NaN values if necessary, depending on your specific needs
    daily_df.dropna(inplace=True)

    # Restore original UNIX timestamps
    daily_df.index = original_timestamps.map(
        lambda x: iso_to_unix(x.isoformat())
    )
    daily_df.index.name = "timestamp"

    return daily_df
