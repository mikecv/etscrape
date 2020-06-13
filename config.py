#!/usr/bin/env python3

import json

# *******************************************
# Program config class
# *******************************************
class Config():
    # Initializer / Instance Attributes
    def __init__(self):

        # Version of configuration.
        self.ConfigVersion = 1

        # Program configuration values
        self.DebugLevel = 20
        self.LogFileSize = 100000
        self.LogBackups = 3
        self.TripPrefix = "Trip"
        self.TripBackColour = "#ffff00"
        self.EventColour = "#0000ff"
        self.AlertColour = "#ff0000"
        self.SummaryAlertColour = "#0000ff"
        self.ShowOtherEvents = 1
        self.OtherEventColour = "#99990C"

        # Read / update configuration from file.
        self.readConfig()

    # *******************************************
    # Read Json configuration file.
    # *******************************************
    def readConfig(self):
        try:
            with open('etscrape.json') as config_file:
                config = json.load(config_file)

                # Update configuration values if possible.
                # If not, just update with default + whatever values read.
                try:
                    self.DebugLevel = config["DebugLevel"]
                    self.LogFileSize = config["LogFileSize"]
                    self.LogBackups = config["LogBackups"]
                    self.TripPrefix = config["TripData"]["TripPrefix"]
                    self.TripBackColour = config["TripData"]["TripBackColour"]
                    self.EventColour = config["TripData"]["EventColour"]
                    self.AlertColour = config["TripData"]["AlertColour"]
                    self.SummaryAlertColour = config["TripData"]["SummaryAlertColour"]
                    self.ShowOtherEvents = config["TripData"]["ShowOtherEvents"]
                    self.OtherEventColour = config["TripData"]["OtherEventColour"]
                except Exception:
                    print("Error reading configuration file.")
                    # Create default configuration file.
                    self.saveConfig()

                # Check configuration version.
                # If version not a match then just update.
                if config["ConfigVersion"] != self.ConfigVersion:
                    self.saveConfig()

        except Exception:
            print("Error opening configuration file.")
            # Create default configuration file.
            self.saveConfig()

    # *******************************************
    # Save Json configuration file.
    # *******************************************
    def saveConfig(self):

        # Format configuration data.
        tripList = {
            "TripPrefix" : self.TripPrefix,
            "TripBackColour" : self.TripBackColour,
            "EventColour" : self.EventColour,
            "AlertColour" : self.AlertColour,
            "SummaryAlertColour" : self.SummaryAlertColour,
            "ShowOtherEvents" : self.ShowOtherEvents,
            "OtherEventColour" : self.OtherEventColour
        }
        mainList = {
            "ConfigVersion" : self.ConfigVersion,
            "DebugLevel" : self.DebugLevel,
            "LogFileSize" : self.LogFileSize,
            "LogBackups" : self.LogBackups,
            "TripData" : tripList
        }

        # Open file for writing.
        try:
            outfile = open("etscrape.json", 'w')
            outfile.write(json.dumps(mainList, sort_keys=False, indent=4, ensure_ascii=False))
            outfile.close()
        except Exception:
            print("Failed to create default configuration file : {0:s}".format('etscrape.json'))
