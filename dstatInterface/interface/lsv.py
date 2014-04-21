#!/usr/bin/env python

import gtk

class lsv:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/lsv.glade')
        self.builder.connect_signals(self)

        self.start_entry = self.builder.get_object('start_entry')
        self.stop_entry = self.builder.get_object('stop_entry')
        self.slope_entry = self.builder.get_object('slope_entry')