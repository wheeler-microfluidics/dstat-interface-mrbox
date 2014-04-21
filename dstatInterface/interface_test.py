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
import dstat_comm as comm

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
        self.adc_pot = adc_pot.adc_pot()
        self.chronoamp = chronoamp.chronoamp()
        self.lsv = lsv.lsv()
        self.cv = cv.cv()
        
        self.error_context_id = self.statusbar.get_context_id("error")
        
        #fill exp_section
        self.exp_section = self.builder.get_object('exp_section_box')
        self.chronoamp_container = self.chronoamp.builder.get_object('scrolledwindow1')
        self.chronoamp_container.reparent(self.exp_section)
        self.lsv_container = self.lsv.builder.get_object('scrolledwindow1')
        self.lsv_container.reparent(self.exp_section)
        self.cv_container = self.cv.builder.get_object('scrolledwindow1')
        self.cv_container.reparent(self.exp_section)
        
        #fill adc_pot_box
        self.adc_pot_box = self.builder.get_object('gain_adc_box')
        self.adc_pot_container = self.adc_pot.builder.get_object('vbox1')
        self.adc_pot_container.reparent(self.adc_pot_box)
        
        #initialize experiment selection combobox
        self.expcombobox = self.builder.get_object('expcombobox')
        self.expcombobox.pack_start(self.cell, True)
        self.expcombobox.add_attribute(self.cell, 'text', 1)
        self.expcombobox.set_active(0)

        self.mainwindow = self.builder.get_object('window1')
        self.mainwindow.set_title("Dstat Interface 0.1")
        self.mainwindow.show_all()
#        self.chronoamp_container.hide()
        self.lsv_container.hide()
        self.cv_container.hide()

    def exp_param_show(self, selection):
        self.chronoamp_container.hide()
        self.lsv_container.hide()
        self.cv_container.hide()
        
        self.statusbar.remove_all(self.error_context_id)

        if selection == 0:
            self.chronoamp_container.show()
        elif selection == 1:
            self.lsv_container.show()
        elif selection == 2:
            self.cv_container.show()
        else:
            self.statusbar.push(self.error_context_id, "Experiment not yet implemented")

    def on_window1_destroy(self, object, data=None):
        print "quit with cancel"
        gtk.main_quit()

    # This is the same as above but for our menu item.
    def on_gtk_quit_activate(self, menuitem, data=None):
        print "quit from menu"
        gtk.main_quit()

    def on_gtk_about_activate(self, menuitem, data=None):
        print "help about selected"
        self.response = self.aboutdialog.run() #waits for user to click close - could test response with if
        self.aboutdialog.hide()

    def on_expcombobox_changed(self, data=None):
        self.exp_param_show(self.expcombobox.get_active())
    
    def on_pot_start_clicked(self, data=None):
        selection = self.expcombobox.get_active()
        
        if selection == 0: #CA
            pass
        elif selection == 1: #LSV
            if self.adc_pot.buffer_toggle.get_active(): #True if box checked
                adc_buffer = "0x2"
            else:
                adc_buffer = "0x0"
            
            self.srate_model = self.adc_pot.srate_combobox.get_model()
            self.pga_model = self.adc_pot.pga_combobox.get_model()
            self.gain_model = self.adc_pot.gain_combobox.get_model()
            
            adc_rate = self.srate_model.get_value(self.adc_pot.srate_combobox.get_active_iter(), 2) #third column
            adc_pga = self.pga_model.get_value(self.adc_pot.pga_combobox.get_active_iter(), 2)
            gain = self.gain_model.get_value(self.adc_pot.gain_combobox.get_active_iter(), 2)
            
            try:
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
                
                comm.lsv_exp(adc_buffer, adc_rate, adc_pga, gain, start, stop, slope)
                
            except ValueError:
                self.statusbar.push(self.error_context_id, "Experiment parameters must be integers.")
            except InputError as e:
                self.statusbar.push(self.error_context_id, e.msg)
        
        elif selection == 2: #CV
            pass
        else:
            pass

if __name__ == "__main__":
    main = main()
    gtk.main()