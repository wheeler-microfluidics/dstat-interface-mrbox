#!/usr/bin/env python

def lsv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, slope):
    s = "L "
    s += (adc_buffer)
    s += " "
    s += (adc_rate)
    s += " "
    s += (adc_pga)
    s += " "
    s += (gain)
    s += " "
    s += str(start)
    s += " "
    s += str(stop)
    s += " "
    s += str(slope)
    print s
#    print ("L ", adc_buffer, adc_rate, adc_pga, gain, start, stop, slope)