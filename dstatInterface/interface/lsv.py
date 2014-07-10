#!/usr/bin/env python

import gtk

class lsv:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/lsv.glade')
        self.builder.connect_signals(self)
        
        
        self.clean_mV = self.builder.get_object('clean_mV')
        self.clean_s = self.builder.get_object('clean_s')
        self.dep_mV = self.builder.get_object('dep_mV')
        self.dep_s = self.builder.get_object('dep_s')
        self.start_entry = self.builder.get_object('start_entry')
        self.stop_entry = self.builder.get_object('stop_entry')
        self.slope_entry = self.builder.get_object('slope_entry')