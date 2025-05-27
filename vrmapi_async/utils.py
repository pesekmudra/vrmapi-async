# --- vrmapi_async/utils.py
"""Utility functions for the VRM API client."""

import math
from datetime import datetime, timezone


def datetime_to_epoch(dt: datetime) -> int:
    """
    Converts a Python datetime object to an epoch timestamp (integer seconds).

    Ensures the datetime is timezone-aware (UTC) before conversion if naive.
    Rounds up to the nearest second to match the original implementation's behavior.

    :params dt: The datetime object to convert.
    :returns: The epoch timestamp as an integer.
    """
    if dt.tzinfo is None:
        # If naive, assume it's in the system's local timezone and convert to UTC
        # Or, for consistency, always assume UTC if naive:
        dt = dt.replace(tzinfo=timezone.utc)

    # Use timestamp() which returns seconds since epoch as a float, then ceil and int
    return int(math.ceil(dt.timestamp()))
