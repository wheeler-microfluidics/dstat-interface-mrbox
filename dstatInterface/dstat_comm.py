#!/usr/bin/env python

import serial, io
from serial.tools import list_ports

# class that holds analog data for N samples
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
        
        self.commands = []
        self.xlabel = ""
        self.ylabel = ""
    
        self.commands += "A "
        self.commands[0] += (adc_buffer)
        self.commands[0] += " "
        self.commands[0] += (adc_rate)
        self.commands[0] += " "
        self.commands[0] += (adc_pga)
        self.commands[1] = "G"
        self.commands[1] += (gain)

    def run(self, strPort, plotbox_instance):
        self.ser = serial.Serial(strPort, 1024000,timeout=2)
        self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser,self.ser,buffer_size=1), newline = '\n', line_buffering = True)
        self.ser.write("ck")
    
        plotbox_instance.changetype(self)
    
        self.ser.flushInput()
        
        self.updatecounter = 0
        
        while True:
            for c in self.commands:
                self.ser.write(c)
                print c
                for line in self.ser:
                    if not line.isspace():
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
                            
                            if self.updatecounter == 5:
                                plotbox_instance.redraw()
                                self.updatecounter = 0
                            else:
                                self.updatecounter +=1
        
            for i in self.data:
                i.pop(0)
                i.pop(0)
            
            plotbox_instance.update(self)
            plotbox_instance.redraw()
            
            break
    
        self.ser.close()


class chronoamp(Experiment):
    def __init__(self, adc_buffer, adc_rate, adc_pga, gain, potential, time):
        self.init(adc_buffer, adc_rate, adc_pga, gain)
        self.datatype = "linearData"
        self.xlabel = "Time (s)"
        self.ylabel = "Current (ADC Index)"
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

#def chronoamp(adc_buffer, adc_rate, adc_pga, gain, potential, time):
#    s = "A "
#    s += (adc_buffer)
#    s += " "
#    s += (adc_rate)
#    s += " "
#    s += (adc_pga)
#    s += " G "
#    s += (gain)
#    s += " R "
#    s += str(len(potential))
#    s += " "
#    for i in potential:
#        s += str(i)
#        s += " "
#    for i in time:
#        s += str (i)
#        s += " "
#    print s

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