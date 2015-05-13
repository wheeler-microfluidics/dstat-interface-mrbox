#!/usr/bin/env python
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

import gtk

class ExpInterface(object):
    """Generic experiment interface class. Should be subclassed to implement
    experiment interfaces by populating self.entry.
    
    Public methods:
    get_params(self)
    """
    def __init__(self, glade_path):
        self.builder = gtk.Builder()
        self.builder.add_from_file(glade_path)
        self.builder.connect_signals(self)
        self.entry = {}

    def get_params(self):
        """Returns a dict of parameters for experiment."""
        parameters = {}    
        for key, value in self.entry.iteritems():
            parameters[key] = int(value.get_text())    
        return parameters
        
class Chronoamp(ExpInterface):
    """Experiment class for chronoamperometry. Extends ExpInterface class to
    support treeview neeeded for CA.
    
    Public methods:
    on_add_button_clicked(self, widget)
    on_remove_button_clicked(self, widget)
    get_params(self)
    """
    def __init__(self):
        """Extends superclass method to support treeview."""
        super(Chronoamp, self).__init__('interface/chronoamp.glade')
        
        self.statusbar = self.builder.get_object('statusbar')
        self.model = self.builder.get_object('ca_list')
        self.treeview = self.builder.get_object('treeview')
        self.cell_renderer = gtk.CellRendererText()
        
        self.treeview.insert_column_with_attributes(-1, "Time",
                                    self.cell_renderer, text=1).set_expand(True)
        self.treeview.insert_column_with_attributes(-1, "Potential",
                                    self.cell_renderer, text=0).set_expand(True)
        
        self.selection = self.treeview.get_selection()
        self.selection.set_mode(gtk.SELECTION_MULTIPLE)

    def on_add_button_clicked(self, widget):
        """Add current values in potential_entry and time_entry to model."""
        
        self.statusbar.remove_all(0)
        
        try:
            potential = int(
                          self.builder.get_object('potential_entry').get_text())
            time = int(self.builder.get_object('time_entry').get_text())
            
            if (potential > 1499 or potential < -1500):
                raise ValueError("Potential out of range")
            if (time < 1 or time > 65535):
                raise ValueError("Time out of range")
        
            self.model.append([potential, time])
        
        except ValueError as err:
            self.statusbar.push(0, str(err))
        except TypeError as err:
            self.statusbar.push(0, str(err))

    def on_remove_button_clicked(self, widget):
        """Remove currently selected items from model."""
        # returns 2-tuple: treemodel, list of paths of selected rows
        selected_rows = list(self.selection.get_selected_rows()[1])
        referencelist = []
        
        for i in selected_rows:
            referencelist.append(gtk.TreeRowReference(self.model, i))
        
        for i in referencelist:
            self.model.remove(self.model.get_iter(i.get_path()))

    def get_params(self):
        """Returns a dict of parameters for experiment. Overrides superclass
        method.
        """
        parameters = {}
        parameters['potential'] = [int(r[0]) for r in self.model]
        parameters['time'] = [int(r[1]) for r in self.model]
        
        return parameters
              
class LSV(ExpInterface):
    """Experiment class for LSV."""
    def __init__(self):
        """Adds entry listings to superclass's self.entry dict"""
        super(LSV, self).__init__('interface/lsv.glade')

        self.entry['clean_mV'] = self.builder.get_object('clean_mV')
        self.entry['clean_s'] = self.builder.get_object('clean_s')
        self.entry['dep_mV'] = self.builder.get_object('dep_mV')
        self.entry['dep_s'] = self.builder.get_object('dep_s')
        self.entry['start'] = self.builder.get_object('start_entry')
        self.entry['stop'] = self.builder.get_object('stop_entry')
        self.entry['slope'] = self.builder.get_object('slope_entry')
        
class CV(ExpInterface):
    """Experiment class for CV."""
    def __init__(self):
        """Adds entry listings to superclass's self.entry dict"""
        super(CV, self).__init__('interface/cv.glade')

        self.entry['clean_mV'] = self.builder.get_object('clean_mV')
        self.entry['clean_s'] = self.builder.get_object('clean_s')
        self.entry['dep_mV'] = self.builder.get_object('dep_mV')
        self.entry['dep_s'] = self.builder.get_object('dep_s')
        self.entry['start'] = self.builder.get_object('start_entry')
        self.entry['v1'] = self.builder.get_object('v1_entry')
        self.entry['v2'] = self.builder.get_object('v2_entry')
        self.entry['slope'] = self.builder.get_object('slope_entry')
        self.entry['scans'] = self.builder.get_object('scans_entry')

class SWV(ExpInterface):
    """Experiment class for SWV."""
    def __init__(self):
        """Adds entry listings to superclass's self.entry dict"""
        super(SWV, self).__init__('interface/swv.glade')

        self.entry['clean_mV'] = self.builder.get_object('clean_mV')
        self.entry['clean_s'] = self.builder.get_object('clean_s')
        self.entry['dep_mV'] = self.builder.get_object('dep_mV')
        self.entry['dep_s'] = self.builder.get_object('dep_s')
        self.entry['start'] = self.builder.get_object('start_entry')
        self.entry['stop'] = self.builder.get_object('stop_entry')
        self.entry['step'] = self.builder.get_object('step_entry')
        self.entry['pulse'] = self.builder.get_object('pulse_entry')
        self.entry['freq'] = self.builder.get_object('freq_entry')
        self.entry['scans'] = self.builder.get_object('scans_entry')
        
    def get_params(self):
        """Extends superclass method to pass status of cyclic_checkbutton"""
        parameters = {}
        parameters['cyclic_checkbutton'] = self.builder.get_object(
                                              'cyclic_checkbutton').get_active()
        parameters.update(super(SWV, self).get_params())
        
        return parameters
        
class DPV(ExpInterface):
    """Experiment class for DPV."""
    def __init__(self):
        """Adds entry listings to superclass's self.entry dict"""
        super(DPV, self).__init__('interface/dpv.glade')

        self.entry['clean_mV'] = self.builder.get_object('clean_mV')
        self.entry['clean_s'] = self.builder.get_object('clean_s')
        self.entry['dep_mV'] = self.builder.get_object('dep_mV')
        self.entry['dep_s'] = self.builder.get_object('dep_s')
        self.entry['start'] = self.builder.get_object('start_entry')
        self.entry['stop'] = self.builder.get_object('stop_entry')
        self.entry['step'] = self.builder.get_object('step_entry')
        self.entry['pulse'] = self.builder.get_object('pulse_entry')
        self.entry['period'] = self.builder.get_object('period_entry')
        self.entry['width'] = self.builder.get_object('width_entry')
        
class ACV(ExpInterface):
    """Experiment class for ACV."""
    def __init__(self):
        """Adds entry listings to superclass's self.entry dict"""
        super(ACV, self).__init__('interface/acv.glade')
        
        self.entry['start'] = self.builder.get_object('start_entry')
        self.entry['stop'] = self.builder.get_object('stop_entry')
        self.entry['slope'] = self.builder.get_object('slope_entry')
        self.entry['amplitude'] = self.builder.get_object('amplitude_entry')
        self.entry['freq'] = self.builder.get_object('freq_entry')

class PD(ExpInterface):
    """Experiment class for PD."""
    def __init__(self):
        """Adds entry listings to superclass's self.entry dict"""
        super(PD, self).__init__('interface/pd.glade')
        
        self.entry['voltage'] = self.builder.get_object('voltage_entry')
        self.entry['time'] = self.builder.get_object('time_entry')
        
class POT(ExpInterface):
    """Experiment class for Potentiometry."""
    def __init__(self):
        """Adds entry listings to superclass's self.entry dict"""
        super(POT, self).__init__('interface/potexp.glade')
        
        self.entry['time'] = self.builder.get_object('time_entry')