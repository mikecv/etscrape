#!/usr/bin/env python3

import json

# *******************************************
# Program config class
# *******************************************
class Config():
    # Initializer / Instance Attributes
    def __init__(self):

        # Version of configuration.
        self.ConfigVersion = 2

        # Program configuration values
        self.DebugLevel = 20
        self.LogFileSize = 100000
        self.LogBackups = 3

        # Trip related data.
        self.TripData = {
            "TripPrefix" : "Trip",
            "TripBackColour" : "#ffff00",
            "TripColour" : "#000000",
            "EventColour" : "#0000ff",
            "AlertColour" : "#ff0000",
            "CommentColour" : "#ff0000",
            "SummaryAlertColour" : "#0000ff",
            "OtherEventColour" : "#99990c",
            "InputEventColour" : "#ffbf00",
            "TmpStatusMessagesMsec" : 10000,
            "ShowInputEvents" : 1,
            "ShowOtherEvents" : 1,
            "ShowOutOfTripEvents" : 0
        }

        # Speed plot data.
        self.SpdPlot = {
            "DefaultLowLimit": 30,
            "DefaultHiLimit": 60,
            "SpeedColour": "#00ff00",
            "SpdLimLowColour": "#ff9933",
            "SpdLimHiColour": "#ff0000",
            "AxesTitleFontSize": 7,
            "PlotTitleFontSize":10
        }

        # Input channel definitions.
        self.Channels = [
            {"No" : 1, "Name" : "Engine Oil Pressure"},
            {"No" : 2, "Name" : "Engine Temperature"},
            {"No" : 3, "Name" : "Ground Speed"},
            {"No" : 4, "Name" : "Engine Speed"},
            {"No" : 5, "Name" : "Passenger Seatbelt"},
            {"No" : 6, "Name" : "Operator Seatbelt"},
            {"No" : 7, "Name" : "Engine Coolant Level"},
            {"No" : 8, "Name" : "Ignition Switch"},
            {"No" : 9, "Name" : "Accelerometer"},
            {"No" : 10, "Name" : "GNSS"}
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
                # If version not a match then just update.
                if config["ConfigVersion"] != self.ConfigVersion:
                    print("Upgrading configuration file.")
                    self.saveConfig()
                else:

                    # Update configuration values if possible.
                    # If not, just update with default + whatever values read.
                    try:
                        self.DebugLevel = config["DebugLevel"]
                        self.LogFileSize = config["LogFileSize"]
                        self.LogBackups = config["LogBackups"]
                        self.TripData = config["TripData"]
                        self.SpdPlot = config["SpdPlot"]
                        self.Channels = config["Channels"]
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
            "TripData" : self.TripData,
            "SpdPlot" : self.SpdPlot,
            "Channels" : self.Channels
        }

        # Open file for writing.
        try:
            outfile = open("etscrape.json", 'w')
            outfile.write(json.dumps(cfgDict, sort_keys=False, indent=4, ensure_ascii=False))
            outfile.close()
        except Exception:
            print("Failed to create default configuration file : {0:s}".format('etscrape.json'))
