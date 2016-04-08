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

import io
import os

import gtk
import numpy as np
import logging

logger = logging.getLogger("dstat.interface.save")

from errors import InputError, VarError
from params import save_params, load_params

def manSave(current_exp):
    fcd = gtk.FileChooserDialog("Save...", None, gtk.FILE_CHOOSER_ACTION_SAVE,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_SAVE, gtk.RESPONSE_OK))

    filters = [gtk.FileFilter()]
    filters[0].set_name("Space separated text (.txt)")
    filters[0].add_pattern("*.txt")

    fcd.set_do_overwrite_confirmation(True)
    for i in filters:
        fcd.add_filter(i)

    response = fcd.run()

    if response == gtk.RESPONSE_OK:
        path = fcd.get_filename()
        logger.info("Selected filepath: %s", path)
        filter_selection = fcd.get_filter().get_name()

        if filter_selection.endswith("(.txt)"):
            save_text(current_exp, path)
            
        fcd.destroy()

    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()

def plot_save_dialog(plots):
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
        logger.info("Selected filepath: %s", path)
        filter_selection = fcd.get_filter().get_name()
        
        if filter_selection.endswith("(.pdf)"):
            if not path.endswith(".pdf"):
                path += ".pdf"

        elif filter_selection.endswith("(.png)"):
            if not path.endswith(".png"):
                path += ".png"
        
        save_plot(plots, path)

        fcd.destroy()

    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()


def man_param_save(window):
    fcd = gtk.FileChooserDialog("Save Parameters…",
                                None,
                                gtk.FILE_CHOOSER_ACTION_SAVE,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_SAVE, gtk.RESPONSE_OK)
                                )

    filters = [gtk.FileFilter()]
    filters[0].set_name("Parameter File (.yml)")
    filters[0].add_pattern("*.yml")

    fcd.set_do_overwrite_confirmation(True)
    for i in filters:
        fcd.add_filter(i)

    response = fcd.run()

    if response == gtk.RESPONSE_OK:
        path = fcd.get_filename()
        logger.info("Selected filepath: %s", path)

        if not path.endswith(".yml"):
            path += '.yml'

        save_params(window, path)

        fcd.destroy()

    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()

def man_param_load(window):
    fcd = gtk.FileChooserDialog("Load Parameters…",
                                None,
                                gtk.FILE_CHOOSER_ACTION_OPEN,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK)
                                )

    filters = [gtk.FileFilter()]
    filters[0].set_name("Parameter File (.yml)")
    filters[0].add_pattern("*.yml")

    for i in filters:
        fcd.add_filter(i)

    response = fcd.run()

    if response == gtk.RESPONSE_OK:
        path = fcd.get_filename()
        logger.info("Selected filepath: %s", path)

        load_params(window, path)

        fcd.destroy()

    elif response == gtk.RESPONSE_CANCEL:
        fcd.destroy()

def autoSave(exp, path, name):
    if name == "":
        name = "file"

    path += '/'
    path += name
     
    save_text(exp, path)

def autoPlot(exp, path, name):
    if name == "":
        name = "file"
        
    path += '/'
    path += name

    if not (path.endswith(".pdf") or path.endswith(".png")):
        path += ".pdf"

    save_plot(exp, path)

def save_text(exp, path):
    name, _sep, ext = path.rpartition('.') # ('','',string) if no match
    if _sep == '':
        name = ext
        ext = 'txt'
    
    num = ''
    j = 0
    
    for dname in exp.data: # Test for any existing files
        while os.path.exists("%s%s-%s.%s" % (name, num, dname, ext)):
            j += 1
            num = j
    
    for dname in exp.data: # save data
        file = open("%s%s-%s.%s" % (name, num, dname, ext), 'w')

        time = exp.time
        header = "".join(['# TIME ', time.isoformat(), "\n"])
    
        header += "# DSTAT COMMANDS\n#  "
        for i in exp.commands:
            header += i

        file.write("".join([header, '\n']))
    
        analysis_buffer = []
    
        if exp.analysis != {}:
            analysis_buffer.append("# ANALYSIS")
            for key, value in exp.analysis.iteritems():
                analysis_buffer.append("#  %s:" % key)
                for scan in value:
                    number, result = scan
                    analysis_buffer.append(
                        "#    Scan %s -- %s" % (number, result)
                        )
    
        for i in analysis_buffer:
            file.write("%s\n" % i)
      
        # Write out actual data  
        line_buffer = []
    
        for scan in zip(*exp.data[dname]):
            for dimension in scan:
                for i in range(len(dimension)):
                    try:
                        line_buffer[i] += "%s     " % dimension[i]
                    except IndexError:
                        line_buffer.append("")
                        line_buffer[i] += "%s     " % dimension[i]
            
        for i in line_buffer:
            file.write("%s\n" % i)

        file.close()
        
def save_plot(exp, path):
    """Saves everything in exp.plots to path. Appends a number for duplicates.
    If no file extension or unknown, uses pdf.
    """
    name, _sep, ext = path.rpartition('.')
    if _sep == '':
        name = ext
        ext = 'pdf'
    
    num = ''
    j = 0
    
    for i in exp.plots: # Test for any existing files
        while os.path.exists("%s%s-%s.%s" % (name, num, i, ext)):
            j += 1
            num = j
    
    for i in exp.plots: # save data
        exp.plots[i].figure.savefig("%s%s-%s.%s" % (name, num, i, ext))