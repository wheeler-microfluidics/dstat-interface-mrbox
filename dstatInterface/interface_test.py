#!/usr/bin/env python

import sys
try:
    import pygtk
    pygtk.require('2.0')
except:
    pass
try:
    import gtk
except:
    print('GTK not available')
    sys.exit(1)

import interface.adc_pot as adc_pot
import interface.chronoamp as chronoamp
import interface.lsv as lsv
import interface.cv as cv
import interface.swv as swv
import interface.acv as acv
import interface.pd as pd
import dstat_comm as comm
from serial import SerialException

import mpltest

class Error(Exception):
    pass

class InputError(Error):
    """Exception raised for errors in the input.
        
        Attributes:
        expr -- input expression in which the error occurred
        msg  -- error message
        """
    
    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

class main:
    
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/dstatinterface.glade')
        self.builder.connect_signals(self)
        self.cell = gtk.CellRendererText()

        #create instance of interface components
        self.statusbar = self.builder.get_object('statusbar')
        self.window = self.builder.get_object('window1')
        self.aboutdialog = self.builder.get_object('aboutdialog1')
        self.databuffer = self.builder.get_object('databuffer1')
        self.adc_pot = adc_pot.adc_pot()
        self.chronoamp = chronoamp.chronoamp()
        self.lsv = lsv.lsv()
        self.cv = cv.cv()
        self.swv = swv.swv()
        self.acv = acv.acv()
        self.pd = pd.pd()
        
        self.error_context_id = self.statusbar.get_context_id("error")
        
        self.plotbox = mpltest.plotbox()
        self.plotwindow = self.builder.get_object('plotbox')
        self.plotbox.vbox.reparent(self.plotwindow)
        self.plotint_checkbox = self.builder.get_object('plotinteractive_checkbutton')
        self.updatelimit_adj = self.builder.get_object('updatesamples_adj')
        
        #fill exp_section
        self.exp_section = self.builder.get_object('exp_section_box')
        self.chronoamp_container = self.chronoamp.builder.get_object('scrolledwindow1')
        self.chronoamp_container.reparent(self.exp_section)
        self.lsv_container = self.lsv.builder.get_object('scrolledwindow1')
        self.lsv_container.reparent(self.exp_section)
        self.cv_container = self.cv.builder.get_object('scrolledwindow1')
        self.cv_container.reparent(self.exp_section)
        self.swv_container = self.swv.builder.get_object('scrolledwindow1')
        self.swv_container.reparent(self.exp_section)
        self.acv_container = self.acv.builder.get_object('scrolledwindow1')
        self.acv_container.reparent(self.exp_section)
        self.pd_container = self.pd.builder.get_object('scrolledwindow1')
        self.pd_container.reparent(self.exp_section)
        
        #fill adc_pot_box
        self.adc_pot_box = self.builder.get_object('gain_adc_box')
        self.adc_pot_container = self.adc_pot.builder.get_object('vbox1')
        self.adc_pot_container.reparent(self.adc_pot_box)
        
        #fill serial
        self.serial_combobox = self.builder.get_object('serial_combobox')
        self.serial_combobox.pack_start(self.cell, True)
        self.serial_combobox.add_attribute(self.cell, 'text', 0)
        
        self.serial_liststore = self.builder.get_object('serial_liststore')
        self.serial_devices = comm.SerialDevices()
        
        for i in self.serial_devices.ports:
            self.serial_liststore.append([i])
        
        self.serial_combobox.set_active(0)
        
        #initialize experiment selection combobox
        self.expcombobox = self.builder.get_object('expcombobox')
        self.expcombobox.pack_start(self.cell, True)
        self.expcombobox.add_attribute(self.cell, 'text', 1)
        self.expcombobox.set_active(0)
        
        self.spinner = self.builder.get_object('spinner')

        self.mainwindow = self.builder.get_object('window1')
        self.mainwindow.set_title("Dstat Interface 0.1")
        self.mainwindow.show_all()
        
        ##hide unused experiment controls
        #self.chronoamp_container.hide()
        self.lsv_container.hide()
        self.cv_container.hide()
        self.swv_container.hide()
        self.acv_container.hide()
        self.pd_container.hide()

    def exp_param_show(self, selection):
        self.chronoamp_container.hide()
        self.lsv_container.hide()
        self.cv_container.hide()
        self.swv_container.hide()
        self.acv_container.hide()
        self.pd_container.hide()
        
        self.statusbar.remove_all(self.error_context_id)

        if selection == 0:
            self.chronoamp_container.show()
        elif selection == 1:
            self.lsv_container.show()
        elif selection == 2:
            self.cv_container.show()
        elif selection == 3:
            self.swv_container.show()
        elif selection == 4:
            self.acv_container.show()
        elif selection == 5:
            self.pd_container.show()
        else:
            self.statusbar.push(self.error_context_id, "Experiment not yet implemented")

    def on_window1_destroy(self, object, data=None):
        print "quit with cancel"
        gtk.main_quit()

    def on_gtk_quit_activate(self, menuitem, data=None):
        print "quit from menu"
        gtk.main_quit()

    def on_gtk_about_activate(self, menuitem, data=None):
        print "help about selected"
        self.response = self.aboutdialog.run() #waits for user to click close
        self.aboutdialog.hide()

    def on_expcombobox_changed(self, data=None):
        self.exp_param_show(self.expcombobox.get_active())

    def on_serial_refresh_clicked(self, data=None):
        self.serial_devices.refresh()
        self.serial_liststore.clear()
        
        for i in self.serial_devices.ports:
            self.serial_liststore.append([i])

    def on_pot_start_clicked(self, data=None):
        selection = self.expcombobox.get_active()
        if self.adc_pot.buffer_toggle.get_active(): #True if box checked
            adc_buffer = "2"
        else:
            adc_buffer = "0"
        self.srate_model = self.adc_pot.srate_combobox.get_model()
        self.pga_model = self.adc_pot.pga_combobox.get_model()
        self.gain_model = self.adc_pot.gain_combobox.get_model()
        
        adc_rate = self.srate_model.get_value(self.adc_pot.srate_combobox.get_active_iter(), 2) #third column
        adc_pga = self.pga_model.get_value(self.adc_pot.pga_combobox.get_active_iter(), 2)
        gain = self.gain_model.get_value(self.adc_pot.gain_combobox.get_active_iter(), 2)
        update = self.plotint_checkbox.get_active()
        updatelimit = int(self.updatelimit_adj.get_value())
        
        try:
            if selection == 0: #CA
                potential = [int(r[0]) for r in self.chronoamp.model]
                time = [int(r[1]) for r in self.chronoamp.model]
            
                if not potential:
                    raise InputError(potential,"Step table is empty")
                
                self.current_exp = comm.chronoamp(adc_buffer, adc_rate, adc_pga, gain, potential, time, update, updatelimit)
                self.current_exp.run(self.serial_liststore.get_value(self.serial_combobox.get_active_iter(), 0), self.plotbox, self.databuffer)
            elif selection == 1: #LSV
                self.statusbar.remove_all(self.error_context_id)
                start = int(self.lsv.start_entry.get_text())
                stop = int(self.lsv.stop_entry.get_text())
                slope = int(self.lsv.slope_entry.get_text())
                
                #check parameters are within hardware limits
                if (start > 1499 or start < -1500):
                    raise InputError(start,"Start parameter exceeds hardware limits.")
                if (stop > 1499 or stop < -1500):
                    raise InputError(stop,"Stop parameter exceeds hardware limits.")
                if (slope > 2000 or slope < 1):
                    raise InputError(slope,"Slope parameter exceeds hardware limits.")
                if start == stop:
                    raise InputError(start,"Start cannot equal Stop.")
            
                self.current_exp = comm.lsv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, slope, update, updatelimit)
                self.current_exp.run(self.serial_liststore.get_value(self.serial_combobox.get_active_iter(), 0), self.plotbox, self.databuffer)
            
            elif selection == 2: #CV
                self.statusbar.remove_all(self.error_context_id) #clear statusbar
                start = int(self.cv.start_entry.get_text())
                slope = int(self.cv.slope_entry.get_text())
                v1 = int(self.cv.v1_entry.get_text())
                v2 = int(self.cv.v2_entry.get_text())
                scans = int(self.cv.scans_entry.get_text())
                
                #check parameters are within hardware limits
                if (start > 1499 or start < -1500):
                    raise InputError(start,"Start parameter exceeds hardware limits.")
                if (slope > 2000 or slope < 1):
                    raise InputError(slope,"Slope parameter exceeds hardware limits.")
                if (v1 > 1499 or v1 < -1500):
                    raise InputError(v1,"Vertex 1 parameter exceeds hardware limits.")
                if (v2 > 1499 or v2 < -1500):
                    raise InputError(v2,"Vertex 2 parameter exceeds hardware limits.")
                if (scans < 1 or scans > 255):
                    raise InputError(scans, "Scans parameter outside limits.")
                if v1 == v2:
                    raise InputError(start,"Vertex 1 cannot equal Vertex 2.")
                
                comm.cv_exp(adc_buffer, adc_rate, adc_pga, gain, v1, v2, start, scans, slope, update, updatelimit)
        
            elif selection == 3: #SWV
                self.statusbar.remove_all(self.error_context_id) #clear statusbar
                start = int(self.swv.start_entry.get_text())
                stop = int(self.swv.stop_entry.get_text())
                step = int(self.swv.step_entry.get_text())
                pulse = int(self.swv.pulse_entry.get_text())
                freq = int(self.swv.freq_entry.get_text())
                
                #check parameters are within hardware limits (doesn't check if pulse will go out of bounds, but instrument checks this (I think))
                if (start > 1499 or start < -1500):
                    raise InputError(start,"Start parameter exceeds hardware limits.")
                if (step > 200 or step < 1):
                    raise InputError(step,"Step height parameter exceeds hardware limits.")
                if (stop > 1499 or stop < -1500):
                    raise InputError(stop,"Stop parameter exceeds hardware limits.")
                if (pulse > 150 or pulse < 1):
                    raise InputError(pulse,"Pulse height parameter exceeds hardware limits.")
                if (freq < 1 or freq > 1000):
                    raise InputError(freq, "Frequency parameter outside limits.")
                if start == stop:
                    raise InputError(start,"Start cannot equal Stop.")
                
                comm.swv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, step, pulse, freq, update, updatelimit)
                    
            else:
                self.statusbar.push(self.error_context_id, "Experiment not yet implemented.")
                
        except ValueError:
            self.statusbar.push(self.error_context_id, "Experiment parameters must be integers.")
        
        except InputError as e:
            self.statusbar.push(self.error_context_id, e.msg)
        
        except SerialException:
            self.statusbar.push(self.error_context_id, "Could not establish serial connection.")

if __name__ == "__main__":
    main = main()
    gtk.main()