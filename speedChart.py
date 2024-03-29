#!/usr/bin/env python3

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.dates as dates

from utils import *

# *******************************************
# Speed plotting class
# *******************************************
class SpeedCanvas(FigureCanvasQTAgg):   
    def __init__(self, data, config, logger, width, height, dpi):

        self.data = data
        self.cfg = config
        self.logger = logger

        self.logger.debug("SpeedCanvas class constructor.")

        # Create Matplotlib figure.
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        # Keep layout tight so that it fits into the frame nicely.
        self.fig.set_tight_layout(True)

        # Set fig date/time formating for x-axis.
        self.fig.autofmt_xdate()

        # Create the axes for the plot.
        self.createAxes()

        super(SpeedCanvas, self).__init__(self.fig)

    # *******************************************
    # Create the axes for the chart.
    # *******************************************
    def createAxes(self):
        self.axes = self.fig.add_subplot(111)
        self.line, = self.axes.plot_date([], [], color=self.cfg.SpdPlot["SpeedColour"], marker='.', linestyle='solid', linewidth=1)
        self.zone, = self.axes.plot_date([], [], color=self.cfg.SpdPlot["ZoneColour"], marker=None, linestyle='dashed', linewidth=1)

        # Setup plot labels.
        self.axes.set_xlabel("Time {0:s}".format(tzone(self.cfg.TimeUTC)), fontsize=self.cfg.SpdPlot["AxesTitleFontSize"])
        self.axes.set_ylabel("Speed", fontsize=self.cfg.SpdPlot["AxesTitleFontSize"])
        self.axes.yaxis.grid(which='major', linestyle='-', linewidth='0.5', color='lightsteelblue')

    # *******************************************
    # Clear the figure.
    # Clear data, the current axes and then create new axes.
    # *******************************************
    def clearFigure(self):
        # Clear the axes and create afresh.
        self.axes.clear()
        self.createAxes()

        # Draw plot.
        self.draw()

    # *******************************************
    # Reset the figure.
    # Clear the figure and recreate blnak axis.
    # Used when there is no data to plot.
    # *******************************************
    def resetFigure(self):
        # Clear figure and recreate axis.
        self.fig.clf()
        self.createAxes()

        # Draw plot.
        self.draw()

    # *******************************************
    # Update plot with new plot.
    # *******************************************
    def updatePlotData(self, No):
        # Add trip number as the plot title.
        if self.data.isZoner == False:
            self.axes.set_title("Trip {0:d} [{1:d}]".format(No, self.data.tripLog[No-1].tripStartId), fontsize=self.cfg.SpdPlot["PlotTitleFontSize"])
        else:
            self.axes.set_title("Ignition Cycle {0:d}".format(No), fontsize=self.cfg.SpdPlot["PlotTitleFontSize"])

        tList = []
        sList = []

        # Update speed data.
        if self.data.isZoner == False:
            for sl in self.data.tripLog[No-1].speedLog:
                # Format time axis list in the correct timezone for display.
                tList.append(timeTZ(sl.time, self.cfg.TimeUTC))
                sList.append(sl.speed)
        else:
            for sl in self.data.zoneXLog[No-1].speedLog:
                # Format time axis list in the correct timezone for display.
                tList.append(timeTZ(sl.time, self.cfg.TimeUTC))
                sList.append(sl.speed)

        # Clear old plot data.
        self.line.set_xdata([])
        self.line.set_ydata([])

        # Update plot data.
        self.line.set_xdata(tList)
        self.line.set_ydata(sList)

        # Rescale axes.
        self.axes.relim()
        self.axes.autoscale_view(True, True, True)

        # Draw plot.
        self.draw()

    # *******************************************
    # Draw zone speed limit lines on plot.
    # *******************************************
    def drawSpeedLimits(self, No):
        tList = []
        zList = []

        if self.data.isZoner == False:
            tObj = self.data.tripLog[No-1]
        else:
            tObj = self.data.zoneXLog[No-1]

        # Add zone crossings.
        for zl in tObj.zoneXings:
            # Format time axis list in the correct timezone for display.
            tList.append(timeTZ(zl.time, self.cfg.TimeUTC))
            # Plot the zone change trace.
            # There are 4 speed zones plus one open speed zone (at the start).
            # Speed zone 0 is the open speed zone, followed by the 4 speed zones.
            zList.append(self.cfg.SpdPlot["zoneSpeed"][zl.zoneOutput])

        # Clear old zone data.
        self.zone.set_xdata([])
        self.zone.set_ydata([])

        # Update zone data.
        self.zone.set_xdata(tList)
        self.zone.set_ydata(zList)

        # Fill below the zone speed line (if we have data).
        if len(zList) > 0:
            self.axes.fill_between(self.zone.get_xdata(), self.zone.get_ydata(), 0, color=self.cfg.SpdPlot["ZoneColour"], alpha=0.1)

        # Draw plot.
        self.draw()
