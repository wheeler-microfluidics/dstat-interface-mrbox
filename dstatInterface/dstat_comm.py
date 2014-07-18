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

class dataCapture(mp.Process):
    def __init__(self, ser_instance, pipe, size):
        mp.Process.__init__(self)
        
        self.size = size
        self.serial = ser_instance
        self.recv_p, self.send_p = pipe

    def run(self):
        scan = 0

        while True:
            for line in self.serial:
                if line.startswith('B'):
                    self.send_p.send((scan,self.serial.read(size=self.size)))
                
                elif line.lstrip().startswith("no"):
                    self.serial.flushInput()
                    self.send_p.close() #causes EOF at other end of pipe
                    print "closed"
                    break
                
                elif line.lstrip().startswith('S'):
                    scan += 1
            break

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
    def __init__(self): #will always be overriden, but self.parameters and self.viewparameters should be defined
        pass
    
    def init(self):
        self.data_extra = [] #must be defined even when not needed
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

    def run(self, strPort):
        print "run"
        self.ser = delayedSerial(strPort, 1024000, timeout=5)
        self.ser.write("ck")
        
        self.ser.flushInput()
        
        self.updatecounter = 0
#        self.databuffer.set_text("")
#        self.databuffer.place_cursor(self.databuffer.get_start_iter())

        for i in self.commands:
#            self.databuffer.insert_at_cursor(i)
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
        self.main_pipe.close()
        self.ser.close()
        
    def data_handler(self):
        recv_p, send_p = mp.Pipe(duplex=False)
    
        capture_proc = dataCapture(self.ser, (recv_p, send_p), self.databytes)
        capture_proc.start()
        send_p.close() #pipe won't trip EOFError unless all connections are closed
        
        while True:
            try:
                if self.main_pipe.poll():
                    if self.main_pipe.recv() == 'a':
                        self.ser.write('a')
                        return
            
                scan, data = recv_p.recv()
                voltage, current = struct.unpack('<Hl', data) #uint16 + int32
                #(line, [data])
                self.main_pipe.send((0, [(voltage-32768)*3000./65536, current*(1.5/self.gain/8388607)]))

            except EOFError:
                print "empty"
                break
    
    def data_postprocessing(self):
        pass

class chronoamp(Experiment):
    def __init__(self, parameters, view_parameters, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters
        self.view_parameters = view_parameters
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
            
    def data_handler(self): #overrides inherited method to not convert x axis
        recv_p, send_p = mp.Pipe(duplex=False)
            
        capture_proc = dataCapture(self.ser, (recv_p, send_p), self.databytes)
        capture_proc.start()
        send_p.close() #pipe won't trip EOFError unless all connections are closed
        
        while True:
            try:
                if self.main_pipe.poll():
                    if self.main_pipe.recv() == 'a':
                        self.ser.write('a')
                        return
                scan, data = recv_p.recv()
                seconds, milliseconds, current = struct.unpack('<HHl', data) #2*uint16 + int32
               #(line, [data])
                self.main_pipe.send((0, [seconds+milliseconds/1000., current*(1.5/self.gain/8388607)]))
            
            except EOFError:
                print "empty"
                break

class lsv_exp(Experiment):
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance, send_pipe):
        self.main_pipe = send_pipe
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance

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
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance
 
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
    
    def data_handler(self):
        recv_p, send_p = mp.Pipe(duplex=False)
            
        capture_proc = dataCapture(self.ser, (recv_p, send_p), self.databytes)
        capture_proc.start()
        send_p.close() #pipe won't trip EOFError unless all connections are closed
        
        while True:
            try:
                if self.main_pipe.poll():
                    if self.main_pipe.recv() == 'a':
                        self.ser.write('a')
                        return
            
                scan, data = recv_p.recv()
                voltage, current = struct.unpack('<Hl', data) #uint16 + int32
                #(line, [data])
                self.main_pipe.send((scan, [(voltage-32768)*3000./65536, current*(1.5/self.gain/8388607)]))
            
            except EOFError:
                print "empty"
                break

class swv_exp(Experiment):
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance

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
    
    def data_handler(self):
        recv_p, send_p = mp.Pipe(duplex=False)
        
        capture_proc = dataCapture(self.ser, (recv_p, send_p), self.databytes)
        capture_proc.start()
        send_p.close() #pipe won't trip EOFError unless all connections are closed
        
        while True:
            try:
                if self.main_pipe.poll():
                    if self.main_pipe.recv() == 'a':
                        self.ser.write('a')
                        return
                
                scan, data = recv_p.recv()
                voltage, forward, reverse = struct.unpack('<Hll', data) #uint16 + int32
                #(line, [data])
                self.main_pipe.send((scan, [(voltage-32768)*3000./65536, (forward-reverse)*(1.5/self.gain/8388607), forward*(1.5/self.gain/8388607), reverse*(1.5/self.gain/8388607)]))
            
            except EOFError:
                print "empty"
                break

class dpv_exp(swv_exp):
    def __init__(self, parameters, view_parameters, plot_instance, databuffer_instance, main_pipe):
        self.main_pipe = main_pipe
        self.parameters = parameters
        self.view_parameters = view_parameters
        self.plot = plot_instance
        self.databuffer = databuffer_instance
        
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
