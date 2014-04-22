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

class plotbox:
    def __init__(self, xyData):
        plt.ion()
        plt.autoscale(True,True,True)
        
        self.figure = Figure(figsize=(5,4), dpi=100)
        self.axe1 = self.figure.add_subplot(111)

        self.line1, = self.axe1.plot(xyData.x, xyData.y)
    
        self.canvas = FigureCanvas(self.figure)
        self.win = gtk.Window()
        self.win.add(self.canvas)

    def update(self, xyData):
        self.line1.set_ydata(xyData.y)
        self.line1.set_xdata(xyData.x)
        self.axe1.relim()
        ax.autoscale_view()
        
        self.figure.canvas.draw()
