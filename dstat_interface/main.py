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
import uuid
from copy import deepcopy
from collections import OrderedDict
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
import logging
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

from version import getVersion
import interface.save as save
from interface.db import DB_Window
import dstat_comm as comm
import interface.exp_window as exp_window
import interface.adc_pot as adc_pot
import plot
import params
import parameter_test
import analysis
import zmq
import db
from errors import InputError

from plugin import DstatPlugin, get_hub_uri

# Setup Logging
root_logger = logging.getLogger("dstat")
root_logger.setLevel(level=logging.INFO)
log_handler = logging.StreamHandler()
log_formatter = logging.Formatter(
                    fmt='%(asctime)s [%(name)s](%(levelname)s) %(message)s',
                    datefmt='%H:%M:%S'
                )
log_handler.setFormatter(log_formatter)
root_logger.addHandler(log_handler)

logger = logging.getLogger("dstat.main")

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
        
        self.db_window = DB_Window()
        self.builder.get_object('menu_database_options').connect_object(
            'activate', DB_Window.show, self.db_window
        )
        self.db_window.connect('db_reset', db.restart_db)

        # Setup Autosave
        self.autosave_checkbox = self.builder.get_object('autosave_checkbutton')
        self.autosavedir_button = self.builder.get_object('autosavedir_button')
        self.autosavename = self.builder.get_object('autosavename')

        # Setup Plots
        self.plot_notebook = self.builder.get_object('plot_notebook')

        self.plot = plot.PlotBox(self.plotwindow)
        self.ft_plot = plot.FT_Box(self.ft_window)

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
            logger.warning("Could not fetch version number")
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
        
        self.metadata = None # Should only be added to by plugin interface
        
        self.plot_notebook.get_nth_page(
                        self.plot_notebook.page_num(self.ft_window)).hide()
        self.plot_notebook.get_nth_page(
                        self.plot_notebook.page_num(self.period_window)).hide()

        self.params_loaded = False
        # Disable 0MQ plugin API by default.
        self.plugin = None
        self.plugin_timeout_id = None
        # UUID for active experiment.
        self.active_experiment_id = None
        # UUIDs for completed experiments.
        self.completed_experiment_ids = OrderedDict()

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
        db.stop_db()
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
            logger.warning("AttributeError: %s", err)
            self.serial_connect.set_sensitive(True)
        except TypeError as err:
            logger.warning("TypeError: %s", err)
            self.serial_connect.set_sensitive(True)

        if self.params_loaded == False:
            try:
                params.load_params(self, 'last_params.yml')
            except IOError:
                logger.info("No previous parameters found.")

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
            logger.warning("AttributeError: %s", err)
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
                logger.info("Start PMT idle mode")
                comm.serial_instance.proc_pipe_p.send(comm.PMTIdle())

            else:
                logger.info("Start OCP")
                comm.serial_instance.proc_pipe_p.send(comm.OCPExp())

            self.ocp_proc = (gobject.timeout_add(300, self.ocp_running_data),
                             gobject.timeout_add(250, self.ocp_running_proc)
                            )
            self.ocp_is_running = True

        else:
            logger.info("OCP measurements not supported on v1.1 boards.")
        return

    def stop_ocp(self):
        """Stop OCP measurements."""

        if self.version[0] >= 1 and self.version[1] >= 2:
            if self.pmt_mode == True:
                logger.info("Stop PMT idle mode")
            else:
                logger.info("Stop OCP")
            comm.serial_instance.ctrl_pipe_p.send('a')

            for i in self.ocp_proc:
                gobject.source_remove(i)
            while self.ocp_running_proc():
                pass
            self.ocp_is_running = False
            self.ocp_disp.set_text("")
        else:
            logger.error("OCP measurements not supported on v1.1 boards.")
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
                logger.debug("ocp_running_proc: %s", proc_buffer)
                if proc_buffer in ["DONE", "SERIAL_ERROR", "ABORT"]:
                    if proc_buffer == "SERIAL_ERROR":
                        self.on_serial_disconnect_clicked()

                    while comm.serial_instance.data_pipe_p.poll():
                        comm.serial_instance.data_pipe_p.recv()
                    return False

                return True

            return True

        except EOFError:
            return False
        except IOError:
            return False

    def on_pot_start_clicked(self, data=None):
        try:
            self.run_active_experiment()
        except (ValueError, KeyError, InputError, SerialException,
                AssertionError):
            # Ignore expected exceptions when triggering experiment from UI.
            pass

    def run_active_experiment(self, param_override=None, metadata=None):
        """Run currently visible experiment."""
        # Assign current experiment a unique identifier.
        experiment_id = uuid.uuid4()
        self.active_experiment_id = experiment_id
        logger.info("Current measurement id: %s", experiment_id.hex)
        
        self.metadata = metadata
        
        if self.metadata is not None:
            logger.info("Loading external metadata")
            self.db_window.update_from_metadata(self.metadata)
        elif self.db_window.params['exp_id_entry'] is None:
            logger.info("DB exp_id field blank, autogenerating")
            self.db_window.on_exp_id_autogen_button_clicked()
            
        self.db_window.params = {'measure_id_entry':experiment_id.hex}

        def exceptions():
            """ Cleans up after errors """
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
            
            if parameters['db_enable_checkbutton']:
                if db.current_db is None:
                    db.start_db()
                elif not db.current_db.connected:
                    db.restart_db()
            
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
        parameters['metadata'] = self.metadata

        # Make sure these are defined
        parameters['sync_true'] = False
        parameters['shutter_true'] = False
        try:
            if param_override is not None:
                params.set_params(self, param_override)
            
            parameters.update(params.get_params(self))
            
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

                return experiment_id

            elif selection == 1: # LSV
                parameter_test.lsv_test(parameters)

                self.current_exp = comm.LSVExp(parameters)
                run_experiment()

                return experiment_id

            elif selection == 2: # CV
                parameter_test.cv_test(parameters)

                self.current_exp = comm.CVExp(parameters)
                run_experiment()

                return experiment_id

            elif selection == 3:  # SWV
                parameter_test.swv_test(parameters)

                self.current_exp = comm.SWVExp(parameters)
                run_experiment()

                return experiment_id

            elif selection == 4:  # DPV
                parameter_test.dpv_test(parameters)

                self.current_exp = comm.DPVExp(parameters)
                run_experiment()

                return experiment_id

            elif selection == 6:  # PD
                parameter_test.pd_test(parameters)

                self.current_exp = comm.PDExp(parameters)
                run_experiment()

                return experiment_id

            elif selection == 7:  # POT
                if not (self.version[0] >= 1 and self.version[1] >= 2):
                    self.statusbar.push(self.error_context_id,
                                "v1.1 board does not support potentiometry.")
                    exceptions()
                    return

                parameter_test.pot_test(parameters)

                self.current_exp = comm.PotExp(parameters)
                run_experiment()

                return experiment_id

            else:
                self.statusbar.push(self.error_context_id,
                                    "Experiment not yet implemented.")
                exceptions()

        except ValueError as i:
            logger.info("ValueError: %s",i)
            self.statusbar.push(self.error_context_id,
                                "Experiment parameters must be integers.")
            exceptions()
            raise

        except KeyError as i:
            logger.info("KeyError: %s", i)
            self.statusbar.push(self.error_context_id,
                                "Experiment parameters must be integers.")
            exceptions()
            raise

        except InputError as err:
            logger.info("InputError: %s", err)
            self.statusbar.push(self.error_context_id, err.msg)
            exceptions()
            raise

        except SerialException as err:
            logger.info("SerialException: %s", err)
            self.statusbar.push(self.error_context_id,
                                "Could not establish serial connection.")
            exceptions()
            raise

        except AssertionError as err:
            logger.info("AssertionError: %s", err)
            self.statusbar.push(self.error_context_id, str(err))
            exceptions()
            raise

    def experiment_running_data(self):
        """Receive data from experiment process and add to
        current_exp.data['data].
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
                    self.current_exp.data['data'].append(
                        deepcopy(self.current_exp.line_data))
                    self.lastdataline = self.line

                for i in range(len(self.current_exp.data['data'][self.line])):
                    self.current_exp.data['data'][self.line][i].append(data[i])

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
                    logger.warning("Unrecognized experiment return code: %s",
                                   proc_buffer)

                return False

            return True

        except EOFError as err:
            logger.warning("EOFError: %s", err)
            self.experiment_done()
            return False
        except IOError as err:
            logger.warning("IOError: %s", err)
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
        try:
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

                line_buffer = []

                for scan in self.current_exp.data['ft']:
                    for dimension in scan:
                        for i in range(len(dimension)):
                            try:
                                line_buffer[i] += "%s     " % dimension[i]
                            except IndexError:
                                line_buffer.append("")
                                line_buffer[i] += "%s     " % dimension[i]

                for i in line_buffer:
                    self.databuffer.insert_at_cursor("%s\n" % i)

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

            for scan in self.current_exp.data['data']:
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
                save.autoSave(self.current_exp,
                              self.autosavedir_button.get_filename(),
                              self.autosavename.get_text()
                              )

                save.autoPlot(self.current_exp,
                              self.autosavedir_button.get_filename(),
                              self.autosavename.get_text()
                              )
            # Database output
            if self.current_exp.parameters['db_enable_checkbutton']:
                meta = {}
                
                if self.current_exp.parameters['metadata'] is not None:
                    metadata = self.current_exp.parameters['metadata']
                    exp_metakeys = ['experiment_uuid', 'patient_id', 'name']
                    meta.update(
                                {k: metadata[k]
                                 for k in metadata
                                 if k not in exp_metakeys
                                 }
                                )
                    
                name = self.current_exp.parameters['measure_name_entry']
                                       
                newname = db.current_db.add_results(
                    measurement_uuid=self.active_experiment_id.hex,
                    measurement_name=name,
                    experiment_uuid=self.current_exp.parameters['exp_id_entry'],
                    experiment_metadata=meta,
                    patient_id=self.current_exp.parameters['patient_id_entry'],
                    timestamp=None,
                    data=self.current_exp.export()
                    )
                    
                self.db_window.params = {'measure_name_entry':newname}
        
        # uDrop
        # UI stuff
        finally:
            self.metadata = None # Reset metadata
            
            self.spinner.stop()
            self.startbutton.set_sensitive(True)
            self.stopbutton.set_sensitive(False)

            self.start_ocp()
            self.completed_experiment_ids[self.active_experiment_id] =\
                datetime.utcnow()

    def on_pot_stop_clicked(self, data=None):
        """Stop current experiment. Signals experiment process to stop."""
        try:
            comm.serial_instance.ctrl_pipe_p.send('a')

        except AttributeError:
            pass
        except:
            logger.warning(sys.exc_info())

    def on_file_save_exp_activate(self, menuitem, data=None):
        """Activate dialogue to save current experiment data. """
        try:
            save.manSave(self.current_exp)
        except AttributeError:
            logger.warning("Tried to save with no experiment run")

    def on_file_save_plot_activate(self, menuitem, data=None):
        """Activate dialogue to save current plot."""
        try:
            save.plot_save_dialog(self.current_exp)
        except AttributeError:
            logger.warning("Tried to save with no experiment run")

    def on_file_save_params_activate(self, menuitem, data=None):
        """Activate dialogue to save current experiment parameters. """
        save.man_param_save(self)

    def on_file_load_params_activate(self, menuitem, data=None):
        """Activate dialogue to load experiment parameters from file. """
        save.man_param_load(self)

    def on_menu_dropbot_connect_activate(self, menuitem, data=None):
        """Listen for remote control connection from µDrop."""

        # Prompt user for 0MQ plugin hub URI.
        zmq_plugin_hub_uri = get_hub_uri(parent=self.window)

        self.dropbot_enabled = True
        self.menu_dropbot_connect.set_sensitive(False)
        self.menu_dropbot_disconnect.set_sensitive(True)
        self.statusbar.push(self.message_context_id,
                            "Waiting for µDrop to connect…")
        self.enable_plugin(zmq_plugin_hub_uri)

    def on_menu_dropbot_disconnect_activate(self, menuitem=None, data=None):
        """Disconnect µDrop connection and stop listening."""
        self.cleanup_plugin()
        self.dropbot_enabled = False
        self.menu_dropbot_connect.set_sensitive(True)
        self.menu_dropbot_disconnect.set_sensitive(False)
        self.statusbar.push(self.message_context_id, "µDrop disconnected.")

    def enable_plugin(self, hub_uri):
        '''
        Connect to 0MQ plugin hub to expose public D-Stat API.

        Args
        ----

            hub_uri (str) : URI for 0MQ plugin hub.
        '''
        self.cleanup_plugin()
        # Initialize 0MQ hub plugin and subscribe to hub messages.
        self.plugin = DstatPlugin(self, 'dstat-interface', hub_uri,
                                  subscribe_options={zmq.SUBSCRIBE: ''})
        # Initialize sockets.
        self.plugin.reset()

        # Periodically process outstanding message received on plugin sockets.
        self.plugin_timeout_id = gtk.timeout_add(500,
                                                 self.plugin.check_sockets)

    def cleanup_plugin(self):
        if self.plugin_timeout_id is not None:
            gobject.source_remove(self.plugin_timeout_id)
        if self.plugin is not None:
            self.plugin = None


if __name__ == "__main__":
    multiprocessing.freeze_support()
    gobject.threads_init()
    MAIN = Main()
    gtk.main()
