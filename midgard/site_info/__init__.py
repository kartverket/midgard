"""Common function used by site_info classes

"""

# Standard library imports
from datetime import datetime
import pytz

def convert_to_utc(time: datetime) -> datetime:
    """Convert datetime object to UTC

    Args:
        time: Time zone aware datetime object

    Returns:
        Time zone unaware datetime object related to UTC
    """
    return time.astimezone(tz=pytz.utc).replace(tzinfo=None)