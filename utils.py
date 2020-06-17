#!/usr/bin/env python3

from PyQt5.QtWidgets import QMessageBox
import os
import time
from datetime import datetime

# *******************************************
# Determine resource path being the relative path to the resource file.
# The resource path changes when built for an executable.loadLogFile
# *******************************************
def res_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

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
def tzone():
        offset =  int(time.timezone / -3600)
        if offset == 0:
            return ("[UTC}")
        else:
            return ("[UTC{0:+d}]".format(int(time.timezone / -3600)))

# *******************************************
# Pop-up message box.
# *******************************************
def showPopup(title, msg, info="", details=""):
    # Create pop-up message box.
    # Mandatory title and message.
    # Optional information and details.
    mb = QMessageBox()
    mb.setIcon(QMessageBox.Information)
    mb.setText(msg)
    if (info != ""):
        mb.setInformativeText(info)
    mb.setWindowTitle(title)
    if (details != ""):
        mb.setDetailedText(details)
    # Show message box.
    mb.exec_()
