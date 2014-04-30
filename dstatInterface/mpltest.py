#!/usr/bin/env python
"""
    show how to add a matplotlib FigureCanvasGTK or FigureCanvasGTKAgg widget to a
    gtk.Window
    """
import gtk
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import numpy as np

#from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas
#from matplotlib.backends.backend_gtkcairo import NavigationToolbar2Cairo as NavigationToolbar
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

class plotbox:
    def __init__(self, plotwindow_instance):
        self.figure = Figure()
        self.figure.subplots_adjust(left=0.07, bottom=0.07, right=0.96, top=0.96)
        self.axe1 = self.figure.add_subplot(111)
        
        self.lines = self.axe1.plot([0,1], [0,1])
        
        self.axe1.ticklabel_format(style='sci', scilimits=(0,3), useOffset=False, axis='y')

        self.canvas = FigureCanvas(self.figure)
        self.win = gtk.Window()
        self.vbox = gtk.VBox()
        self.win.add(self.vbox)
        self.vbox.pack_start(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.win)
        self.vbox.pack_start(self.toolbar, False, False)
        self.vbox.reparent(plotwindow_instance)
    
    def clearall(self):
        for i in self.lines:
            i.remove()
        self.lines = self.axe1.plot([0,1], [0,1])
    
    def clearline(self, line_number):
        self.lines[line_number].remove()
        self.lines.pop(line_number)
    
    def addline(self):
        self.lines.append(self.axe1.plot([0,1], [0,1])[0])
    
    def updateline(self, Experiment, line_number):
        self.lines[line_number].set_ydata(Experiment.data[1+line_number*2][1:])
        self.lines[line_number].set_xdata(Experiment.data[line_number*2][1:])

    def changetype(self, Experiment):
        self.axe1.set_xlabel(Experiment.xlabel)
        self.axe1.set_ylabel(Experiment.ylabel)
        self.axe1.set_xlim(Experiment.xmin, Experiment.xmax)

        self.figure.canvas.draw()

    def redraw(self):
        self.axe1.relim()
        self.axe1.autoscale(True, axis = 'y')
        self.figure.canvas.draw()
        
