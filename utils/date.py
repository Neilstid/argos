from datetime import datetime, timedelta
from typing import Optional, Union


def days_ago(n: int, format: Optional[str] = None) -> Union[int, str]:
    """
    Return a timestamp or formatted date for N days ago.

    :param n: Number of days in the past
    :type n: int
    :param format: Optional strftime format; if provided a formatted string is returned
    :type format: Optional[str], optional
    :return: Unix timestamp (int) when format is None, otherwise formatted date string
    :rtype: Union[int, str]
    """
    if format:
        return (datetime.now() - timedelta(days=n)).strftime(format)
    else:
        return int((datetime.now() - timedelta(days=n)).timestamp())
