#!/usr/bin/env python3

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# *******************************************
# Matplotlib plotting class
# *******************************************
class MplCanvas(FigureCanvasQTAgg):   
    def __init__(self, parent, config, logger, width, height, dpi):

        self.cfg = config
        self.logger = logger

        self.logger.debug("Mplanvas class constructor.")

        # Create Matplotlib figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        # Keep layout tight so that it fits into the frame nicely.
        self.fig.set_tight_layout(True)

        # Single plot with two line plots.
        # One line for speed, and one line for speed limit.        
        self.axes = self.fig.add_subplot(111)
        self.line, = self.axes.plot_date([], [], color=self.cfg.SpdPlot["SpeedColour"], marker='o', linestyle='solid', linewidth=1)
        self.zone, = self.axes.plot_date([], [], color=self.cfg.SpdPlot["ZoneColour"], marker=None, linestyle='dashed', linewidth=1)

        # Setup plot labels.
        self.axes.set_xlabel("Time", fontsize=self.cfg.SpdPlot["AxesTitleFontSize"])
        self.axes.set_ylabel("Speed", fontsize=self.cfg.SpdPlot["AxesTitleFontSize"])

        super(MplCanvas, self).__init__(self.fig)

    # *******************************************
    # Clear the figure.
    # Just by clearing the input data lists.
    # *******************************************
    def clearFigure(self):
        self.updatePlotData(0, [], [])

    # *******************************************
    # Update plot with new plot.
    # *******************************************
    def updatePlotData(self, No, tList, sList):

        # Add trip number as the plot title.
        self.axes.set_title("Trip {0:02d}".format(No), fontsize=self.cfg.SpdPlot["PlotTitleFontSize"])

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
