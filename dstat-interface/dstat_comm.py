#!/usr/bin/env python
#     DStat Interface - An interface for the open hardware DStat potentiostat
#     Copyright (C) 2014  Michael D. M. Dryden - 
#     Wheeler Microfluidics Laboratory <http://microfluidics.utoronto.ca>
#         
#     
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

import serial
from serial.tools import list_ports
import time
import struct
import multiprocessing as mp
from errors import VarError

def call_it(instance, name, args=(), kwargs=None):
    """Indirect caller for instance methods and multiprocessing.
    
    Arguments:
    instance -- instance to which the method belongs
    name -- method to call
    args -- passed to method
    kwargs -- passed to method
    """
    if kwargs is None:
        kwargs = {}
    return getattr(instance, name)(*args, **kwargs)

def version_check(ser_port):
    """Tries to contact DStat and get version. Returns a list of
    [(major, minor), serial instance]. If no response, returns empty tuple.
        
    Arguments:
    ser_port -- address of serial port to use
    """
    
    global serial_instance
    serial_instance = delayedSerial(ser_port, baudrate=1000000, timeout=1)
        
    serial_instance.write("ck")
    
    serial_instance.flushInput()
    serial_instance.write('!')
            
    while not serial_instance.read()=="C":
        time.sleep(.5)
        serial_instance.write('!')
        
    serial_instance.write('V')
    for line in serial_instance:
        if line.startswith('V'):
            input = line.lstrip('V')
        elif line.startswith("#"):
            print line
        elif line.lstrip().startswith("no"):
            print line
            serial_instance.flushInput()
            break
            
    parted = input.rstrip().split('.')
    print parted
    
    return (int(parted[0]), int(parted[1]))
    
    

class delayedSerial(serial.Serial): 
    """Extends Serial.write so that characters are output individually
    with a slight delay
    """
    def write(self, data):
        for i in data:
            serial.Serial.write(self, i)
            time.sleep(.001)

class SerialDevices(object):
    """Retrieves and stores list of serial devices in self.ports"""
    def __init__(self):
        try:
            self.ports, _, _ = zip(*list_ports.comports())
        except ValueError:
            self.ports = []
            print "No serial ports found"
    
    def refresh(self):
        """Refreshes list of ports."""
        self.ports, _, _ = zip(*list_ports.comports())

class Experiment(object):
    """Store and acquire a potentiostat experiment. Meant to be subclassed
    to by different experiment types and not used instanced directly.
    """
    def run_wrapper(self, *argv):
        """Execute experiment indirectly using call_it to bypass lack of fork()
        on Windows for multiprocessing.
        """
        self.proc = mp.Process(target=call_it, args=(self, 'run', argv))
        self.proc.start()

    def __init__(self, parameters, main_pipe):
        """Adds commands for gain and ADC."""
        self.parameters = parameters
        self.main_pipe = main_pipe
        self.databytes = 8

        self.data_extra = []  # must be defined even when not needed
        
        major, minor = self.parameters['version']
        
        if major >= 1:
            if minor == 1:
                self.__gaintable = [1e2, 3e2, 3e3, 3e4, 3e5, 3e6, 3e7, 5e8]
            elif minor >= 2:
                self.__gaintable = [1, 1e2, 3e3, 3e4, 3e5, 3e6, 3e7, 1e8]
        else:
            raise VarError(parameters['version'], "Invalid version parameter.")
            
        self.gain = self.__gaintable[int(self.parameters['gain'])]

        self.commands = ["EA", "EG"]
    
        self.commands[0] += (self.parameters['adc_buffer'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_rate'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_pga'])
        self.commands[0] += " "
        self.commands[1] += (self.parameters['gain'])
        self.commands[1] += " "

    def run(self):
        """Execute experiment. Connects and sends handshake signal to DStat
        then sends self.commands. Don't call directly as a process in Windows,
        use run_wrapper instead.
        """
        self.serial = serial_instance
        
        try:
            self.serial.flushInput()
            
            for i in self.commands:
                print i
                self.serial.write('!')
                
                while not self.serial.read().startswith("C"):
                    pass
    
                self.serial.write(i)
                if not self.serial_handler():
                    self.main_pipe.send("ABORT")
                    break
                    
        except serial.SerialException:
            self.main_pipe.send("ABORT")
            
        finally:
            self.data_postprocessing()
            self.main_pipe.close()
    
    def serial_handler(self):
        """Handles incoming serial transmissions from DStat. Returns False
        if stop button pressed and sends abort signal to instrument. Sends
        data to self.main_pipe as result of self.data_handler).
        """
        scan = 0
        try:
            while True:
                if self.main_pipe.poll():
                    if self.main_pipe.recv() == 'a':
                        self.serial.write('a')
                        print "ABORT!"
                        return False
                            
                for line in self.serial:
                    if self.main_pipe.poll():
                        if self.main_pipe.recv() == 'a':
                            self.serial.write('a')
                            print "ABORT!"
                            return False
                            
                    if line.startswith('B'):
                        self.main_pipe.send(self.data_handler(
                                    (scan, self.serial.read(size=self.databytes))))
                    elif line.startswith('S'):
                        scan += 1
                    elif line.lstrip().startswith("#"):
                        print line
                    elif line.lstrip().startswith("no"):
                        print line
                        self.serial.flushInput()
                        return True
                        
        except serial.SerialException:
            return False
    
    
    def data_handler(self, data_input):
        """Takes data_input as tuple -- (scan, data).
        Returns:
        (scan number, [voltage, current]) -- voltage in mV, current in A
        """
        scan, data = data_input
        voltage, current = struct.unpack('<Hl', data) #uint16 + int32
        return (scan,
                [(voltage-32768)*3000./65536, current*(1.5/self.gain/8388607)])
    
    def data_postprocessing(self):
        """No data postprocessing done by default, can be overridden
        in subclass.
        """
        pass

class Chronoamp(Experiment):
    """Chronoamperometry experiment"""
    def __init__(self, parameters, main_pipe):
        super(Chronoamp, self).__init__(parameters, main_pipe)

        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Current (A)"
        self.data = [[], []]
        self.datalength = 2
        self.databytes = 8
        self.xmin = 0
        self.xmax = 0
        
        for i in self.parameters['time']:
            self.xmax += int(i)
        
        self.commands += "E"
        self.commands[2] += "R"
        self.commands[2] += str(len(self.parameters['potential']))
        self.commands[2] += " "
        for i in self.parameters['potential']:
            self.commands[2] += str(int(i*(65536./3000)+32768))
            self.commands[2] += " "
        for i in self.parameters['time']:
            self.commands[2] += str(i)
            self.commands[2] += " "
        self.commands[2] += "0 " # disable photodiode interlock
            
    def data_handler(self, data_input):
        """Overrides Experiment method to not convert x axis to mV."""
        scan, data = data_input
        # 2*uint16 + int32
        seconds, milliseconds, current = struct.unpack('<HHl', data)
        return (scan,
                [seconds+milliseconds/1000., current*(1.5/self.gain/8388607)])

class PDExp(Chronoamp):
    """Photodiode/PMT experiment"""
    def __init__(self, parameters, main_pipe):
        super(Chronoamp, self).__init__(parameters, main_pipe) # Don't want to call CA's init

        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Current (A)"
        self.data = [[], []]
        self.datalength = 2
        self.databytes = 8
        self.xmin = 0
        self.xmax = self.parameters['time']
        
        self.commands += "E"
        self.commands[2] += "R"
        self.commands[2] += "1"
        self.commands[2] += " "
        
        if self.parameters['voltage'] == 0: # Special case where V=0
            self.commands[2] += "65535"
        else:
            self.commands[2] += str(int(
                            65535-(self.parameters['voltage']*(65536./3000))))
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['time'])
        self.commands[2] += " "
        if self.parameters['interlock']:
            self.commands[2] += "1"
        else:
            self.commands[2] += "0"
        self.commands[2] += " "

class PotExp(Experiment):
    """Potentiometry experiment"""
    def __init__(self, parameters, main_pipe):
        super(PotExp, self).__init__(parameters, main_pipe)

        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Voltage (V)"
        self.data = [[], []]
        self.datalength = 2
        self.databytes = 8
        self.xmin = 0
        self.xmax = self.parameters['time']
        
        self.commands += "E"
        self.commands[2] += "P"
        self.commands[2] += str(self.parameters['time'])
        self.commands[2] += " 1 " #potentiometry mode

    def data_handler(self, data_input):
        """Overrides Experiment method to not convert x axis to mV."""
        scan, data = data_input
        # 2*uint16 + int32
        seconds, milliseconds, voltage = struct.unpack('<HHl', data)
        return (scan,
                [seconds+milliseconds/1000., voltage*(1.5/8388607.)])

class LSVExp(Experiment):
    """Linear Scan Voltammetry experiment"""
    def __init__(self, parameters, main_pipe):
        super(LSVExp, self).__init__(parameters, main_pipe)

        self.datatype = "linearData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[], []]
        self.datalength = 2
        self.databytes = 6  # uint16 + int32
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']
        
        self.commands += "E"
        self.commands[2] += "L"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*
                                (65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*
                                (65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['start'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['stop'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['slope'])
        self.commands[2] += " "

class CVExp(Experiment):
    """Cyclic Voltammetry experiment"""
    def __init__(self, parameters, main_pipe):
        super(CVExp, self).__init__(parameters, main_pipe)
 
        self.datatype = "CVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[], []]
        self.datalength = 2 * self.parameters['scans']  # x and y for each scan
        self.databytes = 6  # uint16 + int32
        self.xmin = self.parameters['v1']
        self.xmax = self.parameters['v2']
        
        self.commands += "E"
        self.commands[2] += "C"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*
                                (65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*
                                (65536./3000)+32768))
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

class SWVExp(Experiment):
    """Square Wave Voltammetry experiment"""
    def __init__(self, parameters, main_pipe):
        super(SWVExp, self).__init__(parameters, main_pipe)

        self.datatype = "SWVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[], []]  # only difference stored here
        self.datalength = 2 * self.parameters['scans']
        self.databytes = 10
        
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']

        self.data_extra = [[], []]  
        
        self.commands += "E"
        self.commands[2] += "S"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*
                                    (65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*
                                    (65536./3000)+32768))
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
    
    def data_handler(self, input_data):
        """Overrides Experiment method to calculate difference current"""
        scan, data = input_data
        # uint16 + int32
        voltage, forward, reverse = struct.unpack('<Hll', data)
        return (scan, [(voltage-32768)*3000./65536,
                       (forward-reverse)*(1.5/self.gain/8388607),
                       forward*(1.5/self.gain/8388607),
                       reverse*(1.5/self.gain/8388607)])


class DPVExp(SWVExp):
    """Diffential Pulse Voltammetry experiment."""
    def __init__(self, parameters, main_pipe):
        """Overrides SWVExp method, extends Experiment method"""
        super(SWVExp, self).__init__(parameters, main_pipe)
        
        self.datatype = "SWVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[], []]  # only difference stored here
        self.datalength = 2
        self.databytes = 10
        
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']

        self.data_extra = [[], []]
        
        self.commands += "E"
        self.commands[2] += "D"
        self.commands[2] += str(self.parameters['clean_s'])
        self.commands[2] += " "
        self.commands[2] += str(self.parameters['dep_s'])
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['clean_mV']*
                                    (65536./3000)+32768))
        self.commands[2] += " "
        self.commands[2] += str(int(self.parameters['dep_mV']*
                                    (65536./3000)+32768))
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

class OCPExp(Experiment):
    """Open circuit potential measumement in statusbar."""
    def __init__(self, main_pipe):
        """Only needs data pipe."""
        self.main_pipe = main_pipe
        self.databytes = 8
        
        self.commands = ["EA", "EP"]
    
        self.commands[0] += "2 " # input buffer
        self.commands[0] += "3 " # 2.5 Hz sample rate
        self.commands[0] += "1 " # 2x PGA
        
        self.commands[1] += "0 " # no timeout
        self.commands[1] += "0 " # OCP measurement mode
        
    def data_handler(self, data_input):
        """Overrides Experiment method to only send ADC values."""
        scan, data = data_input
        # 2*uint16 + int32
        seconds, milliseconds, voltage = struct.unpack('<HHl', data)
        return (voltage/5.592405e6)