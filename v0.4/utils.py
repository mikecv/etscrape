#!/usr/bin/env python3

import time
import os
from datetime import datetime

# *******************************************
# Convert seconds to time string.
# *******************************************
def secsToTime(t):
    secs = t % 60
    mins = t // 60
    hrs = mins // 60
    mins = mins - (hrs * 60)
    return ("{0:02d}:{1:02d}:{2:02d}".format(hrs, mins, secs))

# *******************************************
# Convert Unix time to string.
# *******************************************
def unixTime(t, utc):
    if utc != 0:
        return ("{0:s} [UTC]".format(datetime.utcfromtimestamp(t).strftime('%d/%m/%Y %H:%M:%S')))
    else:
        offset =  int(time.timezone / -3600)
        return ("{0:s} [UTC{1:+d}]".format(datetime.fromtimestamp(t).strftime('%d/%m/%Y %H:%M:%S'), offset))

# *******************************************
# Get time zone string.
# *******************************************
def tzone(useUTC):
    if useUTC:
        # If usig UTC retrun UTC as timezone.
        return ("[UTC}")
    else:
        # Else return the local timezone.
        offset =  int(time.timezone / -3600)
        if offset == 0:
            # Local timezone is actually UTC anyway.
            return ("[UTC}")
        else:
            # Else local timezone is offset from UTC.
            return ("[UTC{0:+d}]".format(int(time.timezone / -3600)))

# *******************************************
# Get path, filename, and extension.
# *******************************************
def getFileParts(fname):
    path, filename = os.path.split(fname)
    fn, fext = os.path.splitext(filename)
    return path, fn, fext
