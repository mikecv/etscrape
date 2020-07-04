#!/usr/bin/env python3

from PyQt5.QtWidgets import QMainWindow, QDialog, QFileDialog, QColorDialog, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem, QHeaderView, qApp, QApplication
from PyQt5 import uic
from PyQt5 import QtCore, QtGui
import logging
import logging.handlers
import json
import re
import time
from datetime import timedelta, datetime
import os
import sys
import webbrowser
import zipfile

from config import *
from utils import *
from tripinfo import *
from mplCharts import *

# *******************************************
# Program history.
# 0.1   MDC 21/05/2020  Original.
# 0.2   MDC 06/06/2020  Added speed chart.
#                       Added ability to read message logs as well.
#                       Numerous bug fixes and cosmetic changes.
# 0.3   MDC 15/06/2020  Added trip report export.
#                       Added configuration to show times in UTC or local time.
#                       Added option to export trip data to file.
#                       Added support to drag and drop log files to application.
#                       Added edit preferences dialog.
#                       Bug fixes.
# 0.4   MDC 29/06/2020  Bug fixes.
#                       Additions to the Trip Summary pane.
# *******************************************

# *******************************************
# TODO List
#
# Option for separate plot that shows all events like HighCharts for current trip.
# *******************************************

# Program version.
progVersion = "0.4"

# Create configuration values class object.
config = Config()

# *******************************************
# Create logger.
# Use rotating log files.
# *******************************************
logger = logging.getLogger('etscrape')
logger.setLevel(config.DebugLevel)
handler = logging.handlers.RotatingFileHandler('etscrape.log', maxBytes=config.LogFileSize, backupCount=config.LogBackups)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s.%(msecs)03d [%(name)s] [%(levelname)-8s] %(message)s', datefmt='%Y%m%d-%H:%M:%S', style='%'))
logging.Formatter.converter = time.localtime
logger.addHandler(handler)

# Log program version.
logger.info("Program version : {0:s}".format(progVersion))

# *******************************************
# Determine resource path being the relative path to the resource file.
# The resource path changes when built for an executable.
# *******************************************
def res_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    resPath = os.path.join(base_path, relative_path)
    return resPath

# *******************************************
# Etscrape class
# *******************************************
class UI(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(UI, self).__init__()
        uic.loadUi(res_path("etscrape.ui"), self)

        # Set up various window and widget icons.
        self.setIcons()

        # Attach to the Load Log File menu item.
        self.actionLoadLog.triggered.connect(self.loadLogFile)

        # Set up show menu items according to configuration.
        # These are just for the session, they are not written to configuration.
        self.actionShowInputEvents.setChecked(config.TripData["ShowInputEvents"])
        self.actionShowOtherEvents.setChecked(config.TripData["ShowOtherEvents"])
        self.actionShowDebugEvents.setChecked(config.TripData["ShowDebugEvents"])
        self.actionShowOutOfTripEvents.setChecked(config.TripData["ShowOutOfTripEvents"])

        # Attach to the show menu items.
        self.actionShowInputEvents.triggered.connect(self.showHideInputEvents)
        self.actionShowOtherEvents.triggered.connect(self.showHideOtherEvents)
        self.actionShowDebugEvents.triggered.connect(self.showHideDebugEvents)
        self.actionShowOutOfTripEvents.triggered.connect(self.showHideOutOfTripEvents)

        # Attach to the Export report for current trip menu item.
        self.actionExportCurrentTrip.triggered.connect(self.exportCurrentTrip)

        # Attach to the Export report for all trips menu item.
        self.actionExportAllTrips.triggered.connect(self.exportAllTrips)

        # Attach to the edit preferences menu item.
        self.actionPreferences.triggered.connect(self.editPreferences)

        # Attach to the Quit menu item.
        self.actionQuit.triggered.connect(app.quit)

        # Attach to the Help menu item.
        self.actionHelp.triggered.connect(self.help)

        # Attach to the Change Log menu item.
        self.actionChangeLog.triggered.connect(self.changeLog)

        # Attach to the About menu item.
        self.actionAbout.triggered.connect(self.about)

        # Set application to accept drag and drop files.
        # Can drop file anywhere on the main window.
        self.setAcceptDrops(True)

        # View actions.
        self.actionCollapseAllLevels.triggered.connect(self.collapseAllLevels)
        self.actionExpandAllLevels.triggered.connect(self.expandAllLevels)

        # Trip summary actions.
        self.NextTripBtn.setEnabled(False)
        self.NextTripBtn.clicked.connect(lambda: self.tripButtonClicked(True))
        self.PrevTripBtn.setEnabled(False)
        self.PrevTripBtn.clicked.connect(lambda: self.tripButtonClicked(False))

        # Create figure for speed plots.
        self.spdFig = MplCanvas(self, config, logger, width=10, height=6, dpi=100)
        self.plotTbar = NavigationToolbar(self.spdFig, self)
        self.ChartLayout.addWidget(self.plotTbar)
        self.ChartLayout.addWidget(self.spdFig)

        # Flag indicating no data to show.
        # And flag indicating no trip selected.
        self.haveTrips = False
        self.selectedTrip = 0

        # If we don't have any trips loaded yet then disable the export menu.
        self.actionExportCurrentTrip.setEnabled(self.haveTrips)
        self.actionExportAllTrips.setEnabled(self.haveTrips)

        # Enable expand / collapse buttons.
        self.actionCollapseAllLevels.setEnabled(False)
        self.actionExpandAllLevels.setEnabled(False)

        # Don't show 'other' events static text if not configured.
        if config.TripData["ShowOtherEvents"] == False:
            self.OtherEventsStaticLbl.hide()

        self.showEpochStatus()

        # Show appliction window.
        self.show()

    # *******************************************
    # Respond to drag / drop events.
    # *******************************************
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            logger.debug("User dropped acceptable file type on application.")
        else:
            event.ignore()
            logger.debug("User dropped unacceptable file type on application.")

    # *******************************************
    # Overwrite response to accepted dropped file method.
    # *******************************************
    def dropEvent(self, event):
        # If more than one file selected to load only load the first one.
        filename = event.mimeData().urls()[0].toLocalFile()
        # Only process files.
        if os.path.isfile(filename):
            logger.debug("File dropped on application: {0:s}".format(filename))

            # Open and read log file.
            with open(filename, encoding='cp1252', errors="surrogateescape") as f:
                self.logData = f.read()

            logger.info("Opened and read log file : {0:s}".format(filename))
            self.showTempStatusMsg("{0:s}".format(filename), config.TripData["TmpStatusMessagesMsec"])

            # Process the loaded log file.
            self.processLogFile()

    # *******************************************
    # Set up various window and widget icons.
    # *******************************************
    def setIcons(self):
        # Set window icon.
        iconG = QtGui.QIcon()
        iconG.addPixmap(QtGui.QPixmap(res_path("./resources/about.png")), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(iconG)

        # Set previous trip button icon.
        iconL = QtGui.QIcon()
        iconL.addPixmap(QtGui.QPixmap(res_path("./resources/leftGrnArrow.png")))
        self.PrevTripBtn.setIcon(iconL)

        # Set next trip button icon.
        iconR = QtGui.QIcon()
        iconR.addPixmap(QtGui.QPixmap(res_path("./resources/rightGrnArrow.png")))
        self.NextTripBtn.setIcon(iconR)

        # Set collapse all trip data button icon.
        iconC = QtGui.QIcon()
        iconC.addPixmap(QtGui.QPixmap(res_path("./resources/collapse.png")))
        self.actionCollapseAllLevels.setIcon(iconC)

        # Set expand all trip data button icon.
        iconE = QtGui.QIcon()
        iconE.addPixmap(QtGui.QPixmap(res_path("./resources/expand.png")))
        self.actionExpandAllLevels.setIcon(iconE)

    # *******************************************
    # Callback function in next/prev trip buttons pressed.
    # *******************************************
    def tripButtonClicked(self, nxtTrip):
        # Only action if we have a trip.
        if self.haveTrips:
            # If next trip button pressed, then increment trip if we can.
            if nxtTrip:
                if self.selectedTrip < self.numTrips:
                    self.selectedTrip += 1
                    self.tripDataTree.setCurrentItem(self.tripDataTree.topLevelItem((self.selectedTrip - 1)))
                    self.updateTripSummary(self.selectedTrip)
                    self.plotTripData(self.selectedTrip)
                    # Check if no more next trips, then disable the button.
                    self.updateTripBtnState()
            else:
                if self.selectedTrip > 1:
                    self.selectedTrip -= 1
                    self.tripDataTree.setCurrentItem(self.tripDataTree.topLevelItem((self.selectedTrip - 1)))
                    self.updateTripSummary(self.selectedTrip)
                    self.plotTripData(self.selectedTrip)
                    # Check if no more previous trips, then disable the button.
                    self.updateTripBtnState()

    # *******************************************
    # Update next/prev trip button state.
    # *******************************************
    def updateTripBtnState(self):
        if self.selectedTrip == self.numTrips:
            self.NextTripBtn.setEnabled(False)
        else:
            self.NextTripBtn.setEnabled(True)
        if self.selectedTrip == 1:
            self.PrevTripBtn.setEnabled(False)
        else:
            self.PrevTripBtn.setEnabled(True)

    # *******************************************
    # Callback function for show/hide input events menu checkbox.
    # *******************************************
    def showHideInputEvents(self):
        logger.debug("User set show event menu state: {0:b}".format(self.actionShowInputEvents.isChecked()))

        # If we have trips clear them and add them again.
        # will lose collapse/expand state though.
        self.rerenderTripData()

    # *******************************************
    # Callback function for show/hide other events menu checkbox.
    # *******************************************
    def showHideOtherEvents(self):
        logger.debug("User set show event menu state: {0:b}".format(self.actionShowOtherEvents.isChecked()))

        # If we have trips clear them and add them again.
        # will lose collapse/expand state though.
        self.rerenderTripData()

    # *******************************************
    # Callback function for show/hide debug events menu checkbox.
    # *******************************************
    def showHideDebugEvents(self):
        logger.debug("User set show event menu state: {0:b}".format(self.actionShowDebugEvents.isChecked()))

        # If we have trips clear them and add them again.
        # will lose collapse/expand state though.
        self.rerenderTripData()

    # *******************************************
    # Callback function for show/hide out of trip events menu checkbox.
    # *******************************************
    def showHideOutOfTripEvents(self):
        logger.debug("User set show event menu state: {0:b}".format(self.actionShowOutOfTripEvents.isChecked()))

        # If we have trips clear them and add them again.
        # will lose collapse/expand state though.
        self.rerenderTripData()

    # *******************************************
    # Re-render trip data.
    # *******************************************
    def rerenderTripData(self):
        if self.haveTrips:
            # Clear triptrip tree.
            self.clearTrips()
            # Clear speed plot.
            self.spdFig.clearFigure()
            # Repopulate trips.
            self.populateTrips()

    # *******************************************
    # Show temporary status message.
    # Pass message string and duration in (msec).
    # Default is for permanent message.
    # *******************************************
    def showTempStatusMsg(self, msg, dur=0):
        self.statusbar.showMessage(msg, dur)

    # *******************************************
    # Show time epoch on status bar.
    # *******************************************
    def showEpochStatus(self):
        boldFont=QtGui.QFont()
        boldFont.setBold(True)
        self.epochLbl = QLabel()
        self.epochLbl.setStyleSheet("color: black; ")
        self.epochLbl.setFont(boldFont)
        self.epochLbl.setText(tzone(config.TimeUTC))
        self.statusBar().addPermanentWidget(self.epochLbl)

    # *******************************************
    # Clear loaded trips.
    # *******************************************
    def clearTrips(self):
        # If we have trip data then delete data.
        if self.haveTrips:
            self.tripDataTree.setParent(None)
            self.tripDataTree = None
            self.spdFig.clearFigure()

    # *******************************************
    # Process log file.
    # *******************************************
    def processLogFile(self):
        logger.debug("Processing loaded log file.")

        # Clear trips if we have any.
        self.clearTrips()

        # Clear trip data to show.
        self.haveTrips = False

        # Disable expand / collapse buttons.
        self.actionCollapseAllLevels.setEnabled(False)
        self.actionExpandAllLevels.setEnabled(False)

        # Disable the export menu.
        self.actionExportCurrentTrip.setEnabled(False)
        self.actionExportAllTrips.setEnabled(False)

        # Change to wait cursor as large files may take a while to open and process.
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        self.numTrips = 0
        self.tripLog = []

        # Look for all the trip starts and capture individual buffers.
        patternStart = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT .+ (SIGNON).?')
        for st in re.finditer(patternStart, self.logData):
            # Store start and end (actually next start) for buffer for each trip.
            edge = st.start(0)
            if (self.numTrips == 0):
                prevStart = edge
            else:
                self.tripLog.append(Trip(config, logger, self.logData[prevStart:edge]))
                prevStart = edge

            # Increment trip counter.
            self.numTrips += 1
        
        # Total trips in file.
        logger.debug("Trips in file : {0:d}".format(self.numTrips))

        # Update last trip to end of file.
        if (self.numTrips > 0):
            self.tripLog.append(Trip(config, logger, self.logData[prevStart:len(self.logData)]))

            # Extract data from all trips.
            for t in self.tripLog:
                t.extractTripData()

            # Set flag indicating we have trip data to show.
            self.haveTrips = True

            # Set first trip as selected trip.
            self.selectedTrip = 1

            # Update prev/next button states.
            self.updateTripBtnState()

            # Enable expand / collapse buttons.
            self.actionCollapseAllLevels.setEnabled(True)
            self.actionExpandAllLevels.setEnabled(True)

            # Enable the export menu.
            self.actionExportCurrentTrip.setEnabled(True)
            self.actionExportAllTrips.setEnabled(True)

            # Populate trip data.updateTripBtnState
            self.populateTrips()
        else:
            # Revert to the normal cursor.
            QApplication.restoreOverrideCursor()

            # Show pop-up indicating no trip data found in log file.
            showPopup("Trip", "Log file contains no trip information.", "(No trip start \"SIGNON\" events encountered)")

        # Revert to the normal cursor.
        QApplication.restoreOverrideCursor()                       

    # *******************************************
    # Populate trip data.
    # *******************************************
    def populateTrips(self):
        # Change to wait cursor as large files may take a while to populate.
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        # Define a tree widget for trip data.
        self.tripDataTree = QTreeWidget()
        self.tripDataTree.setHeaderLabels(['Trip Data', '', ''])
        self.tripDataTree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tripDataTree.header().setStretchLastSection(False)
        self.tripDataTree.setAlternatingRowColors(True)

        fontBold = QtGui.QFont()
        fontBold.setBold(True)
        fontPlain = QtGui.QFont()
        fontPlain.setBold(False)

        # Populate trip titles.
        for idx, t in enumerate(self.tripLog):
            # Add top levels to trees.
            # Label trips with trip number (including signon ID) and time.
            tripNum = "Trip {0:d} [ID {1:d}]".format((idx+1), t.signOnId)
            # Need to check that the trip was ended.
            if t.tripEnd > 0:
                tripTime = "{0:s}  to  {1:s}".format(unixTime(t.tripStart, config.TimeUTC), unixTime(t.tripEnd, config.TimeUTC))
                logger.debug("Adding trip: {0:d}, occurred: {1:s}".format(idx+1, tripTime))
                tripLevel = QTreeWidgetItem(self.tripDataTree, [tripNum, tripTime])
            else:
                tripTime = "{0:s}".format(unixTime(t.tripStart, config.TimeUTC))
                logger.debug("Adding trip: {0:d}, occurred: {1:s}".format(idx+1, tripTime))
                tripLevel = QTreeWidgetItem(self.tripDataTree, [tripNum, tripTime, "No trip end."])
                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))
                tripLevel.setForeground(1, QtGui.QBrush(QtGui.QColor(config.TripData["TripColour"])))
                tripLevel.setForeground(2, QtGui.QBrush(QtGui.QColor(config.TripData["CommentColour"])))
                tripLevel.setFont(2, fontBold)

            tripLevel.setBackground(0, QtGui.QBrush(QtGui.QColor(config.TripData["TripBackColour"])))
            tripLevel.setBackground(1, QtGui.QBrush(QtGui.QColor(config.TripData["TripBackColour"])))
            tripLevel.setFont(0, fontBold)
            tripLevel.setFont(1, fontBold)

            # Populate event titles.
            for idx2, ev in enumerate(t.events):
                # Label events with event type and time.
                eventType = "{0:s}".format(ev.event)
                eventTime = "{0:s}".format(unixTime(ev.serverTime, config.TimeUTC))
                logger.debug("Adding event: {0:s}, occurred: {1:s}".format(eventType, eventTime))
                eventLevel = QTreeWidgetItem(tripLevel, [eventType, eventTime, ev.alertText])

                # Apply specific formatting for normal events.
                # Apply different formatting if INPUT or 'other' events.
                if not ev.isOther:
                    if ev.isInput:
                        eventLevel.setFont(0, fontPlain)
                        eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["InputEventColour"])))
                    elif ev.isDebug:
                        eventLevel.setFont(0, fontPlain)
                        eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["DebugEventColour"])))
                    else:
                        eventLevel.setFont(0, fontBold)
                        eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["EventColour"])))
                else:
                    eventLevel.setFont(0, fontPlain)
                    eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["OtherEventColour"])))

                if ev.alertText != "":
                    eventLevel.setFont(2, fontBold)
                    eventLevel.setForeground(2, QtGui.QBrush(QtGui.QColor(config.TripData["CommentColour"])))

                # Check it see if event is of other type in which case don't have details.
                # Note 'debug' events are also 'other' events.
                if not ev.isOther:
                    # Populate event details.
                    for idx3, evDetail in enumerate(self.getEventDetails(t, ev)):
                        # Include event details for all events.
                        detailLevel = QTreeWidgetItem(eventLevel, [evDetail[0], evDetail[1]])
                        logger.debug("Adding event detail: {0:s}, value: {1:s}".format(evDetail[0], evDetail[1]))
                        detailLevel.setTextAlignment(0, QtCore.Qt.AlignRight)
                        detailLevel.setFont(0, fontBold)
                        if evDetail[2] == True:
                            detailLevel.setFont(1, fontBold)
                            # If detail alert then use alert colour.
                            detailLevel.setForeground(1, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))
                            # If detail alert then also use alert colour for related event.
                            eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))

                            # If detail alert then also use alert colour for related trip.
                            # Don't highlight trip if event is hidden.
                            if (ev.isInput and (self.actionShowInputEvents.isChecked())):
                                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))
                            elif (ev.isDebug and (self.actionShowDebugEvents.isChecked())):
                                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))
                            elif (ev.isOther and (self.actionShowOtherEvents.isChecked())):
                                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))
                            elif ((not ev.isInput) and (not ev.isOther) and (not ev.isDebug)):
                                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))

                # Hide input events if not configured to do so.
                if (ev.isInput and (not self.actionShowInputEvents.isChecked())):
                    eventLevel.setHidden(True)

                # Hide other events if not configured to do so.
                if (ev.isOther and (not self.actionShowOtherEvents.isChecked())):
                    eventLevel.setHidden(True)

                # Hide debug events if not configured to do so.
                if (ev.isDebug and (not self.actionShowDebugEvents.isChecked())):
                    eventLevel.setHidden(True)

                # Hide out of trip events if not configured to do so.
                if (ev.isOutOfTrip and (not self.actionShowOutOfTripEvents.isChecked())):
                    eventLevel.setHidden(True)

        # Add trip data tree to layout.
        self.verticalLayout.addWidget(self.tripDataTree)

        # Set the previously designated current trip as the current trip.
        # The selected trip is initialised to 1 when the log file is loaded,
        # there after the selected trip is maintained so that when log file is re-rendered
        self.tripDataTree.setCurrentItem(self.tripDataTree.topLevelItem(self.selectedTrip - 1))
        self.updateTripSummary(self.selectedTrip)
        self.plotTripData(self.selectedTrip)

        # Define callback if selection is made to a different trip.
        self.tripDataTree.itemSelectionChanged.connect(self.tripItemSelected)

        # Revert to the normal cursor.
        QApplication.restoreOverrideCursor()                       

        # Show the trip data tree.
        self.tripDataTree.show()

    # *******************************************
    # Trip item selected.
    # *******************************************
    def tripItemSelected(self):
        # Same original selected trip to check if it changed.
        originalTrip = self.selectedTrip

        # Determine trip details selected.
        # Get the currently selected item.
        node = self.tripDataTree.selectedItems()[0]
        # Look for the top parent (trip) for selected item.
        while node.parent() != None:
            node = node.parent()
        # Extract the trip number from the column 0 text.
        trip = node.text(0)
        patternTrip = re.compile(r'Trip ([0-9]+) \[')
        t = re.search(patternTrip, trip)
        if t:
            self.selectedTrip = int(t.group(1))
        else:
            # Error if trip number not found.
            # Set selected trip 0 which will cause a termination.
            logger.error("No trip number found.")
            self.selectedTrip = 0

        # If trip changed then update the trip summary information.
        if (self.selectedTrip != originalTrip):
            self.updateTripSummary(self.selectedTrip)
            # Update the state of the prev/next trip buttons.
            self.updateTripBtnState()
            # Update plot trip data.
            self.plotTripData(self.selectedTrip)

    # *******************************************
    # Update trip summary information for selected trip.
    # *******************************************
    def updateTripSummary(self, t):
        ti = self.tripLog[t-1]
        # Trip information.
        self.TripNoLbl.setText("{0:d}".format(t))
        self.TripIdLbl.setText("[{0:d}]".format(ti.signOnId))
        self.StartTimeLbl.setText("{0:s}".format(unixTime(ti.tripStart, config.TimeUTC)))
        self.EndTimeLbl.setText("{0:s}".format(unixTime(ti.tripEnd, config.TimeUTC)))
        self.TripDurationLbl.setText("{0:s}".format(secsToTime(ti.tripEnd - ti.tripStart)))
        # Event counts.
        # Vehicle events.
        self.VehicleEventsLbl.setText("{0:d}".format(ti.numVehicleEvents))
        self.updateSummaryCount(self.VehicleOverspeedLbl, ti.numOverspeed)
        self.updateSummaryCount(self.ZoneOverspeedLbl, ti.numZoneOverspeed)
        self.updateSummaryCount(self.EngineOverspeedLbl, ti.numEngineOverspeed)
        self.updateSummaryCount(self.LowCoolantLbl, ti.numLowCoolant)
        self.updateSummaryCount(self.LowOilPressureLbl, ti.numOilPressure)
        self.updateSummaryCount(self.HighTemperatureLbl, ti.numEngineTemperature)
        self.updateSummaryCount(self.HiImpactLbl, ti.numImpact_H)
        self.updateSummaryCount(self.MidImpactLbl, ti.numImpact_M)
        self.updateSummaryCount(self.LoImpactLbl, ti.numImpact_L)
        # Operator events.
        self.OperatorEventsLbl.setText("{0:d}".format(ti.numOperatorEvents))
        self.updateSummaryCount(self.UnbuckledOpLbl, ti.numUnbuckled_O)
        self.updateSummaryCount(self.UnbuckledPassLbl, ti.numUnbuckled_P)
        self.updateSummaryCount(self.ChecklistLbl, ti.numChecklist)
        self.updateSummaryCount(self.ZoneChangeLbl, ti.numZoneChange)
        # Trip events.
        self.TripEventsLbl.setText("{0:d}".format(ti.numTripEvents))
        # Report events.
        self.ReportEventsLbl.setText("{0:d}".format(ti.numReportEvents))
        # Other events.
        self.OtherEventsLbl.setText("{0:d}".format(ti.numOtherEvents))
        # Debug events.
        self.DebugEventsLbl.setText("{0:d}".format(ti.numDebugEvents))

    # *******************************************
    # Update trip summary information for selected trip.
    # Also highlight if count not zero.
    # *******************************************
    def updateSummaryCount(self, item, count):
        # Set additional still if count > 0.
        # Else clear.
        if count > 0:
            item.setStyleSheet("font-weight: bold; color: {0:s}".format(config.TripData["SummaryAlertColour"]))
        else:
            item.setStyleSheet("")
        # Update count text.
        item.setText("{0:d}".format(count))

    # *******************************************
    # Do plotting of speed etc.
    # *******************************************
    def plotTripData(self, tripNo):

        # Get speed data for the nominated trip.
        tList = []
        sList = []
        for sl in self.tripLog[tripNo-1].speedLog:
            # Format time axis list in the correct timezone for display.
            if config.TimeUTC == 0:
                tList.append(datetime.fromtimestamp(sl.time))
            else:
                tList.append(datetime.utcfromtimestamp(sl.time))
            sList.append(sl.speed)

        # Plot with updated data.
        self.spdFig.updatePlotData(self.selectedTrip, tList, sList)

        # Plot speed limit lines on plot.
        # At this point speed limits from application configuration as not included in log.
        # Get zone change data for the nominated trip.
        tList = []
        zList = []
        for zl in self.tripLog[tripNo-1].zoneXings:
            # Format time axis list in the correct timezone for display.
            if config.TimeUTC == 0:
                tList.append(datetime.fromtimestamp(zl.time))
            else:
                tList.append(datetime.utcfromtimestamp(zl.time))
            if zl.zoneOutput == 1:
                # Slow zone.
                zList.append(config.SpdPlot["DefaultLowLimit"])
            elif zl.zoneOutput == 2:
                # Fast zone.
                zList.append(config.SpdPlot["DefaultHiLimit"])
            else:
                # Open zone.
                zList.append(0)

        self.spdFig.drawSpeedLimits(tList, zList)

        # Need to show plot as originally hidden.
        self.plotTbar.show()
        self.spdFig.show()

    # *******************************************
    # Callback function for export report for current trip menu selection.
    # *******************************************
    def exportCurrentTrip(self):
        logger.debug("User selected Export current trip report menu item.")

        # Configure and launch file selection dialog.
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter("*.txt")
        dialog.setDefaultSuffix('.txt')
        dialog.setViewMode(QFileDialog.List)
        dialog.setAcceptMode(QFileDialog.AcceptSave)

        # If returned filename then open/create.
        if dialog.exec_():
            filenames = dialog.selectedFiles()

            # If have a filename then open.
            if filenames[0] != "":
                # Open file for writing
                xf = open(filenames[0], "w")

                # Export selected trip.
                self.exportTrip(xf, self.tripLog[self.selectedTrip - 1])

                logger.info("Opened and wrote export file : {0:s}".format(filenames[0]))
                self.showTempStatusMsg("{0:s}".format(filenames[0]), config.TripData["TmpStatusMessagesMsec"])

                # Close file after writing.
                xf.close()

    # *******************************************
    # Callback function for export report for all trips menu selection.
    # *******************************************
    def exportAllTrips(self):
        logger.debug("User selected Export all trips report menu item.")

        # Configure and launch file selection dialog.
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter("*.txt")
        dialog.setDefaultSuffix('.txt')
        dialog.setViewMode(QFileDialog.List)
        dialog.setAcceptMode(QFileDialog.AcceptSave)

        # If returned filename then open/create.
        if dialog.exec_():
            filenames = dialog.selectedFiles()

            # If have a filename then open.
            if filenames[0] != "":
                # Open file for writing
                xf = open(filenames[0], "w")

                # Change to wait cursor as exporting a lot of files may take a while.
                QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

                # Cycle through each trip and export.
                for t in self.tripLog:
                    # Export trip.
                    self.exportTrip(xf, t)

                # Retore the wait cursor now that export complete.
                QApplication.restoreOverrideCursor()

                logger.info("Opened and wrote export file : {0:s}".format(filenames[0]))
                self.showTempStatusMsg("{0:s}".format(filenames[0]), config.TripData["TmpStatusMessagesMsec"])

                # Close file after writing.
                xf.close()

    # *******************************************
    # Export report for nominated trip.
    # *******************************************
    def exportTrip(self, xf, ti):
        # Export trip data to file.
        logger.debug("Exporting trip report for Trip ID: {0:d}".format(ti.signOnId))
        xf.write("===================================================\n")
        xf.write("              ____  ____  ____  ____ \n")
        xf.write("             (_  _)(  _ \(_  _)(  _ \\\n")
        xf.write("               )(   )   / _)(_  )___/\n")
        xf.write("              (__) (_)\_)(____)(__)  \n")
        xf.write("                                     \n")
        xf.write("===================================================\n")
        xf.write("Signon ID  : {0:d}\n".format(ti.signOnId))
        xf.write("Start time : {0:s}\n".format(unixTime(ti.tripStart, config.TimeUTC)))
        xf.write("End time   : {0:s}\n".format(unixTime(ti.tripEnd, config.TimeUTC)))
        xf.write("===================================================\n")
        xf.write("===================================================\n")
        xf.write("EVENTS (TOTALS)\n")
        xf.write("===================================================\n")
        xf.write("Vehicle overspeed            : {0:d}\n".format(ti.numOverspeed))
        xf.write("Zone overspeed               : {0:d}\n".format(ti.numZoneOverspeed))
        xf.write("Engine overspeed             : {0:d}\n".format(ti.numEngineOverspeed))
        xf.write("Engine coolant level low     : {0:d}\n".format(ti.numLowCoolant))
        xf.write("Engine oil pressure low      : {0:d}\n".format(ti.numOilPressure))
        xf.write("Engine temperature high      : {0:d}\n".format(ti.numEngineTemperature))
        xf.write("Seatbelt unbuckled operator  : {0:d}\n".format(ti.numUnbuckled_O))
        xf.write("Seatbelt unbuckled passenger : {0:d}\n".format(ti.numUnbuckled_P))
        xf.write("Impact Critical              : {0:d}\n".format(ti.numImpact_H))
        xf.write("Impact High                  : {0:d}\n".format(ti.numImpact_M))
        xf.write("Impact Low                   : {0:d}\n".format(ti.numImpact_L))
        xf.write("Zone change                  : {0:d}\n".format(ti.numZoneChange))
        xf.write("===================================================\n")
        xf.write("===================================================\n")
        xf.write("EVENTS (DETAILS)\n")
        xf.write("===================================================\n")
        for ev in ti.events:
            xf.write("{0:s}\n".format(ev.event))
            xf.write("\tTime              : {0:s}\n".format(unixTime(ev.serverTime, config.TimeUTC)))
            if (ev.event == "SIGNON"):
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tDriver ID         : {0:s}\n".format(ev.driverId))
                xf.write("\tCard ID           : {0:d}\n".format(ev.cardId))
                xf.write("\tResult            : {0:s}\n".format(ev.result))
                xf.write("\tBits Read         : {0:d}\n".format(ev.bitsRead))
                xf.write("\tKeyboard          : {0:s}\n".format(ev.keyboard))
                xf.write("\tCard Reader       : {0:s}\n".format(ev.cardReader))
            elif (ev.event == "OVERSPEED"):
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tDuration          : {0:s}\n".format(str(timedelta(seconds=ev.duration))))
            elif (ev.event == "ZONEOVERSPEED"):
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tDuration          : {0:s}\n".format(str(timedelta(seconds=ev.duration))))
                xf.write("\tMax Speed         : {0:d}\n".format(ev.maxSpeed))
                xf.write("\tZone Output       : {0:d}\n".format(ev.zoneOutput))
            elif (ev.event == "ENGINEOVERSPEED"):
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tDuration          : {0:s}\n".format(str(timedelta(seconds=ev.duration))))
                xf.write("\tMax RPM           : {0:d}\n".format(ev.maxRPM))
            elif ev.event in {"LOWCOOLANT", "OILPRESSURE", "ENGINETEMP"}:
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tDuration          : {0:s}\n".format(str(timedelta(seconds=ev.duration))))
            elif ev.event == "UNBUCKLED":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tDuration          : {0:s}\n".format(str(timedelta(seconds=ev.duration))))
                if ev.seatOwner == "D":
                    seatOwner = "Operator"
                elif ev.seatOwner == "P":
                    seatOwner = "Passenger"
                else:
                    seatOwner = "?"
                xf.write("\tSeat Owner        : {0:s}\n".format(seatOwner))
            elif ev.event == "ZONECHANGE":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tFrom Zone         : {0:d}\n".format(ev.fromZone))
                xf.write("\tTo Zone           : {0:d}\n".format(ev.toZone))
                xf.write("\tZone Output       : {0:d}\n".format(ev.zoneOutput))
            elif ev.event == "IMPACT":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tForward G         : {0:0.1f}\n".format(ev.fwdG))
                xf.write("\tReverse G         : {0:0.1f}\n".format(ev.revG))
                xf.write("\tLeft G            : {0:0.1f}\n".format(ev.leftG))
                xf.write("\tRight G           : {0:0.1f}\n".format(ev.rightG))
                xf.write("\tMax G (1)         : {0:0.1f}\n".format(ev.maxG1))
                xf.write("\tMax G (2)         : {0:0.1f}\n".format(ev.maxG2))
                if ev.severity == "C":
                    severity = "High"
                elif ev.severity == "W":
                    severity = "Medium"
                elif ev.severity == "-":
                    severity = "Low"
                xf.write("\tSeverity          : {0:s}\n".format(severity))
            elif ev.event == "CHECKLIST":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tResult            : {0:s}\n".format(ev.result))
                xf.write("\tFailed Questions  : {0:d}\n".format(ev.failedQ))
                xf.write("\tTime Taken        : {0:s}\n".format(str(timedelta(seconds=ev.duration))))
                xf.write("\tChecklist Version : {0:d}\n".format(ev.failedQ))
                if ev.chkType == "F":
                    chkType = "Full"
                elif ev.chkType == "C":
                    chkType = "Operator Change"
                elif ev.chkType == "B":
                    chkType = "Bypass"
                else:
                    chkType = "?"
                xf.write("\tChecklist Type    : {0:s}\n".format(chkType))
            elif ev.event == "XSIDLESTART":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
            elif ev.event == "XSIDLE":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tMaximum Idle Time : {0:s}\n".format(str(timedelta(seconds=ev.maxIdle))))
            elif ev.event == "SERVICE":
                xf.write("\tService ID        : {0:d}\n".format(ev.serviceId))
            elif ev.event == "REPORT":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tReport Speed      : {0:d}\n".format(ev.speed))
                xf.write("\tDirection         : {0:d}\n".format(ev.direction))
            elif ev.event == "INPUT":
                xf.write("\tCurrent Speed     : {0:d}\n".format(ev.speed))
                xf.write("\tInput             : {0:d} - {1:s}\n".format(ev.inputNo, config.Channels[ev.inputNo - 1]["Name"]))
                xf.write("\tState             : {0:d}\n".format(ev.inputState))
                xf.write("\tActive Time       : {0:s}\n".format(str(timedelta(seconds=ev.activeTime))))
            elif ev.event == "DEBUG":
                xf.write("\tDetails           : {0:s}\n".format(ev.debugInfo))
            elif ev.event == "TRIP":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
                xf.write("\tTime Forward      : {0:s}\n".format(str(timedelta(seconds=ev.timeFwd))))
                xf.write("\tTime Reverse      : {0:s}\n".format(str(timedelta(seconds=ev.timeRev))))
                xf.write("\tTime Idle         : {0:s}\n".format(str(timedelta(seconds=ev.timeIdle))))
                xf.write("\tMax Idle Time     : {0:s}\n".format(str(timedelta(seconds=ev.maxIdle))))
            elif ev.event == "TRIPSUMMARY":
                xf.write("\tSign-on ID        : {0:d}\n".format(ev.signOnId))
        xf.write("===================================================\n\n")
                
    # *******************************************
    # Toolbar to collapse all trip data.
    # *******************************************
    def collapseAllLevels(self):
        logger.debug("User selected Collapse All Levels control.")
        if self.haveTrips:
            self.tripDataTree.collapseAll()

    # *******************************************
    # Toolbar to expand all trip data.
    # *******************************************
    def expandAllLevels(self):
        logger.debug("User selected Expand All Levels control.")
        if self.haveTrips:
            self.tripDataTree.expandAll()

    # *******************************************
    # Get event details for event.
    # *******************************************
    def getEventDetails(self, trip, event):
        # Initialise list of event details
        eventList = []

        # Event details will depend on event type.
        # Check for alert values as well.
        if event.event == "SIGNON":
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            if event.driverId == "*":
                eventList.append(("Driver ID", "{0:s}".format(event.driverId), True))
            else:
                eventList.append(("Driver ID", "{0:d}".format(int(event.driverId)), False))
            eventList.append(("Card ID", "{0:d}".format(event.cardId), False))
            eventList.append(("Result", "{0:s}".format(event.result), False))
            eventList.append(("Bits Read", "{0:d}".format(event.bitsRead), False))
            eventList.append(("Keyboard", "{0:s}".format(event.keyboard), False))
            eventList.append(("Card Reader", "{0:s}".format(event.cardReader), False))
        elif event.event == "OVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
        elif event.event == "ZONEOVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            eventList.append(("Maximum Speed", "{0:d}".format(event.maxSpeed), (event.maxSpeed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Zone Output", "{0:d}".format(event.zoneOutput),(event.zoneOutput == 0)))
        elif event.event == "ENGINEOVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            eventList.append(("Maximum RPM", "{0:d}".format(event.maxRPM), config.TripData["BadRpmLimit"]))
        elif event.event in {"LOWCOOLANT", "OILPRESSURE", "ENGINETEMP", "OFFSEAT", "OVERLOAD"}:
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
        elif event.event == "UNBUCKLED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            if event.seatOwner == "D":
                seatOwner = "Operator"
            elif event.seatOwner == "P":
                seatOwner = "Passenger"
            else:
                seatOwner = "?"
            eventList.append(("Seat Owner", "{0:s}".format(seatOwner), (seatOwner == "?")))
        elif event.event == "ZONECHANGE":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("From Zone", "{0:d}".format(event.fromZone), False))
            eventList.append(("To Zone", "{0:d}".format(event.toZone), False))
            eventList.append(("Zone Output", "{0:d}".format(event.zoneOutput), False))
        elif event.event == "IMPACT":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Forward G", "{0:0.1f}".format(event.fwdG), False))
            eventList.append(("Reverse G", "{0:0.1f}".format(event.revG), False))
            eventList.append(("Left G", "{0:0.1f}".format(event.leftG), False))
            eventList.append(("Right G", "{0:0.1f}".format(event.rightG), False))
            eventList.append(("Max G (1)", "{0:0.1f}".format(event.maxG1), False))
            eventList.append(("Max G (2)", "{0:0.1f}".format(event.maxG2), False))
            if event.severity == "C":
                severity = "High"
            elif event.severity == "W":
                severity = "Medium"
            elif event.severity == "-":
                severity = "Low"
            eventList.append(("Severity", "{0:s}".format(severity), False))
        elif event.event == "CHECKLIST":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Result", "{0:s}".format(event.result), False))
            eventList.append(("Failed Questions", "{0:d}".format(event.failedQ), False))
            eventList.append(("Time Taken", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            eventList.append(("Checklist Version", "{0:d}".format(event.chkVersion), False))
            if event.chkType == "F":
                chkType = "Full"
            elif event.chkType == "C":
                chkType = "Operator Change"
            elif event.chkType == "B":
                chkType = "Bypass"
            else:
                chkType = "?"
            eventList.append(("Checklist Type", "{0:s}".format(chkType), (chkType == "?")))
        elif event.event == "XSIDLESTART":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
        elif event.event == "XSIDLE":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Max Idle Time", "{0:s}".format(str(timedelta(seconds=event.maxIdle))), (event.maxIdle == 0)))
        elif event.event == "CONFIG":
            pass
        elif event.event == "SERVICE":
            eventList.append(("Service ID", "{0:d}".format(event.serviceId), False))
        elif event.event == "POWERDOWN":
            pass
        elif event.event == "REPORT":
            if (event.signOnId == -1):
                eventList.append(("Sign-on ID", "{0:s}".format("*"), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            else:
                eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Report Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Direction", "{0:d}".format(event.direction), ((event.direction < 0) or (event.direction > 360))))
        elif event.event == "CRITICALOUTPUTSET":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), (event.signOnId != trip.signOnId)))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Critical Output Set", "{0:d}".format(event.criticalOutput), False))
        elif event.event == "INPUT":
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= config.TripData["BadSpeedLimit"])))
            eventList.append(("Input", "{0:d} - {1:s}".format(event.inputNo, config.Channels[event.inputNo - 1]["Name"]), ((event.inputNo < 1) or (event.inputNo > 10))))
            eventList.append(("State", "{0:d}".format(event.inputState), ((event.inputState < 0) or (event.inputState > 1))))
            eventList.append(("Active Time", "{0:s}".format(str(timedelta(seconds=event.activeTime))), False))
        elif event.event == "DEBUG":
            eventList.append(("Details", "{0:s}".format(event.debugInfo), ("Time1H" in event.debugInfo)))
        elif event.event == "TRIP":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), (event.signOnId != trip.signOnId)))
            eventList.append(("Time Forward", "{0:s}".format(str(timedelta(seconds=event.timeFwd))), False))
            eventList.append(("Time Reverse", "{0:s}".format(str(timedelta(seconds=event.timeRev))), False))
            eventList.append(("Time Idle", "{0:s}".format(str(timedelta(seconds=event.timeIdle))), False))
            eventList.append(("Max Idle Time", "{0:s}".format(str(timedelta(seconds=event.maxIdle))), False))
        elif event.event == "TRIPSUMMARY":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), (event.signOnId != trip.signOnId)))
        elif event.event == "TRIPLOAD":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), (event.signOnId != trip.signOnId)))
            eventList.append(("Travel Time Loaded", "{0:s}".format(str(timedelta(seconds=event.travelLoaded))), False))
            eventList.append(("Travel Time Unloaded", "{0:s}".format(str(timedelta(seconds=event.travelUnloaded))), False))
            eventList.append(("Idle Time Loaded", "{0:s}".format(str(timedelta(seconds=event.idleLoaded))), False))
            eventList.append(("Idle Time Unloaded", "{0:s}".format(str(timedelta(seconds=event.idleUnloaded))), False))
            eventList.append(("Lift Count", "{0:d}".format(event.liftCount), False))
            eventList.append(("Cummulative Weight", "{0:d}".format(event.cumWeight), False))

        # Return list of all event details to display
        return eventList

    # *******************************************
    # Load log file.
    # *******************************************
    def loadLogFile(self):
        logger.debug("User selected Load Log File control.")
        # Configure and launch file selection dialog.
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setNameFilters(["Log files (*)"])
        
        # If returned filename then open.
        if dialog.exec_():
            filenames = dialog.selectedFiles()

            # If have a filename then open.
            if filenames[0] != "":
                # Open and read log file.
                with open(filenames[0], encoding='cp1252', errors="surrogateescape") as f:
                    self.logData = f.read()

                logger.info("Opened and read log file : {0:s}".format(filenames[0]))
                self.showTempStatusMsg("{0:s}".format(filenames[0]), config.TripData["TmpStatusMessagesMsec"])

                # Process the loaded log file.
                self.processLogFile()
            else:
                logger.info("No log file selected.")

    # *******************************************
    # Edit Preferences control selected.
    # Displays an "About" dialog box.
    # *******************************************
    def editPreferences(self):
        logger.debug("User selected Edit Preferences menu control.")

        # Create edit prefernces dialog.        
        PreferencesDialog(config, self)

    # *******************************************
    # About control selected.
    # Displays an "About" dialog box.
    # *******************************************
    def about(self):
        logger.debug("User selected About menu control.")

        # Create about dialog.        
        AboutDialog(progVersion)

    # *******************************************
    # Change Log control selected.
    # Displays a "Change Log" dialog box.
    # *******************************************
    def changeLog(self):
        logger.debug("User selected Change Log menu control.")

        # Create about dialog.        
        ChangeLogDialog()

    # *******************************************
    # Help control selected.
    # Displays help file using web browser.
    # *******************************************
    def help(self):
        logger.debug("User selected Help menu control.")
    
        # Construct the url.
        url = res_path("./resources/ETscrapeHelp.html")
        url = "file://" + url
        # Call the web browser to render the url.
        # This is not guaranteed to be the default browser on any particular system.
        webbrowser.open(url)

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

# *******************************************
# Preferences dialog class.
# *******************************************
class PreferencesDialog(QDialog):
    def __init__(self, config, app):
        super(PreferencesDialog, self).__init__()
        uic.loadUi(res_path("preferences.ui"), self)

        self.config = config
        self.app = app

        # Preload the configuration values.

        # Debug values.
        self.debugLevelVal.setValidator(QtGui.QIntValidator(0, 100))
        self.debugLevelVal.setText(str(self.config.DebugLevel))
        self.debugFileSizeVal.setValidator(QtGui.QIntValidator(1, 1000))
        self.debugFileSizeVal.setText(str(int(self.config.LogFileSize / 1000)))
        self.debugBackupsVal.setValidator(QtGui.QIntValidator(1, 3))
        self.debugBackupsVal.setText(str(self.config.LogBackups))

        # Locale values.
        self.utcVal.setChecked(not (self.config.TimeUTC == 0))

        # Trip values.
        self.tripTitleBgColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["TripBackColour"]))
        self.tripTitleBgColVal.clicked.connect(lambda: self.getColour(self.tripTitleBgColVal))
        self.tripIDTxtColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["TripColour"]))
        self.tripIDTxtColVal.clicked.connect(lambda: self.getColour(self.TripColour))
        self.eventNameColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["EventColour"]))
        self.eventNameColVal.clicked.connect(lambda: self.getColour(self.eventNameColVal))
        self.alertColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["AlertColour"]))
        self.alertColVal.clicked.connect(lambda: self.getColour(self.alertColVal))
        self.commentColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["CommentColour"]))
        self.commentColVal.clicked.connect(lambda: self.getColour(self.commentColVal))
        self.summaryAlertColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["SummaryAlertColour"]))
        self.summaryAlertColVal.clicked.connect(lambda: self.getColour(self.summaryAlertColVal))
        self.otherEventColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["OtherEventColour"]))
        self.otherEventColVal.clicked.connect(lambda: self.getColour(self.otherEventColVal))
        self.inputEventColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["InputEventColour"]))
        self.inputEventColVal.clicked.connect(lambda: self.getColour(self.inputEventColVal))
        self.debugEventColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.TripData["DebugEventColour"]))
        self.debugEventColVal.clicked.connect(lambda: self.getColour(self.debugEventColVal))
        self.tempMsgMsecVal.setValidator(QtGui.QIntValidator(1, 60))
        self.tempMsgMsecVal.setText(str(int(self.config.TripData["TmpStatusMessagesMsec"] / 1000)))
        self.showOtherVal.setChecked(self.app.actionShowOtherEvents.isChecked())
        self.showInputVal.setChecked(self.app.actionShowInputEvents.isChecked())
        self.showDebugVal.setChecked(self.app.actionShowDebugEvents.isChecked())
        self.showOutOfTripVal.setChecked(self.app.actionShowOutOfTripEvents.isChecked())
        self.speedAlertLimVal.setValidator(QtGui.QIntValidator(30, 160))
        self.speedAlertLimVal.setText(str(self.config.TripData["BadSpeedLimit"]))
        self.rpmAlertLimVal.setValidator(QtGui.QIntValidator(500, 10000))
        self.rpmAlertLimVal.setText(str(self.config.TripData["BadRpmLimit"]))

        # Speed plot values.
        self.lowSpeedVal.setValidator(QtGui.QIntValidator(1, 160))
        self.lowSpeedVal.setText(str(self.config.SpdPlot["DefaultLowLimit"]))
        self.highSpeedVal.setValidator(QtGui.QIntValidator(1, 160))
        self.highSpeedVal.setText(str(self.config.SpdPlot["DefaultHiLimit"]))
        self.speedLineColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.SpdPlot["SpeedColour"]))
        self.speedLineColVal.clicked.connect(lambda: self.getColour(self.speedLineColVal))
        self.zoneLineColVal.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(self.config.SpdPlot["ZoneColour"]))
        self.zoneLineColVal.clicked.connect(lambda: self.getColour(self.zoneLineColVal))
        self.axisFontSizeVal.setValidator(QtGui.QIntValidator(5, 10))
        self.axisFontSizeVal.setText(str(self.config.SpdPlot["AxesTitleFontSize"]))
        self.titleFontSizeVal.setValidator(QtGui.QIntValidator(6, 12))
        self.titleFontSizeVal.setText(str(self.config.SpdPlot["PlotTitleFontSize"]))

        # Connect to SAVE dialog button for processing.
        self.SaveDialogBtn.clicked.connect(self.savePreferences)
        # Connect to CANCEL dialog button to quit dialog.
        self.CancelDialogBtn.clicked.connect(self.close)

        # Show the edit preferences dialog.
        self.showPreferences()

    # *******************************************
    # Pick a colour and set.
    # Set the QPushButton colour to the colour selected.
    # *******************************************
    def getColour(self, colVar):
        colName = QColorDialog.getColor().name()
        colVar.setStyleSheet("QPushButton {{background-color: {0:s}; border: None}}".format(colName))

    # *******************************************
    # Displays a "Preferences" dialog box.
    # *******************************************
    def showPreferences(self):

        # Show dialog.
        self.exec_()

    # *******************************************
    # User selected to save preferences.
    # *******************************************
    def savePreferences(self):
        logger.debug("User saving preferences.")

        # Flag indicating a preference has changed.
        prefChanged = False

        # Flag indicating if need to re-render trip data for prefernece to take effect.
        rerender = False

        ###########################
        # Debugging
        ###########################
        # Debug level.
        val = int(self.debugLevelVal.text())
        if val != self.config.DebugLevel:
            # Set the configuration value.
            self.config.DebugLevel = val
            logger.debug("Change to debug level: {0:d}".format(self.config.DebugLevel))
            logger.setLevel(self.config.DebugLevel)
            prefChanged = True
        # Debug file size.
        val = int(self.debugFileSizeVal.text()) * 1000
        if val != self.config.LogFileSize:
            # Set the configuration value.
            self.config.LogFileSize = val
            logger.debug("Change to debug file size: {0:d}".format(self.config.LogFileSize))
            prefChanged = True
        # Debug backup count.
        val = int(self.debugBackupsVal.text())
        if val != self.config.LogBackups:
            # Set the configuration value.
            self.config.LogBackups = val
            logger.debug("Change to debug backup count: {0:d}".format(self.config.LogBackups))
            prefChanged = True

        ###########################
        # Locale
        ###########################
        # UTC time reference.
        val = self.utcVal.isChecked()
        if val == (self.config.TimeUTC == 0):
            # Set the configuration value.
            self.config.TimeUTC = int(val)
            logger.debug("Change to time reference (UTC): {0:d}".format(self.config.TimeUTC))
            # Update status bar item.
            self.app.epochLbl.setText(tzone(val))
            prefChanged = True
            rerender = True

        ###########################
        # Trip Data
        ###########################
        # Trip title background colour.
        col = self.tripTitleBgColVal.palette().button().color().name()
        if col != self.config.TripData["TripBackColour"]:
            # Set the configuration value.
            self.config.TripData["TripBackColour"] = col
            logger.debug("Change to trip tile background colour: {0:s}".format(self.config.TripData["TripBackColour"]))
            prefChanged = True
            rerender = True
        # Trip ID text colour.
        col = self.tripIDTxtColVal.palette().button().color().name()
        if col != self.config.TripData["TripColour"]:
            # Set the configuration value.
            self.config.TripData["TripColour"] = col
            logger.debug("Change to trip text colour: {0:s}".format(self.config.TripData["TripColour"]))
            prefChanged = True
            rerender = True
        # Event text colour.
        col = self.eventNameColVal.palette().button().color().name()
        if col != self.config.TripData["EventColour"]:
            # Set the configuration value.
            self.config.TripData["EventColour"] = col
            logger.debug("Change to event text colour: {0:s}".format(self.config.TripData["EventColour"]))
            prefChanged = True
            rerender = True
        # Alert text colour.
        col = self.alertColVal.palette().button().color().name()
        if col != self.config.TripData["AlertColour"]:
            # Set the configuration value.
            self.config.TripData["AlertColour"] = col
            logger.debug("Change to alert text colour: {0:s}".format(self.config.TripData["AlertColour"]))
            prefChanged = True
            rerender = True
        # Comment text colour.
        col = self.commentColVal.palette().button().color().name()
        if col != self.config.TripData["CommentColour"]:
            # Set the configuration value.
            self.config.TripData["CommentColour"] = col
            logger.debug("Change to comment text colour: {0:s}".format(self.config.TripData["CommentColour"]))
            prefChanged = True
            rerender = True
        # Summary alert text colour.
        col = self.summaryAlertColVal.palette().button().color().name()
        if col != self.config.TripData["SummaryAlertColour"]:
            # Set the configuration value.
            self.config.TripData["SummaryAlertColour"] = col
            logger.debug("Change to summary alert text colour: {0:s}".format(self.config.TripData["SummaryAlertColour"]))
            prefChanged = True
            rerender = True
        # Other event text colour.
        col = self.otherEventColVal.palette().button().color().name()
        if col != self.config.TripData["OtherEventColour"]:
            # Set the configuration value.
            self.config.TripData["OtherEventColour"] = col
            logger.debug("Change to other event text colour: {0:s}".format(self.config.TripData["OtherEventColour"]))
            prefChanged = True
            rerender = True
        # Input event text colour.
        col = self.inputEventColVal.palette().button().color().name()
        if col != self.config.TripData["InputEventColour"]:
            # Set the configuration value.
            self.config.TripData["InputEventColour"] = col
            logger.debug("Change to input event text colour: {0:s}".format(self.config.TripData["InputEventColour"]))
            prefChanged = True
            rerender = True
        # Debug event text colour.
        col = self.debugEventColVal.palette().button().color().name()
        if col != self.config.TripData["DebugEventColour"]:
            # Set the configuration value.
            self.config.TripData["DebugEventColour"] = col
            logger.debug("Change to debug event text colour: {0:s}".format(self.config.TripData["DebugEventColour"]))
            prefChanged = True
            rerender = True
        # Temporary status message timeout.
        val = int(self.tempMsgMsecVal.text()) * 1000
        if val != self.config.TripData["TmpStatusMessagesMsec"]:
            # Set the configuration value.
            self.config.TripData["TmpStatusMessagesMsec"] = val
            logger.debug("Change to temporary status message timeout: {0:d}".format(self.config.TripData["TmpStatusMessagesMsec"]))
            prefChanged = True
        # Show other events.
        val = self.showOtherVal.isChecked()
        if val != self.app.actionShowOtherEvents.isChecked():
            # Set the configuration value.
            self.config.TripData["ShowOtherEvents"] = int(val)
            logger.debug("Change to show other events: {0:d}".format(self.config.TripData["ShowOtherEvents"]))
            # Update menu item.
            self.app.actionShowOtherEvents.setChecked(val)
            prefChanged = True
            rerender = True
        # Show input events.
        val = self.showInputVal.isChecked()
        if val != self.app.actionShowInputEvents.isChecked():
            # Set the configuration value.
            self.config.TripData["ShowInputEvents"] = int(val)
            logger.debug("Change to show input events: {0:d}".format(self.config.TripData["ShowInputEvents"]))
            # Update menu item.
            self.app.actionShowInputEvents.setChecked(val)
            prefChanged = True
            rerender = True
        # Show debug events.
        val = self.showDebugVal.isChecked()
        if val != self.app.actionShowDebugEvents.isChecked():
            # Set the configuration value.
            self.config.TripData["ShowDebugEvents"] = int(val)
            logger.debug("Change to show debug events: {0:d}".format(self.config.TripData["ShowDebugEvents"]))
            # Update menu item.
            self.app.actionShowDebugEvents.setChecked(val)
            prefChanged = True
            rerender = True
        # Show out of trip events.
        val = self.showOutOfTripVal.isChecked()
        if val != self.app.actionShowOutOfTripEvents.isChecked():
            # Set the configuration value.
            self.config.TripData["ShowOutOfTripEvents"] = int(val)
            logger.debug("Change to show out of trip events: {0:d}".format(self.config.TripData["ShowOutOfTripEvents"]))
            # Update menu item.
            self.app.actionShowOutOfTripEvents.setChecked(val)
            prefChanged = True
            rerender = True
        # Bad vehicle speed limit.
        val = int(self.speedAlertLimVal.text())
        if val != self.config.TripData["BadSpeedLimit"]:
            # Set the configuration value.
            self.config.TripData["BadSpeedLimit"] = val
            logger.debug("Change to bad vehicle speed limit: {0:d}".format(self.config.TripData["BadSpeedLimit"]))
            prefChanged = True
            rerender = True
        # Bad engine speed limit.
        val = int(self.rpmAlertLimVal.text())
        if val != self.config.TripData["BadRpmLimit"]:
            # Set the configuration value.
            self.config.TripData["BadRpmLimit"] = val
            logger.debug("Change to bad engine speed limit: {0:d}".format(self.config.TripData["BadRpmLimit"]))
            prefChanged = True

        # Cancel, so close dialog.
        self.close()

        ###########################
        # Speed Plot Data
        ###########################
        # Default slow zone speed limit.
        val = int(self.lowSpeedVal.text())
        if val != self.config.SpdPlot["DefaultLowLimit"]:
            # Set the configuration value.
            self.config.SpdPlot["DefaultLowLimit"] = val
            logger.debug("Change to default slow zone speed limit: {0:d}".format(self.config.SpdPlot["DefaultLowLimit"]))
            prefChanged = True
        # Default fast zone speed limit.
        val = int(self.highSpeedVal.text())
        if val != self.config.SpdPlot["DefaultHiLimit"]:
            # Set the configuration value.
            self.config.SpdPlot["DefaultHiLimit"] = val
            logger.debug("Change to default fast zone speed limit: {0:d}".format(self.config.SpdPlot["DefaultHiLimit"]))
            prefChanged = True
        # Speed line colour.
        col = self.speedLineColVal.palette().button().color().name()
        if col != self.config.SpdPlot["SpeedColour"]:
            # Set the configuration value.
            self.config.SpdPlot["SpeedColour"] = col
            logger.debug("Change to speed plot line colour: {0:s}".format(self.config.SpdPlot["SpeedColour"]))
            prefChanged = True
        # Zone change line colour.
        col = self.zoneLineColVal.palette().button().color().name()
        if col != self.config.SpdPlot["ZoneColour"]:
            # Set the configuration value.
            self.config.SpdPlot["ZoneColour"] = col
            logger.debug("Change to zone change plot line colour: {0:s}".format(self.config.SpdPlot["ZoneColour"]))
            prefChanged = True
        # Plot axis text font size.
        val = int(self.axisFontSizeVal.text())
        if val != self.config.SpdPlot["AxesTitleFontSize"]:
            # Set the configuration value.
            self.config.SpdPlot["AxesTitleFontSize"] = val
            logger.debug("Change to plot axis text font size: {0:d}".format(self.config.SpdPlot["AxesTitleFontSize"]))
            prefChanged = True
        # Plot title text font size.
        val = int(self.titleFontSizeVal.text())
        if val != self.config.SpdPlot["PlotTitleFontSize"]:
            # Set the configuration value.
            self.config.SpdPlot["PlotTitleFontSize"] = val
            logger.debug("Change to plot title text font size: {0:d}".format(self.config.SpdPlot["PlotTitleFontSize"]))
            prefChanged = True

        # Save the configuration values (if changed).
        if prefChanged:
            logger.debug("Changes saved to preferences.")
            self.config.saveConfig()

        # Rerender display if UI preference changed.
        if rerender:
            self.app.rerenderTripData()

# *******************************************
# About dialog class.
# *******************************************
class AboutDialog(QDialog):
    def __init__(self, version):
        super(AboutDialog, self).__init__()
        uic.loadUi(res_path("about.ui"), self)

        self.showAbout(version)

    # *******************************************
    # Displays an "About" dialog box.
    # *******************************************
    def showAbout(self, version):
        # Set dialog window icon.
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(res_path("./resources/about.png")))
        self.setWindowIcon(icon)

        # Update version information.
        self.versionLbl.setText("Version : {0:s}".format(version))

        # Update dialog icon.
        self.aboutIcon.setPixmap(QtGui.QPixmap(res_path("./resources/about.png")))

        # Show dialog.
        self.exec_()

# *******************************************
# Change Log dialog class.
# *******************************************
class ChangeLogDialog(QDialog):
    def __init__(self):
        super(ChangeLogDialog, self).__init__()
        uic.loadUi(res_path("changeLog.ui"), self)

        # Show the change log.
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
        self.changeLogText.textCursor().insertHtml("<h2><b>Version 0.4</b></h2>")
        self.changeLogText.textCursor().insertHtml("<ul>"\
            "<li>Fixed zone change line in speed plot which was inadvertantly broken in previous release.</li>" \
            "<li>Removed time reversal check on POWERDOWN event as always out of order. \
                also removed POWERDOWN event from speed plot.</li>"
            "<li>Save selected trip so not lost when rerendering the trip data, e.g. after showning hidden events.</li>" \
            "<li>Fixed crash if opening bad codec files, e.g. zipped files.</li>" \
            "<li>Fixed bug with editing preferences where Show menu items did not reflect changes to configuration, \
                also fixed Cancel/Save buttons which are swapped for Linux/Windows.</li>" \
            "<li>Fixed bug when upgrading configuration file.</li>" \
            "<li>Fixed bug with time zone in status bar always showing local timezone.</li>" \
            "<li>Fixed summary pane data some static text being cropped, \
                also added checklist total to summary data.</li>" \
            "<li>Removed video file from help page as not compliant with all browsers.</li>" \
            "<li>Added Added DEBUG totals to Trip Summary pane; \
                changed so that summary totals always updated even if event type not shown.</li>" \
            "<li>Added rerendering of trip data if UI changes were made to preferences so would apply straight away.</ul><br>")
        self.changeLogText.textCursor().insertHtml("<h2><b>Version 0.3</b></h2>")
        self.changeLogText.textCursor().insertHtml("<ul>"\
            "<li>Added menu items to export data for the selected trip or for all trips to a file.</li>" \
            "<li>Added ability to drag and drop log files onto application and have them open automatically.</li>" \
            "<li>Added Edit Preferences dialog from main menu. Saves changes to configuration file.</li>" \
            "<li>Added configuration to show times in UTC or local time. \
                Includes epoch indicator in status bar and suffix on displayed times.</li>" \
            "<li>Included signon ID in trip number in trip data pane and trip summary pane to relate better to logs.</li>" \
            "<li>Added option to show/hide DEBUG events. Also added additional detail on DEBUG events, \
                including alerting if 1H time correction is detected.</li>" \
            "<li>Fixed bug where speed plot always had time axis in local timezone.</li>" \
            "<li>Fixed bug where SIGNON events with no (*) driver ID were not being detected properly.</li>" \
            "<li>Fixed bug when opening log file so current file not cleared unless new log file selected.</li>" \
            "<li>Don't plot post trip speed points as detracts from trip events.</li>" \
            "<li>Set empty speed plot pane visible at start to highlight trip data area.</li>" \
            "<li>Made speed and tacho high limits configuration values.</li>" \
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

# *******************************************
# Create UI
# *******************************************
app = QApplication(sys.argv)
etscrape = UI()
app.exec_()
