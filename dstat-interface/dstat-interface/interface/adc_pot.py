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

import gtk

class adc_pot:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/adc_pot.glade')
        self.builder.connect_signals(self)
        self.cell = gtk.CellRendererText()
        
        self.buffer_toggle = self.builder.get_object('buffer_checkbutton')

        #initialize comboboxes
        self.pga_combobox = self.builder.get_object('pga_combobox')
        self.pga_combobox.pack_start(self.cell, True)
        self.pga_combobox.add_attribute(self.cell, 'text', 1)
        self.pga_combobox.set_active(1)

        self.srate_combobox = self.builder.get_object('srate_combobox')
        self.srate_combobox.pack_start(self.cell, True)
        self.srate_combobox.add_attribute(self.cell, 'text', 1)
        self.srate_combobox.set_active(7)
        
        self.gain_combobox = self.builder.get_object('gain_combobox')
        self.gain_combobox.pack_start(self.cell, True)
        self.gain_combobox.add_attribute(self.cell, 'text', 1)
        self.gain_combobox.set_active(2)