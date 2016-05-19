#!/usr/bin/env python
#     DStat Interface - An interface for the open hardware DStat potentiostat
#     Copyright (C) 2014  Michael D. M. Dryden -
#     Wheeler Microfluidics Laboratory <http://microfluidics.utoronto.ca>
#
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Creates data plot.
"""
from matplotlib.figure import Figure
import gtk
import matplotlib as mpl
import matplotlib.pyplot as plt
import si_prefix as si

#from matplotlib.backends.backend_gtkcairo\
#   import FigureCanvasGTKCairo as FigureCanvas
#from matplotlib.backends.backend_gtkcairo\
#   import NavigationToolbar2Cairo as NavigationToolbar
from matplotlib.backends.backend_gtkagg \
    import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg \
    import NavigationToolbar2GTKAgg as NavigationToolbar
try:
    import seaborn as sns
except ImportError:
    pass

from numpy import sin, linspace, pi, mean, trapz
from scipy import fft, arange
from dstat_interface.analysis import dstat_to_fft_frame


# Format float values as string w.r.t. amps, e.g., `A`, `mA`, `uA`, etc.
A_formatter = mpl.ticker.FuncFormatter(lambda x, pos:
                                       '{}A'.format(si.si_format(x)))


def plotSpectrum(y,Fs):
    """
    Plots a Single-Sided Amplitude Spectrum of y(t)
    """
    y = y-mean(y)
    n = len(y) # length of the signal
    k = arange(n)
    T = n/Fs
    frq = k/T # two sides frequency range
    frq = frq[range(n/2)] # one side frequency range
    Y = fft(y)/n # fft computing and normalization
    Y = abs(Y[range(n/2)])

    return (frq, Y)

def integrateSpectrum(x, y, target, bandwidth):
    """
    Returns integral of range of bandwidth centered on target (both in Hz).
    """
    j = 0
    k = len(x)

    for i in range(len(x)):
        if x[i] >= target-bandwidth/2:
            j = i
            break

    for i in range(j,len(x)):
        if x[i] >= target+bandwidth/2:
            k = i
            break

    return trapz(y=y[j:k], x=x[j:k])

def findBounds(y):
    start_index = 0;
    stop_index = len(y)-1;

    for i in range(len(y)):
        if (y[i] <= mean(y) and y[i+1] > mean(y)):
            start_index = i
            break

    for i in range(len(y)):
        if (y[-(i+1)] <= mean(y) and y[-i] > mean(y)):
            stop_index = len(y)-1-i  # len(y) is last index + 1
            break

    return (start_index, stop_index)


class PlotBox(object):
    """Contains main data plot and associated methods."""
    def __init__(self, plotwindow_instance):
        """Creates plot and moves it to a gtk container.

        Arguments:
        plotwindow_instance -- gtk container to hold plot.
        """

        self.figure = Figure()
        self.figure.subplots_adjust(left=0.07, bottom=0.07,
                                    right=0.96, top=0.96)
        self.axe1 = self.figure.add_subplot(111)

        self.axe1.plot([0, 1], [0, 1])

        self.axe1.ticklabel_format(style='sci', scilimits=(0, 3),
                                   useOffset=False, axis='y')

        self.canvas = FigureCanvas(self.figure)
        self.win = gtk.Window()
        self.vbox = gtk.VBox()
        self.win.add(self.vbox)
        self.vbox.pack_start(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.win)
        self.vbox.pack_start(self.toolbar, False, False)
        self.vbox.reparent(plotwindow_instance)

    def clearall(self):
        """Remove all lines on plot. """
        for i in range(len(self.axe1.lines)):
            self.axe1.lines.pop(0)
        self.addline()

    def clearline(self, line_number):
        """Remove a line specified by line_number."""
        self.lines[line_number].remove()
        self.lines.pop(line_number)

    def addline(self):
        """Add a new line to plot. (initialized with dummy data)))"""
        self.axe1.plot([0, 1], [0, 1])

    def updateline(self, Experiment, line_number):
        """Update a line specified by line_number with data stored in
        the Experiment instance.
        """
        # limits display to 2000 data points per line
        divisor = len(Experiment.data['data'][line_number][0]) // 2000 + 1

        self.axe1.lines[line_number].set_ydata(
                Experiment.data['data'][line_number][1][1::divisor])
        self.axe1.lines[line_number].set_xdata(
                Experiment.data['data'][line_number][0][1::divisor])
        # Format y-axis tick labels to be like `1.0nA`, `3.7mA`, etc.
        self.axe1.yaxis.set_major_formatter(A_formatter)

    def changetype(self, Experiment):
        """Change plot type. Set axis labels and x bounds to those stored
        in the Experiment instance. Stores class instance in Experiment.
        """
        self.axe1.set_xlabel(Experiment.xlabel)
        self.axe1.set_ylabel(Experiment.ylabel)
        self.axe1.set_xlim(Experiment.xmin, Experiment.xmax)

        Experiment.plots['data'] = self

        self.figure.canvas.draw()

    def redraw(self):
        """Autoscale and refresh the plot."""
        self.axe1.relim()
        self.axe1.autoscale(True, axis = 'y')
        self.figure.canvas.draw()

        return True

class FT_Box(PlotBox):
    def updateline(self, Experiment, line_number):
        def search_value(data, target):
            for i in range(len(data)):
                if data[i] > target:
                    return i

        y = Experiment.data['data'][line_number][1]
        x = Experiment.data['data'][line_number][0]
        freq = Experiment.parameters['adc_rate_hz']
        i = search_value(x, float(Experiment.parameters['fft_start']))
        y1 = y[i:]
        x1 = x[i:]
        avg = mean(y1)
        min_index, max_index = findBounds(y1)
        y1[min_index] = avg
        y1[max_index] = avg
        f, Y = plotSpectrum(y1[min_index:max_index],freq)
        self.axe1.lines[line_number].set_ydata(Y)
        self.axe1.lines[line_number].set_xdata(f)
        Experiment.data['ft'] = [(f, Y)]

    def changetype(self, Experiment):
        """Change plot type. Set axis labels and x bounds to those stored
        in the Experiment instance. Stores class instance in Experiment.
        """
        self.axe1.set_xlabel("Freq (Hz)")
        self.axe1.set_ylabel("|Y| (A/Hz)")
        self.axe1.set_xlim(0, Experiment.parameters['adc_rate_hz']/2)

        Experiment.plots['ft'] = self

        self.figure.canvas.draw()


def plot_dstat_data(df_data, settling_period_s=2., axes=None, label=None):
    '''
    Plot DStat experiment current measurement results.

    Args
    ----

        df_data (pandas.DataFrame) : DStat experiment results with at
            least the columns `time_s`, and `current_amps`.  For synchronous
            detection experiments the table must also include the columns
            `sample_frequency_hz`, `target_hz`.
        axes (list) : List of at least two `matplotlib` axes to plot to.  The
            first axis is used to plot the `current_amp` values.  The second
            axis is used to plot the FFT for experiments using synchronous
            detection. If `None`, axes are automatically created.

    Returns
    -------

        (list) : List of two `matplotlib` axes use for current amps and FFT
            plots, respectively.
    '''
    if axes is None:
        fig, axes = plt.subplots(2, figsize=(12, 8))

    # Get style properties to use for plot `i`.
    plot_props = axes[0]._get_lines.prop_cycler.next()
    # Plot measured DStat current at each time point.
    df_data.set_index('time_s').current_amps.plot(ax=axes[0], label=label,
                                                  **plot_props)

    # Compute median measured current.  The median helps to eliminate outliers.
    median = df_data.current_amps.median()
    # Plot median as a straight line.
    axes[0].plot(axes[0].get_xlim(), 2 * [median], linewidth=2, **plot_props)

    #     # Annotate the median with the name of the sample.
    #     axes[0].text(axes[0].get_xlim()[0], median, label, fontsize=14,
    #               color='black')

    # Format y-axes[0] tick labels to be like `1.0nA`, `3.7mA`, etc.
    axes[0].yaxis.set_major_formatter(A_formatter)

    if 'sample_frequency_hz' in df_data and (df_data.iloc[0]
                                             ['sample_frequency_hz'] > 0):
        # Synchronous detection (e.g., shuttered).
        #
        # Compute FFT of signal measured at specified sampling frequency.
        df_fft = dstat_to_fft_frame(df_data, sample_frequency_hz=
                                    df_data.iloc[0]['sample_frequency_hz'],
                                    settling_period_s=settling_period_s)
        df_fft.plot(x='frequency', y='amplitude', ax=axes[1], label=label)
    return axes
