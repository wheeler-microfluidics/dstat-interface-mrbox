#!/usr/bin/env python

import gtk

class pd:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/pd.glade')
        self.builder.connect_signals(self)

        self.voltage_entry = self.builder.get_object('voltage_entry')
        self.time_entry = self.builder.get_object('time_entry')