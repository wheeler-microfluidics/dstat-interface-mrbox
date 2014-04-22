#!/usr/bin/env python

import gtk

class swv:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/swv.glade')
        self.builder.connect_signals(self)

        self.start_entry = self.builder.get_object('start_entry')
        self.stop_entry = self.builder.get_object('stop_entry')
        self.step_entry = self.builder.get_object('step_entry')
        self.pulse_entry = self.builder.get_object('pulse_entry')
        self.freq_entry = self.builder.get_object('freq_entry')