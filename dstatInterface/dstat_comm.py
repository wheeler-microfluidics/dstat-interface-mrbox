#!/usr/bin/env python

import serial, io, time, struct
from types import *
from serial.tools import list_ports
import numpy as np

class delayedSerial(serial.Serial): #overrides normal serial write so that characters are output individually with a slight delay
    def write(self, data):
        for i in data:
            serial.Serial.write(self, i)
            time.sleep(.001)

class linearData:
    # constr
    def __init__(self):
        self.xdata = []
        self.ydata = []
        self.first = 1
    
    # add data
    def add(self, data):
        if self.first == 1:
            self.first = 0
            return
        assert(len(data) == 2)
        self.x.append(data[0])
        self.y.append(data[1])
    
    # clear data
    def clear(self):
        self.first = 1
        self.ax = []
        self.ay = []


class SerialDevices:
    def __init__(self):
        self.ports, _, _ = zip(*list_ports.comports())
    
    def refresh(self):
        self.ports, _, _ = zip(*list_ports.comports())

class Experiment:
    def __init__(self): #will always be overriden, but self.parameters and self.viewparameters should be defined
        pass
    
    def init(self):
        self.__gaintable = [1e2, 3e2, 3e3, 3e4, 3e5, 3e6, 3e7, 5e8]
        self.gain = self.__gaintable[int(self.parameters['gain'])]
        self.updatelimit = self.view_parameters['updatelimit']
        self.update = self.view_parameters['update']

        self.commands = ["A","G"]
    
        self.commands[0] += (self.parameters['adc_buffer'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_rate'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_pga'])
        self.commands[0] += " "
        self.commands[1] += (self.parameters['gain'])
        self.commands[1] += " "
    
        self.plot.clearall()
        self.plot.changetype(self)

    def run(self, strPort):
        self.ser = delayedSerial(strPort, 1024000, timeout=5)
        self.ser.write("ck")
        
        self.ser.flushInput()
        
        self.updatecounter = 0
        self.databuffer.set_text("")
        self.databuffer.place_cursor(self.databuffer.get_start_iter())
        
        for i in self.commands:
            self.databuffer.insert_at_cursor(i)
            self.ser.flush()
            self.ser.write("!")
            while True:
                for line in self.ser:
                    if line.lstrip().startswith('C'):
                        self.ser.flushInput()
                        break
            
                break
        
            self.ser.flushInput()
            self.ser.write(i)
            print i
            
            self.data_handler() #Will be overridden by experiment classes to deal with more complicated data

        self.data_postprocessing()
        
        self.plot.updateline(self, 0)
        self.plot.redraw()

        self.ser.close()

    def data_handler(self):
        while True:
            for line in self.ser:
                if line.startswith('B'):
                    inputdata = self.ser.read(size=6) #uint16 + int32
                    voltage, current = struct.unpack('<Hl', inputdata)
                    
                    self.data[0].append((voltage-32768)*3000./65536)
                    self.data[1].append(current*(1.5/self.gain/8388607))
                    
                    self.plot.updateline(self, 0)
                    
                    if self.update:
                        if self.updatecounter == self.updatelimit:
                            self.plot.redraw()
                            self.updatecounter = 0
                        
                        else:
                            self.updatecounter +=1
                
                elif line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
            
            break
    
    def data_postprocessing(self):
        pass

class chronoamp(Experiment):
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance):
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance
        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.xmin = 0
        self.xmax = 0
        
        for i in self.parameters['time']:
            self.xmax += int(i)
        
        self.init() #need to call after xmin and xmax are set
        
        self.commands += "R"
        self.commands[2] += str(len(self.parameters['potential']))
        self.commands[2] += " "
        for i in self.parameters['potential']:
            self.commands[2] += str(int(i*(65536./3000)+32768))
            self.commands[2] += " "
        for i in self.parameters['time']:
            self.commands[2] += str(i)
            self.commands[2] += " "
            
    def data_handler(self): #overrides inherited method to not convert x axis
        while True:
            for line in self.ser:
                if line.startswith('B'):
                    inputdata = self.ser.read(size=8) #2*uint16 + int32
                    seconds, milliseconds, current = struct.unpack('<HHl', inputdata)
                    
                    self.data[0].append(seconds+milliseconds/1000.)
                    self.data[1].append(current*(1.5/self.gain/8388607))

                    self.plot.updateline(self, 0)
                    
                    if self.update:
                        if self.updatecounter == self.updatelimit:
                            self.plot.redraw()
                            self.updatecounter = 0
                            
                        else:
                            self.updatecounter +=1
        
                elif line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
            
            break

class lsv_exp(Experiment):
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance):
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance

        self.datatype = "linearData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']
        
        self.init() #need to call after xmin and xmax are set
        
        self.commands += "L"
        self.commands[2] += str(self.parameters['start'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['stop'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['slope'])
        self.commands[2] += " "

class cv_exp(Experiment):
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance):
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance
 
        self.datatype = "CVData"
        self.xlabel = "Voltage (DAC units)"
        self.ylabel = "Current (A)"
        self.data = [[],[]] #Will have to alter data_handler to add new lists as needed
        self.datalength = 2 * self.parameters['scans'] #x and y for each scan
        self.xmin = self.parameters['v1']
        self.xmax = self.parameters['v2']
        
        self.init()
        
        self.commands += "C"
        self.commands[2] += str(self.parameters['v1'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['v2'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['start'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['scans'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['slope'])
        self.commands[2] += " "
    
    def data_handler(self):
        scan = 0
        
        while True:
            for line in self.ser:
                if line.startswith('B'):
                    inputdata = self.ser.read(size=6) #uint16 + int32
                    voltage, current = struct.unpack('<Hl', inputdata)
                    
                    self.data[2*scan].append((voltage-32768)*3000./65536)
                    self.data[2*scan+1].append(current*(1.5/self.gain/8388607))
                    
                    self.plot.updateline(self, scan)
                    
                    if self.update:
                        if self.updatecounter == self.updatelimit:
                            self.plot.redraw()
                            self.updatecounter = 0
                        
                        else:
                            self.updatecounter +=1
                
                elif line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
                
                elif line.lstrip().startswith('S'):
                    self.plot.redraw()
                    self.plot.addline()
                    self.data.append([])
                    self.data.append([])
                    scan += 1
                
                elif line.lstrip().startswith('D'):
                    self.data.pop()
                    self.data.pop() #instrument signals with S after each cycle, so last one will be blank, D singals end of experiment
                    self.plot.clearline(scan)
                    self.plot.redraw()
                    
            break

class swv_exp(Experiment):
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance):
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance

        self.datatype = "SWVData"
        self.xlabel = "Voltage (DAC units)"
        self.ylabel = "Current (A)"
        self.data = [[],[],[],[]] #one extra for difference
        self.datalength = 4
        
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']
        
        self.init()
        
        self.commands += "S"
        self.commands[2] += str(self.parameters['start'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['stop'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['step'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['pulse'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['freq'])
        self.commands[2] += " "
    
    def data_handler(self):
        while True:
            for line in self.ser:
                if line.startswith('B'):
                    inputdata = self.ser.read(size=10) #uint16 + 2*int32
                    voltage, forward, reverse = struct.unpack('<Hll', inputdata)

                    self.data[0].append((voltage-32768)*3000./65536)
                    self.data[1].append((forward-reverse)*(1.5/self.gain/8388607))
                    self.data[2].append(forward*(1.5/self.gain/8388607))
                    self.data[3].append(reverse*(1.5/self.gain/8388607))
                    
                    self.plot.updateline(self, 0) #displays only difference current, but forward and reverse stored
                    
                    if self.update:
                        if self.updatecounter == self.updatelimit:
                            self.plot.redraw()
                            self.updatecounter = 0
                        
                        else:
                            self.updatecounter +=1
                
                elif line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
            
            break

