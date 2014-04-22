#!/usr/bin/env python

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

def cv_exp(adc_buffer, adc_rate, adc_pga, gain, start, v1, v2, scans, slope):
    s = "A "
    s += (adc_buffer)
    s += " "
    s += (adc_rate)
    s += " "
    s += (adc_pga)
    s += " G "
    s += (gain)
    s += " C "
    s += str(start)
    s += " "
    s += str(v1)
    s += " "
    s += str(v2)
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