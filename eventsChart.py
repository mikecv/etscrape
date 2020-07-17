#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from utils import *

# *******************************************
# Events chart class
# *******************************************
class EventCanvas(FigureCanvasQTAgg):   
    def __init__(self, data, config, logger, width, height, dpi):
        
        self.data = data
        self.cfg = config
        self.logger = logger

        self.logger.debug("EventCanvas class constructor.")

        # Check to see how many event charts are configured.
        self.numEvCharts = len(self.cfg.EventTraces)
        self.logger.debug("Number of events chart traces: {0:d}".format(self.numEvCharts))

        # Create Matplotlib figure.
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        # Keep layout tight so that it fits into the frame nicely.
        self.fig.set_tight_layout(True)

        # Create the axes for the plot.
        self.createAxes()

        super(EventCanvas, self).__init__(self.fig)

    # *******************************************
    # Create the axes for the chart.
    # *******************************************
    def createAxes(self):
        # One line trace in each subplot for each event.
        self.traces = []

        # Create trace for trip.
        axes = self.fig.add_subplot(int("{0:d}{1:d}{2:d}".format((self.numEvCharts + 1), 1, (self.numEvCharts + 1))))
        line, = axes.plot_date([], [], color=self.cfg.EvPlot["TripTraceColour"], linestyle='solid', marker=None, linewidth=1)
        # Set y axis range 0 to 1 for all subplots.
        axes.set_ylim([0, 1])
        # Hide y axis ticks and tick labels.
        axes.set_yticks([])
        axes.set_yticklabels([])
        # Set y axis title to "Trip"".
        axes.set_ylabel("Trip", rotation=0, horizontalalignment='right', verticalalignment='center', fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
        # Set x axis title and font.
        axes.set_xlabel("Time {0:s}".format(tzone(self.cfg.TimeUTC)), fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
        axes.tick_params(labelsize=self.cfg.EvPlot["AxisLabelFontSize"])
        self.traces.append((line, axes))

        # Create trace for each event.
        for ev in range(self.numEvCharts):
            # Create trace for each event subplot.
            axes = self.fig.add_subplot(int("{0:d}{1:d}{2:d}".format((self.numEvCharts + 1), 1, (ev+1))))
            line, = axes.plot_date([], [], color=self.cfg.EvPlot["EventTraceColour"], linestyle='solid', marker=None, linewidth=1)
            # Set y axis range 0 to 1 for all subplots.
            axes.set_ylim([0, 1])
            # Hide y axis ticks and tick labels.
            axes.set_yticks([])
            axes.set_yticklabels([])
            # Set y axis title to event name for trace.
            # Name in reverse so trace 1 ends up at the bottom.
            axes.set_ylabel(self.cfg.EventTraces[self.numEvCharts - ev - 1]["Title"], rotation=0, horizontalalignment='right', verticalalignment='center', fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
            # Set x axis title and font.
            axes.set_xlabel("Time {0:s}".format(tzone(self.cfg.TimeUTC)), fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
            axes.tick_params(labelsize=self.cfg.EvPlot["AxisLabelFontSize"])
            self.traces.append((line, axes))

    # *******************************************
    # Clear the figure.
    # Clear data, the current axes and then create new axes.
    # *******************************************
    def clearFigure(self):
            # Clear the axes and create afresh.
            for t in self.traces:
                t[1].clear()
            self.createAxes()

    # *******************************************
    # Update plot with new plot.
    # *******************************************
    def updatePlotData(self, No):
        # Clear old plot data.
        for t in self.traces:
            t[0].set_xdata([])
            t[0].set_ydata([])

            # Rescale axes.
            t[1].relim()
            t[1].autoscale_view()

        # Add trip number as the plot title.
        self.fig.suptitle("Trip {0:d} [{1:d}]".format(No, self.data.tripLog[No-1].signOnId), y=1.0, fontsize=self.cfg.EvPlot["PlotTitleFontSize"])

        # Get start and end trip times to use for all event plots.
        # Trip start will correspond to SIGNON event.
        tripStartTime = timeTZ(self.data.tripLog[No-1].tripStart, self.cfg.TimeUTC)
        plotStartTime = timeTZ((self.data.tripLog[No-1].tripStart - 60), self.cfg.TimeUTC)
        # Trip end will correspond to TRIP event if one is included.
        if self.data.tripLog[No-1].tripEnd == 0:
            # Look for last event in the trip (so far) and make this the end of the trip.
            tripEndTime = timeTZ(self.data.tripLog[No-1].events[-1].serverTime, self.cfg.TimeUTC)
            plotEndTime = timeTZ((self.data.tripLog[No-1].events[-1].serverTime + 60), self.cfg.TimeUTC)
        else:
            tripEndTime = timeTZ(self.data.tripLog[No-1].tripEnd, self.cfg.TimeUTC)
            plotEndTime = timeTZ((self.data.tripLog[No-1].tripEnd + 60), self.cfg.TimeUTC)

        # Create data for trip trace.
        tList = []
        eList = []
        tList.append(tripStartTime)
        eList.append(0)
        tList.append(tripStartTime)
        eList.append(1)
        tList.append(tripEndTime)
        eList.append(1)
        tList.append(tripEndTime)
        eList.append(0)

        # Clear old plot data.
        self.traces[0][0].set_xdata([])
        self.traces[0][0].set_ydata([])

        # Update plot data.
        self.traces[0][0].set_xdata(tList.copy())
        self.traces[0][0].set_ydata(eList.copy())

        # Fill in the event bars.
        self.traces[0][1].fill_between(self.traces[0][0].get_xdata(), self.traces[0][0].get_ydata(), 0, color=self.cfg.EvPlot["TripFillColour"], alpha=0.5)

        # Set axis for trace to trip extents.
        self.traces[0][1].set_xlim([plotStartTime, plotEndTime])

        # Create data for each event trace.
        # Iterate in reverse to line up with how traces have been stacked.
        for idx in range((self.numEvCharts - 1), -1, -1):
            t = self.cfg.EventTraces[idx]
            tList = []
            eList = []
            # Initialise flag if we are dealing with an INPUT event.
            inputEv = False
            # Initialise trace started flag.
            traceStarted = False
            # See if any matching events for the trip.
            for ev in self.data.tripLog[No-1].events:
                if t["Event"] == ev.event:
                    # Check if INPUT event as treated differently.
                    if ev.isInput:
                        if int(t["Channel"]) == ev.inputNo:
                            inputEv = True
                            # Found a matching event for this event INPUT channel.
                            # Check if we need to start the trace.
                            if traceStarted == False:
                                # Start trace with start of trip.
                                tList.append(tripStartTime)
                                if ev.inputState == 1:
                                    eList.append(0)
                                else:
                                    eList.append(1)
                                traceStarted = True
                            # Add start of event to trace. Need to check what state input has changed to.
                            if ev.inputState == 1:
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(0)
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(1)
                                finalState = 1
                            else:
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(1)
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(0)
                                finalState = 0
                    else:
                        # Check if we need to start the trace.
                        if traceStarted == False:
                            # Start trace with start of trip.
                            tList.append(tripStartTime)
                            eList.append(0)
                            traceStarted = True
                        # Found a matching event for this trace.
                        # Add start of event to trace. Event is at the end of events for events with a duration.
                        tList.append(timeTZ((ev.serverTime - ev.duration), self.cfg.TimeUTC))
                        eList.append(0)
                        tList.append(timeTZ((ev.serverTime - ev.duration), self.cfg.TimeUTC))
                        eList.append(1)
                        # Add end of event to trace.
                        tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                        eList.append(1)
                        tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                        eList.append(0)

            # End trace with end of trip.
            if inputEv:
                tList.append(tripEndTime)
                eList.append(finalState)
            else:
                tList.append(tripEndTime)
                eList.append(0)

            # Clear old plot data.
            self.traces[self.numEvCharts - idx][0].set_xdata([])
            self.traces[self.numEvCharts - idx][0].set_ydata([])

            # Update plot data.
            self.traces[self.numEvCharts - idx][0].set_xdata(tList.copy())
            self.traces[self.numEvCharts - idx][0].set_ydata(eList.copy())

            # Set axis for trace to trip extents.
            self.traces[self.numEvCharts - idx][1].set_xlim([plotStartTime, plotEndTime])

            # Fill in the event bars.
            self.traces[self.numEvCharts - idx][1].fill_between(self.traces[self.numEvCharts - idx][0].get_xdata(), self.traces[self.numEvCharts - idx][0].get_ydata(), 0, color=self.cfg.EvPlot["EventFillColour"], alpha=0.5)

        # Draw plot.
        self.draw()
