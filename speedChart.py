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

        # Set fig date/time formating for x-axis.
        self.fig.autofmt_xdate()
        self.xfmt = dates.DateFormatter('%H:%M:%S')

        # Keep layout tight so that it fits into the frame nicely.
        self.fig.set_tight_layout(True)

        # Create the axes for the plot.
        self.createAxes()

        super(SpeedCanvas, self).__init__(self.fig)

    # *******************************************
    # Create the axes for the chart.
    # *******************************************
    def createAxes(self):
        self.axes = self.fig.add_subplot(111)
        self.line, = self.axes.plot_date([], [], color=self.cfg.SpdPlot["SpeedColour"], marker='o', linestyle='solid', linewidth=1)
        self.zone, = self.axes.plot_date([], [], color=self.cfg.SpdPlot["ZoneColour"], marker=None, linestyle='dashed', linewidth=1)
        # Set date/time format for x-axis.
        self.axes.xaxis.set_major_formatter(self.xfmt)

        # Setup plot labels.
        self.axes.set_xlabel("Time {0:s}".format(tzone(self.cfg.TimeUTC)), fontsize=self.cfg.SpdPlot["AxesTitleFontSize"])
        self.axes.set_ylabel("Speed", fontsize=self.cfg.SpdPlot["AxesTitleFontSize"])

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
        self.axes.set_title("Trip {0:d} [{1:d}]".format(No, self.data.tripLog[No-1].signOnId), fontsize=self.cfg.SpdPlot["PlotTitleFontSize"])

        tList = []
        sList = []

        # Update speed data.
        for sl in self.data.tripLog[No-1].speedLog:
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

        # Update zone data.
        for zl in self.data.tripLog[No-1].zoneXings:
            # Format time axis list in the correct timezone for display.
            tList.append(timeTZ(zl.time, self.cfg.TimeUTC))
            if zl.zoneOutput == 1:
                # Slow zone.
                zList.append(self.cfg.SpdPlot["DefaultLowLimit"])
            elif zl.zoneOutput == 2:
                # Fast zone.
                zList.append(self.cfg.SpdPlot["DefaultHiLimit"])
            else:
                # Open zone.
                zList.append(0)

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
