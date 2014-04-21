#!/usr/bin/env python

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
        self.gain_combobox.set_active(1)