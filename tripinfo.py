#!/usr/bin/env python3

import logging
import re
from datetime import datetime

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
        # Indicate if 'debug' event.
        self.isDebug = False
        # Indicate if out of trip event.
        self.isOutOfTrip = False

        # Additional event variables.
        self.driverId = ""
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
        self.debugInfo = ""
        self.criticalOutput = 0
        self.travelLoaded = 0
        self.travelUnloaded = 0
        self.idleLoaded = 0
        self.idleUnloaded = 0
        self.liftCount = 0
        self.cumWeight = 0

# *******************************************
# Speed Info class.
# *******************************************
class SpeedInfo():
    # Initializer / Instance Attributes
    def __init__(self, eTime, eSpeed):

        self.time = eTime
        self.speed = eSpeed

# *******************************************
# Zone Crossing Info class.
# Zone is zone output and not zone number.
# *******************************************
class ZoneInfo():
    # Initializer / Instance Attributes
    def __init__(self, xTime, fromZ, toZ, zOut):

        self.time = xTime
        self.fromZone = fromZ
        self.toZone = toZ
        self.zoneOutput = zOut

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

        # Zone crossings.
        self.zoneXings = []

    # *******************************************
    # Extract trip data from buffer snippet.
    # *******************************************
    def extractTripData(self):
        # TimingTrip(
        self.tripStart = 0
        self.tripEnd = 0
        self.signOnId = 0

        # Total event category totals.
        self.numVehicleEvents = 0
        self.numOperatorEvents = 0
        self.numTripEvents = 0
        self.numReportEvents = 0
        self.numOtherEvents = 0
        self.numDebugEvents = 0

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
        self.numChecklist = 0
        self.numUnbuckled_O = 0
        self.numUnbuckled_P = 0
        self.numZoneChange = 0

        # Track last time to check if event time going backwards.
        self.lastTime = 0

        # Track first from zone.
        self.firstFromZone = None

        # Initialise flag to stop collecting trip speed plot data.
        self.stopSpeedData = False

        # ******************************
        # Look for SIGNON event.
        # ******************************
        patternStart = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) (.+)/(.+)/(.+)/([0-9]+)/([0-9]+) (SIGNON) (.+)$', re.MULTILINE)

        su = re.search(patternStart, self.logBuf)
        if su:
            # Break out some of the event data explicitly.
            eventSpecifics = su.group(11)

            specPatern = re.compile(r'([-\*\+0-9]+) ([0-9a-f]+) (.+?) ([0-9]+) ([0-9]+) (.+?)')
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
                event.driverId = sp.group(1)
                event.cardId = int(sp.group(2), base=16)
                event.result = sp.group(3)
                event.bitsRead = int(sp.group(4))
                event.keyboard = sp.group(5)
                event.cardReader = sp.group(6)

                # Check for Bypass condition; indicated by driver ID of -12.
                if event.driverId == "-12":
                    event.alertText = appendAlertText(event.alertText, "Bypass detected.")

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

                # Check for event time in the past, except if event is POWERDOWN as this is always in the past.
                if su.group(10) != "POWERDOWN":
                    if int(su.group(4)) < self.lastTime:
                        event.alertText = appendAlertText(event.alertText, "Event time reversal.")
                    self.lastTime = int(su.group(4))

                # Get speed data from event header.
                # But only if still collecting speed data, i.e. trip has not ended.
                if not self.stopSpeedData:
                    event.speed = int(su.group(9))
                    # Don't get speed from POWERDOWN event as these events occur out of order.
                    if su.group(10) != "POWERDOWN": 
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
                # LOWCOOLANT, OILPRESSURE, ENGINETEMP, OFFSEAT, OVERLOAD event (all the same format)
                # =============================================================================
                elif event.event in {"LOWCOOLANT", "OILPRESSURE", "ENGINETEMP", "OFFSEAT", "OVERLOAD"}:
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

                        # Record the zone change event in the zone change log.
                        # This can be used if we plot zone speed limits on speed plot.
                        # Record the previous zone change at this time so that we can get a step function.
                        if len(self.zoneXings) > 0:
                            self.zoneXings.append(ZoneInfo(int(su.group(4)), self.zoneXings[-1].fromZone, self.zoneXings[-1].toZone, self.zoneXings[-1].zoneOutput))
                        else:
                            # Record first from zone so that we can possibly do step at first zonechange.
                            self.firstFromZone = event.fromZone

                        self.zoneXings.append(ZoneInfo(int(su.group(4)), event.fromZone, event.toZone, event.zoneOutput))

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
                        self.numChecklist += 1

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

                        # Indicate that event is OTHER event.
                        # The event is supported, but still considered other.
                        event.isOther = True

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
                # CRITICALOUTPUTSET event.
                # *********************************************************************************************************************************************
                elif event.event == "CRITICALOUTPUTSET":   
                    specPatern = re.compile(r'([0-9]+) ([0-9]+)')
                    sp = re.search(specPatern, eventSpecifics)
                    if sp:
                        event.signOnId = int(sp.group(1))
                        event.criticalOutput = int(sp.group(2))

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
                        # Note that activeTime refers to time in the active state.
                        # That is, if inputState is inactive state (0) then active time will always be 0.

                        # For input events add the input number to the alert field.
                        # This is useful for looking for particular inputs when the events column is collapsed.
                        event.alertText = appendAlertText(event.alertText, "Input : {0:d}".format(event.inputNo))

                        # Indicate event is Input event to control presentation format.
                        event.isInput = True

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # DEBUG event.
                # *********************************************************************************************************************************************
                elif event.event == "DEBUG":   

                        # Don't decode extra information, just report all.
                        event.debugInfo = eventSpecifics

                        # Check and alert for known critical debug issues.
                        if "Time1H:" in eventSpecifics:
                            event.alertText = appendAlertText(event.alertText, "Time correction.")

                        elif "Time1H INV:" in eventSpecifics:
                            event.alertText = appendAlertText(event.alertText, "Invalid time detected.")

                        elif "Time(BAD)" in eventSpecifics:
                            event.alertText = appendAlertText(event.alertText, "BAD time detected.")

                        # Indicate event is Debug event to control presentation format.
                        event.isDebug = True
                        self.numDebugEvents += 1

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

                        # At end of trip can extend last zone to end of trip.
                        if len(self.zoneXings) > 0:
                            self.zoneXings.append(ZoneInfo(int(su.group(4)), self.zoneXings[-1].fromZone, self.zoneXings[-1].toZone, self.zoneXings[-1].zoneOutput))

                        # Can also check if we can extend the zone at the beginning of the trip.
                        # Can only do this if we have revisited the first zone during the trip.
                        for z in self.zoneXings[1:]:
                            # See if we visited first zone later in the trip.
                            if self.firstFromZone == z.toZone:
                                fz1 = ZoneInfo(self.tripStart, 0, 0, z.zoneOutput)
                                fz2 = ZoneInfo(self.zoneXings[0].time, 0, 0, z.zoneOutput)
                                # Have been in zone before, so add step at start of speed plot.
                                self.zoneXings.insert(0, fz2)
                                self.zoneXings.insert(0, fz1)
                                break

                        # Can do a check if time in traction / idle adds up to trip duration.
                        totalTimes = event.timeFwd + event.timeRev + event.timeIdle
                        tripTime = self.tripEnd - self.tripStart
                        diff = tripTime - totalTimes
                        if diff != 0:
                            event.alertText = appendAlertText(event.alertText, "Trip time inconsistent.")

                        # Don't want to collect eny more speed data as not useful for trip speed plots.
                        self.stopSpeedData = True

                        # Add event to list of events.
                        self.events.append(event)

                        # *********************************************************************************************************************************************
                        # Look for trip summary type event. These occurs after the TRIP event but are only generated if events occurred during the trip.
                        # Doing this event separately as it a different format to the other event messages.
                        # *********************************************************************************************************************************************
                        patternSummary = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,22}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) .+ (TRIP[A-Z]+) (.+)$', re.MULTILINE)
                        su = re.search(patternSummary, self.logBuf)
                        if su:
                            # Initialised with event type and time as in all events.
                            event = Event(su.group(5), int(su.group(4)))
                            self.logger.debug("Detected trip summary {0:s} at {1:s}".format(su.group(5), datetime.fromtimestamp(int(su.group(4))).strftime('%d/%m/%Y %H:%M:%S')))

                            # Check for event time in the past.
                            if int(su.group(4)) < self.lastTime:
                                event.alertText = appendAlertText(event.alertText, "Event time reversal.")
                            self.lastTime = int(su.group(4))

                            # Break out some of the event data explicitly.
                            eventSpecifics = su.group(6)

                            if su.group(5) == "TRIPSUMMARY":
                                specPatern = re.compile(r'([0-9]+)')
                                sp = re.search(specPatern, eventSpecifics)
                                if sp:
                                    event.signOnId = int(sp.group(1))

                                    # Increment event counters.
                                    self.numTripEvents += 1

                                    # Add event to list of events.
                                    self.events.append(event)
                            elif su.group(5) == "TRIPLOAD":
                                specPatern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)')
                                sp = re.search(specPatern, eventSpecifics)
                                if sp:
                                    event.signOnId = int(sp.group(1))
                                    event.travelLoaded = int(sp.group(2))
                                    event.travelUnloaded = int(sp.group(3))
                                    event.idleLoaded = int(sp.group(4))
                                    event.idleUnloaded = int(sp.group(5))
                                    event.liftCount = int(sp.group(6))
                                    event.cumWeight = int(sp.group(7))

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
                    if event.event not in ["SIGNON", "TRIP", "TRIPSUMMARY", "TRIPLOAD"]:

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
