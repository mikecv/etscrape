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
# Convert Unix time to string with timezone.
# *******************************************
def unixTimeString(t, utc):
    if utc != 0:
        return ("{0:s} [UTC]".format(datetime.utcfromtimestamp(t).strftime('%d/%m/%Y %H:%M:%S')))
    else:
        offset =  int(time.timezone / -3600)
        return ("{0:s} [UTC{1:+d}]".format(datetime.fromtimestamp(t).strftime('%d/%m/%Y %H:%M:%S'), offset))

# *******************************************
# Convert Unix time to string without timezone.
# *******************************************
def timeTZ(t, utc):
    if utc != 0:
        return datetime.utcfromtimestamp(t)
    else:
        return datetime.fromtimestamp(t)

# *******************************************
# Get time zone string.
# *******************************************
def tzone(useUTC):
    if useUTC:
        # If usig UTC retrun UTC as timezone.
        return ("[UTC]")
    else:
        # Else return the local timezone.
        offset =  int(time.timezone / -3600)
        if offset == 0:
            # Local timezone is actually UTC anyway.
            return ("[UTC]")
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

# *******************************************
# Split string to multiple strings of maximum length.
# Don't split words.
# *******************************************
def splitLongString(longString, maxLen):

    lineLength = 0
    lineString = ""
    lineWords = 0
    splitString = ""
    splitLines = 0

    if len(longString) > maxLen:
        # Get words in the long string as a list.
        words = longString.split()

        # Cycle through words in list and concatenate until max length exceeded.
        for idx, w in enumerate(words):
            newLineLength = lineLength + len(w)
            if lineWords > 0:
                newLineLength += 1

            # Check if line too long.
            if newLineLength > maxLen:
                # Line too long so back off last word.
                # If only word on line then have to accept it.
                if lineWords == 0:
                    # If this is the first line then title is just this line.
                    if splitLines == 0:
                        splitString = w
                        splitLines += 1
                    # Else, add newline first.
                        splitString = "{0:s}\n{1:s}".format(splitString, w)
                        splitLines += 1
                        lineLength = 0
                # Already at least one word on this line, so put new word on next line.
                else:
                    # Add the existing part of the current line to the title.
                    if splitLines == 0:
                        splitString = "{0:s}".format(lineString)
                        splitLines += 1
                    else:
                        splitString = "{0:s}\n{1:s}".format(splitString, lineString)
                        splitLines += 1
                    # Add the new word to the next line.
                    lineString = w
                    lineWords = 1
                    lineLength = len(w)
            # Can add new word to current line as not over the limit yet.
            else:
                # If not the only word on the line then add a space first.
                if lineWords == 0:
                    lineString = w
                    lineLength += len(w)
                else:
                    lineString = "{0:s} {1:s}".format(lineString, w)
                    lineLength += (len(w) + 1)
                lineWords += 1
            # If there are no more words to go then add current line to the title.
            if idx == (len(words) - 1):
                if splitLines == 0:
                    splitString = "{0:s}".format(lineString)
                else:
                    splitString = "{0:s}\n{1:s}".format(splitString, lineString)
    else:
        splitString = longString

    return splitString