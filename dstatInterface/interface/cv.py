#!/usr/bin/env python

import gtk

class cv:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/cv.glade')
        self.builder.connect_signals(self)
