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

"""
Functions for analyzing data.
""" 
import logging

import pygtk
import gtk
from numpy import mean, trapz

logger = logging.getLogger('dstat.analysis')

class AnalysisOptions(object):
    """Analysis options window."""
    def __init__(self, builder):
        self.builder = builder
        self.builder.add_from_file('interface/analysis_options.glade')
        self.builder.connect_signals(self)
        
        self.window = self.builder.get_object('analysis_dialog')
        self.stats_button = self.builder.get_object('stats_button')
        self.stats_start = self.builder.get_object('stats_start_spin')
        self.stats_start_button = self.builder.get_object('stats_start_button')
        self.stats_stop = self.builder.get_object('stats_stop_spin')        
        self.stats_stop_button = self.builder.get_object('stats_stop_button')

        self.stats_button.connect('toggled',
                                  self.on_button_toggled_hide,
                                      [self.stats_stop, 
                                       self.stats_stop_button,
                                       self.stats_start,
                                       self.stats_start_button
                                       ]
                                  )
        
        self._params = {'stats_true':False,
                        'stats_start_true':False,
                        'stats_stop':0,
                        'stats_stop_true':False,
                        'stats_start':0
                        }
    
    def show(self):
        """Show options window."""
        self.window.run()
        self.window.hide()
    
    def on_button_toggled_hide(self, control, widgets):
        """Hide unchecked fields"""
        active = control.get_active()
        
        for widget in widgets:
            widget.set_sensitive(active)
    
    @property
    def params(self):
        """Getter for analysis params"""
        self._params['stats_true'] = self.stats_button.get_active()
        
        self._params['stats_start_true'] = self.stats_start_button.get_active()
        self._params['stats_start'] = self.stats_start.get_value()
        
        self._params['stats_stop_true'] = self.stats_stop_button.get_active()
        self._params['stats_stop'] = self.stats_stop.get_value()

        return self._params
    
    @params.setter
    def params(self, params):
        for key in self._params:
            if key in params:
                self._params[key] = params[key]
        
        self.stats_button.set_active(self._params['stats_true'])
        self.stats_start_button.set_active(self._params['stats_start_true'])
        self.stats_start.set_value(self._params['stats_start'])
        self.stats_stop_button.set_active(self._params['stats_stop_true'])
        self.stats_stop.set_value(self._params['stats_stop'])

def do_analysis(experiment):
    """Takes an experiment class instance and runs selected analysis."""
    
    experiment.analysis = {}
    
    if experiment.parameters['stats_true']:
        if (experiment.parameters['stats_start_true'] or
            experiment.parameters['stats_stop_true']):
            
            if experiment.parameters['stats_start_true']:
                start = experiment.parameters['stats_start']
            else:
                start = min(experiment.data['data'][0][0])
        
            if experiment.parameters['stats_stop_true']:
                stop = experiment.parameters['stats_stop']
            else:
                stop = min(experiment.data['data'][0][0])
                
            data = _data_slice(experiment.data['data'],
                               start,
                               stop
                               )
        else:
            data = experiment.data['data']
        
        experiment.analysis.update(_summary_stats(data))
    
    try:
        x, y = experiment.data['ft'][0]
        experiment.analysis['FT Integral'] = _integrateSpectrum(
                x,
                y,
                float(experiment.parameters['sync_freq']),
                float(experiment.parameters['fft_int'])
        )

    except KeyError:
        pass

def _data_slice(data, start, stop):
    """Accepts data (as list of tuples of lists) and returns copy of data
    between start and stop (in whatever x-axis units for the experiment type).
    """
    output = []
    
    for scan in range(len(data)):
        t = []
        for i in range(len(data[scan])):
            t.append([])
        output.append(tuple(t))
        
        for i in range(len(data[scan][0])): # x-axis column
            if data[scan][0][i] >= start or data[scan][0][i] <= stop:
                for d in range(len(output[scan])):
                    output[scan][d].append(data[scan][d][i])              
    
    return output
                    
def _summary_stats(data):
    """Takes data and returns summary statistics of first y variable as dict of 
    name, (scan, values).
    """
    
    stats = {'min':[],'max':[], 'mean':[]}
    
    for scan in range(len(data)):
        stats['min'].append(
                            (scan, min(data[scan][1]))
                            )
        stats['max'].append(
                            (scan, max(data[scan][1]))
                            )
        stats['mean'].append(
                            (scan, mean(data[scan][1]))
                            )
    return stats
    
def _integrateSpectrum(x, y, target, bandwidth):
    """
    Returns integral of range of bandwidth centered on target.
    """
    j = 0
    k = len(x)

    for i in range(len(x)):
        if x[i] >= target-bandwidth/2:
            j = i
            break
    
    for i in range(j,len(x)):
        if x[i] >= target+bandwidth/2:
            k = i
            break

    return [(0, trapz(y=y[j:k], x=x[j:k]))]