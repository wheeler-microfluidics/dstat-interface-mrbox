#!/usr/bin/env python

import serial, io, time, struct
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
    
    def init(self, adc_buffer, adc_rate, adc_pga, gain, update, updatelimit, plot_instance):
        self.datatype = ""
        self.datalength = 2
        self.data = [[],[]]
        
        self.__gaintable = [1e2, 3e2, 3e3, 3e4, 3e5, 3e6, 3e7, 5e8]
        self.gain = self.__gaintable[int(gain)]
        self.updatelimit = updatelimit
        self.update = update

        self.commands = ["A","G"]
    
        self.commands[0] += (adc_buffer)
        self.commands[0] += " "
        self.commands[0] += (adc_rate)
        self.commands[0] += " "
        self.commands[0] += (adc_pga)
        self.commands[0] += " "
        self.commands[1] += (gain)
        self.commands[1] += " "
    
        plot_instance.clearall()
        plot_instance.changetype(self)

    def run(self, strPort, plot_instance, databuffer_instance):
        self.ser = delayedSerial(strPort, 1024000, timeout=3)
        self.ser.write("ck")
        
        self.ser.flushInput()
        
        self.updatecounter = 0
        databuffer_instance.set_text("")
        databuffer_instance.place_cursor(databuffer_instance.get_start_iter())
        
        for i in self.commands:
            databuffer_instance.insert_at_cursor(i)
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
            
            self.data_handler(plot_instance, databuffer_instance) #Will be overridden by experiment classes to deal with more complicated data

        self.data_postprocessing()
        
        plot_instance.updateline(self, 0)
        plot_instance.redraw()

        self.ser.close()

    def data_handler(self, plot_instance, databuffer_instance):
        while True:
            for line in self.ser:
                if line.startswith('B'):
                    inputdata = self.ser.read(size=6) #uint16 + int32
                    voltage, current = struct.unpack('<Hl', inputdata)
                    
                    self.data[0].append((voltage-32768)*3000./65536)
                    self.data[1].append(current*(1.5/self.gain/8388607))
                    
                    plot_instance.updateline(self, 0)
                    
                    if self.update:
                        if self.updatecounter == self.updatelimit:
                            plot_instance.redraw()
                            self.updatecounter = 0
                        
                        else:
                            self.updatecounter +=1
                
                if line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
            
            break
    
    def data_postprocessing(self):
        pass
        #remove first two data points - usually bad // Do this when calling for display updates
#        for i in self.data:
#            i.pop(0)
#            i.pop(0)

class chronoamp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, potential, time, update, updatelimit, plot_instance):
        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.xmin = 0
        self.xmax = 0
        
        for i in time:
            self.xmax += int(i)
        
        self.init(adc_buffer, adc_rate, adc_pga, gain, update, updatelimit, plot_instance) #need to call after xmin and xmax are set
        
        self.commands += "R"
        self.commands[2] += str(len(potential))
        self.commands[2] += " "
        for i in potential:
            self.commands[2] += str(int(i*(65536./3000)+32768))
            self.commands[2] += " "
        for i in time:
            self.commands[2] += str(i)
            self.commands[2] += " "
            
    def data_handler(self, plot_instance, databuffer_instance): #overrides inherited method to not convert x axis
        while True:
            for line in self.ser:
                if line.startswith('B'):
                    inputdata = self.ser.read(size=8) #2*uint16 + int32
                    seconds, milliseconds, current = struct.unpack('<HHl', inputdata)
                    
                    self.data[0].append(seconds+milliseconds/1000.)
                    self.data[1].append(current*(1.5/self.gain/8388607))

                    plot_instance.updateline(self, 0)
                    
                    if self.update:
                        if self.updatecounter == self.updatelimit:
                            plot_instance.redraw()
                            self.updatecounter = 0
                            
                        else:
                            self.updatecounter +=1
        
                if line.lstrip().startswith("no"):
                    self.ser.flushInput()
                    break
            
            break

class lsv_exp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, start, stop, slope, update, updatelimit, plot_instance):

        self.datatype = "linearData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.xmin = start
        self.xmax = stop
        
        self.init(adc_buffer, adc_rate, adc_pga, gain, update, updatelimit, plot_instance) #need to call after xmin and xmax are set
        
        self.commands += "L"
        self.commands[2] += str(start)
        self.commands[2] += " "
        self.commands[2] += str(stop)
        self.commands[2] += " "
        self.commands[2] += str(slope)
        self.commands[2] += " "

class cv_exp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, v1, v2, start, scans, slope, update, updatelimit, plot_instance):
        self.init(adc_buffer, adc_rate, adc_pga, gain, update, updatelimit, plot_instance)
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
                        
                        plot_instance.updateline(self, 0)
                        
                        if self.updatecounter == 5:
                            plot_instance.redraw()
                            self.updatecounter = 0
                        
                        else:
                            self.updatecounter +=1
            
            break


class swv_exp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, start, stop, step, pulse, freq, update, updatelimit, plot_instance):
        self.init(adc_buffer, adc_rate, adc_pga, gain, update, updatelimit)
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


