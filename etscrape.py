#!/usr/bin/env python3

from PyQt5.QtWidgets import QMainWindow, QDialog, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QHeaderView, qApp, QApplication
from PyQt5 import QtCore, QtGui
from PyQt5 import uic
import logging
import logging.handlers
import json
import re
import time
from datetime import timedelta, datetime
import os
import sys
import webbrowser

from config import *
from tripinfo import *

# *******************************************
# Program history.
# 0.1   MDC 21/05/2020  Original.
# *******************************************

# Program version.
progVersion = "0.1"

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
    return os.path.join(base_path, relative_path)

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

        # Attach to the Quit menu item.
        self.actionQuit.triggered.connect(app.quit)

        # Attach to the Help menu item.
        self.actionHelp.triggered.connect(self.help)

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

        # Flag indicating no data to show.
        # And flag indicating no trip selected.
        self.haveTrips = False
        self.selectedTrip = 0

        # Enable expand / collapse buttons.
        self.actionCollapseAllLevels.setEnabled(False)
        self.actionExpandAllLevels.setEnabled(False)

        # Don't show 'other' events static text if not configured.
        if config.ShowOtherEvents == False:
            self.OtherEventsStaticLbl.hide()

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
                    # Check if no more next trips, then disable the button.
                    self.updateTripBtnState()
            else:
                if self.selectedTrip > 1:
                    self.selectedTrip -= 1
                    self.tripDataTree.setCurrentItem(self.tripDataTree.topLevelItem((self.selectedTrip - 1)))
                    self.updateTripSummary(self.selectedTrip)
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
    # Show temporary status message.
    # Pass message string and duration in (msec).
    # *******************************************
    def showTempStatusMsg(self, msg, dur=10000):
        self.statusbar.showMessage(msg, dur)

    # *******************************************
    # Load log file.
    # *******************************************
    def loadLogFile(self):
        logger.debug("User selected Load Log File control.")

        # If we have trip data then delete data.
        if self.haveTrips:
            self.tripDataTree.setParent(None)
            self.tripDataTree = None

        # Clear trip data to show.
        self.haveTrips = False

        # Enable expand / collapse buttons.
        self.actionCollapseAllLevels.setEnabled(False)
        self.actionExpandAllLevels.setEnabled(False)

        # Get log file to load.
        self.openLogFile()

        self.numTrips = 0
        self.tripLog = []

        # Look for all the trip starts and capture individual buffers.
        patternStart = re.compile(r'([0-9]{2}/[0-9]{2}/[0-9]{4}) ([0-9]{2}:[0-9]{2}:[0-9]{2}) EVENT .+ (SIGNON).?')
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

            # Populate trip data.updateTripBtnState
            self.populateTrips()
        else:
            # Show pop-up indicating no trip data found in log file.
            showPopup("Trip", "Log file contains no trip information.", "(No trip start \"SIGNON\" events encountered)")

    # *******************************************
    # Populate trip data.
    # *******************************************
    def populateTrips(self):
        # Define a tree widget for trip data.
        self.tripDataTree = QTreeWidget()
        self.tripDataTree.setHeaderLabels(['Trip Data', ''])
        self.tripDataTree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tripDataTree.header().setStretchLastSection(False)

        # Populate trip titles.
        for idx, t in enumerate(self.tripLog):
            # Add top levels to trees.
            # Label trips with trip number and time.
            tripNum = "{0:s} {1:02d}".format(config.TripPrefix, (idx+1))
            tripTime = "{0:s} to {1:s}".format(datetime.fromtimestamp(t.tripStart).strftime('%d/%m/%Y %H:%M:%S'),
                                        datetime.fromtimestamp(t.tripEnd).strftime('%d/%m/%Y %H:%M:%S'))

            logger.debug("Adding trip: {0:d}, occurred: {1:s}".format(idx+1, tripTime))
            tripLevel = QTreeWidgetItem(self.tripDataTree, [tripNum, tripTime])
            tripLevel.setBackground(0, QtGui.QBrush(QtGui.QColor(config.TripBackColour)))
            tripLevel.setBackground(1, QtGui.QBrush(QtGui.QColor(config.TripBackColour)))
            font0 = QtGui.QFont()
            font0.setBold(True)
            tripLevel.setFont(0, font0)

            # Populate event titles.
            for idx2, ev in enumerate(t.events):
                # Check to see if we have to show 'Other' type events as well.
                if ((ev.isOther and config.ShowOtherEvents) or (not ev.isOther)):
                    # Label events with event type and time.
                    eventType = "{0:s}".format(ev.event)
                    eventTime = "{0:s}".format(datetime.fromtimestamp(ev.serverTime).strftime('%d/%m/%Y %H:%M:%S'))
                    logger.debug("Adding event: {0:s}, occurred: {1:s}".format(eventType, eventTime))
                    eventLevel = QTreeWidgetItem(tripLevel, [eventType, eventTime])
                    # If this is an Other event then do specific colouring.
                    if not ev.isOther:
                        eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.EventColour)))
                    else:
                        eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.OtherEventColour)))
                    font0 = QtGui.QFont()
                    font0.setBold(True)
                    eventLevel.setFont(0, font0)

                    # Check it see if event is of other type in which case don't have details.
                    if  not ev.isOther:
                        # Populate event details.
                        for idx3, evDetail in enumerate(self.getEventDetails(ev)):
                            # Include event details for all events.
                            detailLevel = QTreeWidgetItem(eventLevel, [evDetail[0], evDetail[1]])
                            logger.debug("Adding event detail: {0:s}, value: {1:s}".format(evDetail[0], evDetail[1]))
                            detailLevel.setTextAlignment(0, QtCore.Qt.AlignRight)
                            font0 = QtGui.QFont()
                            font0.setBold(True)
                            detailLevel.setFont(0, font0)
                            if evDetail[2] == True:
                                font1 = QtGui.QFont()
                                font1.setBold(True)
                                detailLevel.setFont(1, font1)
                                # If detail alert then use alert colour.
                                detailLevel.setForeground(1, QtGui.QBrush(QtGui.QColor(config.AlertColour)))
                                # If detail alert then also use alert colour for related event.
                                eventLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.AlertColour)))
                                # If detail alert then also use alert colour for related trip.
                                tripLevel.setForeground(0, QtGui.QBrush(QtGui.QColor(config.AlertColour)))

        # Add trip data tree to layout.
        self.verticalLayout.addWidget(self.tripDataTree)

        # Set the first trip as the current trip.
        # This is so that we can populate the trip details frame.
        self.tripDataTree.setCurrentItem(self.tripDataTree.topLevelItem(0))
        self.selectedTrip = 1
        self.updateTripSummary(1)

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
        self.selectedTrip = int(trip[(len(config.TripPrefix)+1):])

        # If trip changed then update the trip summary information.
        if (self.selectedTrip != originalTrip):
            self.updateTripSummary(self.selectedTrip)
            # Update the state of the prev/next trip buttons.
            self.updateTripBtnState()

    # *******************************************
    # Update trip summary information for selected trip.
    # *******************************************
    def updateTripSummary(self, t):
        ti = self.tripLog[t-1]
        # Trip information.
        self.TripNoLbl.setText("{0:02d}".format(t))
        self.StartTimeLbl.setText("{0:s}".format(datetime.fromtimestamp(ti.tripStart).strftime('%d/%m/%Y %H:%M:%S')))
        self.EndTimeLbl.setText("{0:s}".format(datetime.fromtimestamp(ti.tripEnd).strftime('%d/%m/%Y %H:%M:%S')))
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
        if config.ShowOtherEvents:
            self.OtherEventsLbl.setText("{0:d}".format(ti.numOtherEvents))

    # *******************************************
    # Update trip summary information for selected trip.
    # Also highlight if count not zero.
    # *******************************************
    def updateSummaryCount(self, item, count):
        # Set additional still if count > 0.
        # Else clear.
        if count > 0:
            item.setStyleSheet("font-weight: bold; color: {0:s}".format(config.SummaryAlertColour))
        else:
            item.setStyleSheet("")
        # Update count text.
        item.setText("{0:d}".format(count))

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
    def getEventDetails(self, event):
        # Initialise list of event details
        eventList = []

        # Event details will depend on event type.
        # Check for alert values as well.
        if event.event == "SIGNON":
            eventList.append(("Driver ID", "{0:d}".format(event.driverId), False))
            eventList.append(("Card ID", "{0:d}".format(event.cardId), False))
            eventList.append(("Result", "{0:s}".format(event.result), False))
            eventList.append(("Bits Read", "{0:d}".format(event.bitsRead), False))
            eventList.append(("Keyboard", "{0:s}".format(event.keyboard), False))
            eventList.append(("Card Reader", "{0:s}".format(event.cardReader), False))
        elif event.event == "OVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Maximum Speed", "{0:d}".format(event.maxSpeed), (event.maxSpeed == 150)))
        elif event.event == "ZONEOVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            eventList.append(("Maximum Speed", "{0:d}".format(event.maxSpeed), (event.maxSpeed == 150)))
            eventList.append(("Zone Output", "{0:d}".format(event.zoneOutput), False))
        elif event.event == "ENGINEOVERSPEED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            eventList.append(("Maximum RPM", "{0:d}".format(event.maxRPM), False))
        elif event.event in {"LOWCOOLANT", "OILPRESSURE", "ENGINETEMP"}:
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
        elif event.event == "UNBUCKLED":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Duration", "{0:s}".format(str(timedelta(seconds=event.duration))), (event.duration == 0)))
            if event.seatOwner == "D":
                seatOwner = "Operator"
            elif event.seatOwner == "P":
                seatOwner = "Passenger"
            else:
                seatOwner = "?"
            eventList.append(("Seat Owner", "{0:s}".format(seatOwner), (seatOwner == "?")))
        elif event.event == "ZONECHANGE":
            eventList.append(("From Zone", "{0:d}".format(event.fromZone), False))
            eventList.append(("To Zone", "{0:d}".format(event.toZone), False))
            eventList.append(("Zone Output", "{0:d}".format(event.zoneOutput), False))
        elif event.event == "IMPACT":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
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
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
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
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Max Idle Time", "{0:s}".format(str(timedelta(seconds=event.maxIdle))), (event.maxIdle == 0)))
        elif event.event == "CONFIG":
            pass
        elif event.event == "REPORT":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Speed", "{0:d}".format(event.speed), (event.speed == 150)))
            eventList.append(("Direction", "{0:d}".format(event.direction), ((event.direction < 0) or (event.direction > 360))))
        elif event.event == "TRIP":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))
            eventList.append(("Time Forward", "{0:s}".format(str(timedelta(seconds=event.timeFwd))), False))
            eventList.append(("Time Reverse", "{0:s}".format(str(timedelta(seconds=event.timeRev))), False))
            eventList.append(("Time Idle", "{0:s}".format(str(timedelta(seconds=event.timeIdle))), False))
            eventList.append(("Max Idle Time", "{0:s}".format(str(timedelta(seconds=event.maxIdle))), False))
        elif event.event == "TRIPSUMMARY":
            eventList.append(("Sign-on ID", "{0:d}".format(event.signOnId), False))

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
                self.showTempStatusMsg("Opened and read log file : {0:s}".format(filenames[0]), 10000)

    # *******************************************
    # About control selected.
    # Displays an "About" dialog box.
    # *******************************************
    def about(self):
        logger.debug("User selected About menu control.")

        # Create about dialog.        
        dlg = AboutDialog(self)

        # Set dialog window icon.
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(res_path("./resources/about.png")))
        dlg.setWindowIcon(icon)

        # Update version information.
        dlg.updateVersion("Version : {0:s}".format(progVersion))

        # Update dialog icon.
        dlg.aboutIcon.setPixmap(QtGui.QPixmap(res_path("./resources/about.png")))

        # Show dialog.
        dlg.exec_()

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
# Help dialog class.
# *******************************************
class HelpDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(HelpDialog, self).__init__(*args, **kwargs)
        uic.loadUi(res_path("help.ui"), self)

# *******************************************
# About dialog class.
# *******************************************
class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)
        uic.loadUi(res_path("about.ui"), self)

    # *******************************************
    # Update version string in about dialog.
    # *******************************************
    def updateVersion(self, version):
        self.versionLbl.setText(version)

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
# Convert seconds to time string.
# *******************************************
def secsToTime(t):
    secs = t % 60
    mins = t // 60
    hrs = mins // 60
    mins = mins - (hrs * 60)
    return ("{0:02d}:{1:02d}:{2:02d}".format(hrs, mins, secs))

# *******************************************
# Create UI
# *******************************************
app = QApplication(sys.argv)
etscrape = UI()
app.exec_()
