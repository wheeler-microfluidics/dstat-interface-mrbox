#!/usr/bin/env python

import gtk, io
import numpy as np

class npSave:
    def __init__(self, current_exp):
        self.exp = current_exp
        self.fcd = gtk.FileChooserDialog("Save...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        
        self.filters = [gtk.FileFilter()]
        self.filters[0].set_name("NumPy binary (.npy)")
        self.filters[0].add_pattern("*.npy")
        self.filters.append(gtk.FileFilter())
        self.filters[1].set_name("Space separated text (.txt)")
        self.filters[1].add_pattern("*.txt")
        
        self.fcd.set_do_overwrite_confirmation(True)
        for i in self.filters:
            self.fcd.add_filter(i)
                     
        self.response = self.fcd.run()
        
        if self.response == gtk.RESPONSE_OK:
            self.path = self.fcd.get_filename()
            print "Selected filepath: %s" % self.path
            filter_selection = self.fcd.get_filter().get_name()
            
            if filter_selection.endswith("(.npy)"):
                self.npy()
            elif filter_selection.endswith("(.txt)"):
                self.text()
            self.fcd.destroy()
    
    def npy(self):
        self.data = np.array(self.exp.data)
        np.save(self.path, self.data())

    def text(self):
        if not self.path.endswith(".txt"):
            self.path += ".txt"
        
        self.data = np.array(self.exp.data)
        header = ""
        for i in self.exp.commands:
            header += i
        np.savetxt(self.path, self.data.transpose(), header=header, newline='\n')


