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

""" GUI Interface for Wheeler Lab DStat """

import sys
import os
import multiprocessing
import time
from copy import deepcopy
from datetime import datetime

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    print "ERR: PyGTK 2.0 not available"
    sys.exit(1)
try:
    import gtk
except ImportError:
    print "ERR: GTK not available"
    sys.exit(1)
try:
    import gobject
except ImportError:
    print "ERR: gobject not available"
    sys.exit(1)
from serial import SerialException
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

from version import getVersion
import interface.save as save
import dstat_comm as comm
import interface.exp_window as exp_window
import interface.adc_pot as adc_pot
import plot
import microdrop
import params
import parameter_test
import analysis
from errors import InputError, VarError, ErrorLogger
_logger = ErrorLogger(sender="dstat-interface-main")

class Main(object):
    """Main program """
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/dstatinterface.glade')
        self.builder.connect_signals(self)
        self.cell = gtk.CellRendererText()

        # Create instance of interface components
        self.statusbar = self.builder.get_object('statusbar')
        self.ocp_disp = self.builder.get_object('ocp_disp')
        self.window = self.builder.get_object('window1')
        self.aboutdialog = self.builder.get_object('aboutdialog1')
        self.rawbuffer = self.builder.get_object('databuffer1')
        self.databuffer = self.builder.get_object('databuffer2')
        self.stopbutton = self.builder.get_object('pot_stop')
        self.startbutton = self.builder.get_object('pot_start')
        self.adc_pot = adc_pot.adc_pot()
        
        self.error_context_id = self.statusbar.get_context_id("error")
        self.message_context_id = self.statusbar.get_context_id("message")
        
        self.plotwindow = self.builder.get_object('plotbox')
        self.ft_window = self.builder.get_object('ft_box')
        self.period_window = self.builder.get_object('period_box')
        
        self.exp_window = exp_window.Experiments(self.builder)
        self.analysis_opt_window = analysis.AnalysisOptions(self.builder)
        
        # Setup Autosave
        self.autosave_checkbox = self.builder.get_object('autosave_checkbutton')
        self.autosavedir_button = self.builder.get_object('autosavedir_button')
        self.autosavename = self.builder.get_object('autosavename')
        
        # Setup Plots
        self.plot_notebook = self.builder.get_object('plot_notebook')
        
        self.plot = plot.plotbox(self.plotwindow)
        self.ft_plot = plot.ft_box(self.ft_window)
        
        #fill adc_pot_box
        self.adc_pot_box = self.builder.get_object('gain_adc_box')
        self.adc_pot_container = self.adc_pot.builder.get_object('vbox1')
        self.adc_pot_container.reparent(self.adc_pot_box)
        
        #fill serial
        self.serial_connect = self.builder.get_object('serial_connect')
        self.serial_pmt_connect = self.builder.get_object('pmt_mode')
        self.serial_disconnect = self.builder.get_object('serial_disconnect')
        self.serial_disconnect.set_sensitive(False)
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
        self.expcombobox.add_attribute(self.cell, 'text', 2)
        self.expcombobox.set_active(0)
        
        self.spinner = self.builder.get_object('spinner')

        self.mainwindow = self.builder.get_object('window1')
        
        # Set Version Strings
        try:
            ver = getVersion()
        except ValueError:
            ver = "1.x"
            _logger.error("Could not fetch version number", "WAR")
        self.mainwindow.set_title(" ".join(("DStat Interface", ver)))
        self.aboutdialog.set_version(ver)
        
        self.mainwindow.show_all()
        
        self.on_expcombobox_changed()

        self.expnumber = 0
        
        self.connected = False
        self.pmt_mode = False
        
        self.menu_dropbot_connect = self.builder.get_object(
                                                         'menu_dropbot_connect')
        self.menu_dropbot_disconnect = self.builder.get_object(
                                                      'menu_dropbot_disconnect')
        self.dropbot_enabled = False
        self.dropbot_triggered = False
        
        self.plot_notebook.get_nth_page(
                        self.plot_notebook.page_num(self.ft_window)).hide()
        self.plot_notebook.get_nth_page(
                        self.plot_notebook.page_num(self.period_window)).hide()
                        
        self.params_loaded = False
                        

    def on_window1_destroy(self, object, data=None):
        """ Quit when main window closed."""
        self.quit()

    def on_gtk_quit_activate(self, menuitem, data=None):
        """Quit when Quit selected from menu."""
        self.quit()
        
    def quit(self):
        """Disconnect and save parameters on quit."""
        params.save_params(self, 'last_params.yml')
        
        self.on_serial_disconnect_clicked()
        gtk.main_quit()

    def on_gtk_about_activate(self, menuitem, data=None):
        """Display the about window."""
        self.response = self.aboutdialog.run()  # waits for user to click close
        self.aboutdialog.hide()
    
    def on_menu_analysis_options_activate(self, menuitem, data=None):
        self.analysis_opt_window.show()

    def on_expcombobox_changed(self, data=None):
        """Change the experiment window when experiment box changed."""
        model = self.expcombobox.get_model()
        _, id, _ = model[self.expcombobox.get_active()]  # id is in 2nd col
        self.statusbar.remove_all(self.error_context_id)
        if not self.exp_window.set_exp(id):
            self.statusbar.push(
                self.error_context_id, "Experiment not yet implemented")

    def on_serial_refresh_clicked(self, data=None):
        """Refresh list of serial devices."""
        self.serial_devices.refresh()
        self.serial_liststore.clear()
        
        for i in self.serial_devices.ports:
            self.serial_liststore.append([i])
            
    def on_serial_connect_clicked(self, data=None):
        """Connect and retrieve DStat version."""
        
        try:
            self.serial_connect.set_sensitive(False)
            self.version = comm.version_check(self.serial_liststore.get_value(
                                    self.serial_combobox.get_active_iter(), 0))
            
            self.statusbar.remove_all(self.error_context_id)
            
            if not len(self.version) == 2:
                self.statusbar.push(self.error_context_id,
                    "Communication Error")
                return
            
            else:
                self.adc_pot.set_version(self.version)
                self.statusbar.push(self.error_context_id,
                                    "".join(["DStat version: ",
                                    str(self.version[0]),
                                    ".", str(self.version[1])])
                                )
                                
                comm.read_settings()
                
                self.start_ocp()
                self.connected = True
                self.serial_connect.set_sensitive(False)
                self.serial_pmt_connect.set_sensitive(False)
                self.serial_disconnect.set_sensitive(True)
        
        except AttributeError as err:
            _logger.error(err, 'WAR')
            self.serial_connect.set_sensitive(True)
        except TypeError as err:
            _logger.error(err, 'WAR')
            self.serial_connect.set_sensitive(True)
        
        if self.params_loaded == False:
            try:
                params.load_params(self, 'last_params.yml')
            except IOError:
                _logger.error("No previous parameters found.", 'INFO')
            
    def on_serial_disconnect_clicked(self, data=None):
        """Disconnect from DStat."""
        if self.connected == False:
            return
        
        try:
            if self.ocp_is_running:
                self.stop_ocp()
            else:
                self.on_pot_stop_clicked()
            comm.serial_instance.ctrl_pipe_p.send("DISCONNECT")
            comm.serial_instance.proc.terminate()
            
        except AttributeError as err:
            _logger.error(err, 'WAR')
            pass
        
        self.pmt_mode = False
        self.connected = False
        self.serial_connect.set_sensitive(True)
        self.serial_pmt_connect.set_sensitive(True)
        self.serial_disconnect.set_sensitive(False)
        self.adc_pot.ui['short_true'].set_sensitive(True)
    
    def on_pmt_mode_clicked(self, data=None):
        """Connect in PMT mode"""
        self.pmt_mode = True
        self.adc_pot.ui['short_true'].set_active(True)
        self.adc_pot.ui['short_true'].set_sensitive(False)
        self.on_serial_connect_clicked()

    def start_ocp(self):
        """Start OCP measurements."""
        
        if self.version[0] >= 1 and self.version[1] >= 2:
            # Flush data pipe
            while comm.serial_instance.data_pipe_p.poll():
                comm.serial_instance.data_pipe_p.recv()
            
            if self.pmt_mode == True:
                _logger.error("Start PMT idle mode", "INFO")
                comm.serial_instance.proc_pipe_p.send(comm.PMTIdle())
            
            else:
                _logger.error("Start OCP", "INFO")
                comm.serial_instance.proc_pipe_p.send(comm.OCPExp())
                
            self.ocp_proc = (gobject.timeout_add(300, self.ocp_running_data),
                             gobject.timeout_add(250, self.ocp_running_proc)
                            )
            self.ocp_is_running = True
            
        else:
            _logger.error("OCP measurements not supported on v1.1 boards.",'INFO')
        return
        
    def stop_ocp(self):
        """Stop OCP measurements."""

        if self.version[0] >= 1 and self.version[1] >= 2:
            if self.pmt_mode == True:
                _logger.error("Stop PMT idle mode",'INFO')
            else:
                _logger.error("Stop OCP",'INFO')
            comm.serial_instance.ctrl_pipe_p.send('a')

            for i in self.ocp_proc:
                gobject.source_remove(i)
            while self.ocp_running_proc():
                pass
            self.ocp_is_running = False
            self.ocp_disp.set_text("")
        else:
            logger.error("OCP measurements not supported on v1.1 boards.",'INFO')
        return
        
    def ocp_running_data(self):
        """Receive OCP value from experiment process and update ocp_disp field
        
        Returns:
        True -- when experiment is continuing to keep function in GTK's queue.
        False -- when experiment process signals EOFError or IOError to remove
            function from GTK's queue.
        """
        
        try:
            if comm.serial_instance.data_pipe_p.poll():                   
                incoming = comm.serial_instance.data_pipe_p.recv()
    
                if isinstance(incoming, basestring): # test if incoming is str
                    self.on_serial_disconnect_clicked()
                    return False
                    
                data = "".join(["OCP: ",
                                "{0:.3f}".format(incoming),
                                " V"])
                self.ocp_disp.set_text(data)
                
                if comm.serial_instance.data_pipe_p.poll():
                    self.ocp_running_data()
                return True
            
            return True
            
        except EOFError:
            return False
        except IOError:
            return False

    def ocp_running_proc(self):
        """Handles signals on proc_pipe_p for OCP.
        
        Returns:
        True -- when experiment is continuing to keep function in GTK's queue.
        False -- when experiment process signals EOFError or IOError to remove
            function from GTK's queue.
        """
        
        try:
            if comm.serial_instance.proc_pipe_p.poll(): 
                proc_buffer = comm.serial_instance.proc_pipe_p.recv()
                _logger.error("".join(("ocp_running_proc: ", proc_buffer)), 'DBG')
                if proc_buffer in ["DONE", "SERIAL_ERROR", "ABORT"]:                
                    if proc_buffer == "SERIAL_ERROR":
                        self.on_serial_disconnect_clicked()
                    
                    while comm.serial_instance.data_pipe_p.poll():
                        comm.serial_instance.data_pipe_p.recv()
                    
                    gobject.source_remove(self.ocp_proc[0])
                    return False
                        
                return True
            
            return True
            
        except EOFError:
            return False
        except IOError:
            return False
            
    def on_pot_start_clicked(self, data=None):
        """Run currently visible experiment."""
        def exceptions():
            """ Cleans up after errors """
            if self.dropbot_enabled == True:
                if self.dropbot_triggered == True:
                    self.dropbot_triggered = False
                    self.microdrop.reply(microdrop.EXPFINISHED)
                    self.microdrop_proc = gobject.timeout_add(500,
                                                          self.microdrop_listen)
            self.spinner.stop()
            self.startbutton.set_sensitive(True)
            self.stopbutton.set_sensitive(False)
            self.start_ocp()
        
        def run_experiment():
            """ Starts experiment """
            self.plot.clearall()
            self.plot.changetype(self.current_exp)
            
            nb = self.plot_notebook
            
            if (parameters['sync_true'] and parameters['shutter_true']):
                nb.get_nth_page(
                    nb.page_num(self.ft_window)).show()
                # nb.get_nth_page(
                #     nb.page_num(self.period_window)).show()
                self.ft_plot.clearall()
                self.ft_plot.changetype(self.current_exp)
            else:
                nb.get_nth_page(nb.page_num(self.ft_window)).hide()
                # nb.get_nth_page(nb.page_num(self.period_window)).hide()

            comm.serial_instance.proc_pipe_p.send(self.current_exp)
            
            # Flush data pipe
            while comm.serial_instance.data_pipe_p.poll():
                comm.serial_instance.data_pipe_p.recv()

            self.plot_proc = gobject.timeout_add(200,
                                                self.experiment_running_plot)
            self.experiment_proc = (
                    gobject.idle_add(self.experiment_running_data),
                    gobject.idle_add(self.experiment_running_proc)
                                    )
        
        
        self.stop_ocp()
        self.statusbar.remove_all(self.error_context_id)
        
        while comm.serial_instance.data_pipe_p.poll(): # Clear data pipe
            comm.serial_instance.data_pipe_p.recv()
        
        selection = self.expcombobox.get_active()
        parameters = {}
        parameters['version'] = self.version
        
        # Make sure these are defined
        parameters['sync_true'] = False
        parameters['shutter_true'] = False
        try:
            parameters.update(self.adc_pot.params)
            parameters.update(self.analysis_opt_window.params)

            self.line = 0
            self.lastline = 0
            self.lastdataline = 0
        
            self.spinner.start()
            self.startbutton.set_sensitive(False)
            self.stopbutton.set_sensitive(True)
            self.statusbar.remove_all(self.error_context_id)

            if selection == 0:  # CA
                # Add experiment parameters to existing
                parameters.update(self.exp_window.get_params('cae'))
                if not parameters['potential']:
                    raise InputError(parameters['potential'],
                                     "Step table is empty")
                
                
                self.current_exp = comm.Chronoamp(parameters)
                
                self.rawbuffer.set_text("")
                self.rawbuffer.place_cursor(self.rawbuffer.get_start_iter())
                
                for i in self.current_exp.commands:
                    self.rawbuffer.insert_at_cursor(i)
                   
                run_experiment()
                
                return
        
            elif selection == 1: # LSV
                parameters.update(self.exp_window.get_params('lsv'))
                parameter_test.lsv_test(parameters)
                
                self.current_exp = comm.LSVExp(parameters)
                run_experiment()

                return
            
            elif selection == 2: # CV
                parameters.update(self.exp_window.get_params('cve'))
                parameter_test.cv_test(parameters)    
                
                self.current_exp = comm.CVExp(parameters)
                run_experiment()
                
                return
                
            elif selection == 3:  # SWV
                parameters.update(self.exp_window.get_params('swv'))
                parameter_test.swv_test(parameters)
                
                self.current_exp = comm.SWVExp(parameters)
                run_experiment()
                
                return
        
            elif selection == 4:  # DPV
                parameters.update(self.exp_window.get_params('dpv'))
                parameter_test.dpv_test(parameters)
                
                self.current_exp = comm.DPVExp(parameters)
                run_experiment()
                
                return
                
            elif selection == 6:  # PD                    
                parameters.update(self.exp_window.get_params('pde'))
                parameter_test.pd_test(parameters)
                
                self.current_exp = comm.PDExp(parameters)
                run_experiment()
                
                return
                            
            elif selection == 7:  # POT
                if not (self.version[0] >= 1 and self.version[1] >= 2):
                    self.statusbar.push(self.error_context_id, 
                                "v1.1 board does not support potentiometry.")
                    exceptions()
                    return
                    
                parameters.update(self.exp_window.get_params('pot'))
                parameter_test.pot_test(parameters)
                
                self.current_exp = comm.PotExp(parameters)
                run_experiment()
                
                return
                
            else:
                self.statusbar.push(self.error_context_id, 
                                    "Experiment not yet implemented.")
                exceptions()
                
        except ValueError as i:
            _logger.error(i, "INFO")
            self.statusbar.push(self.error_context_id, 
                                "Experiment parameters must be integers.")
            exceptions()
        
        except KeyError as i:
            _logger.error("KeyError: %s" % i, "INFO")
            self.statusbar.push(self.error_context_id,
                                "Experiment parameters must be integers.")
            exceptions()
        
        except InputError as err:
            _logger.error(err, "INFO")
            self.statusbar.push(self.error_context_id, err.msg)
            exceptions()
        
        except SerialException as err:
            _logger.error(err, "INFO")
            self.statusbar.push(self.error_context_id, 
                                "Could not establish serial connection.")
            exceptions()

        except AssertionError as err:
            _logger.error(err, "INFO")
            self.statusbar.push(self.error_context_id, str(err))
            exceptions()
        

    def experiment_running_data(self):
        """Receive data from experiment process and add to current_exp.data.
        Run in GTK main loop.
        
        Returns:
        True -- when experiment is continuing to keep function in GTK's queue.
        False -- when experiment process signals EOFError or IOError to remove
            function from GTK's queue.
        """
        try:
            if comm.serial_instance.data_pipe_p.poll(): 
                incoming = comm.serial_instance.data_pipe_p.recv()
                
                self.line, data = incoming
                if self.line > self.lastdataline:
                    self.current_exp.data.append(
                        deepcopy(self.current_exp.line_data))
                    self.lastdataline = self.line

                for i in range(len(self.current_exp.data[self.line])):
                    self.current_exp.data[self.line][i].append(data[i])
                
                if comm.serial_instance.data_pipe_p.poll():
                    self.experiment_running_data()
                return True
            
            return True

        except EOFError as err:
            print err
            self.experiment_done()
            return False
        except IOError as err:
            print err
            self.experiment_done()
            return False
            
    def experiment_running_proc(self):
        """Receive proc signals from experiment process.
        Run in GTK main loop.
        
        Returns:
        True -- when experiment is continuing to keep function in GTK's queue.
        False -- when experiment process signals EOFError or IOError to remove
            function from GTK's queue.
        """
        try:
            if comm.serial_instance.proc_pipe_p.poll(): 
                proc_buffer = comm.serial_instance.proc_pipe_p.recv()
    
                if proc_buffer in ["DONE", "SERIAL_ERROR", "ABORT"]:
                    self.experiment_done()
                    if proc_buffer == "SERIAL_ERROR":
                        self.on_serial_disconnect_clicked()
                    
                else:
                    e = "Unrecognized experiment return code "
                    e += proc_buffer
                    _logger.error(e, 'WAR')
                
                return False
            
            return True

        except EOFError as err:
            _logger.error(err, 'WAR')
            self.experiment_done()
            return False
        except IOError as err:
            _logger.error(err, 'WAR')
            self.experiment_done()
            return False
            
    def experiment_running_plot(self):
        """Plot all data in current_exp.data.
        Run in GTK main loop. Always returns True so must be manually
        removed from GTK's queue.
        """
        if self.line > self.lastline:
            self.plot.addline()
            # make sure all of last line is added
            self.plot.updateline(self.current_exp, self.lastline) 
            self.lastline = self.line
        self.plot.updateline(self.current_exp, self.line)
        self.plot.redraw()
        return True

    def experiment_done(self):
        """Clean up after data acquisition is complete. Update plot and
        copy data to raw data tab. Saves data if autosave enabled.
        """
        self.current_exp.time = datetime.now()
        gobject.source_remove(self.experiment_proc[0])
        gobject.source_remove(self.plot_proc)  # stop automatic plot update
        self.experiment_running_plot()  # make sure all data updated on plot
        

        
        self.databuffer.set_text("")
        self.databuffer.place_cursor(self.databuffer.get_start_iter())
        self.rawbuffer.insert_at_cursor("\n")
        self.rawbuffer.set_text("")
        self.rawbuffer.place_cursor(self.rawbuffer.get_start_iter())
        
        # Shutter stuff
        if (self.current_exp.parameters['shutter_true'] and
            self.current_exp.parameters['sync_true']):
            self.ft_plot.updateline(self.current_exp, 0) 
            self.ft_plot.redraw()
            for col in zip(*self.current_exp.ftdata):
                for row in col:
                    self.databuffer.insert_at_cursor(str(row)+ "    ")
                self.databuffer.insert_at_cursor("\n")
        
        # Run Analysis
        analysis.do_analysis(self.current_exp)
        
        # Write DStat commands
        for i in self.current_exp.commands:
            self.rawbuffer.insert_at_cursor(i)

        self.rawbuffer.insert_at_cursor("\n")
        
        try:
            self.statusbar.push(
                self.message_context_id, 
                "Integral: %s A" % self.current_exp.analysis['FT Integral'][0][1]
            )
        except KeyError:
            pass
        
        # Data Output
        analysis_buffer = []
        
        if self.current_exp.analysis != {}:
            analysis_buffer.append("# ANALYSIS")
            for key, value in self.current_exp.analysis.iteritems():
                analysis_buffer.append("#  %s:" % key)
                for scan in value:
                    number, result = scan
                    analysis_buffer.append(
                        "#    Scan %s -- %s" % (number, result)
                        )
        
        for i in analysis_buffer:
            self.rawbuffer.insert_at_cursor("%s\n" % i)
        
        line_buffer = []
        
        for scan in self.current_exp.data:
            for dimension in scan:
                for i in range(len(dimension)):
                    try:
                        line_buffer[i] += "%s     " % dimension[i]
                    except IndexError:
                        line_buffer.append("")
                        line_buffer[i] += "%s     " % dimension[i]
                
        for i in line_buffer:
            self.rawbuffer.insert_at_cursor("%s\n" % i)
        
        # Autosaving
        if self.autosave_checkbox.get_active():
            save.autoSave(self.current_exp, self.autosavedir_button,
                          self.autosavename.get_text(), self.expnumber)
            plots = {'data':self.plot}
            
            if (self.current_exp.parameters['shutter_true'] and
                self.current_exp.parameters['sync_true']):
                plots['ft'] = self.ft_plot
            
            save.autoPlot(plots, self.autosavedir_button,
                          self.autosavename.get_text(), self.expnumber)
            self.expnumber += 1
            
        # uDrop
        if self.dropbot_enabled == True:
            if self.dropbot_triggered == True:
                self.dropbot_triggered = False
                self.microdrop.reply(microdrop.EXPFINISHED)
            self.microdrop_proc = gobject.timeout_add(500,
                                                      self.microdrop_listen)
        
        # UI stuff
        self.spinner.stop()
        self.startbutton.set_sensitive(True)
        self.stopbutton.set_sensitive(False)
        
        self.start_ocp()

    def on_pot_stop_clicked(self, data=None):
        """Stop current experiment. Signals experiment process to stop."""
        try:
            comm.serial_instance.ctrl_pipe_p.send('a')

        except AttributeError:
            pass
        except:
            _logger.error(sys.exc_info(),'WAR')
    
    def on_file_save_exp_activate(self, menuitem, data=None):
        """Activate dialogue to save current experiment data. """
        if self.current_exp:
            save.manSave(self.current_exp)
    
    def on_file_save_plot_activate(self, menuitem, data=None):
        """Activate dialogue to save current plot."""
        plots = {'data':self.plot}
        
        if (self.current_exp.parameters['shutter_true'] and
            self.current_exp.parameters['sync_true']):
            plots['ft'] = self.ft_plot
        
        save.plotSave(plots)
    
    def on_file_save_params_activate(self, menuitem, data=None):
        """Activate dialogue to save current experiment parameters. """
        save.man_param_save(self)
    
    def on_file_load_params_activate(self, menuitem, data=None):
        """Activate dialogue to load experiment parameters from file. """
        save.man_param_load(self)
        
    def on_menu_dropbot_connect_activate(self, menuitem, data=None):
        """Listen for remote control connection from µDrop."""
        self.microdrop = microdrop.microdropConnection()
        self.dropbot_enabled = True
        self.menu_dropbot_connect.set_sensitive(False)
        self.menu_dropbot_disconnect.set_sensitive(True)
        self.statusbar.push(self.message_context_id,
                            "Waiting for µDrop to connect…")
        self.microdrop_proc = gobject.timeout_add(500, self.microdrop_listen)
    
    def on_menu_dropbot_disconnect_activate(self, menuitem=None, data=None):
        """Disconnect µDrop connection and stop listening."""
        gobject.source_remove(self.microdrop_proc)
        self.microdrop.reset()
        del self.microdrop
        self.dropbot_enabled = False
        self.menu_dropbot_connect.set_sensitive(True)
        self.menu_dropbot_disconnect.set_sensitive(False)
        self.statusbar.push(self.message_context_id, "µDrop disconnected.")

    def microdrop_listen(self):
        """Manage signals from µDrop. Must be added to GTK's main loop to
        run periodically.
        """
        drdy, data = self.microdrop.listen()
        if drdy == False:
            return True

        if data == microdrop.EXP_FINISH_REQ:
            if self.dropbot_triggered:
                if self.connected:
                    self.on_pot_start_clicked()
                else:
                    _logger.error("µDrop requested experiment but DStat disconnected",
                                 'WAR')
                    self.statusbar.push(self.message_context_id,
                                        "Listen stopped—DStat disconnected.")
                    self.microdrop.reply(microdrop.EXPFINISHED)
                    self.on_menu_dropbot_disconnect_activate()
                    return False  # Removes function from GTK's main loop 
            else:
                _logger.error("µDrop requested experiment finish confirmation without starting experiment.",
                             'WAR')
                self.microdrop.reply(microdrop.EXPFINISHED)
            
        elif data == microdrop.STARTEXP:
            self.microdrop.connected = True
            self.statusbar.push(self.message_context_id, "µDrop connected.")
            self.dropbot_triggered = True
            self.microdrop.reply(microdrop.START_REP)
        else:
            _logger.error("Received invalid command from µDrop",'WAR')
            self.microdrop.reply(microdrop.INVAL_CMD)
        return True


if __name__ == "__main__":
    multiprocessing.freeze_support()
    gobject.threads_init()
    MAIN = Main()
    gtk.main()