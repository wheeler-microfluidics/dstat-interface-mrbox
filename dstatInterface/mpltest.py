#!/usr/bin/env python
"""
    show how to add a matplotlib FigureCanvasGTK or FigureCanvasGTKAgg widget to a
    gtk.Window
    """
import gtk
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from numpy import arange, sin, pi

# uncomment to select /GTK/GTKAgg/GTKCairo
#from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas
from matplotlib.backends.backend_gtkcairo import NavigationToolbar2Cairo as NavigationToolbar

class plotbox:
    def __init__(self, xyData):
        self.figure = Figure()
        self.figure.subplots_adjust(left=0.07, bottom=0.07, right=0.96, top=0.96)
        self.axe1 = self.figure.add_subplot(111)

        self.line1, = self.axe1.plot(xyData.x, xyData.y)
    
        self.canvas = FigureCanvas(self.figure)
        self.win = gtk.Window()
        self.vbox = gtk.VBox()
        self.win.add(self.vbox)
        self.vbox.pack_start(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.win)
        self.vbox.pack_start(self.toolbar, False, False)

    def update(self, xyData):
        self.axe1.set_ydata(xyData.y)
        self.axe1.set_xdata(xyData.x)
        self.axe1.relim()
        ax.autoscale_view()
        
        self.figure.canvas.draw()

    def changetype(self, labels):
        self.axe1.set_xlabel(labels.x)
        self.axe1.set_ylabel(labels.y)

        self.figure.canvas.draw()
