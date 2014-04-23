#!/usr/bin/env python

import serial, io
from serial.tools import list_ports

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

class SerialDevices:
    def __init__(self):
        self.ports, _, _ = zip(*list_ports.comports())
    
    def refresh(self):
        self.ports, _, _ = zip(*list_ports.comports())

def chronoamp(adc_buffer, adc_rate, adc_pga, gain, potential, time):
    s = "A "
    s += (adc_buffer)
    s += " "
    s += (adc_rate)
    s += " "
    s += (adc_pga)
    s += " G "
    s += (gain)
    s += " R "
    s += str(len(potential))
    s += " "
    for i in potential:
        s += str(i)
        s += " "
    for i in time:
        s += str (i)
        s += " "
    print s

def lsv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, slope):
    s = "A "
    s += (adc_buffer)
    s += " "
    s += (adc_rate)
    s += " "
    s += (adc_pga)
    s += " G "
    s += (gain)
    s += " L "
    s += str(start)
    s += " "
    s += str(stop)
    s += " "
    s += str(slope)
    print s
#    print ("L ", adc_buffer, adc_rate, adc_pga, gain, start, stop, slope)

def cv_exp(adc_buffer, adc_rate, adc_pga, gain, v1, v2, start, scans, slope):
    s = "A "
    s += (adc_buffer)
    s += " "
    s += (adc_rate)
    s += " "
    s += (adc_pga)
    s += " G "
    s += (gain)
    s += " C "
    s += str(v1)
    s += " "
    s += str(v2)
    s += " "
    s += str(start)
    s += " "
    s += str(scans)
    s += " "
    s += str(slope)
    print s

def swv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, step, pulse, freq):
    s = "A "
    s += (adc_buffer)
    s += " "
    s += (adc_rate)
    s += " "
    s += (adc_pga)
    s += " G "
    s += (gain)
    s += " S "
    s += str(start)
    s += " "
    s += str(stop)
    s += " "
    s += str(step)
    s += " "
    s += str(pulse)
    s += " "
    s += str(freq)
    print s