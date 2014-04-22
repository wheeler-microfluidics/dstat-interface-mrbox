#!/usr/bin/env python

import gtk

class acv:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/acv.glade')
        self.builder.connect_signals(self)

        self.start_entry = self.builder.get_object('start_entry')
        self.stop_entry = self.builder.get_object('stop_entry')
        self.slope_entry = self.builder.get_object('slope_entry')
        self.amplitude_entry = self.builder.get_object('amplitude_entry')
        self.freq_entry = self.builder.get_object('freq_entry')