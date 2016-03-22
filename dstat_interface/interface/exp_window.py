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
        
        self.classes = {}
        self.classes['cae'] = exp.Chronoamp()
        self.classes['lsv'] = exp.LSV()
        self.classes['cve'] = exp.CV()
        self.classes['swv'] = exp.SWV()
        self.classes['dpv'] = exp.DPV()
        self.classes['acv'] = exp.ACV()
        self.classes['pde'] = exp.PD()
        self.classes['pot'] = exp.POT()
        self.classes['cal'] = exp.CAL()
 
        #fill exp_section
        exp_section = self.builder.get_object('exp_section_box')
        self.containers = {}
        
        for key, cls in self.classes.iteritems():
            self.containers[key] = cls.builder.get_object('scrolledwindow1')

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
        
        return True
        
    def get_params(self, experiment):
        return self.classes[experiment].param_group.parameters
    
    def set_params(self, experiment, parameters):
        self.classes[experiment].param_group.parameters = parameters