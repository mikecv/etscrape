#!/usr/bin/env python3

import logging
import logging.handlers
import json
import re
from datetime import timedelta, datetime

# *******************************************
# Event class.
# *******************************************
class Event():
    # Initializer / Instance Attributes
    def __init__(self, eType, eTime):
        # All event variables.
        self.event = eType
        self.serverTime = eTime
        # Event alert text.
        self.alertText = ""
        # Indicate if 'other' event.
        self.isOther = False
        # Indicate if 'input' event.
        self.isInput = False
        # Indicate if out of trip event.
        self.isOutOfTrip = False

        # Additional event variables.
        self.driverId = 0
        self.cardId = 0
        self.result = ""
        self.bitsRead = 0
        self.keyboard = ""
        self.cardReader = ""
        self.signOnId = 0
        self.maxSpeed = 0
        self.duration = 0
        self.zoneOutput = 0
        self.maxRPM = 0
        self.seatOwner = ""
        self.fromZone = 0
        self.toZone = 0
        self.fwdG = 0.0
        self.revG = 0.0
        self.leftG = 0.0
        self.rightG = 0.0
        self.maxG1 = 0.0
        self.maxG2 = 0.0
        self.severity = ""
        self.failedQ = 0
        self.chkVersion = 0
        self.chkType = ""
        self.maxIdle = 0
        self.timeFwd = 0
        self.timeRev = 0
        self.timeIdle = 0
        self.speed = 0
        self.direction = 0
        self.inputNo = 0
        self.inputState = 0
        self.activeTime = 0
        self.serviceId = 0

# *******************************************
# Speed Info class.
# *******************************************
class SpeedInfo():
    # Initializer / Instance Attributes
    def __init__(self, eTime, eSpeed):

        self.time = eTime
        self.speed = eSpeed

# *******************************************
# Trip class.
# *******************************************
class Trip():
    # Initializer / Instance Attributes
    def __init__(self, config, logger, logBuf):

        self.cfg = config
        self.logger = logger

        self.logger.debug("Trip class constructor.")

        # Buffer snippet for trip.
        self.logBuf = logBuf

        # Event data.
        self.events = []
    
        # Speed data.
        self.speedLog = []

    # *******************************************
    # Extract trip data from buffer snippet.
    # *******************************************
    def extractTripData(self):
        # Timing
        self.tripStart = 0
        self.tripEnd = 0
        self.signOnId = 0

        # Total event category totals.
        self.numVehicleEvents = 0
        self.numOperatorEvents = 0
        self.numTripEvents = 0
        self.numReportEvents = 0
        self.numOtherEvents = 0

        # Total specific vehicle events.
        self.numOverspeed = 0
        self.numZoneOverspeed = 0
        self.numEngineOverspeed = 0
        self.numLowCoolant = 0
        self.numOilPressure = 0
        self.numEngineTemperature = 0
        self.numImpact_H = 0
        self.numImpact_M = 0
        self.numImpact_L = 0
        # Total specific Operator events.
        self.numUnbuckled_O = 0
        self.numUnbuckled_P = 0
        self.numZoneChange = 0

        # Track last time to check if event time going backwards.
        self.lastTime = 0

        # ******************************
        # Look for SIGNON event.
        # ******************************
        patternStart = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) (.+)/(.+)/(.+)/([0-9]+)/([0-9]+) (SIGNON) (.+)$', re.MULTILINE)

        su = re.search(patternStart, self.logBuf)
        if su:
            # Break out some of the event data explicitly.
            eventSpecifics = su.group(11)

            specPatern = re.compile(r'([-\+0-9]+) ([0-9a-f]+) (.+?) ([0-9]+) ([0-9]+) (.+?)')
            sp = re.search(specPatern, eventSpecifics)
            if sp:
                # Create event object.
                # Initialised with event type and time as in all events.
                event = Event(su.group(10), int(su.group(4)))
                self.tripStart = int(su.group(4))
                self.logger.debug("Detected trip at {0:s}".format(datetime.fromtimestamp(self.tripStart).strftime('%d/%m/%Y %H:%M:%S')))

                # Initialise last time to start of trip.
                self.lastTime = self.tripStart

                # Save sign-on ID at sign-on event for checking against other events; they should be the same.
                self.signOnId = int(su.group(3))

                # Add additional event data.
                event.signOnId = int(su.group(3))
                event.driverId = int(sp.group(1))
                event.cardId = int(sp.group(2), base=16)
                event.result = sp.group(3)
                event.bitsRead = int(sp.group(4))
                event.keyboard = sp.group(5)
                event.cardReader = sp.group(6)

                # Get speed data from event header.
                event.speed = int(su.group(9))

                # Increment event counters.
                self.numTripEvents += 1

                # Add event to list of events.
                self.events.append(event)

            # **************************************************************
            # Look for specific events other than the SIGNON event.
            # **************************************************************
            patternData = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) (.+)/(.+)/(.+)/([0-9]+)/([0-9]+) ([ _A-Z]+) (.+)$', re.MULTILINE)
            for su in re.finditer(patternData, self.logBuf):

                # Found trip event.
                event = Event(su.group(10), int(su.group(4)))
                self.logger.debug("Detected event: {0:s}, at: {1:s}".format(su.group(10), datetime.fromtimestamp(int(su.group(4))).strftime('%d/%m/%Y %H:%M:%S')))

                # Check for event time in the past.
                if int(su.group(4)) < self.lastTime:
                    event.alertText = appendAlertText(event.alertText, "Event time reversal.")
                self.lastTime = int(su.group(4))

                # Get speed data from event header.
                event.speed = int(su.group(9))
                # If speedlog already has speed for this time then skip, else append to list.
                if self.checkForSpeedTime(int(su.group(4))) == False:
                    self.speedLog.append(SpeedInfo(int(su.group(4)), int(su.group(9))))
                    self.logger.debug("Logged speed: {0:d}, at {1:s}".format(int(su.group(9)), datetime.fromtimestamp(int(su.group(4))).strftime('%d/%m/%Y %H:%M:%S')))

                # Check if out of trip event, i.e. end trip time > 0.
                if self.tripEnd > 0:
                    event.isOutOfTrip = True

                # Break out some of the event data explicitly.
                eventSpecifics = su.group(11)

                # =============================================================================
                # OVERSPEED event
                # =============================================================================
                if event.event == "OVERSPEED":
                    specPatern = re.compile(r'([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.duration = int(sp.group(2))

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        self.numOverspeed += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # ZONEOVERSPEED event
                # =============================================================================
                elif event.event == "ZONEOVERSPEED":
                    specPatern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.duration = int(sp.group(2))
                        event.maxSpeed = int(sp.group(3))
                        event.zoneOutput = int(sp.group(4))

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        self.numZoneOverspeed += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # ENGINEOVERSPEED event
                # =============================================================================
                elif event.event == "ENGINEOVERSPEED":
                    specPatern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.duration = int(sp.group(2))
                        event.maxRPM = int(sp.group(3))

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        self.numEngineOverspeed += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # LOWCOOLANT, OILPRESSURE, or ENGINETEMP event (all the same format)
                # =============================================================================
                elif event.event in {"LOWCOOLANT", "OILPRESSURE", "ENGINETEMP"}:
                    specPatern = re.compile(r'([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.duration = int(sp.group(2))

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        if su.group(10) == "LOWCOOLANT":
                            self.numLowCoolant += 1
                        elif su.group(10) == "OILPRESSURE":
                            self.numOilPressure += 1
                        elif su.group(10) == "ENGINETEMP":
                            self.numEngineTemperature += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # UNBUCKLED event
                # =============================================================================
                elif event.event == "UNBUCKLED":
                    specPatern = re.compile(r'([0-9]+) ([0-9]+) ([DP])')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.duration = int(sp.group(2))
                        event.seatOwner = sp.group(3)

                        # Increment event counters.
                        self.numOperatorEvents += 1
                        if (sp.group(3) == "D"):
                            self.numUnbuckled_O += 1
                        else:
                            self.numUnbuckled_P += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # ZONECHANGE event
                # =============================================================================
                elif event.event == "ZONECHANGE":
                    specPatern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.fromZone = int(sp.group(2))
                        event.toZone = int(sp.group(3))
                        event.zoneOutput = int(sp.group(4))

                        # Increment event counters.
                        self.numOperatorEvents += 1
                        self.numZoneChange += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # IMPACT event
                # =============================================================================
                elif event.event == "IMPACT":
                    specPatern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([\-a-zA-Z]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.fwdG = int(sp.group(2)) / 10.0
                        event.revG = int(sp.group(3)) / 10.0
                        event.leftG = int(sp.group(4)) / 10.0
                        event.rightG = int(sp.group(5)) / 10.0
                        event.maxG1 = int(sp.group(6)) / 10.0
                        event.maxG2 = int(sp.group(7)) / 10.0
                        event.severity = sp.group(8)

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        if event.severity == "C":
                            self.numImpact_H += 1
                        elif event.severity == "W":
                            self.numImpact_M += 1
                        elif event.severity == "-":
                            self.numImpact_L += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # CHECKLIST event
                # =============================================================================
                elif event.event == "CHECKLIST":
                    specPatern = re.compile(r'([0-9]+) (OK|CANCEL|NOFILE) ([0-9]+) ([0-9]+) ([0-9]+) ([\-a-zA-Z]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.result = sp.group(2)
                        event.failedQ = int(sp.group(3))
                        event.duration = int(sp.group(4))
                        event.chkVersion = int(sp.group(5))
                        event.chkType = sp.group(6)

                        # Increment event counters.
                        self.numOperatorEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # XSIDLESTART event
                # =============================================================================
                elif event.event == "XSIDLESTART":
                    specPatern = re.compile(r'([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))

                        # Increment event counters.
                        self.numVehicleEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # XSIDLE event
                # =============================================================================
                elif event.event == "XSIDLE":
                    specPatern = re.compile(r'([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.maxIdle = int(sp.group(2))

                        # Increment event counters.
                        self.numVehicleEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # CONFIG event
                # =============================================================================
                elif event.event == "CONFIG":

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # SERVICE event
                # =============================================================================
                elif event.event == "SERVICE":

                    specPatern = re.compile(r'([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.serviceId = int(sp.group(1))

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # POWERDOWN event
                # =============================================================================
                elif event.event == "POWERDOWN":

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # REPORT event.
                # *********************************************************************************************************************************************
                elif event.event == "REPORT":   
                    specPatern = re.compile(r'(\*|[0-9]+) ([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        # Check for bad sign-on ID, i.e. "*".
                        if (sp.group(1) == "*"):
                            event.signOnId = -1
                        else:
                            event.signOnId = int(sp.group(1))
                        event.speed = int(sp.group(2))
                        event.direction = int(sp.group(3))

                        # Increment event counters.
                        self.numReportEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # INPUT event.
                # *********************************************************************************************************************************************
                elif event.event == "INPUT":   
                    specPatern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.inputNo = int(sp.group(1))
                        event.inputState = int(sp.group(2))
                        event.activeTime = int(sp.group(3))

                        # Indicate event is Input event to control presentation format.
                        event.isInput = True

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # TRIP event.
                # *********************************************************************************************************************************************
                elif event.event == "TRIP":   

                    self.tripEnd = int(su.group(4))
                    self.logger.debug("Detected trip end at {0:s}".format(datetime.fromtimestamp(self.tripEnd).strftime('%d/%m/%Y %H:%M:%S')))

                    specPatern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.timeFwd = int(sp.group(2))
                        event.timeRev = int(sp.group(3))
                        event.timeIdle = int(sp.group(4))
                        event.maxIdle = int(sp.group(5))

                        # Increment event counters.
                        self.numTripEvents += 1

                        # Add event to list of events.
                        self.events.append(event)

                        # *********************************************************************************************************************************************
                        # Look for trip summary event. This occurs after the TRIP event but is only generated if events occurred during the trip.
                        # Doing this event separately as it a different format to the other event messages.
                        # *********************************************************************************************************************************************
                        patternSummary = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,22}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) .+ (TRIPSUMMARY) (.+)$', re.MULTILINE)
                        su = re.search(patternSummary, self.logBuf)
                        if su:
                            # Initialised with event type and time as in all events.
                            event = Event(su.group(5), int(su.group(4)))
                            self.logger.debug("Detected trip summary at {0:s}".format(datetime.fromtimestamp(int(su.group(4))).strftime('%d/%m/%Y %H:%M:%S')))

                            # Check for event time in the past.
                            if int(su.group(4)) < self.lastTime:
                                event.alertText = appendAlertText(event.alertText, "Event time reversal.")
                            self.lastTime = int(su.group(4))

                            # Break out some of the event data explicitly.
                            eventSpecifics = su.group(6)

                            specPatern = re.compile(r'([0-9]+)')
                            sp = re.search(specPatern, eventSpecifics)
                            if sp:
                                event.signOnId = int(sp.group(1))

                                # Increment event counters.
                                self.numTripEvents += 1

                                # Add event to list of events.
                                self.events.append(event)

                # *********************************************************************************************************************************************
                # Other events
                # Only event names checked, parameter details ignored.
                # *********************************************************************************************************************************************
                else:
                    # Don't include SIGNON, TRIP, and TRIPSUMMARY as they are detected separately.
                    if event.event not in ["SIGNON", "TRIP", "TRIPSUMMARY"]:

                        # Indicate that event is OTHER event, i.e. not supported (yet).
                        event.isOther = True

                        # Increment event counters.
                        self.numOtherEvents += 1

                        # Add event to list of events.
                        self.events.append(event)

    # *******************************************
    # Check if speed time already in speed log.
    # *******************************************
    def checkForSpeedTime(self, spdTime):
        # Initialise time found flag.
        timeFound = False
        # Go through speed log looking for a match.
        for sd in self.speedLog:
            if sd.time == spdTime:
                timeFound = True
        return timeFound

# *******************************************
# Append to event alert text.
# *******************************************
def appendAlertText(altText, newAlertText):
    # If alert text blank then just copy new text.
    if altText == "":
        return (newAlertText)
    # Else append after space to existing text.
    else:
        return ("{0:s} {1:s}".format(altText, newAlertText))
