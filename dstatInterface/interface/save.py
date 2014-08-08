#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk, io, os
import numpy as np
from datetime import datetime

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
        
    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()

def plotSave(plot):
    fcd = gtk.FileChooserDialog("Save Plot…", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))

    filters = [gtk.FileFilter()]
    filters[0].set_name("Portable Document Format (.pdf)")
    filters[0].add_pattern("*.pdf")
    filters.append(gtk.FileFilter())
    filters[1].set_name("Portable Network Graphics (.png)")
    filters[1].add_pattern("*.png")
    
    fcd.set_do_overwrite_confirmation(True)
    for i in filters:
        fcd.add_filter(i)
    
    response = fcd.run()
    
    if response == gtk.RESPONSE_OK:
        path = fcd.get_filename()
        print "Selected filepath: %s" % path
        filter_selection = fcd.get_filter().get_name()
        
        if filter_selection.endswith("(.pdf)"):
            if not path.endswith(".pdf"):
                path += ".pdf"
        
        elif filter_selection.endswith("(.png)"):
            if not path.endswith(".png"):
                path += ".png"

        plot.figure.savefig(path) #savefig determines format from file extension
        fcd.destroy()
    
    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()

def autoSave(current_exp, dir_button, name, expnumber):
    if name == "":
        name = "file"
    path = dir_button.get_filename()
    path += '/'
    path += name
    path += str(expnumber)

    text(current_exp, path, auto=True)

def autoPlot(plot, dir_button, name, expnumber):
    if name == "":
        name = "file"
    
    path = dir_button.get_filename()
    path += '/'
    path += name
    path += str(expnumber)
    
    if path.endswith(".pdf"):
        path = path.rstrip(".pdf")

    j = 1
    while os.path.exists("".join([path, ".pdf"])):
        if j > 1:
            path = path[:-len(str(j))]
        path += str(j)
        j += 1

    path += ".pdf"
    plot.figure.savefig(path)


def npy(exp, path, auto=False):
    if path.endswith(".npy"):
        path = path.rstrip(".npy")

    data = np.array(exp.data)

    if auto == True:
        j = 1
        while os.path.exists("".join([path, ".npy"])):
            if j > 1:
                path = path[:-len(str(j))]
            path += str(j)
            j += 1

    np.save(path, data)

def text(exp, path, auto=False):
    if path.endswith(".txt"):
        path = path.rstrip(".txt")
    
    if auto == True:
        j = 1
        
        while os.path.exists("".join([path, ".txt"])):
            if j > 1:
                path = path[:-len(str(j))]
            path += str(j)
            j += 1
    
    path += ".txt"
    file = open(path, 'w')
    
    time = datetime.now()

    data = np.array(exp.data)
    header = "".join(['#', time.isoformat(), "\n#"])
    for i in exp.commands:
        header += i

    file.write("".join([header, '\n']))
    for col in zip(*exp.data):
        for row in col:
            file.write(str(row)+ "    ")
        file.write('\n')
    
    file.close()


