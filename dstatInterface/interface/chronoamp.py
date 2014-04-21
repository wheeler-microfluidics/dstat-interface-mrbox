#!/usr/bin/env python

import gtk

class chronoamp:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/chronoamp.glade')
        self.builder.connect_signals(self)
        self.cell = gtk.CellRendererText()