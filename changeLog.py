#!/usr/bin/env python3

from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5 import QtGui

from utils import *

# *******************************************
# Change Log dialog class.
# *******************************************
class ChangeLogDialog(QDialog):
    def __init__(self):
        super(ChangeLogDialog, self).__init__()
        uic.loadUi(res_path("changeLog.ui"), self)

        self.showChangeLog()

    # *******************************************
    # Displays a "Change Log" dialog box.
    # *******************************************
    def showChangeLog(self):

        # Set dialog window icon.
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(res_path("./resources/about.png")))
        self.setWindowIcon(icon)

        # Update change log.
        self.changeLogText.textCursor().insertHtml("<h1><b>CHANGE LOG</b></h1><br>")
        self.changeLogText.textCursor().insertHtml("<h2><b>Version 0.3</b></h2>")
        self.changeLogText.textCursor().insertHtml("<ul>"\
            "<li>Added configuration to show times in UTC or local time. \
                Includes epoch indicator in status bar and suffix on displayed times.</li>" \
            "<li>Included signon ID in trip number in trip data pane and trip summary pane to relate better to logs.</li>" \
            "<li>Fixed bug where speed plot always had time axis in local timezone.</li>" \
            "<li>Fixed bug where SIGNON events with no (*) driver ID were not being detected properly.</li>" \
            "<li>Don't plot post trip speed points as detracts from trip events.</li>" \
            "<li>Set empty speed plot pane visible at start to highlight trip data area.</li>" \
            "<li>Fixed bug with wait cursor if log contains no trips.</li></ul><br>")
        self.changeLogText.textCursor().insertHtml("<h2><b>Version 0.2</b></h2>")
        self.changeLogText.textCursor().insertHtml("<ul>" \
            "<li>Added plot of speed data.</li>" \
            "<li>Added ability to read message logs (.csv) as well as debuglog files.</li>" \
            "<li>Added speed in event header data to events details information.</li>" \
            "<li>Added plot of vehicle speed. \
                Added zone speed limit line which is based on zone change events and \
                zone 1 & 2 speed limits as defined in application configuration.</li>" \
            "<li>Added check for trips without end of trip (TRIP) event.</li>" \
            "<li>Added check for bad speed values in SIGNON event header, i.e. > 150kph.</li>" \
            "<li>Added check for events with different Trip ID to sign-on event, or event times that are going backwards.</li>" \
            "<li>Added INPUT event to report input changes; events can be hidden using configuration parameter.</li>" \
            "<li>Added option to hide out of trip events; not that this option overrides showing input and other event configuration. \
                Added menu items to show/hide out of trip events as wells as INPUT events and other events. \
                These menu items are initialised from configuration and only persist for the application session.</li>" \
            "<li>Corrected checking of Trip ID for out of trip events, i.e. not checking.</li>" \
            "<li>Added additional events POWERDOWN and SERVICE.</li>" \
            "<li>Added _ underscore and spacebar characters in event name search to catch oddball events.</li>" \
            "<li>Refactored configuration file format; additional parameters added.</li>" \
            "<li>Set trip data tree to use alternate row colours to improve readability.</li>" \
            "<li>Show wait cursor when opening log files as large files can take time to load.</li>" \
            "<li>Cosmetic changes to improve readability.</li></ul><br>")
        self.changeLogText.textCursor().insertHtml("<h2><b>Version 0.1</b></h2>")
        self.changeLogText.textCursor().insertHtml("<ul>" \
            "<li>Initial draft release.</li>" \
            "<li>Parses log files and displays event data.</li>" \
            "<li>Not all event types supported.</li></ul>")

        # Show dialog.
        self.exec_()
