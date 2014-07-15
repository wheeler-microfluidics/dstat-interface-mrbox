#!/usr/bin/env python

import sys
try:
    import pygtk
    pygtk.require('2.0')
except:
    pass
try:
    import gtk
    import gobject
except:
    print('GTK not available')
    sys.exit(1)

try:
    import gobject
except:
    print('gobject not available')
    sys.exit(1)

import interface.adc_pot as adc_pot
import interface.chronoamp as chronoamp
import interface.lsv as lsv
import interface.cv as cv
import interface.swv as swv
import interface.acv as acv
import interface.pd as pd
import interface.save as save
import dstat_comm as comm
from serial import SerialException
import multiprocessing

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
        self.rawbuffer = self.builder.get_object('databuffer1')
        self.databuffer = self.builder.get_object('databuffer2')
        self.stopbutton = self.builder.get_object('pot_stop')
        self.startbutton = self.builder.get_object('pot_start')
        self.adc_pot = adc_pot.adc_pot()
        self.chronoamp = chronoamp.chronoamp()
        self.lsv = lsv.lsv()
        self.cv = cv.cv()
        self.swv = swv.swv()
        self.acv = acv.acv()
        self.pd = pd.pd()
        
        self.error_context_id = self.statusbar.get_context_id("error")
        
        self.plotwindow = self.builder.get_object('plotbox')
        self.plotint_checkbox = self.builder.get_object('plotinteractive_checkbutton')
        self.updatelimit_adj = self.builder.get_object('updatesamples_adj')
        self.plot = mpltest.plotbox(self.plotwindow)
        
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
        parameters = {}
        view_parameters = {}
        
        if self.adc_pot.buffer_toggle.get_active(): #True if box checked
            parameters['adc_buffer'] = "2"
        else:
            parameters['adc_buffer'] = "0"
        
        srate_model = self.adc_pot.srate_combobox.get_model()
        pga_model = self.adc_pot.pga_combobox.get_model()
        gain_model = self.adc_pot.gain_combobox.get_model()
        
        parameters['adc_rate'] = srate_model.get_value(self.adc_pot.srate_combobox.get_active_iter(), 2) #third column
        parameters['adc_pga'] = pga_model.get_value(self.adc_pot.pga_combobox.get_active_iter(), 2)
        parameters['gain'] = gain_model.get_value(self.adc_pot.gain_combobox.get_active_iter(), 2)
        
        view_parameters['update'] = self.plotint_checkbox.get_active()
        view_parameters['updatelimit'] = int(self.updatelimit_adj.get_value())
        
        self.line = 0
        self.lastline = 0
        self.lastdataline = 0
        
        self.spinner.start()
        self.startbutton.set_sensitive(False)
        self.stopbutton.set_sensitive(True)
        self.statusbar.remove_all(self.error_context_id)
        
        try:
            if selection == 0: #CA
                parameters['potential'] = [int(r[0]) for r in self.chronoamp.model]
                parameters['time'] = [int(r[1]) for r in self.chronoamp.model]
            
                if not parameters['potential']:
                    raise InputError(parameters['potential'],"Step table is empty")
                
                self.recv_p, self.send_p = multiprocessing.Pipe(duplex=True)
                self.current_exp = comm.chronoamp(parameters, view_parameters, self.plot, self.rawbuffer, self.send_p)
                
                self.p = multiprocessing.Process(target=self.current_exp.run, args=(self.serial_liststore.get_value(self.serial_combobox.get_active_iter(), 0), ))
                self.p.start()
                
                self.send_p.close() #need to close this copy of connection object for EOF signal to work
                
                self.plot_proc = gobject.timeout_add(200, self.experiment_running_plot)
                gobject.idle_add(self.experiment_running)
        
            elif selection == 1: #LSV
                parameters['clean_mV'] = int(self.lsv.clean_mV.get_text())
                parameters['clean_s'] = int(self.lsv.clean_s.get_text())
                parameters['dep_mV'] = int(self.lsv.dep_mV.get_text())
                parameters['dep_s'] = int(self.lsv.dep_s.get_text())
                parameters['start'] = int(self.lsv.start_entry.get_text())
                parameters['stop'] = int(self.lsv.stop_entry.get_text())
                parameters['slope'] = int(self.lsv.slope_entry.get_text())
                
                #check parameters are within hardware limits
                if (parameters['clean_mV'] > 1499 or parameters['clean_mV'] < -1500):
                    raise InputError(parameters['clean_mV'],"Clean potential exceeds hardware limits.")
                if (parameters['dep_mV'] > 1499 or parameters['dep_mV'] < -1500):
                    raise InputError(parameters['dep_mV'],"Deposition potential exceeds hardware limits.")
                if (parameters['clean_s'] < 0):
                    raise InputError(parameters['clean_s'],"Clean time cannot be negative.")
                if (parameters['dep_s'] < 0):
                    raise InputError(parameters['dep_s'],"Deposition time cannot be negative.")
                if (parameters['start'] > 1499 or parameters['start'] < -1500):
                    raise InputError(parameters['start'],"Start parameter exceeds hardware limits.")
                if (parameters['stop'] > 1499 or parameters['stop'] < -1500):
                    raise InputError(parameters['stop'],"Stop parameter exceeds hardware limits.")
                if (parameters['slope'] > 2000 or parameters['slope'] < 1):
                    raise InputError(parameters['slope'],"Slope parameter exceeds hardware limits.")
                if parameters['start'] == parameters['stop']:
                    raise InputError(parameters['start'],"Start cannot equal Stop.")

                self.recv_p, self.send_p = multiprocessing.Pipe(duplex=True)
                self.current_exp = comm.lsv_exp(parameters, view_parameters, self.plot, self.rawbuffer, self.send_p)
                
                self.p = multiprocessing.Process(target=self.current_exp.run, args=(self.serial_liststore.get_value(self.serial_combobox.get_active_iter(), 0), ))
                self.p.start()
                
                self.send_p.close()

                self.plot_proc = gobject.timeout_add(200, self.experiment_running_plot)
                gobject.idle_add(self.experiment_running)
            
            elif selection == 2: #CV
                parameters['clean_mV'] = int(self.cv.clean_mV.get_text())
                parameters['clean_s'] = int(self.cv.clean_s.get_text())
                parameters['dep_mV'] = int(self.cv.dep_mV.get_text())
                parameters['dep_s'] = int(self.cv.dep_s.get_text())
                parameters['start'] = int(self.cv.start_entry.get_text())
                parameters['slope'] = int(self.cv.slope_entry.get_text())
                parameters['v1'] = int(self.cv.v1_entry.get_text())
                parameters['v2'] = int(self.cv.v2_entry.get_text())
                parameters['scans'] = int(self.cv.scans_entry.get_text())
                
                #check parameters are within hardware limits
                if (parameters['clean_mV'] > 1499 or parameters['clean_mV'] < -1500):
                    raise InputError(parameters['clean_mV'],"Clean potential exceeds hardware limits.")
                if (parameters['dep_mV'] > 1499 or parameters['dep_mV'] < -1500):
                    raise InputError(parameters['dep_mV'],"Deposition potential exceeds hardware limits.")
                if (parameters['clean_s'] < 0):
                    raise InputError(parameters['clean_s'],"Clean time cannot be negative.")
                if (parameters['dep_s'] < 0):
                    raise InputError(parameters['dep_s'],"Deposition time cannot be negative.")
                if (parameters['start'] > 1499 or parameters['start'] < -1500):
                    raise InputError(parameters['start'],"Start parameter exceeds hardware limits.")
                if (parameters['slope'] > 2000 or parameters['slope'] < 1):
                    raise InputError(parameters['slope'],"Slope parameter exceeds hardware limits.")
                if (parameters['v1'] > 1499 or parameters['v1'] < -1500):
                    raise InputError(parameters['v1'],"Vertex 1 parameter exceeds hardware limits.")
                if (parameters['v2'] > 1499 or parameters['v2'] < -1500):
                    raise InputError(parameters['v2'],"Vertex 2 parameter exceeds hardware limits.")
                if (parameters['scans'] < 1 or parameters['scans'] > 255):
                    raise InputError(parameters['scans'], "Scans parameter outside limits.")
                if parameters['v1'] == parameters['v2']:
                    raise InputError(parameters['v1'],"Vertex 1 cannot equal Vertex 2.")
                
                self.recv_p, self.send_p = multiprocessing.Pipe(duplex=True)
                self.current_exp = comm.cv_exp(parameters, view_parameters, self.plot, self.rawbuffer, self.send_p)
                
                self.p = multiprocessing.Process(target=self.current_exp.run, args=(self.serial_liststore.get_value(self.serial_combobox.get_active_iter(), 0), ))
                self.p.start()
                
                self.send_p.close()
                
                self.plot_proc = gobject.timeout_add(200, self.experiment_running_plot)
                gobject.idle_add(self.experiment_running)
                
            elif selection == 3: #SWV
                parameters['clean_mV'] = int(self.swv.clean_mV.get_text())
                parameters['clean_s'] = int(self.swv.clean_s.get_text())
                parameters['dep_mV'] = int(self.swv.dep_mV.get_text())
                parameters['dep_s'] = int(self.swv.dep_s.get_text())
                parameters['start'] = int(self.swv.start_entry.get_text())
                parameters['stop'] = int(self.swv.stop_entry.get_text())
                parameters['step'] = int(self.swv.step_entry.get_text())
                parameters['pulse'] = int(self.swv.pulse_entry.get_text())
                parameters['freq'] = int(self.swv.freq_entry.get_text())
                
                if self.swv.cyclic_checkbutton.get_active():
                    parameters['scans'] = int(self.swv.scans_entry.get_text())
                    if parameters['scans'] < 1:
                        raise InputError(parameters['scans'],"Must have at least one scan.")
                else:
                    parameters['scans'] = 0
                
                #check parameters are within hardware limits (doesn't check if pulse will go out of bounds, but instrument checks this (I think))
                if (parameters['clean_mV'] > 1499 or parameters['clean_mV'] < -1500):
                    raise InputError(parameters['clean_mV'],"Clean potential exceeds hardware limits.")
                if (parameters['dep_mV'] > 1499 or parameters['dep_mV'] < -1500):
                    raise InputError(parameters['dep_mV'],"Deposition potential exceeds hardware limits.")
                if (parameters['clean_s'] < 0):
                    raise InputError(parameters['clean_s'],"Clean time cannot be negative.")
                if (parameters['dep_s'] < 0):
                    raise InputError(parameters['dep_s'],"Deposition time cannot be negative.")
                if (parameters['start'] > 1499 or parameters['start'] < -1500):
                    raise InputError(parameters['start'],"Start parameter exceeds hardware limits.")
                if (parameters['step'] > 200 or parameters['step'] < 1):
                    raise InputError(parameters['step'],"Step height parameter exceeds hardware limits.")
                if (parameters['stop'] > 1499 or parameters['stop'] < -1500):
                    raise InputError(parameters['stop'],"Stop parameter exceeds hardware limits.")
                if (parameters['pulse'] > 150 or parameters['pulse'] < 1):
                    raise InputError(parameters['pulse'],"Pulse height parameter exceeds hardware limits.")
                if (parameters['freq'] < 1 or parameters['freq'] > 1000):
                    raise InputError(parameters['freq'], "Frequency parameter outside limits.")
                if parameters['start'] == parameters['stop']:
                    raise InputError(parameters['start'],"Start cannot equal Stop.")
                    
                self.recv_p, self.send_p = multiprocessing.Pipe(duplex=True)
                self.current_exp = comm.swv_exp(parameters, view_parameters, self.plot, self.rawbuffer, self.send_p)
                
                self.p = multiprocessing.Process(target=self.current_exp.run, args=(self.serial_liststore.get_value(self.serial_combobox.get_active_iter(), 0), ))
                self.p.start()
                
                self.send_p.close()
                
                self.plot_proc = gobject.timeout_add(200, self.experiment_running_plot)
                gobject.idle_add(self.experiment_running)
                
            else:
                self.statusbar.push(self.error_context_id, "Experiment not yet implemented.")
                self.startbutton.set_sensitive(True)
                self.stopbutton.set_sensitive(False)
                
        except ValueError:
            self.spinner.stop()
            self.statusbar.push(self.error_context_id, "Experiment parameters must be integers.")
            self.startbutton.set_sensitive(True)
            self.stopbutton.set_sensitive(False)
        
        except InputError as e:
            self.spinner.stop()
            self.statusbar.push(self.error_context_id, e.msg)
            self.startbutton.set_sensitive(True)
            self.stopbutton.set_sensitive(False)
        
        except SerialException:
            self.spinner.stop()
            self.statusbar.push(self.error_context_id, "Could not establish serial connection.")
            self.startbutton.set_sensitive(True)
            self.stopbutton.set_sensitive(False)

        except AssertionError as e:
            self.spinner.stop()
            self.statusbar.push(self.error_context_id, str(e))
            self.startbutton.set_sensitive(True)
            self.stopbutton.set_sensitive(False)

    def experiment_running(self):
        try:
            if self.recv_p.poll():
                self.line, data = self.recv_p.recv()
                print self.line, data
                if self.line > self.lastdataline:
                    self.current_exp.data += [[],[]]
                    if len(data) > 2:
                        self.current_exp.data_extra += [[],[]]
                    self.lastdataline = self.line
                for i in range(2):
                    self.current_exp.data[2*self.line+i].append(data[i])
                if len(data) > 2:
                    self.current_exp.data_extra[2*self.line+i].append(data[i])
            return True
        except EOFError:
            self.experiment_done()
            return False
            
    def experiment_running_plot(self):
        if self.line > self.lastline:
            self.plot.addline()
            self.plot.updateline(self.current_exp, self.lastline) #make sure all of last line is added
            self.lastline = self.line
        self.plot.updateline(self.current_exp, self.line)
        self.plot.redraw()
        return True

    def experiment_done(self):
        gobject.source_remove(self.plot_proc) #stop automatic plot update
        self.experiment_running_plot() #make sure all data updated on plot
        
        self.databuffer.set_text("")
        self.databuffer.place_cursor(self.databuffer.get_start_iter())
        self.rawbuffer.set_text("")
        self.rawbuffer.place_cursor(self.rawbuffer.get_start_iter())
        
        for col in zip(*self.current_exp.data):
            for row in col:
                self.rawbuffer.insert_at_cursor(str(row)+ "\t")
            self.rawbuffer.insert_at_cursor("\n")
        
        
        if self.current_exp.data_extra:
            for col in zip(*self.current_exp.data_extra):
                for row in col:
                    self.databuffer.insert_at_cursor(str(row)+ "\t")
                self.databuffer.insert_at_cursor("\n")
        
        
        self.spinner.stop()
        self.startbutton.set_sensitive(True)
        self.stopbutton.set_sensitive(False)

    def on_pot_stop_clicked(self, data=None):
        if self.recv_p:
            print "stop"
            self.recv_p.send('a')
    
    def on_file_save_exp_activate(self, menuitem, data=None):
        if self.current_exp:
            self.save = save.npSave(self.current_exp)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    gobject.threads_init()
    main = main()
    gtk.main()