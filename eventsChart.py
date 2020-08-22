#!/usr/bin/env python3

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes, Subplot
import matplotlib.dates as dates
from math import ceil, floor

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

        # Create Matplotlib figure.
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        # Keep layout tight so that it fits into the frame nicely.
        self.fig.set_tight_layout(True)

        # Set fig date/time formating for x-axis.
        self.fig.autofmt_xdate()
        self.xfmt = dates.DateFormatter('%H:%M:%S')

        # Create the axes for the plot.
        self.createAxes()
        super(EventCanvas, self).__init__(self.fig)

    # *******************************************
    # Create the axes for the chart.
    # *******************************************
    def createAxes(self):
        # Check to see how many event charts are configured.
        self.numEvCharts = len(self.cfg.EventTraces)
        self.logger.debug("Number of events chart traces: {0:d}".format(self.numEvCharts))

        # One line trace in each subplot for each event.
        self.traces = []

        # Create trace for trip.
        axes = self.fig.add_subplot(int("{0:d}{1:d}{2:d}".format((self.numEvCharts + 1), 1, (self.numEvCharts + 1))))
        line, = axes.plot_date([], [], color=self.cfg.EvPlot["TripTraceColour"], linestyle='solid', marker=None, linewidth=1)
        # Set y axis range 0 to 1 for all subplots.
        axes.set_ylim([-0.2, 1.2])
        # Hide y axis ticks and tick labels.
        axes.set_yticks([])
        axes.set_yticklabels([])
        # Set y axis title to "Trip"".
        axes.set_ylabel("Trip", rotation=0, horizontalalignment='right', verticalalignment='center', fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
        # Set x axis title and font.
        axes.set_xlabel("Time {0:s}".format(tzone(self.cfg.TimeUTC)), fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
        # Set axis label font.
        axes.tick_params(labelsize=self.cfg.EvPlot["AxisLabelFontSize"])
        # Set date/time format for x-axis.
        axes.xaxis.set_major_formatter(self.xfmt)
        # Add axis to list of axes.
        self.traces.append((line, axes))

        # Create trace for each event.
        for ev in range(self.numEvCharts):
            # Create trace for each event subplot.
            axes = self.fig.add_subplot(int("{0:d}{1:d}{2:d}".format((self.numEvCharts + 1), 1, (ev+1))))
            # Add plot line with marker, although will only show markers for zero duration INPUT events.
            line, = axes.plot_date([], [], color=self.cfg.EvPlot["EventTraceColour"], linestyle='solid', marker='.', linewidth=1)
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
                # Split title if too long for one line. Basic splitting to max line length.
                # Only appling line length limit to non-INPUT events.
                splitTitle = splitLongString(self.cfg.EventTraces[self.numEvCharts - ev - 1]["Title"], self.cfg.EvPlot["MaxTitleLineLength"])
                axes.set_ylabel(splitTitle, rotation=0, horizontalalignment='right', verticalalignment='center', fontsize=self.cfg.EvPlot["AxesTitleFontSize"])
            # Set axis label font.
            axes.tick_params(labelsize=self.cfg.EvPlot["AxisLabelFontSize"])
            # Set date/time format for x-axis.
            axes.xaxis.set_major_formatter(self.xfmt)
            # Add axis to list of axes.
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
        # Clear old plot data.
        for t in self.traces:
            t[0].set_xdata([])
            t[0].set_ydata([])

            # Rescale axes.
            t[1].relim()
            t[1].autoscale_view()

        # Add trip number as the plot title.
        self.fig.suptitle("Controller {0:d} Trip {1:d} [{2:d}]".format(self.data.controllerID, No, self.data.tripLog[No-1].signOnId), y=1.0, fontsize=self.cfg.EvPlot["PlotTitleFontSize"])

        # Get start and end trip times to use for all event plots.
        # Trip start will correspond to SIGNON event.
        tripStartTime = timeTZ(self.data.tripLog[No-1].tripStart, self.cfg.TimeUTC)
        # Trip end will correspond to TRIP event if one is included.
        # Look for TRIP event as we don't want to report after that.
        endEvent = 0
        tripEnded = False
        tripJustSignon = False
        if len(self.data.tripLog[No-1].events) == 1:
            tripJustSignon = True
        else:
            for idx, ev in enumerate(self.data.tripLog[No-1].events):
                if ev.event == "TRIP":
                    tripEnded = True
                    break
            endEvent = idx

        # Look for last event in the trip (so far) and make this the end of the trip.
        tripEndTime = timeTZ(self.data.tripLog[No-1].events[endEvent].serverTime, self.cfg.TimeUTC)
        tripDuration = self.data.tripLog[No-1].events[endEvent].serverTime - self.data.tripLog[No-1].tripStart

        # Create start/end of chart. Make a bit wider than the trip.
        # Add 10% or some arbitrary time, whichever is less, to the trip.
        plotEntre = int(tripDuration * 0.1)
        if plotEntre > 60:
            plotEntre = 60

        # Plot start and end time.
        self.plotStartTime = timeTZ((self.data.tripLog[No-1].tripStart - plotEntre), self.cfg.TimeUTC)
        self.plotEndTime = timeTZ((self.data.tripLog[No-1].events[endEvent].serverTime + plotEntre), self.cfg.TimeUTC)

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
            tList.append(self.plotEndTime)
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
        self.traces[0][1].set_xlim([self.plotStartTime, self.plotEndTime])

        # Rescale axes.
        self.traces[0][1].axes.relim()
        self.traces[0][1].autoscale_view(True, True, False)

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
            # Previous INPUT event time.
            preInputTime = 0

            # Don't need to check for 'special' "Vehicle" events as not real events.
            if (t["Event"] != "Vehicle Speed") and (t["Event"] != "Battery Voltage"):
                # See if any matching events for the trip.
                for ev in self.data.tripLog[No-1].events[0:endEvent]:
                    if t["Event"] == ev.event:
                        # Check if INPUT event as treated differently.
                        if ev.isInput:
                            # Event is an INPUT.
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
                                # So mark INPUT events to transition to inactive state if active time is 0,
                                # or if active state and previous transition time was the same.
                                if ev.inputState == 0:
                                    if ev.activeTime == 0:
                                        nullMarkers.append(markerIdx - 1)
                                else:
                                    if ev.serverTime == preInputTime:
                                        nullMarkers.append(markerIdx - 2)
                                # Save INPUT event time to compare with next INPUT event.
                                preInputTime = ev.serverTime
                        # Event is an IMPACT event.
                        # Show intensity on trace.
                        elif ev.event == "IMPACT":
                            if traceStarted == False:
                                # Start trace with start of trip.
                                tList.append(tripStartTime)
                                eList.append(0)
                                markerIdx += 1
                                traceStarted = True
                            # Found a matching event for this trace.
                            # Add start of event to trace. Event is at the end of events for events with a duration.
                            tList.append(timeTZ((ev.serverTime - ev.duration), self.cfg.TimeUTC))
                            eList.append(0)
                            markerIdx += 1
                            tList.append(timeTZ((ev.serverTime - ev.duration), self.cfg.TimeUTC))
                            # Set the height of the trace according to the severity (3 levels)
                            if ev.severity == 'C':
                                tLevel = 1.0
                            elif ev.severity == 'W':
                                tLevel = 0.6
                            else:
                                tLevel = 0.2
                            eList.append(tLevel)
                            markerIdx += 1
                            nullMarkers.append(markerIdx - 1)
                            # Add end of event to trace.
                            tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                            eList.append(tLevel)
                            markerIdx += 1
                            tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                            eList.append(0)
                            markerIdx += 1
                            finalState = 0
                        # Event is a ZONECHANGE event.
                        # Show zone output on trace.
                        elif ev.event == "ZONECHANGE":
                            if traceStarted == False:
                                # Start trace with start of trip.
                                tList.append(tripStartTime)
                                eList.append(0)
                                markerIdx += 1
                                traceStarted = True
                            # Found a matching event for this trace.
                            # Add start of event to trace. Event is at the end of events for events with a duration.
                            tList.append(timeTZ((ev.serverTime - ev.duration), self.cfg.TimeUTC))
                            eList.append(0)
                            markerIdx += 1
                            tList.append(timeTZ((ev.serverTime - ev.duration), self.cfg.TimeUTC))
                            # Set the height of the trace according to the zone output (2 levels)
                            if ev.zoneOutput == 1:
                                tLevel = 0.5
                            else:
                                tLevel = 1.0
                            eList.append(tLevel)
                            markerIdx += 1
                            nullMarkers.append(markerIdx - 1)
                            # Add end of event to trace.
                            tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                            eList.append(tLevel)
                            markerIdx += 1
                            tList.append(timeTZ(ev.serverTime, self.cfg.TimeUTC))
                            eList.append(0)
                            markerIdx += 1
                            finalState = 0
                        else:
                            # Event is not special, i.e. not INPUT, IMPACT, or ZONECHANGE event.
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
                    tList.append(tripEndTime)
                    eList.append(finalState)
            else:
                # Special vehicle event.
                if t["Event"] == "Vehicle Speed":
                    # Update speed data.
                    maxSpeed = 0
                    for sl in self.data.tripLog[No-1].speedLog:
                        # Format time axis list in the correct timezone for display.
                        tList.append(timeTZ(sl.time, self.cfg.TimeUTC))
                        eList.append(sl.speed)
                        # Get max speed for plot limits.
                        if sl.speed > maxSpeed:
                            maxSpeed = sl.speed
                elif t["Event"] == "Battery Voltage":
                    # Update battery voltage data.
                    minBattery = 100.0
                    maxBattery = 0.0
                    for bl in self.data.tripLog[No-1].batteryLevel:
                        # Format time axis list in the correct timezone for display.
                        tList.append(timeTZ(bl.time, self.cfg.TimeUTC))
                        eList.append(bl.battery)
                        # Get battery voltage for plot limits.
                        if bl.battery > maxBattery:
                            maxBattery = bl.battery
                        if bl.battery < minBattery:
                            minBattery = bl.battery

            # Clear old plot data.
            self.traces[self.numEvCharts - idx][0].set_xdata([])
            self.traces[self.numEvCharts - idx][0].set_ydata([])

            # Update plot data.
            self.traces[self.numEvCharts - idx][0].set_xdata(tList.copy())
            self.traces[self.numEvCharts - idx][0].set_ydata(eList.copy())

            # Set axis for trace to trip extents.
            self.traces[self.numEvCharts - idx][1].set_xlim([self.plotStartTime, self.plotEndTime])

            # Rescale axes.
            self.traces[self.numEvCharts - idx][1].axes.relim()
            self.traces[self.numEvCharts - idx][1].autoscale_view(True, True, False)

            # Only set markers where zero duration INPUT events have been detected.
            # Marker list will be empty for non-INPUT events.
            self.traces[self.numEvCharts - idx][0].set_markevery(nullMarkers)

            # Set up shading etc for plots, special for vehicle speed plots.
            if t["Event"] == "Vehicle Speed":
                # Work out y-axis labels (5) for speed range.
                yinc = ceil(maxSpeed / 4.0)
                ymax = yinc * 5
                yticks = []
                yLabels = []
                for tck in range(0, 5):
                    yticks.append(tck * yinc)
                    yLabels.append("{0:d}".format(tck * yinc))
                # Set y axis limits and labels.
                self.traces[self.numEvCharts - idx][1].set_ylim([0, ymax])
                self.traces[self.numEvCharts - idx][1].set_yticks(yticks)
                self.traces[self.numEvCharts - idx][1].set_yticklabels(yLabels, color='cornflowerblue')
                self.traces[self.numEvCharts - idx][1].yaxis.grid(which='major', linestyle='-', linewidth='0.5', color='lightsteelblue')
            elif t["Event"] == "Battery Voltage":
                # Work out y-axis labels (5) for battery voltage range range.
                ymin = minBattery - 0.25
                ymax = maxBattery + 0.25
                yinc = (ymax - ymin) / 4.0
                yticks = []
                yLabels = []
                for tck in range(0, 5):
                    yticks.append(ymin + (tck * yinc))
                    yLabels.append("{0:2.2f}".format(ymin + (tck * yinc)))
                # Set y axis limits and labels.
                self.traces[self.numEvCharts - idx][1].set_ylim([ymin, ymax])
                self.traces[self.numEvCharts - idx][1].set_yticks(yticks)
                self.traces[self.numEvCharts - idx][1].set_yticklabels(yLabels, color='cornflowerblue')
                self.traces[self.numEvCharts - idx][1].yaxis.grid(which='major', linestyle='-', linewidth='0.5', color='lightsteelblue')
            else:
                # Fill in the event bars.
                self.traces[self.numEvCharts - idx][1].fill_between(self.traces[self.numEvCharts - idx][0].get_xdata(), self.traces[self.numEvCharts - idx][0].get_ydata(), 0, color=self.cfg.EvPlot["EventFillColour"], alpha=0.35)

            # Do special axis treatments for particular events.
            if t["Event"] == "IMPACT":
                self.traces[self.numEvCharts - idx][1].set_yticks([0.2, 0.6, 1.0])
                self.traces[self.numEvCharts - idx][1].set_yticklabels(["Lo", "Med", "Hi"], color='cornflowerblue')
                self.traces[self.numEvCharts - idx][1].yaxis.grid(which='major', linestyle='-', linewidth='0.5', color='lightsteelblue')
            elif t["Event"] == "ZONECHANGE":
                self.traces[self.numEvCharts - idx][1].set_yticks([0.5, 1.0])
                self.traces[self.numEvCharts - idx][1].set_yticklabels(["Slow", "Fast"], color='cornflowerblue')
                self.traces[self.numEvCharts - idx][1].yaxis.grid(which='major', linestyle='-', linewidth='0.5', color='lightsteelblue')

        # Draw plot.
        self.draw()

    # *******************************************
    # Aline x-axis plots to most restrictive.
    # *******************************************
    def alignEventTraces(self):

        firstTrace = True

        # Get most restrictive x-axis scale.
        for idx in range((self.numEvCharts - 1), -1, -1):
            txMin, txMax = self.traces[self.numEvCharts - idx][1].get_xlim()
            if firstTrace:
                # Initialise limits to that of first trace.
                xMin = txMin
                xMax = txMax
                firstTrace = False
            else:
                # Set if more restrictive.
                if txMin > xMin:
                    xMin = txMin
                if txMax < xMax:
                    xMax = txMax
        # Set all x-axis to new scale.
        for idx in range((self.numEvCharts - 1), -1, -1):
            self.traces[self.numEvCharts - idx][1].set_xlim([xMin, xMax])

            # Rescale axes.
            self.traces[self.numEvCharts - idx][1].axes.relim()
            self.traces[self.numEvCharts - idx][1].autoscale_view(True, True, False)

        # Set trace for trip to the same x scale too.
        self.traces[0][1].set_xlim([xMin, xMax])

        # Rescale axes.
        self.traces[0][1].axes.relim()
        self.traces[0][1].autoscale_view(True, True, False)

        # Draw plot.
        self.draw()
