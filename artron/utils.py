# -*- coding: utf-8 -*-
"""
artron.utils
~~~~~~~~~~~

artron utilities shared between modules
"""
import time
import datetime


def strgmtime(gmtime):
    """Convert time to human readable format

    Parameters
    ----------
    gmtime : time.struct_time
        Time to convert. Allow float type.

    Returns
    -------
    date : str
        Time in format '%H:%M:%S'

    Example
    -------
    >>> strgmtime(time.gmtime(1.8))
    '00:00:01'
    >>> strgmtime(1.8)
    '00:00:01'
    """
    if isinstance(gmtime, float):
        gmtime = time.gmtime(gmtime)

    if not isinstance(gmtime, time.struct_time):
        raise ValueError("Wrong type %s. Required time.struct_time." \
            % type(gmtime).__name__)

    return time.strftime('%H:%M:%S', gmtime)


def strdate(date=None):
    """Convert datetime to human readable format

    Parameters
    ----------
    date : datetime.datetime
        Datetime to convert

    Returns
    -------
    date : str
        Date in format %Y-%m-%dT%H:%M:%S.%f

    Example
    -------
    >>> strdate(date=datetime.utcnow())
    '2018-07-31T12:15:03.749Z'
    """
    if not date:
        date = datetime.datetime.utcnow()

    # ensure datetime
    if not isinstance(date, datetime.datetime):
        raise ValueError("Wrong type %s. Required datetime.datetime" \
            % type(date).__name__)

    return str("{0}Z".format(
        date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    ))
