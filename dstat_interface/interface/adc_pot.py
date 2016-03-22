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

import gtk
from parameters import ParametersGroup

v1_1_gain = [(0, "100 Ω (15 mA FS)", 0),
             (1, "300 Ω (5 mA FS)", 1),
             (2, "3 kΩ (500 µA FS)", 2),
             (3, "30 kΩ (50 µA FS)", 3),
             (4, "300 kΩ (5 µA FS)", 4),
             (5, "3 MΩ (500 nA FS)", 5),
             (6, "30 MΩ (50 nA FS)", 6),
             (7, "500 MΩ (3 nA FS)", 7)]

v1_2_gain = [(0, "Bypass", 0),
             (1, "100 Ω (15 mA FS)", 1),
             (2, "3 kΩ (500 µA FS)", 2),
             (3, "30 kΩ (50 µA FS)", 3),
             (4, "300 kΩ (5 µA FS)", 4),
             (5, "3 MΩ (500 nA FS)", 5),
             (6, "30 MΩ (50 nA FS)", 6),
             (7, "100 MΩ (15 nA FS)", 7)]
             

class adc_pot(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/adc_pot.glade')
        self.builder.connect_signals(self)
        self.cell = gtk.CellRendererText()
        
        # list of options
        param_keys = []
        
        self.buffer_toggle = self.builder.get_object('buffer_checkbutton')
        param_keys.append(('adc_buffer_true',
                          self.buffer_toggle.get_active,
                          self.buffer_toggle.set_active))
        self.short_toggle = self.builder.get_object('short_checkbutton')
        param_keys.append(('pot_short_true',
                          self.short_toggle.get_active,
                          self.short_toggle.set_active))
        
        #initialize comboboxes
        self.pga_combobox = self.builder.get_object('pga_combobox')
        self.pga_combobox.pack_start(self.cell, True)
        self.pga_combobox.add_attribute(self.cell, 'text', 1)
        self.pga_combobox.set_active(1)
        param_keys.append(('adc_pga_index',
                          self.pga_combobox.get_active,
                          self.pga_combobox.set_active))

        self.srate_combobox = self.builder.get_object('srate_combobox')
        self.srate_combobox.pack_start(self.cell, True)
        self.srate_combobox.add_attribute(self.cell, 'text', 1)
        self.srate_combobox.set_active(7)
        param_keys.append(('adc_srate_index',
                          self.srate_combobox.get_active,
                          self.srate_combobox.set_active))
        
        self.gain_combobox = self.builder.get_object('gain_combobox')
        self.gain_liststore = self.builder.get_object('gain_liststore')
        self.gain_combobox.pack_start(self.cell, True)
        self.gain_combobox.add_attribute(self.cell, 'text', 1)
        self.gain_combobox.set_active(2)
        param_keys.append(('pot_gain_index',
                          self.gain_combobox.get_active,
                          self.gain_combobox.set_active))
        
        keys, getters, setters = zip(*param_keys)
        self.param_group = ParametersGroup(keys, getters, setters)
        
    def set_version(self, version):
        """ Sets menus for DStat version. """
        self.gain_liststore.clear()
        if version[0] == 1:
            if version[1] == 1:
                for i in v1_1_gain:
                    self.gain_liststore.append(i)
            elif version[1] >= 2:
                for i in v1_2_gain:
                    self.gain_liststore.append(i)
            
        