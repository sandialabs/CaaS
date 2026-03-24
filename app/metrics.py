import logging
from datetime import datetime

logger = logging.getLogger("caas.metrics")


def to_unix_timestamp(timestamp):
    """Convert a timestamp in various formats to Unix (from epoch) timestamp.

    Args:
        timestamp: Input timestamp in str, datetime, object, or numeric format

    Returns:
        Unix timestamp as integer
    """
    if isinstance(timestamp, datetime):
        unix_time = timestamp.timestamp()
    elif isinstance(timestamp, (int, float)):
        # Checks if it's in milliseconds
        if timestamp > 1e10:  # likely milliseconds
            unix_time = timestamp / 1000
        else:
            unix_time = timestamp
    elif isinstance(timestamp, str):
        # Common timestamp formats to try
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%Y%m%d %H%M%S",
            "%Y%m%d",
        ]

        dt = None
        for format in formats:
            try:
                dt = datetime.strptime(timestamp.strip(), format)
                break
            except ValueError:
                continue

        if dt is None:
            raise ValueError(f"Unable to parse timestamp {timestamp}")

        unix_time = dt.timestamp()
    else:
        raise TypeError(f"Unsupported timestamp type {type(timestamp)}")

    return int(unix_time * 1000)
