#!/usr/bin/env python

import gtk, io
import numpy as np

class npSave:
    def __init__(self, current_exp):
        self.exp = current_exp
        self.fcd = gtk.FileChooserDialog("Save...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        
        self.fcd.set_do_overwrite_confirmation(True)
                     
        self.response = self.fcd.run()
        
        if self.response == gtk.RESPONSE_OK:
            self.path = self.fcd.get_filename()
            print "Selected filepath: %s" % self.path
            self.npy()
            self.fcd.destroy()
    
    def npy(self):
        self.data = np.array(self.exp.data)
        np.save(self.path, self.data)


