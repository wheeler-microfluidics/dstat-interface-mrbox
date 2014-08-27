#!/usr/bin/env python

import serial
from serial.tools import list_ports
import time
import struct
import multiprocessing as mp

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
        self.__gaintable = [1e2, 3e2, 3e3, 3e4, 3e5, 3e6, 3e7, 5e8]
        self.gain = self.__gaintable[int(self.parameters['gain'])]

        self.commands = ["A", "G"]
    
        self.commands[0] += (self.parameters['adc_buffer'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_rate'])
        self.commands[0] += " "
        self.commands[0] += (self.parameters['adc_pga'])
        self.commands[0] += " "
        self.commands[1] += (self.parameters['gain'])
        self.commands[1] += " "

    def run(self, ser_port):
        """Execute experiment. Connects and sends handshake signal to DStat
        then sendsself.commands. Don't call directly as a process in Windows,
        use run_wrapper instead.
        
        Arguments:
        ser_port -- address of serial port to use
        """
        self.serial = delayedSerial(ser_port, 1024000, timeout=1)
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
        """Handles incoming serial transmissions from DStat. Returns False
        if stop button pressed and sends abort signal to instrument. Sends
        data to self.main_pipe as result of self.data_handler).
        """
        scan = 0
        while True:
            if self.main_pipe.poll():
                print "abort"
                if self.main_pipe.recv() == 'a':
                    self.serial.write('a')
                    return False
                        
            for line in self.serial:
                if line.startswith('B'):
                    self.main_pipe.send(self.data_handler(
                                 (scan, self.serial.read(size=self.databytes))))
                elif line.startswith('S'):
                    scan += 1
                elif line.startswith("#"):
                    print line
                elif line.lstrip().startswith("no"):
                    print line
                    self.serial.flushInput()
                    return True
    
    
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
        
        self.commands += "R"
        self.commands[2] += str(len(self.parameters['potential']))
        self.commands[2] += " "
        for i in self.parameters['potential']:
            self.commands[2] += str(int(i*(65536./3000)+32768))
            self.commands[2] += " "
        for i in self.parameters['time']:
            self.commands[2] += str(i)
            self.commands[2] += " "
            
    def data_handler(self, data_input):
        """Overrides Experiment method to not convert x axis to mV."""
        scan, data = data_input
        # 2*uint16 + int32
        seconds, milliseconds, current = struct.unpack('<HHl', data)
        return (scan,
                [seconds+milliseconds/1000., current*(1.5/self.gain/8388607)])

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
        
        self.init()  # need to call after xmin and xmax are set
        
        self.commands += "L"
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
        
        self.commands += "C"
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

        # forward/reverse stored here - needs to be after 
        # self.init to keep from being redefined
        self.data_extra = [[], []]  
        
        self.commands += "S"
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
        """Overrides SWVExp method"""
        super(DPVExp, self).__init__(parameters, main_pipe)
        
        self.datatype = "SWVData"
        self.xlabel = "Voltage (mV)"
        self.ylabel = "Current (A)"
        self.data = [[], []]  # only difference stored here
        self.datalength = 2
        self.databytes = 10
        
        self.xmin = self.parameters['start']
        self.xmax = self.parameters['stop']
        
        self.init()
        # forward/reverse stored here - needs to be after self.init to
        # keep from being redefined
        self.data_extra = [[], []]
        
        self.commands += "D"
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