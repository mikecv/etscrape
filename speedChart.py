#!/usr/bin/env python3

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates
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

    # *******************************************
    # Update plot with new plot.
    # *******************************************
    def updatePlotData(self, No, tList, sList):

        # Add trip number as the plot title.
        self.axes.set_title("Trip {0:d} [{1:d}]".format(No, self.data.tripLog[No-1].signOnId), fontsize=self.cfg.SpdPlot["PlotTitleFontSize"])

        # Clear old plot data.
        self.line.set_xdata([])
        self.line.set_ydata([])

        # Update plot data.
        self.line.set_xdata(tList)
        self.line.set_ydata(sList)

        # Rescale axes.
        self.axes.relim()
        self.axes.autoscale_view()

        # Draw plot.
        self.draw()

    # *******************************************
    # Draw zone speed limit lines on plot.
    # *******************************************
    def drawSpeedLimits(self, tList, zList):
        # Clear old zone data.
        self.zone.set_xdata([])
        self.zone.set_ydata([])

        # Update zone data.
        self.zone.set_xdata(tList)
        self.zone.set_ydata(zList)

        # Fill below the zone speed line (if we have data).
        if len(zList) > 0:
            self.axes.fill_between(self.zone.get_xdata(), self.zone.get_ydata(), 0, color=self.cfg.SpdPlot["ZoneColour"], alpha=0.1)

        # Rescale axes.
        self.axes.relim()
        self.axes.autoscale_view()

        # Draw plot.
        self.draw()