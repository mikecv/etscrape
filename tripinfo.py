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
        # Indicate if 'report' event.
        self.isReport = False
        # Indicate if out of trip event.
        self.isOutOfTrip = False

        # Event in alert.
        # Used by trip data display.
        self.eventInAlert = False

        # Additional event variables.
        self.driverId = ""
        self.cardId = 0
        self.result = ""
        self.bitsRead = 0
        self.keyboard = ""
        self.cardReader = ""

        self.tripStartId = 0
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
        self.failedQNo = 0
        self.chkVersion = 0
        self.chkType = ""
        self.maxIdle = 0
        self.xsidleReason = 0
        self.timeFwd = 0
        self.timeRev = 0
        self.timeIdle = 0
        self.timeOnSeat = 0
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
        self.battery = 0.0
        self.voltage = 0.0
        self.oosReason = 0
        self.batteryState = ""
        self.toZoneOutput = 0
        self.transition = ""

# *******************************************
# Speed Info class.
# *******************************************
class SpeedInfo():
    # Initializer / Instance Attributes
    def __init__(self, eTime, eSpeed):

        self.time = eTime
        self.speed = eSpeed

# *******************************************
# Battery Voltage Info class.
# *******************************************
class BatteryInfo():
    # Initializer / Instance Attributes
    def __init__(self, eTime, eBattery):

        self.time = eTime
        self.battery = eBattery

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

        # Battery level.
        self.batteryLevel = []

    # *******************************************
    # Extract trip data from buffer snippet.
    # *******************************************
    def extractTripData(self):
        # Trip timing.
        self.tripStart = 0
        self.tripEnd = 0
        self.tripStartId = 0
        self.tripTrip = False

        # Trip in alert.
        # Used by trip data display.
        self.tripInAlert = False

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
        self.numTransition = 0

        # Track last time to check if event time going backwards.
        self.lastTime = 0

        # Track first from zone and zone transition.
        self.firstFromZone = None

        # Initialise flag to stop collecting extra data past end of trip.
        self.stopExtraData = False

        # ******************************
        # Look for SIGNON event.
        # ******************************
        patternStart = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) (.+)/(.+)/(.+)/([-0-9]+)/([0-9]+) (SIGNON) (.+)$', re.MULTILINE)

        su = re.search(patternStart, self.logBuf)
        if su:
            # Break out some of the event data explicitly.
            eventSpecifics = su.group(11)
            specPattern = re.compile(r'([-\*\+0-9]+) ([0-9a-fA-F]+) (.+?) ([0-9]+) ([0-9]+) ([0-9]+) (.+?)$')
            sp = re.search(specPattern, eventSpecifics)
            if sp:
                # Create event object.
                # Initialised with event type and time as in all events.
                event = Event(su.group(10), int(su.group(4)))
                self.tripStart = int(su.group(4))
                self.logger.debug("Detected trip at {0:s}".format(datetime.fromtimestamp(self.tripStart).strftime('%d/%m/%Y %H:%M:%S')))

                # Initialise last time to start of trip.
                self.lastTime = self.tripStart

                # Save sign-on ID at sign-on event for checking against other events; they should be the same.
                self.tripStartId = int(su.group(3))

                # Add additional event data.
                event.tripStartId = int(su.group(3))
                event.driverId = sp.group(1)
                event.cardId = int(sp.group(2), base=16)
                event.result = sp.group(3)
                event.bitsRead = int(sp.group(4))
                event.keyboard = sp.group(5)
                event.cardReader = sp.group(6)

                # Diagnostics to indicate sign-on ID. Useful for reference to log file.
                self.logger.debug("Trip SIGNON ID {0:d}".format(event.tripStartId))

                # Check for Bypass condition; indicated by driver ID of -12.
                if event.driverId == "-12":
                    event.alertText = appendAlertText(event.alertText, "Bypass detected.")

                # Get speed data from event header.
                event.speed = int(su.group(9))

                # Read battery voltage from event header.
                # But only if still collecting extra data, i.e. trip has not ended.
                if not self.stopExtraData:
                    # The voltage at end of event strings appears to be optional, so need to check if it exists.
                    voltPattern = re.compile(r'v:([0-9]+)$')
                    vp = re.search(voltPattern, sp.group(7))
                    if vp:
                        # Extract battery voltage.
                        event.battery = int(vp.group(1)) / 10.0

                        # And add to battery level list.
                        self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                        # Check for negative battery voltage condition.
                        if event.battery < 0:
                            event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                # Increment event counters.
                self.numTripEvents += 1

                # Add event to list of events.
                self.events.append(event)

                # Initialise trip not ended, in TRIP event not reached.
                self.tripTrip = False

            # **************************************************************
            # Look for specific events other than the SIGNON event.
            # **************************************************************
            patternData = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) (.+)/(.+)/(.+)/([-0-9]+)/([0-9]+) ([ _a-zA-Z]+) (.+)$', re.MULTILINE)
            for su in re.finditer(patternData, self.logBuf):

                # Found event.
                event = Event(su.group(10), int(su.group(4)))
                self.logger.debug("Detected event: {0:s}, at: {1:s}".format(su.group(10), datetime.fromtimestamp(int(su.group(4))).strftime('%d/%m/%Y %H:%M:%S')))

                # Check for event time in the past, except if event is POWERDOWN as this is always in the past.
                if su.group(10) != "POWERDOWN":
                    if int(su.group(4)) < self.lastTime:
                        event.alertText = appendAlertText(event.alertText, "Event time reversal.")
                    self.lastTime = int(su.group(4))

                # Get speed data from event header.
                # But only if still collecting extra data, i.e. trip has not ended.
                if not self.stopExtraData:
                    event.speed = int(su.group(9))
                    # Don't get speed from POWERDOWN event as these events occur out of order.
                    if su.group(10) != "POWERDOWN": 
                        # If speedlog already has speed for this time then skip, else append to list.
                        # If event is REPORT then don't log speed as speed in other field (with direction).
                        if su.group(10) != "REPORT":
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
                    specPattern = re.compile(r'([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.duration = int(sp.group(2))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(3))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        self.numOverspeed += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # ZONEOVERSPEED event
                # =============================================================================
                elif event.event == "ZONEOVERSPEED":
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.duration = int(sp.group(2))
                        event.maxSpeed = int(sp.group(3))
                        event.zoneOutput = int(sp.group(4))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(5))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        self.numZoneOverspeed += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # ENGINEOVERSPEED event
                # =============================================================================
                elif event.event == "ENGINEOVERSPEED":
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) v:([0-9]+)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.duration = int(sp.group(2))
                        event.maxRPM = int(sp.group(3))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numVehicleEvents += 1
                        self.numEngineOverspeed += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # LOWCOOLANT, OILPRESSURE, ENGINETEMP, OFFSEAT, OVERLOAD event (all the same format)
                # =============================================================================
                elif event.event in {"LOWCOOLANT", "OILPRESSURE", "ENGINETEMP", "OFFSEAT", "OVERLOAD"}:
                    specPattern = re.compile(r'([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.duration = int(sp.group(2))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(3))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

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
                    # Need to cater for Smartrack UNBUCKLED events, which have the same name but different format.
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([DP])(.*)$')
                    specPatternST = re.compile(r'([0-9]+) (.*)$')

                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.duration = int(sp.group(2))
                        event.seatOwner = sp.group(3)

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numOperatorEvents += 1
                        if (sp.group(3) == "D"):
                            self.numUnbuckled_O += 1
                        else:
                            self.numUnbuckled_P += 1

                        # Add event to list of events.
                        self.events.append(event)
                    else:
                        sp = re.search(specPatternST, eventSpecifics)
                        if sp:
                            event.tripStartId = int(sp.group(1))

                            # Read battery voltage from event header.
                            # But only if still collecting extra data, i.e. trip has not ended.
                            if not self.stopExtraData:
                                # The voltage at end of event strings appears to be optional, so need to check if it exists.
                                # Note that Smartrack has floats instead of integers for battery voltage.
                                voltPattern = re.compile(r'.*v:([.0-9]+)$')
                                vp = re.search(voltPattern, sp.group(2))
                                if vp:
                                    event.battery = float(vp.group(1))
                                    # And add to battery level list.
                                    self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                    # Check for negative battery voltage condition.
                                    if event.battery < 0:
                                        event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                            # Smartrack unbuckled event so assume Operator (Driver) is the owner.
                            event.seatOwner = "D"

                            # Increment event counters.
                            self.numUnbuckled_O += 1

                            # Add event to list of events.
                            self.events.append(event)
                # =============================================================================
                # ZONECHANGE event
                # =============================================================================
                elif event.event == "ZONECHANGE":
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.fromZone = int(sp.group(2))
                        event.toZone = int(sp.group(3))
                        event.zoneOutput = int(sp.group(4))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(5))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

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
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([\-a-zA-Z]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.fwdG = int(sp.group(2)) / 10.0
                        event.revG = int(sp.group(3)) / 10.0
                        event.leftG = int(sp.group(4)) / 10.0
                        event.rightG = int(sp.group(5)) / 10.0
                        event.maxG1 = int(sp.group(6)) / 10.0
                        event.maxG2 = int(sp.group(7)) / 10.0
                        event.severity = sp.group(8)

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(9))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

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
                    specPattern = re.compile(r'([0-9]+) (OK|CANCEL|NOFILE) ([0-9]+) ([0-9]+) ([0-9]+) ([\-a-zA-Z]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.result = sp.group(2)
                        event.failedQ = int(sp.group(3))
                        event.duration = int(sp.group(4))
                        event.chkVersion = int(sp.group(5))
                        event.chkType = sp.group(6)

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(7))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numOperatorEvents += 1
                        self.numChecklist += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # CLFAIL event
                # =============================================================================
                elif event.event == "CLFAIL":
                    specPattern = re.compile(r'([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.failedQNo = int(sp.group(2))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(3))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # XSIDLESTART event
                # =============================================================================
                elif event.event == "XSIDLESTART":
                    specPattern = re.compile(r'([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(2))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numVehicleEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # XSIDLE event
                # (variation with XSIDLE reason)
                # Need to check for longest search string first.
                # =============================================================================
                elif event.event == "XSIDLE":
                    specPattern1 = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    specPattern2 = re.compile(r'([0-9]+) ([0-9]+)(.*)$')
                    sp1 = re.search(specPattern1, eventSpecifics)
                    sp2 = re.search(specPattern2, eventSpecifics)
                    # Check for extended XSIDLE event with added event reason.
                    if sp1:
                        event.tripStartId = int(sp1.group(1))
                        event.maxIdle = int(sp1.group(2))
                        event.xsidleReason = int(sp1.group(3))

                        # For charting of XSIDLE like other duration based events copy the max idle time to event duration.
                        event.duration = event.maxIdle

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp1.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numVehicleEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                    # Check for basic XSIDLE event.
                    elif sp2:
                        event.tripStartId = int(sp2.group(1))
                        event.maxIdle = int(sp2.group(2))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp2.group(3))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

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

                    specPattern = re.compile(r'([0-9]+)')
                    sp = re.search(specPattern, eventSpecifics)
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
                    specPattern = re.compile(r'(\*|[0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        # Check for bad sign-on ID, i.e. "*".
                        if (sp.group(1) == "*"):
                            event.tripStartId = -1
                        else:
                            event.tripStartId = int(sp.group(1))
                        event.speed = int(sp.group(2))
                        event.direction = int(sp.group(3))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Indicate event is Report event to control presentation format.
                        event.isReport = True
                        self.numReportEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # CRITICALOUTPUTSET event.
                # *********************************************************************************************************************************************
                elif event.event == "CRITICALOUTPUTSET":   
                    specPattern = re.compile(r'([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.speed = int(sp.group(2))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(3))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Add event to list of events.
                        self.events.append(event)
                # =============================================================================
                # OOS PM/UPM event
                # =============================================================================
                elif ((event.event == "OOS PM") or (event.event == "OOS UPM")):

                    specPattern = re.compile(r'([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.oosReason = int(sp.group(2))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(3))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numVehicleEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # INPUT event.
                # *********************************************************************************************************************************************
                elif event.event == "INPUT":   
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.inputNo = int(sp.group(1))
                        event.inputState = int(sp.group(2))
                        event.activeTime = int(sp.group(3))
                        # Note that activeTime refers to time in the active state.
                        # That is, if inputState is inactive state (0) then active time will always be 0.

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

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

                    specPattern = re.compile(r'(.+)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:

                        # Debug information.
                        event.debugInfo = sp.group(1)

                        # Check and alert for known critical debug issues.
                        if "Time1H:" in event.debugInfo:
                            event.alertText = appendAlertText(event.alertText, "Time correction.")

                        elif "Time1H INV:" in event.debugInfo:
                            event.alertText = appendAlertText(event.alertText, "Invalid time detected.")

                        elif "Time(BAD)" in event.debugInfo:
                            event.alertText = appendAlertText(event.alertText, "BAD time detected.")
                        elif "v:" in event.debugInfo:
                            # Read battery voltage from event header.
                            # But only if still collecting extra data, i.e. trip has not ended.
                            if not self.stopExtraData:
                                # The voltage at end of event strings appears to be optional, so need to check if it exists.
                                voltPattern = re.compile(r'.*v:([0-9]+)$')
                                vp = re.search(voltPattern, event.debugInfo)
                                if vp:
                                    event.battery = int(vp.group(1)) / 10.0
                                    # And add to battery level list.
                                    self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                    # Check for negative battery voltage condition.
                                    if event.battery < 0:
                                        event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Indicate event is Debug event to control presentation format.
                        event.isDebug = True
                        self.numDebugEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # POWER event.
                # *********************************************************************************************************************************************
                elif event.event == "POWER":
                    specPattern = re.compile(r'([0-9]+) ([ _A-Z]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(3))
                        event.voltage = int(sp.group(1)) / 10.0
                        event.batteryState = sp.group(2)

                        # If battery voltage not okay set alert text.
                        if event.batteryState != "OK":
                            event.alertText = appendAlertText(event.alertText, "Battery not OK.")

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # TRIP event
                # (variation with no On Seat time)
                # Need to check for longest search string first.
                # *********************************************************************************************************************************************
                elif event.event == "TRIP":   

                    self.tripEnd = int(su.group(4))
                    self.logger.debug("Detected trip end at {0:s}".format(datetime.fromtimestamp(self.tripEnd).strftime('%d/%m/%Y %H:%M:%S')))

                    specPattern1 = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    specPattern2 = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp1 = re.search(specPattern1, eventSpecifics)
                    sp2 = re.search(specPattern2, eventSpecifics)
                    # Check TRIP event with on seat time.
                    if sp1:
                        event.tripStartId = int(sp1.group(1))
                        event.timeFwd = int(sp1.group(2))
                        event.timeRev = int(sp1.group(3))
                        event.timeIdle = int(sp1.group(4))
                        event.maxIdle = int(sp1.group(5))
                        event.timeOnSeat = int(sp1.group(6))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp1.group(7))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numTripEvents += 1

                    # Check TRIP event without on seat time.
                    elif sp2:
                        event.tripStartId = int(sp2.group(1))
                        event.timeFwd = int(sp2.group(2))
                        event.timeRev = int(sp2.group(3))
                        event.timeIdle = int(sp2.group(4))
                        event.maxIdle = int(sp2.group(5))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp2.group(6))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numTripEvents += 1

                    # If either type of TRIP event then do end of trip processing.
                    if sp1 or sp2:
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

                        # Don't want to collect any more extra data as not useful for trip plots.
                        self.stopExtraData = True

                        # Add event to list of events.
                        self.events.append(event)

                        # Set TRIP event reached flag. Used so that we can look for TRIPSUMMARY and/or TRIPLOAD events.
                        self.tripTrip = True
                # *********************************************************************************************************************************************
                # Other events
                # Only event names checked, parameter details ignored.
                # *********************************************************************************************************************************************
                else:
                    # Don't include SIGNON, TRIP, TRIPSUMMARY, and TRIPLOAD as they are detected separately.
                    if event.event not in ["SIGNON", "TRIP", "TRIPSUMMARY", "TRIPLOAD"]:

                        # Indicate that event is OTHER event, i.e. not supported (yet).
                        event.isOther = True

                        # Increment event counters.
                        self.numOtherEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # Look for trip summary type events. These occurs after the TRIP event but are only generated if events occurred during the trip.
                # Doing these events separately as they are different format to the OTHER event messages.
                # *********************************************************************************************************************************************
                if self.tripTrip == True:
                    if event.event == "TRIPSUMMARY":
                        specPattern = re.compile(r'([0-9]+)')
                        sp = re.search(specPattern, eventSpecifics)
                        if sp:
                            event.tripStartId = int(sp.group(1))

                            # Increment event counters.
                            self.numTripEvents += 1

                            # Normally this event would be tagged "out of trip" as occurred after TRIP event.
                            # Treat it specially as part of the trip, really.
                            event.isOutOfTrip = False

                            # Add event to list of events.
                            self.events.append(event)
                    elif event.event == "TRIPLOAD":
                        specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)')
                        sp = re.search(specPattern, eventSpecifics)
                        if sp:
                            event.tripStartId = int(sp.group(1))
                            event.travelLoaded = int(sp.group(2))
                            event.travelUnloaded = int(sp.group(3))
                            event.idleLoaded = int(sp.group(4))
                            event.idleUnloaded = int(sp.group(5))
                            event.liftCount = int(sp.group(6))
                            event.cumWeight = int(sp.group(7))

                            # Increment event counters.
                            self.numTripEvents += 1

                            # Normally this event would be tagged "out of trip" as occurred after TRIP event.
                            # Treat it specially as part of the trip, really.
                            event.isOutOfTrip = False

                            # Add event to list of events.
                            self.events.append(event)

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

                            # Don't want to collect any more extra data as not useful for trip plots.
                            self.stopExtraData = True

                            # Add event to list of events.
                            self.events.append(event)

                            # Set TRIP event reached flag.
                            self.tripTrip = True

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
# Zone Transition class.
# *******************************************
class ZoneX():
    # Initializer / Instance Attributes
    def __init__(self, config, logger, logBuf):

        self.cfg = config
        self.logger = logger

        self.logger.debug("ZoneX class constructor.")

        # Buffer snippet for zone change / transition.
        self.logBuf = logBuf

        # Event data.
        self.events = []
    
        # Speed data.
        self.speedLog = []

        # Zone crossings.
        self.zoneXings = []

        # Battery level.
        self.batteryLevel = []

    # *******************************************
    # Extract power cycle data from buffer snippet.
    # *******************************************
    def extractZoneData(self):

        # power cycle timing.
        # Not trips but use same variables to make reporting easier.
        self.tripStart = 0
        self.tripEnd = 0
        self.tripStartId = 0

        # Trip in alert.
        # Used by trip data display.
        self.tripInAlert = False

        # Total event category totals.
        self.numOperatorEvents = 0
        self.numTripEvents = 0
        self.numReportEvents = 0
        self.numOtherEvents = 0
        self.numDebugEvents = 0

        # Total event category totals.
        self.numOperatorEvents = 0

        # Total specific Operator events.
        self.numZoneChange = 0
        self.numTransition = 0

        # Track last time to check if event time going backwards.
        self.lastTime = 0

        # Track first from zone.
        self.firstFromZone = None

        # Initialise flag to stop collecting extra data past end of trip.
        self.stopExtraData = False

        # ******************************
        # Look for IGN_ON event.
        # ******************************
        patternStart = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) (.+)/(.+)/(.+)/([-0-9]+)/([0-9]+) (HARDWARE IGN_ON) (.+)$', re.MULTILINE)

        su = re.search(patternStart, self.logBuf)
        if su:
            # Break out some of the event data explicitly.
            eventSpecifics = su.group(11)
            specPattern = re.compile(r'(.+?)$')
            sp = re.search(specPattern, eventSpecifics)
            if sp:
                # Create event object.
                # Initialised with event type and time as in all events.
                event = Event(su.group(10), int(su.group(4)))
                self.tripStart = int(su.group(4))
                self.logger.debug("Detected power ON at: {0:s}".format(datetime.fromtimestamp(self.tripStart).strftime('%d/%m/%Y %H:%M:%S')))

                # Initialise last time to start of trip.
                self.lastTime = self.tripStart

                # Get speed data from event header.
                event.speed = int(su.group(9))

                # Read battery voltage from event header.
                # But only if still collecting extra data, i.e. trip has not ended.
                if not self.stopExtraData:
                    # The voltage at end of event strings appears to be optional, so need to check if it exists.
                    voltPattern = re.compile(r'v:([0-9]+)$')
                    vp = re.search(voltPattern, sp.group(1))
                    if vp:
                        # Extract battery voltage.
                        event.battery = int(vp.group(1)) / 10.0

                        # And add to battery level list.
                        self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                        # Check for negative battery voltage condition.
                        if event.battery < 0:
                            event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                # Increment event counters.
                self.numTripEvents += 1

                # Add event to list of events.
                self.events.append(event)

                # Initialise power cycle not ended.
                self.ignCycleOpen = False

            # **************************************************************
            # Look for specific events other than the hardware power cycle event.
            # **************************************************************
            patternData = re.compile(r'([0-9]{1,2}/[0-9]{2}/[0-9]{4}) ([0-9]{1,2}:[0-9]{2}:[0-9]{2}) .*?\,*?EVENT ([0-9]+) ([0-9]+) (.+)/(.+)/(.+)/([-0-9]+)/([0-9]+) ([ _a-zA-Z]+) (.+)$', re.MULTILINE)
            for su in re.finditer(patternData, self.logBuf):

                # Found event.
                event = Event(su.group(10), int(su.group(4)))
                self.logger.debug("Detected event: {0:s}, at: {1:s}".format(su.group(10), datetime.fromtimestamp(int(su.group(4))).strftime('%d/%m/%Y %H:%M:%S')))

                # Check for event time in the past, except if event is POWERDOWN as this is always in the past.
                if su.group(10) != "POWERDOWN":
                    if int(su.group(4)) < self.lastTime:
                        event.alertText = appendAlertText(event.alertText, "Event time reversal.")
                    self.lastTime = int(su.group(4))

                # Get speed data from event header.
                # But only if still collecting extra data, i.e. trip has not ended.
                if not self.stopExtraData:
                    event.speed = int(su.group(9))
                    # Don't get speed from POWERDOWN event as these events occur out of order.
                    if su.group(10) != "POWERDOWN": 
                        # If speedlog already has speed for this time then skip, else append to list.
                        # If event is REPORT then don't log speed as speed in other field (with direction).
                        if su.group(10) != "REPORT":
                            if self.checkForSpeedTime(int(su.group(4))) == False:
                                self.speedLog.append(SpeedInfo(int(su.group(4)), int(su.group(9))))
                                self.logger.debug("Logged speed: {0:d}, at {1:s}".format(int(su.group(9)), datetime.fromtimestamp(int(su.group(4))).strftime('%d/%m/%Y %H:%M:%S')))

                # Break out some of the event data explicitly.
                eventSpecifics = su.group(11)

                # =============================================================================
                # ZONECHANGE event
                # =============================================================================
                if event.event == "ZONECHANGE":
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.fromZone = int(sp.group(2))
                        event.toZone = int(sp.group(3))
                        event.zoneOutput = int(sp.group(4))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(5))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

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
                # ZONETRANSITION event
                # =============================================================================
                elif event.event == "ZONETRANSITION":
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) (ENTRY|EXIT) (.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(1))
                        event.fromZone = int(sp.group(2))
                        event.toZone = int(sp.group(3))
                        event.toZoneOutput = int(sp.group(4))
                        event.transition = sp.group(5)

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(6))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numTransition += 1

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
                    specPattern = re.compile(r'(\*|[0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        # Check for bad sign-on ID, i.e. "*".
                        if (sp.group(1) == "*"):
                            event.tripStartId = -1
                        else:
                            event.tripStartId = int(sp.group(1))
                        event.speed = int(sp.group(2))
                        event.direction = int(sp.group(3))

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Indicate event is Report event to control presentation format.
                        event.isReport = True
                        self.numReportEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # INPUT event.
                # *********************************************************************************************************************************************
                elif event.event == "INPUT":   
                    specPattern = re.compile(r'([0-9]+) ([0-9]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.inputNo = int(sp.group(1))
                        event.inputState = int(sp.group(2))
                        event.activeTime = int(sp.group(3))
                        # Note that activeTime refers to time in the active state.
                        # That is, if inputState is inactive state (0) then active time will always be 0.

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

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

                    specPattern = re.compile(r'(.+)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:

                        # Debug information.
                        event.debugInfo = sp.group(1)

                        # Check and alert for known critical debug issues.
                        if "Time1H:" in event.debugInfo:
                            event.alertText = appendAlertText(event.alertText, "Time correction.")

                        elif "Time1H INV:" in event.debugInfo:
                            event.alertText = appendAlertText(event.alertText, "Invalid time detected.")

                        elif "Time(BAD)" in event.debugInfo:
                            event.alertText = appendAlertText(event.alertText, "BAD time detected.")
                        elif "v:" in event.debugInfo:
                            # Read battery voltage from event header.
                            # But only if still collecting extra data, i.e. trip has not ended.
                            if not self.stopExtraData:
                                # The voltage at end of event strings appears to be optional, so need to check if it exists.
                                voltPattern = re.compile(r'.*v:([0-9]+)$')
                                vp = re.search(voltPattern, event.debugInfo)
                                if vp:
                                    event.battery = int(vp.group(1)) / 10.0
                                    # And add to battery level list.
                                    self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                    # Check for negative battery voltage condition.
                                    if event.battery < 0:
                                        event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Indicate event is Debug event to control presentation format.
                        event.isDebug = True
                        self.numDebugEvents += 1

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # POWER event.
                # *********************************************************************************************************************************************
                elif event.event == "POWER":
                    specPattern = re.compile(r'([0-9]+) ([ _A-Z]+) ([0-9]+)(.*)$')
                    sp = re.search(specPattern, eventSpecifics)
                    if sp:
                        event.tripStartId = int(sp.group(3))
                        event.voltage = int(sp.group(1)) / 10.0
                        event.batteryState = sp.group(2)

                        # If battery voltage not okay set alert text.
                        if event.batteryState != "OK":
                            event.alertText = appendAlertText(event.alertText, "Battery not OK.")

                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(4))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Add event to list of events.
                        self.events.append(event)
                # *********************************************************************************************************************************************
                # Power off event
                # *********************************************************************************************************************************************
                elif event.event == "HARDWARE IGN_OFF":   

                    self.tripEnd = int(su.group(4))
                    self.logger.debug("Detected power OFF at: {0:s}".format(datetime.fromtimestamp(self.tripEnd).strftime('%d/%m/%Y %H:%M:%S')))

                    specPattern = re.compile(r'(.+?)$')
                    sp = re.search(specPattern, eventSpecifics)
                    # Check TRIP event with on seat time.
                    if sp:
                        # Read battery voltage from event header.
                        # But only if still collecting extra data, i.e. trip has not ended.
                        if not self.stopExtraData:
                            # The voltage at end of event strings appears to be optional, so need to check if it exists.
                            voltPattern = re.compile(r'.*v:([0-9]+)$')
                            vp = re.search(voltPattern, sp.group(1))
                            if vp:
                                event.battery = int(vp.group(1)) / 10.0
                                # And add to battery level list.
                                self.batteryLevel.append(BatteryInfo(int(su.group(4)), event.battery))

                                # Check for negative battery voltage condition.
                                if event.battery < 0:
                                    event.alertText = appendAlertText(event.alertText, "Battery voltage negative.")

                        # Increment event counters.
                        self.numTripEvents += 1
                # *********************************************************************************************************************************************
                # Other events
                # Only event names checked, parameter details ignored.
                # *********************************************************************************************************************************************
                else:
                    # Don't include SIGNON, TRIP, TRIPSUMMARY, and TRIPLOAD as they are detected separately.
                    if event.event not in ["HARDWARE IGN_ON", "HARDWARE IGN_OFF"]:

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
