#!/usr/bin/env python3

import json

# *******************************************
# Program config class
# *******************************************
class Config():
    # Initializer / Instance Attributes
    def __init__(self):

        # Version of configuration.
        self.ConfigVersion = 12

        # Logger configuration values
        self.DebugLevel = 20
        self.LogFileSize = 100000
        self.LogBackups = 3

        # Application general configuration
        self.TimeUTC = 1

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
            {"Event" : "UNBUCKLED", "Title" : "Unbuckled"},
            {"Event" : "XSIDLE", "Title" : "Excess Idle"},
            {"Event" : "ZONECHANGE", "Title" : "Zone Change"},
            {"Event" : "ZONETRANSITION", "Title" : "Zone Transition"},
            {"Event" : "ZONEOVERSPEED", "Title" : "Zone Overspeed"}
            ]

        # Supported Events (for event filtering)
        self.filterEvents = ["CHECKLIST", "CLFAIL", "CRITICALOUTPUTSET", "DEBUG", "Time1H", "Time1H INV", "Time1H (BAD)",
            "ENGINEOVERSPEED", "ENGINETEMP", "IMPACT", "LOWCOOLANT", "OFFSEAT", "OILPRESSURE",
            "OVERLOAD", "OVERSPEED", "POWER", "TRIPLOAD", "TRIPSUMMARY", "UNBUCKLED", "XSIDLE",
            "ZONECHANGE", "ZONETRANSITION", "ZONEOVERSPEED"]

        # Trip related data.
        self.TripData = {
            "MinColumnWidth" : 185,
            "DefaultColumn2Width" : 375,
            "TripBackColour" : "#f0e68c",
            "TripColour" : "#000000",
            "EventColour" : "#0000ff",
            "AlertColour" : "#ff0000",
            "CommentColour" : "#550000",
            "SummaryAlertColour" : "#0000ff",
            "OtherEventColour" : "#99990c",
            "InputEventColour" : "#aa5500",
            "DebugEventColour" : "#00fa9a",
            "ReportEventColour" : "#320096",
            "TmpStatusMessagesMsec" : 10000,
            "ShowOtherEvents" : 0,
            "ShowInputEvents" : 1,
            "ShowDebugEvents" : 1,
            "ShowReportEvents" : 0,
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
            "MaxTitleLineLength": 12,
            "EventTraceColourXtra": "#DF7401",
            "EventFillColourXtra": "#DF7401"
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
                    updateConfig = True
                try:
                    self.LogFileSize = config["LogFileSize"]
                except Exception:
                    updateConfig = True
                try:
                    self.LogBackups = config["LogBackups"]
                except Exception:
                    updateConfig = True
                try:
                    self.TimeUTC = config["TimeUTC"]
                except Exception:
                    updateConfig = True
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
                # Checking elements of SpdPlot from user configuration (json).
                # *********************************************************
                # Try setting DefaultLowLimit from user configuration (json).
                try:
                    paramSaved = self.SpdPlot["DefaultLowLimit"]
                    self.SpdPlot["DefaultLowLimit"] = config["SpdPlot"]["DefaultLowLimit"]
                except Exception:
                    self.SpdPlot["DefaultLowLimit"] = paramSaved
                    updateConfig = True
                # Try setting DefaultHiLimit from user configuration (json).
                try:
                    paramSaved = self.SpdPlot["DefaultHiLimit"]
                    self.SpdPlot["DefaultHiLimit"] = config["SpdPlot"]["DefaultHiLimit"]
                except Exception:
                    self.SpdPlot["DefaultHiLimit"] = paramSaved
                    updateConfig = True
                 # Try setting SpeedColour from user configuration (json).
                try:
                    paramSaved = self.SpdPlot["SpeedColour"]
                    self.SpdPlot["SpeedColour"] = config["SpdPlot"]["SpeedColour"]
                except Exception:
                    self.SpdPlot["SpeedColour"] = paramSaved
                    updateConfig = True
                 # Try setting ZoneColour from user configuration (json).
                try:
                    paramSaved = self.SpdPlot["ZoneColour"]
                    self.SpdPlot["ZoneColour"] = config["SpdPlot"]["ZoneColour"]
                except Exception:
                    self.SpdPlot["ZoneColour"] = paramSaved
                    updateConfig = True
                 # Try setting AxesTitleFontSize from user configuration (json).
                try:
                    paramSaved = self.SpdPlot["AxesTitleFontSize"]
                    self.SpdPlot["AxesTitleFontSize"] = config["SpdPlot"]["AxesTitleFontSize"]
                except Exception:
                    self.SpdPlot["AxesTitleFontSize"] = paramSaved
                    updateConfig = True
                 # Try setting PlotTitleFontSize from user configuration (json).
                try:
                    paramSaved = self.SpdPlot["PlotTitleFontSize"]
                    self.SpdPlot["PlotTitleFontSize"] = config["SpdPlot"]["PlotTitleFontSize"]
                except Exception:
                    self.SpdPlot["PlotTitleFontSize"] = paramSaved
                    updateConfig = True
                # *********************************************************
                # Checking elements of EvPlot.
                # *********************************************************
                # Try setting DefaultLowLimit from user configuration (json).
                try:
                    paramSaved = self.EvPlot["AxesTitleFontSize"]
                    self.EvPlot["AxesTitleFontSize"] = config["EvPlot"]["AxesTitleFontSize"]
                except Exception:
                    self.EvPlot["AxesTitleFontSize"] = paramSaved
                    updateConfig = True
                # Try setting PlotTitleFontSize from user configuration (json).
                try:
                    paramSaved = self.EvPlot["PlotTitleFontSize"]
                    self.EvPlot["PlotTitleFontSize"] = config["EvPlot"]["PlotTitleFontSize"]
                except Exception:
                    self.EvPlot["PlotTitleFontSize"] = paramSaved
                    updateConfig = True
                # Try setting AxisLabelFontSize from user configuration (json).
                try:
                    paramSaved = self.EvPlot["AxisLabelFontSize"]
                    self.EvPlot["AxisLabelFontSize"] = config["EvPlot"]["AxisLabelFontSize"]
                except Exception:
                    self.EvPlot["AxisLabelFontSize"] = paramSaved
                    updateConfig = True
                # Try setting EventTraceColour from user configuration (json).
                try:
                    paramSaved = self.EvPlot["EventTraceColour"]
                    self.EvPlot["EventTraceColour"] = config["EvPlot"]["EventTraceColour"]
                except Exception:
                    self.EvPlot["EventTraceColour"] = paramSaved
                    updateConfig = True
                # Try setting TripTraceColour from user configuration (json).
                try:
                    paramSaved = self.EvPlot["TripTraceColour"]
                    self.EvPlot["TripTraceColour"] = config["EvPlot"]["TripTraceColour"]
                except Exception:
                    self.EvPlot["TripTraceColour"] = paramSaved
                    updateConfig = True
                # Try setting EventFillColour from user configuration (json).
                try:
                    paramSaved = self.EvPlot["EventFillColour"]
                    self.EvPlot["EventFillColour"] = config["EvPlot"]["EventFillColour"]
                except Exception:
                    self.EvPlot["EventFillColour"] = paramSaved
                    updateConfig = True
                # Try setting TripFillColour from user configuration (json).
                try:
                    paramSaved = self.EvPlot["TripFillColour"]
                    self.EvPlot["TripFillColour"] = config["EvPlot"]["TripFillColour"]
                except Exception:
                    self.EvPlot["TripFillColour"] = paramSaved
                    updateConfig = True
                # Try setting MaxTitleLineLength from user configuration (json).
                try:
                    paramSaved = self.EvPlot["MaxTitleLineLength"]
                    self.EvPlot["MaxTitleLineLength"] = config["EvPlot"]["MaxTitleLineLength"]
                except Exception:
                    self.EvPlot["MaxTitleLineLength"] = paramSaved
                    updateConfig = True
                # Try setting EventTraceColourXtra from user configuration (json).
                try:
                    paramSaved = self.EvPlot["EventTraceColourXtra"]
                    self.EvPlot["EventTraceColourXtra"] = config["EvPlot"]["EventTraceColourXtra"]
                except Exception:
                    self.EvPlot["EventTraceColourXtra"] = paramSaved
                    updateConfig = True
                # Try setting EventFillColourXtra from user configuration (json).
                try:
                    paramSaved = self.EvPlot["EventFillColourXtra"]
                    self.EvPlot["EventFillColourXtra"] = config["EvPlot"]["EventFillColourXtra"]
                except Exception:
                    self.EvPlot["EventFillColourXtra"] = paramSaved
                    updateConfig = True
                # *********************************************************
                # Try setting Channels from user configuration (json).
                # Accept unless there are not the right number of entries in the list.
                try:
                    paramSaved = self.Channels
                    self.Channels = config["Channels"]
                    if len(self.Channels) != 10:
                        self.Channels = paramSaved
                        updateConfig = True
                except Exception:
                    self.Channels = paramSaved
                    updateConfig = True
                # Try setting EventTraces from user configuration (json).
                # Accept unless there are too many entries in the list.
                try:
                    paramSaved = self.EventTraces
                    self.EventTraces = config["EventTraces"]
                    if len(self.EventTraces) > 8:
                        self.EventTraces = paramSaved
                        updateConfig = True
                except Exception:
                    self.EventTraces = paramSaved
                    updateConfig = True

                # If required, i.e. couldn't update all data from user configuration, then save default.
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
