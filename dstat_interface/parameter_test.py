#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import logging

from errors import InputError

logger = logging.getLogger("dstat.parameter_test")

def lsv_test(params):
    """Test LSV parameters for sanity"""
    test_parameters = ['clean_mV', 'dep_mV', 'clean_s', 'dep_s', 'start',
                       'stop', 'slope']
    parameters = {}
    for i in params:
        if i in test_parameters:
            parameters[i] = int(params[i])
    
    if (parameters['clean_mV'] > 1499 or 
            parameters['clean_mV'] < -1500):
        raise InputError(parameters['clean_mV'],
                         "Clean potential exceeds hardware limits.")
    if (parameters['dep_mV'] > 1499 or
            parameters['dep_mV'] < -1500):
        raise InputError(parameters['dep_mV'],
                    "Deposition potential exceeds hardware limits.")
    if (parameters['clean_s'] < 0):
        raise InputError(parameters['clean_s'],
                         "Clean time cannot be negative.")
    if (parameters['dep_s'] < 0):
        raise InputError(parameters['dep_s'],
                         "Deposition time cannot be negative.")
    if (parameters['start'] > 1499 or parameters['start'] < -1500):
        raise InputError(parameters['start'],
                         "Start parameter exceeds hardware limits.")
    if (parameters['stop'] > 1499 or parameters['stop'] < -1500):
        raise InputError(parameters['stop'],
                         "Stop parameter exceeds hardware limits.")
    if (parameters['slope'] > 2000 or parameters['slope'] < 1):
        raise InputError(parameters['slope'],
                         "Slope parameter exceeds hardware limits.")
    if parameters['start'] == parameters['stop']:
        raise InputError(parameters['start'],
                         "Start cannot equal Stop.")

def cv_test(params):
    """Test CV parameters for sanity"""
    test_parameters = ['clean_mV', 'dep_mV', 'clean_s', 'dep_s', 'start',
                       'stop', 'slope', 'v1', 'v2', 'scans']
    parameters = {}
    for i in params:
        if i in test_parameters:
            parameters[i] = int(params[i])
            
    if (parameters['clean_mV'] > 1499 or
            parameters['clean_mV'] < -1500):
        raise InputError(parameters['clean_mV'],
                         "Clean potential exceeds hardware limits.")
    if (parameters['dep_mV'] > 1499 or
            parameters['dep_mV'] < -1500):
        raise InputError(parameters['dep_mV'],
                    "Deposition potential exceeds hardware limits.")
    if (parameters['clean_s'] < 0):
        raise InputError(parameters['clean_s'],
                         "Clean time cannot be negative.")
    if (parameters['dep_s'] < 0):
        raise InputError(parameters['dep_s'],
                         "Deposition time cannot be negative.")
    if (parameters['start'] > 1499 or parameters['start'] < -1500):
        raise InputError(parameters['start'],
                         "Start parameter exceeds hardware limits.")
    if (parameters['slope'] > 2000 or parameters['slope'] < 1):
        raise InputError(parameters['slope'],
                         "Slope parameter exceeds hardware limits.")
    if (parameters['v1'] > 1499 or parameters['v1'] < -1500):
        raise InputError(parameters['v1'],
                      "Vertex 1 parameter exceeds hardware limits.")
    if (parameters['v2'] > 1499 or parameters['v2'] < -1500):
        raise InputError(parameters['v2'],
                      "Vertex 2 parameter exceeds hardware limits.")
    if (parameters['scans'] < 1 or parameters['scans'] > 255):
        raise InputError(parameters['scans'], 
                         "Scans parameter outside limits.")
    if parameters['v1'] == parameters['v2']:
        raise InputError(parameters['v1'],
                         "Vertex 1 cannot equal Vertex 2.")
                         
def swv_test(params):
    """Test SWV parameters for sanity"""
    test_parameters = ['clean_mV', 'dep_mV', 'clean_s', 'dep_s', 'start',
                       'stop', 'step', 'pulse', 'freq']
    parameters = {}
    for i in params:
        if i in test_parameters:
            parameters[i] = int(params[i])
    
    if params['cyclic_true'] :
        if int(params['scans']) < 1:
            raise InputError(params['scans'],
                            "Must have at least one scan.")
    else:
        params['scans'] = 0
    
    # check parameters are within hardware limits (doesn't
    # check if pulse will go out of bounds, but instrument
    # checks this (I think))
    if (parameters['clean_mV'] > 1499 or
            parameters['clean_mV'] < -1500):
        raise InputError(parameters['clean_mV'],
                         "Clean potential exceeds hardware limits.")
    if (parameters['dep_mV'] > 1499 or
            parameters['dep_mV'] < -1500):
        raise InputError(parameters['dep_mV'],
                    "Deposition potential exceeds hardware limits.")
    if (parameters['clean_s'] < 0):
        raise InputError(parameters['clean_s'],
                         "Clean time cannot be negative.")
    if (parameters['dep_s'] < 0):
        raise InputError(parameters['dep_s'],
                         "Deposition time cannot be negative.")
    if (parameters['start'] > 1499 or parameters['start'] < -1500):
        raise InputError(parameters['start'],
                         "Start parameter exceeds hardware limits.")
    if (parameters['step'] > 200 or parameters['step'] < 1):
        raise InputError(parameters['step'],
                   "Step height parameter exceeds hardware limits.")
    if (parameters['stop'] > 1499 or parameters['stop'] < -1500):
        raise InputError(parameters['stop'],
                          "Stop parameter exceeds hardware limits.")
    if (parameters['pulse'] > 150 or parameters['pulse'] < 1):
        raise InputError(parameters['pulse'],
                  "Pulse height parameter exceeds hardware limits.")
    if (parameters['freq'] < 1 or parameters['freq'] > 1000):
        raise InputError(parameters['freq'],
                         "Frequency parameter outside limits.")
    if parameters['start'] == parameters['stop']:
        raise InputError(parameters['start'],
                         "Start cannot equal Stop.")
                         
def dpv_test(params):
    """Test DPV parameters for sanity"""
    test_parameters = ['clean_mV', 'dep_mV', 'clean_s', 'dep_s', 'start',
                       'stop', 'step', 'pulse', 'period', 'width']
    parameters = {}
    for i in params:
        if i in test_parameters:
            parameters[i] = int(params[i])

    if (parameters['clean_mV'] > 1499 or
            parameters['clean_mV'] < -1500):
        raise InputError(parameters['clean_mV'],
                         "Clean potential exceeds hardware limits.")
    if (parameters['dep_mV'] > 1499 or
            parameters['dep_mV'] < -1500):
        raise InputError(parameters['dep_mV'],
                    "Deposition potential exceeds hardware limits.")
    if (parameters['clean_s'] < 0):
        raise InputError(parameters['clean_s'],
                         "Clean time cannot be negative.")
    if (parameters['dep_s'] < 0):
        raise InputError(parameters['dep_s'],
                         "Deposition time cannot be negative.")
    if (parameters['start'] > 1499 or parameters['start'] < -1500):
        raise InputError(parameters['start'],
                         "Start parameter exceeds hardware limits.")
    if (parameters['step'] > 200 or parameters['step'] < 1):
        raise InputError(parameters['step'],
                   "Step height parameter exceeds hardware limits.")
    if (parameters['stop'] > 1499 or parameters['stop'] < -1500):
        raise InputError(parameters['stop'],
                         "Stop parameter exceeds hardware limits.")
    if (parameters['pulse'] > 150 or parameters['pulse'] < 1):
        raise InputError(parameters['pulse'],
            "Pulse height parameter exceeds hardware limits.")
    if (parameters['period'] < 1 or parameters['period'] > 1000):
        raise InputError(parameters['period'], 
                        "Period parameter outside limits.")
    if (parameters['width'] < 1 or parameters['width'] > 1000):
        raise InputError(parameters['width'],
                         "Width parameter outside limits.")
    if parameters['period'] <= parameters['width']:
        raise InputError(parameters['width'],
                         "Width must be less than period.")
    if parameters['start'] == parameters['stop']:
        raise InputError(parameters['start'],
                         "Start cannot equal Stop.")    
                             
def pd_test(parameters):
    """Test PD parameters for sanity"""                         
                             
    if (int(parameters['time']) <= 0):
        raise InputError(parameters['time'],
                         "Time must be greater than zero.")
    if (int(parameters['time']) > 65535):
        raise InputError(parameters['time'],
                         "Time must fit in 16-bit counter.")
    if (parameters['sync_true'] and parameters['shutter_true']):
        if (float(parameters['sync_freq']) > 30 or
            float(parameters['sync_freq']) <= 0):
            raise InputError(parameters['sync_freq'],
                            "Frequency must be between 0 and 30 Hz.")
        if (float(parameters['fft_start']) < 0 or
            float(parameters['fft_start']) > float(parameters['time'])-1):
            raise InputError(parameters['fft_start'],
                            "FFT must start between 0 and time-1.")
        if float(parameters['fft_int']) < 0:
            raise InputError(
                parameters['fft_int'],
                "Integral bandwidth must be greater than 0"
            )       

def pot_test(params):
    """Test POT parameters for sanity"""
    test_parameters = ['time']
    parameters = {}
    for i in params:
        if i in test_parameters:
            parameters[i] = int(params[i])
            
    if (int(parameters['time']) <= 0):
        raise InputError(parameters['time'],
                         "Time must be greater than zero.")
    if (int(parameters['time']) > 65535):
        raise InputError(parameters['time'],
                         "Time must fit in 16-bit counter.")