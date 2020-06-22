#!/usr/bin/env python3

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QLabel, QTreeWidget, QTreeWidgetItem, QHeaderView, qApp, QApplication
from PyQt5 import QtCore, QtGui
from PyQt5 import uic
import logging
import logging.handlers
import json
import re
import time
from datetime import timedelta, datetime
import sys
import webbrowser

from config import *
from utils import *
from tripinfo import *
from mplCharts import *
from changeLog import *
from about import *

# *******************************************
# Program history.
# 0.1   MDC 21/05/2020  Original.
# 0.2   MDC 06/06/2020  Added speed chart.
#                       Added ability to read message logs as well.
#                       Numerous bug fixes and cosmetic changes.
# 0.3   MDC 15/06/2020  Added trip report export.
#                       Added configuration to show times in UTC or local time.
#                       Bug fixes.
# *******************************************

# *******************************************
# TODO List
#
# Add details to DEBUG messages; useful for detecting 1H time shift errors.
# Look at drag and drop of files into application to open automatically.
# INPUT event names for smartrack logs is wrong; look into options, perhaps smartrack mode in configuration, check log for smartrack.
# When adding log file ask to append or flush and add new; do we need to separate log files in the tree (maybe not).
# Generate trip report. IN PROGRESS.
# Add properties dialog to set all parameters and generate config file.
# *******************************************

# Program version.
progVersion = "0.3 (wip)"

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
        self.actionShowOutOfTripEvents.setChecked(config.TripData["ShowOutOfTripEvents"])

        # Attach to the show menu items.
        self.actionShowInputEvents.triggered.connect(self.showHideInputEvents)
        self.actionShowOtherEvents.triggered.connect(self.showHideOtherEvents)
        self.actionShowOutOfTripEvents.triggered.connect(self.showHideOutOfTripEvents)

        # Attach to the Export report for current trip menu item.
        self.actionExportCurrentTrip.triggered.connect(self.exportCurrentTrip)

        # Attach to the Quit menu item.
        self.actionQuit.triggered.connect(app.quit)

        # Attach to the Help menu item.
        self.actionHelp.triggered.connect(self.help)

        # Attach to the Change Log menu item.
        self.actionChangeLog.triggered.connect(self.changeLog)

        # Attach to the About menu item.
        self.actionAbout.triggered.connect(self.about)

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
        if self.haveTrips:
            # Clear triptrip tree.
            self.clearTrips()
            # Clear speed plot.
            self.spdFig.clearFigure()
            # Repopulate trips.
            self.populateTrips()

    # *******************************************
    # Callback function for show/hide other events menu checkbox.
    # *******************************************
    def showHideOtherEvents(self):
        logger.debug("User set show event menu state: {0:b}".format(self.actionShowOtherEvents.isChecked()))

        # If we have trips clear them and add them again.
        # will lose collapse/expand state though.
        if self.haveTrips:
            # Clear triptrip tree.
            self.clearTrips()
            # Clear speed plot.
            self.spdFig.clearFigure()
            # Repopulate trips.
            self.populateTrips()

    # *******************************************
    # Callback function for show/hide out of trip events menu checkbox.
    # *******************************************
    def showHideOutOfTripEvents(self):
        logger.debug("User set show event menu state: {0:b}".format(self.actionShowOutOfTripEvents.isChecked()))

        # If we have trips clear them and add them again.
        # will lose collapse/expand state though.
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
        self.epochLbl.setText(tzone())
        self.statusBar().addPermanentWidget(self.epochLbl)

    # *******************************************
    # Clear loaded trips.
    # *******************************************
    def clearTrips(self):
        # If we have trip data then delete data.
        if self.haveTrips:
            self.tripDataTree.setParent(None)
            self.tripDataTree = None

    # *******************************************
    # Load log file.
    # *******************************************
    def loadLogFile(self):
        logger.debug("User selected Load Log File control.")

        # Clear trips if we have any.
        self.clearTrips()

        # Clear trip data to show.
        self.haveTrips = False

        # Delete log data.
        self.logData = ""

        # Disable expand / collapse buttons.
        self.actionCollapseAllLevels.setEnabled(False)
        self.actionExpandAllLevels.setEnabled(False)

        # Disable the export menu.
        self.actionExportCurrentTrip.setEnabled(False)

        # Get log file to load.
        self.openLogFile()

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
                if  not ev.isOther:
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
                            elif (ev.isOther and (self.actionShowOtherEvents.isChecked())):
                                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))
                            elif ((not ev.isInput) and (not ev.isOther)):
                                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.TripData["AlertColour"])))

                # Hide input events if not configured to do so.
                if (ev.isInput and (not self.actionShowInputEvents.isChecked())):
                    eventLevel.setHidden(True)

                # Hide other events if not configured to do so.
                if (ev.isOther and (not self.actionShowOtherEvents.isChecked())):
                    eventLevel.setHidden(True)

                # Hide out of trip events if not configured to do so.
                if (ev.isOutOfTrip and (not self.actionShowOutOfTripEvents.isChecked())):
                    eventLevel.setHidden(True)

        # Add trip data tree to layout.
        self.verticalLayout.addWidget(self.tripDataTree)

        # Set the first trip as the current trip.
        # This is so that we can populate the trip details frame.
        self.tripDataTree.setCurrentItem(self.tripDataTree.topLevelItem(0))
        self.selectedTrip = 1
        self.updateTripSummary(1)
        self.plotTripData(self.selectedTrip)

        # Define callback if selection is made to a different trip.
        self.tripDataTree.itemSelectionChanged.connect(self.tripItemSelected)

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
        self.updateSummaryCount(self.UnbuckledOpLbl, ti.numUnbuckled_O)
        self.updateSummaryCount(self.UnbuckledPassLbl, ti.numUnbuckled_P)
        # Operator events.
        self.OperatorEventsLbl.setText("{0:d}".format(ti.numOperatorEvents))
        self.updateSummaryCount(self.HiImpactLbl, ti.numImpact_H)
        self.updateSummaryCount(self.MidImpactLbl, ti.numImpact_M)
        self.updateSummaryCount(self.LoImpactLbl, ti.numImpact_L)
        self.updateSummaryCount(self.ZoneChangeLbl, ti.numZoneChange)
        # Trip events.
        self.TripEventsLbl.setText("{0:d}".format(ti.numTripEvents))
        # Report events.
        self.ReportEventsLbl.setText("{0:d}".format(ti.numReportEvents))
        # Other events.
        if config.TripData["ShowOtherEvents"] != 0:
            self.OtherEventsLbl.setText("{0:d}".format(ti.numOtherEvents))

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
        # At this point speed limits from application configuration as not include in log.
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
                self.exportTrip(xf, self.selectedTrip)

                # Close file after writing.
                xf.close()

    # *******************************************
    # Export report for nominated trip.
    # *******************************************
    def exportTrip(self, xf, t):
        # Get trip info.
        ti = self.tripLog[t-1]
        # Export trip data to file.
        logger.debug("Exporting trip report for trip: {0:d}".format(t))
        xf.write("===================================================\n")
        xf.write("Signon ID  : {0:d}\n".format(ti.signOnId))
        xf.write("Start time : {0:s}\n".format(unixTime(ti.tripStart, config.TimeUTC)))
        xf.write("End time   : {0:s}\n".format(unixTime(ti.tripEnd, config.TimeUTC)))
        xf.write("===================================================\n\n")
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
        xf.write("===================================================\n\n")
        xf.write("===================================================\n")
        xf.write("EVENTS (DETAILS)\n")
        xf.write("===================================================\n")
        for ev in ti.events:
            xf.write("{0:s}\n".format(ev.event))
            if (ev.event == "SIGNON"):
                xf.write("\tTime        : {0:s}\n".format(unixTime(ev.serverTime, config.TimeUTC)))
                xf.write("\tDriver ID   : {0:s}\n".format(ev.driverId))
                xf.write("\tCard ID     : {0:d}\n".format(ev.cardId))
                xf.write("\tResult      : {0:s}\n".format(ev.result))
                xf.write("\tBits Read   : {0:d}\n".format(ev.bitsRead))
                xf.write("\tKeyboard    : {0:s}\n".format(ev.keyboard))
                xf.write("\tCard Reader : {0:s}\n".format(ev.cardReader))

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
        if self.haveTrips:# Fix wait cursor when opening log and get an error; change back to normal cursor.

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
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
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
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
        elif event.event == "ZONEOVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            eventList.append(("Maximum Speed", "{0:d}".format(event.maxSpeed), (event.maxSpeed >= 150)))
            eventList.append(("Zone Output", "{0:d}".format(event.zoneOutput), False))
        elif event.event == "ENGINEOVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            eventList.append(("Maximum RPM", "{0:d}".format(event.maxRPM), False))
        elif event.event in {"LOWCOOLANT", "OILPRESSURE", "ENGINETEMP"}:
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
        elif event.event == "UNBUCKLED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
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
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
            eventList.append(("From Zone", "{0:d}".format(event.fromZone), False))
            eventList.append(("To Zone", "{0:d}".format(event.toZone), False))
            eventList.append(("Zone Output", "{0:d}".format(event.zoneOutput), False))
        elif event.event == "IMPACT":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), ((event.signOnId != trip.signOnId) and (not event.isOutOfTrip))))
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
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
            eventList.append(("Report Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
            eventList.append(("Direction", "{0:d}".format(event.direction), ((event.direction < 0) or (event.direction > 360))))
        elif event.event == "INPUT":
            eventList.append(("Current Speed", "{0:d}".format(event.speed), (event.speed >= 150)))
            eventList.append(("Input", "{0:d} - {1:s}".format(event.inputNo, config.Channels[event.inputNo - 1]["Name"]), ((event.inputNo < 1) or (event.inputNo > 10))))
            eventList.append(("State", "{0:d}".format(event.inputState), ((event.inputState < 0) or (event.inputState > 1))))
            eventList.append(("Active Time", "{0:s}".format(str(timedelta(seconds=event.activeTime))), False))
        elif event.event == "TRIP":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), (event.signOnId != trip.signOnId)))
            eventList.append(("Time Forward", "{0:s}".format(str(timedelta(seconds=event.timeFwd))), False))
            eventList.append(("Time Reverse", "{0:s}".format(str(timedelta(seconds=event.timeRev))), False))
            eventList.append(("Time Idle", "{0:s}".format(str(timedelta(seconds=event.timeIdle))), False))
            eventList.append(("Max Idle Time", "{0:s}".format(str(timedelta(seconds=event.maxIdle))), False))
        elif event.event == "TRIPSUMMARY":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), (event.signOnId != trip.signOnId)))

        # Return list of all event details to display
        return eventList

    # *******************************************
    # Open log file.
    # *******************************************
    def openLogFile(self):
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
                with open(filenames[0], encoding='cp1252') as f:
                    self.logData = f.read()
                logger.info("Opened and read log file : {0:s}".format(filenames[0]))
                self.showTempStatusMsg("{0:s}".format(filenames[0]), config.TripData["TmpStatusMessagesMsec"])

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
# Create UI
# *******************************************
app = QApplication(sys.argv)
etscrape = UI()
app.exec_()
