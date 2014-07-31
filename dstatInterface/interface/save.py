#!/usr/bin/env python

import gtk, io, os
import numpy as np

def manSave(current_exp):
    exp = current_exp
    fcd = gtk.FileChooserDialog("Save...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
    
    filters = [gtk.FileFilter()]
    filters[0].set_name("NumPy binary (.npy)")
    filters[0].add_pattern("*.npy")
    filters.append(gtk.FileFilter())
    filters[1].set_name("Space separated text (.txt)")
    filters[1].add_pattern("*.txt")
    
    fcd.set_do_overwrite_confirmation(True)
    for i in filters:
        fcd.add_filter(i)
                 
    response = fcd.run()
    
    if response == gtk.RESPONSE_OK:
        path = fcd.get_filename()
        print "Selected filepath: %s" % path
        filter_selection = fcd.get_filter().get_name()
        
        if filter_selection.endswith("(.npy)"):
            npy(exp, path)
        elif filter_selection.endswith("(.txt)"):
            text(exp, path)
        fcd.destroy()
        

def autoSave(current_exp, dir_button, name, expnumber):
    if name == "":
        name = "file"
    path = dir_button.get_filename()
    path += '/'
    path += name
    path += str(expnumber)

    text(current_exp, path)


def npy(exp, path):
    if path.endswith(".npy"):
        path = path.rstrip(".npy")

    data = np.array(exp.data)
    j = 1
    while os.path.exists("".join([path, ".npy"])):
        if j > 1:
            path = path[:-len(str(j))]
        path += str(j)
        j += 1
    np.save(path, data)

def text(exp, path):
    if path.endswith(".txt"):
        path = path.rstrip(".txt")
    
    j = 1
    
    while os.path.exists("".join([path, ".txt"])):
        if j > 1:
            path = path[:-len(str(j))]
        path += str(j)
        j += 1
    
    path += ".txt"
    
    data = np.array(exp.data)
    header = ""
    for i in exp.commands:
        header += i

    np.savetxt(path, data.transpose(), header=header, newline='\n')


