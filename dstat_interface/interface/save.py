#!/usr/bin/env python
# -*- coding: utf-8 -*-
#     DStat Interface - An interface for the open hardware DStat potentiostat
#     Copyright (C) 2014  Michael D. M. Dryden - 
#     Wheeler Microfluidics Laboratory <http://microfluidics.utoronto.ca>
#         
#     
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk, io, os
import numpy as np

from errors import InputError, VarError, ErrorLogger
_logger = ErrorLogger(sender="dstat-interface-save")

def manSave(current_exp):
    fcd = gtk.FileChooserDialog("Save...", None, gtk.FILE_CHOOSER_ACTION_SAVE,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_SAVE, gtk.RESPONSE_OK))
    
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
        _logger.error(" ".join(("Selected filepath:", path)),'INFO')
        filter_selection = fcd.get_filter().get_name()
        
        if filter_selection.endswith("(.npy)"):
            if (current_exp.parameters['shutter'] and current_exp.parameters['sync']):
                npy(current_exp, current_exp.data, "-".join((path,'data')))
                npy(current_exp, current_exp.ftdata, "-".join((path,'ft')))
            else:
                npy(current_exp, current_exp.data, path, auto=True)
        elif filter_selection.endswith("(.txt)"):
            if (current_exp.parameters['shutter'] and current_exp.parameters['sync']):
                text(current_exp, current_exp.data, "-".join((path,'data')))
                text(current_exp, current_exp.ftdata, "-".join((path,'ft')))
            else:
                text(current_exp, current_exp.data, path, auto=True)
        fcd.destroy()
        
    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()

def plotSave(plots):
    fcd = gtk.FileChooserDialog("Save Plot…", None,
                                gtk.FILE_CHOOSER_ACTION_SAVE,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_SAVE, gtk.RESPONSE_OK))

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
        _logger.error(" ".join(("Selected filepath:", path)),'INFO')
        filter_selection = fcd.get_filter().get_name()
        
        for i in plots:
            path += '-'
            path += i
        
            if filter_selection.endswith("(.pdf)"):
                if not path.endswith(".pdf"):
                    path += ".pdf"
            
            elif filter_selection.endswith("(.png)"):
                if not path.endswith(".png"):
                    path += ".png"
    
            plots[i].figure.savefig(path)  # determines format from file extension
        fcd.destroy()
    
    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()

def autoSave(current_exp, dir_button, name, expnumber):
    if name == "":
        name = "file"
    path = dir_button.get_filename()
    path += '/'
    path += name
    path += '-'
    path += str(expnumber)
    
    if (current_exp.parameters['shutter'] and current_exp.parameters['sync']):
        text(current_exp, current_exp.data, "-".join((path,'data')), auto=True)
        text(current_exp, current_exp.ftdata, "-".join((path,'ft')), auto=True)
    else:
        text(current_exp, current_exp.data, path, auto=True)

def autoPlot(plots, dir_button, name, expnumber):
    for i in plots:
        if name == "":
            name = "file"
        
        path = dir_button.get_filename()
        path += '/'
        path += name
        path += '-'
        path += str(expnumber)
        path += '-'
        path += i
        
        if path.endswith(".pdf"):
            path = path.rstrip(".pdf")
    
        j = 1
        while os.path.exists("".join([path, ".pdf"])):
            if j > 1:
                path = path[:-len(str(j))]
            path += str(j)
            j += 1
    
        path += ".pdf"
        plots[i].figure.savefig(path)

def npy(exp, data, path, auto=False):
    if path.endswith(".npy"):
        path = path.rstrip(".npy")

    if auto == True:
        j = 1
        while os.path.exists("".join([path, ".npy"])):
            if j > 1:
                path = path[:-len(str(j))]
            path += str(j)
            j += 1

    np.save(path, data)

def text(exp, data, path, auto=False):
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
    
    time = exp.time

    header = "".join(['#', time.isoformat(), "\n#"])
    for i in exp.commands:
        header += i
    
    try:
        if exp.ft_int:
            header += "\n"
            header += "".join(
                (
                    "# FT Integral (",
                    str(exp.parameters['sync_freq']),
                    "±",
                    str(exp.parameters['fft_int']/2),
                    " Hz): ",
                    str(exp.ft_int),
                    " A"
                )
            )
    except AttributeError:
        pass

    file.write("".join([header, '\n']))
    for col in zip(*data):
        for row in col:
            file.write(str(row)+ "    ")
        file.write('\n')
    
    file.close()
