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

import interface.exp_int as exp

class Experiments:
    def __init__(self, builder):
        self.builder = builder
        
        # (experiment index in UI, experiment)
        self.classes = {}
        self.classes['cae'] = (0, exp.Chronoamp())
        self.classes['lsv'] = (1, exp.LSV())
        self.classes['cve'] = (2, exp.CV())
        self.classes['swv'] = (3, exp.SWV())
        self.classes['dpv'] = (4, exp.DPV())
        self.classes['acv'] = (5, exp.ACV())
        self.classes['pde'] = (6, exp.PD())
        self.classes['pot'] = (7, exp.POT())
        self.classes['cal'] = (8, exp.CAL())
        
        # Create reverse lookup
        self.select_to_key = {}
        for key, value in self.classes.iteritems():
            self.select_to_key[value[0]] = key
 
        #fill exp_section
        exp_section = self.builder.get_object('exp_section_box')
        self.containers = {}
        
        for key, cls in self.classes.iteritems():
            self.containers[key] = cls[1].builder.get_object('scrolledwindow1')

        for key in self.containers:
            self.containers[key].reparent(exp_section)
            self.containers[key].hide()
        
    def set_exp(self, selection):
        """Changes parameter tab to selected experiment. Returns True if 
        successful, False if invalid selection received.
        
        Arguments:
        selection -- id string of experiment type
        """
        for key in self.containers:
            self.containers[key].hide()

        self.containers[selection].show()
        self.selected_exp = selection
        
        return True
        
    def get_params(self, experiment):
        return self.classes[experiment][1].params
    
    def set_params(self, experiment, parameters):
        self.classes[experiment][1].params = parameters