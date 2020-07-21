#!/usr/bin/env python3

import json

# *******************************************
# Program config class
# *******************************************
class Config():
    # Initializer / Instance Attributes
    def __init__(self):

        # Version of configuration.
        self.ConfigVersion = 4

        # Logger configuration values
        self.DebugLevel = 20
        self.LogFileSize = 100000
        self.LogBackups = 3

        # Application general configuration
        self.TimeUTC = 1

        # Supported Events (for events chart)
        self.events = ["", "SIGNON", "ZONEOVERSPEED", "ENGINEOVERSPEED", "LOWCOOLANT", "OILPRESSURE", "ENGINETEMP", "INPUT"]

        # Trip related data.
        self.TripData = {
            "TripBackColour" : "#ffff00",
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
            "BadSpeedLimit" : 150,
            "BadRpmLimit" : 5000
        }

        # Speed plot data.
        self.SpdPlot = {
            "DefaultLowLimit": 30,
            "DefaultHiLimit": 60,
            "SpeedColour": "#0000ff",
            "ZoneColour": "#ff66ff",
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
            "TripFillColour": "#ffff00"
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
            {"Event" : "ZONEOVERSPEED", "Title" : "Zone\nOverspeed"},
            {"Event" : "ENGINEOVERSPEED", "Title" : "Engine\nOverspeed"},
            {"Event" : "LOWCOOLANT", "Title" : "Engine Coolant\nLevel Low"},
            {"Event" : "OILPRESSURE", "Title" : "Engine Oil\nPressure Low"},
            {"Event" : "ENGINETEMP", "Title" : "Engine\nTemperature High"},
            {"Event" : "INPUT", "Channel" : 1},
            {"Event" : "INPUT", "Channel" : 2},
            {"Event" : "INPUT", "Channel" : 8}
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
                else:

                    # Update configuration values if possible.
                    # If not, just update with default + whatever values read.
                    try:
                        self.DebugLevel = config["DebugLevel"]
                        self.LogFileSize = config["LogFileSize"]
                        self.LogBackups = config["LogBackups"]
                        self.TimeUTC = config["TimeUTC"]
                        self.TripData = config["TripData"]
                        self.SpdPlot = config["SpdPlot"]
                        self.EvPlot = config["EvPlot"]
                        self.Channels = config["Channels"]
                        self.EventTraces = config["EventTraces"]
                    except Exception:
                        print("Error reading configuration file.")

        except Exception:
            print("Error opening configuration file.")
            # Create default configuration file.
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
