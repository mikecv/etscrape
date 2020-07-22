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
            # Add plot line with marker, although will only show markers for zero duration INPUT events.
            line, = axes.plot_date([], [], color=self.cfg.EvPlot["EventTraceColour"], linestyle='solid', marker='o', linewidth=1)
            # Set y axis range 0 to 1 for all subplots.
            axes.set_ylim([-0.2, 1.2])
            # Hide y axis ticks and tick labels.
            axes.set_yticks([])
            axes.set_yticklabels([])
            # Set y axis title to event name for trace.
            # Name in reverse so trace 1 ends up at the bottom.
            if self.cfg.EventTraces[self.numEvCharts - ev - 1]["Event"] == "INPUT":
                axes.set_ylabel("Input {0:d}".format(self.cfg.EventTraces[self.numEvCharts - ev - 1]["Channel"]), rotation=0, horizontalalignment='right', verticalalignment='center', fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
            else:
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
        # Trip end will correspond to TRIP event if one is included.
        # Look for TRIP event as we don't want to report much after that.
        endEvent = 0
        tripEnded = False
        for idx, ev in enumerate(self.data.tripLog[No-1].events):
            if ev.event == "TRIP":
                endEvent = idx
                tripEnded = True
        # Go an event after the TRIP event.
        # This should catch trip summary type events.
        endEvent += 1
        if endEvent > len(self.data.tripLog[No-1].events):
            endEvent = self.data.tripLog[No-1]

        # Look for last event in the trip (so far) and make this the end of the trip.
        tripEndTime = timeTZ(self.data.tripLog[No-1].events[endEvent - 1].serverTime, self.cfg.TimeUTC)
        tripDuration = self.data.tripLog[No-1].events[endEvent - 1].serverTime - self.data.tripLog[No-1].tripStart

        # Create start/end of chart. Make a bit wider than the trip.
        # Add 10% or some arbitrary time, whichever is less, to the trip.
        plotEntre = int(tripDuration * 0.1)
        if plotEntre > 60:
            plotEntre = 60

        # Plot start and end time.
        plotStartTime = timeTZ((self.data.tripLog[No-1].tripStart - plotEntre), self.cfg.TimeUTC)
        plotEndTime = timeTZ((self.data.tripLog[No-1].events[endEvent].serverTime + plotEntre), self.cfg.TimeUTC)

        # Create data for trip trace.
        tList = []
        eList = []
        tList.append(tripStartTime)
        eList.append(0)
        tList.append(tripStartTime)
        eList.append(1)
        if tripEnded:
            tList.append(tripEndTime)
            eList.append(1)
            tList.append(tripEndTime)
            eList.append(0)
        else:
            tList.append(plotEndTime)
            eList.append(1)

        # Clear old plot data.
        self.traces[0][0].set_xdata([])
        self.traces[0][0].set_ydata([])

        # Update plot data.
        self.traces[0][0].set_xdata(tList.copy())
        self.traces[0][0].set_ydata(eList.copy())

        # Fill in the event bars.
        self.traces[0][1].fill_between(self.traces[0][0].get_xdata(), self.traces[0][0].get_ydata(), 0, color=self.cfg.EvPlot["TripFillColour"], alpha=0.35)

        # Set axis for trace to trip extents.
        self.traces[0][1].set_xlim([plotStartTime, plotEndTime])

        # Create data for each event trace.
        # Iterate in reverse to line up with how traces have been stacked.
        for idx in range((self.numEvCharts - 1), -1, -1):
            t = self.cfg.EventTraces[idx]
            tList = []
            eList = []
            # Initilise list of special markers for zero duration INPUT events.
            # Need to keep track of points where zero duration INPUT events occur.
            # This is useful if there is a problem.
            nullMarkers = []
            markerIdx = 0
            # Initialise flag if we are dealing with an INPUT event.
            inputEv = False
            # Initialise trace started flag.
            traceStarted = False
            # See if any matching events for the trip.
            for ev in self.data.tripLog[No-1].events[0:endEvent]:
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
                                    markerIdx += 1
                                    finalState = 0
                                else:
                                    eList.append(1)
                                    markerIdx += 1
                                    finalState = 1
                                traceStarted = True
                            # Add start of event to trace. Need to check what state input has changed to.
                            if ev.inputState == 1:
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(finalState)
                                markerIdx += 1
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(1)
                                markerIdx += 1
                                finalState = 1
                            else:
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(finalState)
                                markerIdx += 1
                                tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                                eList.append(0)
                                markerIdx += 1
                                finalState = 0
                            # Check if we need to add a marker for a zero duration event.
                            # Note that active time is always 0 for transitions to the inactive state.
                            if (ev.activeTime == 0):
                                nullMarkers.append(markerIdx - 1)
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
                        finalState = 0

            # End trace with final state value to end of plot (if event trace was started that is).
            if traceStarted:
                tList.append(plotEndTime)
                eList.append(finalState)

            # Clear old plot data.
            self.traces[self.numEvCharts - idx][0].set_xdata([])
            self.traces[self.numEvCharts - idx][0].set_ydata([])

            # Update plot data.
            self.traces[self.numEvCharts - idx][0].set_xdata(tList.copy())
            self.traces[self.numEvCharts - idx][0].set_ydata(eList.copy())

            # Set axis for trace to trip extents.
            self.traces[self.numEvCharts - idx][1].set_xlim([plotStartTime, plotEndTime])

            # Only set markers where zero duration INPUT events have been detected.
            # Marker list will be empty for non-INPUT events.
            self.traces[self.numEvCharts - idx][0].set_markevery(nullMarkers)

            # Fill in the event bars.
            self.traces[self.numEvCharts - idx][1].fill_between(self.traces[self.numEvCharts - idx][0].get_xdata(), self.traces[self.numEvCharts - idx][0].get_ydata(), 0, color=self.cfg.EvPlot["EventFillColour"], alpha=0.35)

        # Draw plot.
        self.draw()
