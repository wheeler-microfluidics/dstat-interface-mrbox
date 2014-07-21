#!/usr/bin/env python

import serial, io, time, struct, sys, os
from types import *
from serial.tools import list_ports
import numpy as np
import multiprocessing as mp
from Queue import Empty

def call_it(instance, name, args=(), kwargs=None):
    "indirect caller for instance methods and multiprocessing"
    if kwargs is None:
        kwargs = {}
    return getattr(instance, name)(*args, **kwargs)


class delayedSerial(serial.Serial): #overrides normal serial write so that characters are output individually with a slight delay
    def write(self, data):
        for i in data:
            serial.Serial.write(self, i)
            time.sleep(.001)

class SerialDevices:
    def __init__(self):
        try:
            self.ports, _, _ = zip(*list_ports.comports())
        except ValueError:
            self.ports = []
            print "No serial ports found"
    
    def refresh(self):
        self.ports, _, _ = zip(*list_ports.comports())

class Experiment:
    def run_wrapper(self, *argv):
        self.p = mp.Process(target=call_it, args=(self, 'run', argv))
        self.p.start()

    def __init__(self): #will always be overriden, but self.parameters, self.viewparameters, and self.databytes should be defined
        pass
    
    def init(self):
        self.data_extra = [] #must be defined even when not needed
        self.__gaintable = [1e2, 3e2, 3e3, 3e4, 3e5, 3e6, 3e7, 5e8]
        self.gain = self.__gaintable[int(self.parameters['gain'])]

        self.commands = ["A","G"]
    
        self.commands[0] += (self.parameters['adc_buffer'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_rate'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_pga'])
        self.commands[0] += " "
        self.commands[1] += (self.parameters['gain'])
        self.commands[1] += " "

    def run(self, strPort):
        self.serial = delayedSerial(strPort, 1024000, timeout=1)
        self.serial.write("ck")
        
        self.serial.flushInput()
        
        for i in self.commands:
            print i
            self.serial.write('!')
            
            while not self.serial.read().startswith("C"):
                pass

            self.serial.write(i)
            if not self.serial_handler():
                break

        self.data_postprocessing()
        self.serial.close()
        self.main_pipe.close()
    
    def serial_handler(self):
        scan = 0
        while True:
            if self.main_pipe.poll():
                print "abort"
                if self.main_pipe.recv() == 'a':
                    self.serial.write('a')
                    return False
                        
            for line in self.serial:
                if line.startswith('B'):
                    self.main_pipe.send(self.data_handler((scan, self.serial.read(size=self.databytes))))
                elif line.startswith('S'):
                    scan += 1
                elif line.startswith("#"):
                    print line
                elif line.lstrip().startswith("no"):
                    print line
                    self.serial.flushInput()
                    return True
    
    
    def data_handler(self, input):
        scan, data = input
        voltage, current = struct.unpack('<Hl', data) #uint16 + int32
        return (scan, [(voltage-32768)*3000./65536, current*(1.5/self.gain/8388607)])
    
    def data_postprocessing(self):
        pass

class chronoamp(Experiment):
    def __init__(self, parameters, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters
        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.databytes = 8
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
            
    def data_handler(self, input): #overrides inherited method to not convert x axis
        scan, data = input
        seconds, milliseconds, current = struct.unpack('<HHl', data) #2*uint16 + int32
        return (scan, [seconds+milliseconds/1000., current*(1.5/self.gain/8388607)])

class lsv_exp(Experiment):
    def __init__(self, parameters, send_pipe):
        self.main_pipe = send_pipe
        self.parameters = parameters

        self.datatype = "linearData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[],[]]
        self.datalength = 2
        self.databytes = 6 #uint16 + int32
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']
        
        self.init() #need to call after xmin and xmax are set
        
        self.commands += "L"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*(65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*(65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['start'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['stop'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['slope'])
        self.commands[2] += " "

class cv_exp(Experiment):
    def __init__(self, parameters, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters
 
        self.datatype = "CVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[],[]] #Will have to alter data_handler to add new lists as needed
        self.datalength = 2 * self.parameters['scans'] #x and y for each scan
        self.databytes = 6 #uint16 + int32
        self.xmin = self.parameters['v1']
        self.xmax = self.parameters['v2']
        
        self.init()
        
        self.commands += "C"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*(65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*(65536./3000)+32768))
        self.commands[2] += " "
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
    
    def data_handler(self, input):
        scan, data = input
        voltage, current = struct.unpack('<Hl', data) #uint16 + int32
        return (scan, [(voltage-32768)*3000./65536, current*(1.5/self.gain/8388607)])

class swv_exp(Experiment):
    def __init__(self, parameters, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters

        self.datatype = "SWVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[],[]] #only difference stored here
        self.datalength = 2 * self.parameters['scans']
        self.databytes = 10
        
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']
        
        self.init()
        self.data_extra = [[],[]] #forward/reverse stored here - needs to be after self.init to keep from being redefined
        
        self.commands += "S"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*(65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*(65536./3000)+32768))
        self.commands[2] += " "
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
        self.commands[2] += str(self.parameters['scans'])
        self.commands[2] += " "
    
    def data_handler(self, input):
        scan, data = input
        voltage, forward, reverse = struct.unpack('<Hll', data) #uint16 + int32
        return (scan, [(voltage-32768)*3000./65536, (forward-reverse)*(1.5/self.gain/8388607), forward*(1.5/self.gain/8388607), reverse*(1.5/self.gain/8388607)])


class dpv_exp(swv_exp):
    def __init__(self, parameters, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters
        
        self.datatype = "SWVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[],[]] #only difference stored here
        self.datalength = 2
        self.databytes = 10
        
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']
        
        self.init()
        self.data_extra = [[],[]] #forward/reverse stored here - needs to be after self.init to keep from being redefined
        
        self.commands += "D"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*(65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*(65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['start'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['stop'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['step'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['pulse'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['period'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['width'])
        self.commands[2] += " "
