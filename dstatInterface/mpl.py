#!/usr/bin/env python

import sys, serial, io
import numpy as np
import matplotlib
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas
import gtk
from time import sleep
from collections import deque
from matplotlib import pyplot as plt


# class that holds analog data for N samples
class AnalogData:
    # constr
    def __init__(self):
        self.ax = []
        self.ay = []
        self.first = 1
    
    # add data
    def add(self, data):
        if self.first == 1:
            self.first = 0
            return
        assert(len(data) == 2)
        self.ax.append(data[0])
        self.ay.append(data[1])

    # clear data
    def clear(self):
        self.first = 1
        self.ax = []
        self.ay = []


# plot class
class AnalogPlot:
    
    # constr
    def __init__(self, analogData):
        self.i = 0
        # set plot to animated
        plt.ion() #interactive mode on
        plt.autoscale(True,True,True)
        
        self.line = plt.plot(analogData.ax,analogData.ay)
    
    # update plot
    def update(self, analogData):
        if self.i < 5:
            self.i += 1
            return
        plt.setp(self.line,xdata=analogData.ax, ydata=analogData.ay)
        ax = plt.gca()

        # recompute the ax.dataLim
        ax.relim()
        # update ax.viewLim using the new dataLim
        ax.autoscale_view()
        plt.draw()
        self.i=0

# main() function
def main():
#    # expects 1 arg - serial port string
#    if(len(sys.argv) != 2):
#        print 'Example usage: python showdata.py "/dev/tty.usbmodem411"'
#        exit(1)

    #strPort = '/dev/tty.usbserial-A7006Yqh'
    #strPort = sys.argv[1];
    strPort = '/dev/tty.usbmodem12...E1'

    # open serial port
    ser = serial.Serial(strPort, 1024000,timeout=2)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser,ser,buffer_size=1),
                            newline = '\n',
                            line_buffering = True)
    ser.write("ck")

    # plot parameters
    digiData = AnalogData()
    digiPlot = AnalogPlot(digiData)

    try:
        while True:
            output = raw_input('Commands:')
            ser.flushInput() #clear input buffer
            digiData.clear() #clear old data
            ser.write(output)
            print output
            
            while True:
                for line in ser:
                    print line
                    if line.lstrip().startswith("no"):
                        ser.flushInput()
                        break
                    if not (line.isspace() or line.lstrip().startswith('#')):
                        #print line
                        data = [float(val) for val in line.split()]
                        if(len(data) == 2):
                            digiData.add(data)
                            digiPlot.update(digiData)

                break
#                if not line.lstrip().startswith('#'):
#                    data = [float(val) for val in line.split()]
##                    if(len(data) == 2):
##                        analogData.add(data)
##                        analogPlot.update(analogData)
#                    block.append(line)
#                    print line
#            print block
    except KeyboardInterrupt:
        print 'exiting'
    # close serial
    ser.flush()
    ser.close()

# call main
if __name__ == '__main__':
    main()