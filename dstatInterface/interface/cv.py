#!/usr/bin/env python

import gtk

class cv:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/cv.glade')
        self.builder.connect_signals(self)

        self.clean_mV = self.builder.get_object('clean_mV')
        self.clean_s = self.builder.get_object('clean_s')
        self.dep_mV = self.builder.get_object('dep_mV')
        self.dep_s = self.builder.get_object('dep_s')
        self.start_entry = self.builder.get_object('start_entry')
        self.v1_entry = self.builder.get_object('v1_entry')
        self.v2_entry = self.builder.get_object('v2_entry')
        self.slope_entry = self.builder.get_object('slope_entry')
        self.scans_entry = self.builder.get_object('scans_entry')