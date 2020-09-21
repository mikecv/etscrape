#!/usr/bin/env python3

import json

# *******************************************
# Program config class
# *******************************************
class Config():
    # Initializer / Instance Attributes
    def __init__(self):

        # Version of configuration.
        self.ConfigVersion = 8

        # Logger configuration values
        self.DebugLevel = 20
        self.LogFileSize = 100000
        self.LogBackups = 3

        # Application general configuration
        self.TimeUTC = 1

        # Supported Events (for events chart)
        self.events = ["ENGINEOVERSPEED", "ENGINETEMP", "IMPACT", "INPUT", "LOWCOOLANT",
            "OFFSEAT", "OILPRESSURE" , "OVERLOAD", "OVERSPEED", "UNBUCKLED", "ZONECHANGE", "ZONEOVERSPEED"]

        # Supported Events (for events chart)
        self.chartEvents = [
            {"Event" : "", "Title" : ""},
            {"Event" : "Vehicle Speed", "Title" : "Vehicle Speed"},
            {"Event" : "Battery Voltage", "Title" : "Battery Voltage"},
            {"Event" : "ENGINEOVERSPEED", "Title" : "Engine Overspeed"},
            {"Event" : "ENGINETEMP", "Title" : "Engine Temperature High"},
            {"Event" : "IMPACT", "Title" : "Vehicle Impact"},
            {"Event" : "INPUT", "Title" : "Input"},
            {"Event" : "LOWCOOLANT", "Title" : "Engine Coolant Level Low"},
            {"Event" : "OFFSEAT", "Title" : "Operator Off Seat"},
            {"Event" : "OILPRESSURE", "Title" : "Engine Oil Pressure Low"},
            {"Event" : "OVERLOAD", "Title" : "Overload"},
            {"Event" : "OVERSPEED", "Title" : "Vehicle Overspeed"},
            {"Event" : "UNBUCKLED", "Title" : "Operator Unbuckled"},
            {"Event" : "ZONECHANGE", "Title" : "Zone Change"},
            {"Event" : "ZONEOVERSPEED", "Title" : "Zone Overspeed"}
            ]

        # Supported Events (for event filtering)
        self.filterEvents = ["CHECKLIST", "CRITICALOUTPUTSET", "DEBUG", "Time1H", "Time1H INV", "Time1H (BAD)",
            "ENGINEOVERSPEED", "ENGINETEMP", "IMPACT", "LOWCOOLANT", "OFFSEAT", "OILPRESSURE",
            "OVERLOAD", "OVERSPEED", "POWER", "TRIPLOAD", "UNBUCKLED", "XSIDLE", "ZONECHANGE", "ZONEOVERSPEED"]

        # Trip related data.
        self.TripData = {
            "MinColumnWidth" : 185,
            "DefaultColumn2Width" : 375,
            "TripBackColour" : "#f0e68c",
            "TripColour" : "#000000",
            "EventColour" : "#0000ff",
            "AlertColour" : "#ff0000",
            "CommentColour" : "#ff0000",
            "SummaryAlertColour" : "#0000ff",
            "OtherEventColour" : "#99990c",
            "InputEventColour" : "#ffbf00",
            "DebugEventColour" : "#00fa9a",
            "TmpStatusMessagesMsec" : 10000,
            "ShowOtherEvents" : 1,
            "ShowInputEvents" : 1,
            "ShowDebugEvents" : 1,
            "ShowOutOfTripEvents" : 0,
            "BadSpeedLimit" : 100,
            "BadRpmLimit" : 5200
        }

        # Speed plot data.
        self.SpdPlot = {
            "DefaultLowLimit": 30,
            "DefaultHiLimit": 60,
            "SpeedColour": "#0000ff",
            "ZoneColour": "#ff0000",
            "AxesTitleFontSize": 7,
            "PlotTitleFontSize": 10
        }

        # Event plot data.
        self.EvPlot = {
            "AxesTitleFontSize": 7,
            "PlotTitleFontSize": 10,
            "AxisLabelFontSize": 6,
            "EventTraceColour": "#0000ff",
            "TripTraceColour": "#000000",
            "EventFillColour": "#0000ff",
            "TripFillColour": "#ffff00",
            "MaxTitleLineLength": 12
        }

        # Input channel definitions.
        self.Channels = [
            {"No" : 1, "Name" : "[ET] Engine Oil Pressure, [ST] Seat"},
            {"No" : 2, "Name" : "[ET] Engine Temperature"},
            {"No" : 3, "Name" : "[ET] Ground Speed, [ST] Work 1"},
            {"No" : 4, "Name" : "[ET] Engine Speed, [ST] Work 2"},
            {"No" : 5, "Name" : "[ET] Passenger Seatbelt, [ST] Weight"},
            {"No" : 6, "Name" : "[ET][ST] Operator Seatbelt"},
            {"No" : 7, "Name" : "[ET] Engine Coolant Level, [ST] Work 3"},
            {"No" : 8, "Name" : "[ET][ST] Ignition Switch"},
            {"No" : 9, "Name" : "[ET][ST] Accelerometer"},
            {"No" : 10, "Name" : "[ET][ST] GNSS"}
            ]

        # Event chart.
        self.EventTraces = [
            {"Event" : "Vehicle Speed", "Title" : "Vehicle Speed"},
            {"Event" : "ENGINEOVERSPEED", "Title" : "Engine Overspeed"},
            {"Event" : "OILPRESSURE", "Title" : "Engine Oil Pressure Low"},
            {"Event" : "INPUT", "Channel" : 1},
            {"Event" : "INPUT", "Channel" : 3},
            {"Event" : "INPUT", "Channel" : 4}
            ]

        # Read / update configuration from file.
        self.readConfig()

    # *******************************************
    # Read Json configuration file.
    # *******************************************
    def readConfig(self):
        try:
            with open('etscrape.json') as config_file:
                config = json.load(config_file)

                # Check configuration version.
                # If version not a match then update completely.
                if config["ConfigVersion"] != self.ConfigVersion:
                    print("Upgrading configuration file.")
                    # Save configuration to file.
                    self.saveConfig()

                # Update configuration values if possible.
                # If not, just update with default + whatever values read.
                updateConfig = False
                try:
                    self.DebugLevel = config["DebugLevel"]
                except Exception:
                    print("Error reading Debug Level configuration data.")
                try:
                    self.LogFileSize = config["LogFileSize"]
                except Exception:
                    print("Error reading Log File Size configuration data.")
                try:
                    self.LogBackups = config["LogBackups"]
                except Exception:
                    print("Error reading Log File Backups configuration data.")
                try:
                    self.TimeUTC = config["TimeUTC"]
                except Exception:
                    print("Error reading UTC Time configuration data.")
                # *********************************************************
                # Checking elements of TripData.
                # *********************************************************
                # Try setting MinColumnWidth from user configuration (json).
                try:
                    paramSaved = self.TripData["MinColumnWidth"]
                    self.TripData["MinColumnWidth"] = config["TripData"]["MinColumnWidth"]
                except Exception:
                    self.TripData["MinColumnWidth"] = paramSaved
                    updateConfig = True
                # Try setting DefaultColumn2Width from user configuration (json).
                try:
                    paramSaved = self.TripData["DefaultColumn2Width"]
                    self.TripData["DefaultColumn2Width"] = config["TripData"]["DefaultColumn2Width"]
                except Exception:
                    self.TripData["DefaultColumn2Width"] = paramSaved
                    updateConfig = True
                # Try setting TripBackColour from user configuration (json).
                try:
                    paramSaved = self.TripData["TripBackColour"]
                    self.TripData["TripBackColour"] = config["TripData"]["TripBackColour"]
                except Exception:
                    self.TripData["TripBackColour"] = paramSaved
                    updateConfig = True
                # Try setting TripBackColour from user configuration (json).
                try:
                    paramSaved = self.TripData["TripBackColour"]
                    self.TripData["TripBackColour"] = config["TripData"]["TripBackColour"]
                except Exception:
                    self.TripData["TripBackColour"] = paramSaved
                    updateConfig = True
                # Try setting TripColour from user configuration (json).
                try:
                    paramSaved = self.TripData["TripColour"]
                    self.TripData["TripColour"] = config["TripData"]["TripColour"]
                except Exception:
                    self.TripData["TripColour"] = paramSaved
                    updateConfig = True
                # Try setting EventColour from user configuration (json).
                try:
                    paramSaved = self.TripData["EventColour"]
                    self.TripData["EventColour"] = config["TripData"]["EventColour"]
                except Exception:
                    self.TripData["EventColour"] = paramSaved
                    updateConfig = True
                # Try setting CommentColour from user configuration (json).
                try:
                    paramSaved = self.TripData["AlertColour"]
                    self.TripData["AlertColour"] = config["TripData"]["AlertColour"]
                except Exception:
                    self.TripData["AlertColour"] = paramSaved
                    updateConfig = True
                # Try setting CommentColour from user configuration (json).
                try:
                    paramSaved = self.TripData["CommentColour"]
                    self.TripData["CommentColour"] = config["TripData"]["CommentColour"]
                except Exception:
                    self.TripData["CommentColour"] = paramSaved
                    updateConfig = True
                # Try setting SummaryAlertColour from user configuration (json).
                try:
                    paramSaved = self.TripData["SummaryAlertColour"]
                    self.TripData["SummaryAlertColour"] = config["TripData"]["SummaryAlertColour"]
                except Exception:
                    self.TripData["SummaryAlertColour"] = paramSaved
                    updateConfig = True
                # Try setting OtherEventColour from user configuration (json).
                try:
                    paramSaved = self.TripData["OtherEventColour"]
                    self.TripData["OtherEventColour"] = config["TripData"]["OtherEventColour"]
                except Exception:
                    self.TripData["OtherEventColour"] = paramSaved
                    updateConfig = True
                # Try setting InputEventColour from user configuration (json).
                try:
                    paramSaved = self.TripData["InputEventColour"]
                    self.TripData["InputEventColour"] = config["TripData"]["InputEventColour"]
                except Exception:
                    self.TripData["InputEventColour"] = paramSaved
                    updateConfig = True
                # *********************************************************
                # Try setting ShowDebugEvents from user configuration (json).
                try:
                    paramSaved = self.TripData["ShowDebugEvents"]
                    self.TripData["ShowDebugEvents"] = config["TripData"]["ShowDebugEvents"]
                except Exception:
                    self.TripData["ShowDebugEvents"] = paramSaved
                    updateConfig = True
                # Try setting ShowOutOfTripEvents from user configuration (json).
                try:
                    paramSaved = self.TripData["ShowOutOfTripEvents"]
                    self.TripData["ShowOutOfTripEvents"] = config["TripData"]["ShowOutOfTripEvents"]
                except Exception:
                    self.TripData["ShowOutOfTripEvents"] = paramSaved
                    updateConfig = True
                # Try setting BadSpeedLimit from user configuration (json).
                try:
                    paramSaved = self.TripData["BadSpeedLimit"]
                    self.TripData["BadSpeedLimit"] = config["TripData"]["BadSpeedLimit"]
                except Exception:
                    self.TripData["BadSpeedLimit"] = paramSaved
                    updateConfig = True
                # Try setting BadRpmLimit from user configuration (json).
                try:
                    paramSaved = self.TripData["BadRpmLimit"]
                    self.TripData["BadRpmLimit"] = config["TripData"]["BadRpmLimit"]
                except Exception:
                    self.TripData["BadRpmLimit"] = paramSaved
                    updateConfig = True
                # *********************************************************
                try:
                    self.SpdPlot = config["SpdPlot"]
                except Exception:
                    print("Error reading Speed Plot configuration data.")
                try:
                    self.EvPlot = config["EvPlot"]
                except Exception:
                    print("Error reading Event Plot configuration data.")
                try:
                    self.Channels = config["Channels"]
                except Exception:
                    print("Error reading Channels configuration data.")
                try:
                    self.EventTraces = config["EventTraces"]
                except Exception:
                    print("Error reading Event Traces configuration data.")

                if updateConfig:
                    print("Saving configuration file due to user changed parameter.")
                    self.saveConfig()

        except Exception:
            print("Error opening configuration file.")
            # Create default configuration file.
            print("Saving default configuration data.")
            self.saveConfig()
        
    # *******************************************
    # Save Json configuration file.
    # *******************************************
    def saveConfig(self):

        # Format configuration data.
        cfgDict = {
            "ConfigVersion" : self.ConfigVersion,
            "DebugLevel" : self.DebugLevel,
            "LogFileSize" : self.LogFileSize,
            "LogBackups" : self.LogBackups,
            "TimeUTC" : self.TimeUTC,
            "TripData" : self.TripData,
            "SpdPlot" : self.SpdPlot,
            "EvPlot" : self.EvPlot,
            "Channels" : self.Channels,
            "EventTraces" : self.EventTraces
        }

        # Open file for writing.
        try:
            outfile = open("etscrape.json", 'w')
            outfile.write(json.dumps(cfgDict, sort_keys=False, indent=4, ensure_ascii=False))
            outfile.close()
        except Exception:
            print("Failed to create default configuration file : {0:s}".format('etscrape.json'))
