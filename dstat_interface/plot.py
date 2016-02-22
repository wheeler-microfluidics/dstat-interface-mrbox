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
import gtk
from matplotlib.figure import Figure

#from matplotlib.backends.backend_gtkcairo\
#   import FigureCanvasGTKCairo as FigureCanvas
#from matplotlib.backends.backend_gtkcairo\
#   import NavigationToolbar2Cairo as NavigationToolbar
from matplotlib.backends.backend_gtkagg \
    import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg \
    import NavigationToolbar2GTKAgg as NavigationToolbar
    
from numpy import sin, linspace, pi, mean, trapz
from scipy import fft, arange
from scipy.signal import blackman

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
    W = blackman(n)
    Y = fft(y*W)/n # fft computing and normalization
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
    
    
class plotbox(object):
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
        
        self.lines = self.axe1.plot([0, 1], [0, 1])
        
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
        for i in self.lines:
            i.remove()
        self.lines = self.axe1.plot([0, 1], [0, 1])
    
    def clearline(self, line_number):
        """Remove a line specified by line_number."""
        self.lines[line_number].remove()
        self.lines.pop(line_number)
    
    def addline(self):
        """Add a new line to plot. (initialized with dummy data)))"""
        self.lines.append(self.axe1.plot([0, 1], [0, 1])[0])
    
    def updateline(self, Experiment, line_number):
        """Update a line specified by line_number with data stored in
        the Experiment instance.
        """
        # limits display to 2000 data points per line
        divisor = len(Experiment.data[1+line_number*2]) // 2000 + 1
        
        self.lines[line_number].set_ydata(
                                   Experiment.data[1+line_number*2][1::divisor])
        self.lines[line_number].set_xdata(
                                   Experiment.data[line_number*2][1::divisor])

    def changetype(self, Experiment):
        """Change plot type. Set axis labels and x bounds to those stored
        in the Experiment instance.
        """
        self.axe1.set_xlabel(Experiment.xlabel)
        self.axe1.set_ylabel(Experiment.ylabel)
        self.axe1.set_xlim(Experiment.xmin, Experiment.xmax)

        self.figure.canvas.draw()

    def redraw(self):
        """Autoscale and refresh the plot."""
        self.axe1.relim()
        self.axe1.autoscale(True, axis = 'y')
        self.figure.canvas.draw()

        return True

class ft_box(plotbox):
    def updateline(self, Experiment, line_number):
        def search_value(data, target):
            for i in range(len(data)):
                if data[i] > target:
                    return i
        
        y = Experiment.data[1+line_number*2]
        x = Experiment.data[line_number*2]
        freq = Experiment.parameters['adc_rate_hz']
        i = search_value(x, Experiment.parameters['fft_start'])
        
        f, Y = plotSpectrum(y[i:],freq)
        Experiment.ft_int = integrateSpectrum(
                                f,
                                Y,
                                Experiment.parameters['sync_freq'],
                                Experiment.parameters['fft_int']
                                )
        self.lines[line_number].set_ydata(Y)
        self.lines[line_number].set_xdata(f)
        Experiment.ftdata = (f, Y)
        
    def changetype(self, Experiment):
        """Change plot type. Set axis labels and x bounds to those stored
        in the Experiment instance.
        """
        self.axe1.set_xlabel("Freq (Hz)")
        self.axe1.set_ylabel("|Y| (A/Hz)")
        self.axe1.set_xlim(0, Experiment.parameters['adc_rate_hz']/2)

        self.figure.canvas.draw()
                                
        
