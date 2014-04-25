#!/usr/bin/env python

import serial, io, time
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
    def __init__(self):
        pass
    
    def init(self, adc_buffer, adc_rate, adc_pga, gain):
        self.datatype = ""
        self.datalength = 2
        self.data = []
        
        self._gaintable = [1e2, 3e2, 3e3, 3e4, 3e5, 3e6, 3e7, 5e8]
        self.gain = self._gaintable[int(gain)]
        
        self.commands = ["A","G"]
        self.xlabel = ""
        self.ylabel = ""
    
#        self.commands += "A"
        self.commands[0] += (adc_buffer)
        self.commands[0] += " "
        self.commands[0] += (adc_rate)
        self.commands[0] += " "
        self.commands[0] += (adc_pga)
        self.commands[0] += " "
#        self.commands[1] += "G"
        self.commands[1] += (gain)
        self.commands[1] += " "

    def data_handler(self):
        while True:
            for line in self.ser:
                print line
                if line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
                
                if not (line.isspace() or line.lstrip().startswith('#')):
                    #                        print line
                    self.inputdata = [float(val) for val in line.split()]
                    if(len(self.inputdata) == self.datalength):
                        #                            print self.inputdata
                        
                        for i in range(self.datalength):
                            self.data[i].append(self.inputdata[i])
                        
                        plotbox_instance.update(self)
                        
                        if self.updatecounter == 5: #how often to redraw (pick as function of sample rate?)
                            plotbox_instance.redraw()
                            self.updatecounter = 0
                        
                        else:
                            self.updatecounter +=1
            
            break



    def run(self, strPort, plotbox_instance):
        self.ser = delayedSerial(strPort, 1024000, timeout=3)
        self.ser.write("ck")
    
        plotbox_instance.changetype(self)
    
        self.ser.flushInput()
        
        self.updatecounter = 0
        
        for i in self.commands:
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

        for i in self.data:
            i.pop(0)
            i.pop(0)
        
        #conversion to Amperes
        self.dataarray = np.array(self.data[1:])
        self.dataarray = self.dataarray/8388607/self.gain*1.5

        for i in range(self.datalength-1):
            self.data[i+1] = list(self.dataarray[i])

        plotbox_instance.update(self)
        plotbox_instance.redraw()

        self.ser.close()


class chronoamp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, potential, time):
        self.init(adc_buffer, adc_rate, adc_pga, gain)
        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.xmin = 0
        self.xmax = 0
        
        for i in time:
            self.xmax += int(i)

        self.commands += "R"
        self.commands[2] += str(len(potential))
        self.commands[2] += " "
        for i in potential:
            self.commands[2] += str(int(i*(65536./3000)+32768))
            self.commands[2] += " "
        for i in time:
            self.commands[2] += str(i)
            self.commands[2] += " "

class lsv_exp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, start, stop, slope):
        self.init(adc_buffer, adc_rate, adc_pga, gain)
        self.datatype = "linearData"
        self.xlabel = "Voltage (DAC units)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.xmin = 0
        self.xmax = 0
        
        self.xmin = start
        self.xmax = stop
        
        self.commands += "L"
        self.commands[2] += str(start)
        self.commands[2] += " "
        self.commands[2] += str(stop)
        self.commands[2] += " "
        self.commands[2] += str(slope)
        self.commands[2] += " "

#def lsv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, slope):
#    s = "A "
#    s += (adc_buffer)
#    s += " "
#    s += (adc_rate)
#    s += " "
#    s += (adc_pga)
#    s += " G "
#    s += (gain)
#    s += " L "
#    s += str(start)
#    s += " "
#    s += str(stop)
#    s += " "
#    s += str(slope)
#    print s
##    print ("L ", adc_buffer, adc_rate, adc_pga, gain, start, stop, slope)

class cv_exp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, v1, v2, start, scans, slope):
        self.init(adc_buffer, adc_rate, adc_pga, gain)
        self.datatype = "CVData"
        self.xlabel = "Voltage (DAC units)"
        self.ylabel = "Current (A)"
        self.data = [[],[]] #Will have to alter data_handler to add new lists as needed
        self.datalength = 2 #2 * scans #x and y for each scan
        self.xmin = 0
        self.xmax = 0
        
        self.xmin = v1
        self.xmax = v2
        
        self.commands += "C"
        self.commands[2] += str(v1)
        self.commands[2] += " "
        self.commands[2] += str(v2)
        self.commands[2] += " "
        self.commands[2] += str(start)
        self.commands[2] += " "
        self.commands[2] += str(scans)
        self.commands[2] += " "
        self.commands[2] += str(slope)
        self.commands[2] += " "
    
    def data_handler(self): #Placeholder - need to handle multiple scans
        while True:
            for line in self.ser:
                print line
                if line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
                
                if not (line.isspace() or line.lstrip().startswith('#')):
                    self.inputdata = [float(val) for val in line.split()]
                    if(len(self.inputdata) == self.datalength):
                        
                        for i in range(self.datalength):
                            self.data[i].append(self.inputdata[i])
                        
                        plotbox_instance.update(self)
                        
                        if self.updatecounter == 5:
                            plotbox_instance.redraw()
                            self.updatecounter = 0
                        
                        else:
                            self.updatecounter +=1
            
            break

#def cv_exp(adc_buffer, adc_rate, adc_pga, gain, v1, v2, start, scans, slope):
#    s = "A "
#    s += (adc_buffer)
#    s += " "
#    s += (adc_rate)
#    s += " "
#    s += (adc_pga)
#    s += " G "
#    s += (gain)
#    s += " C "
#    s += str(v1)
#    s += " "
#    s += str(v2)
#    s += " "
#    s += str(start)
#    s += " "
#    s += str(scans)
#    s += " "
#    s += str(slope)
#    print s

class swv_exp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, start, stop, step, pulse, freq):
        self.init(adc_buffer, adc_rate, adc_pga, gain)
        self.datatype = "SWVData"
        self.xlabel = "Voltage (DAC units)"
        self.ylabel = "Current (A)"
        self.data = [[],[],[],[]] #one extra for difference
        self.datalength = 3
        self.xmin = 0
        self.xmax = 0
        
        self.xmin = start
        self.xmax = stop
        
        self.commands += "S"
        self.commands[2] += str(start)
        self.commands[2] += " "
        self.commands[2] += str(stop)
        self.commands[2] += " "
        self.commands[2] += str(step)
        self.commands[2] += " "
        self.commands[2] += str(pulse)
        self.commands[2] += " "
        self.commands[2] += str(freq)
        self.commands[2] += " "

#def swv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, step, pulse, freq):
#    s = "A "
#    s += (adc_buffer)
#    s += " "
#    s += (adc_rate)
#    s += " "
#    s += (adc_pga)
#    s += " G "
#    s += (gain)
#    s += " S "
#    s += str(start)
#    s += " "
#    s += str(stop)
#    s += " "
#    s += str(step)
#    s += " "
#    s += str(pulse)
#    s += " "
#    s += str(freq)
#    print s
