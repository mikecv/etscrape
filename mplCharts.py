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

        # Single chart.        
        self.axes = self.fig.add_subplot(111)
        self.line, = self.axes.plot_date([], [], color=self.cfg.SpdPlot["SpeedColour"], marker='o', linestyle='solid', linewidth=1)
        
        super(MplCanvas, self).__init__(self.fig)

    # *******************************************
    # Update plot with new plot.
    # *******************************************
    def updatePlotData(self, tList, sList):
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
    def drawSpeedLimits(self, lim1, lim2):
        self.axes.axhline(lim1, color=self.cfg.SpdPlot["SpdLimLowColour"], linestyle='dashed', linewidth=1, alpha=0.5)
        self.axes.axhline(lim2, color=self.cfg.SpdPlot["SpdLimHiColour"], linestyle='dashed', linewidth=1, alpha=0.5)

    # *******************************************
    # Shade zone overspeed areas on plot.
    # *******************************************
    def shadeOverspeedZones(self):
        pass
