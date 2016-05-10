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

import os
import sys
import logging
from uuid import uuid4

import gtk
import gobject

logger = logging.getLogger('dstat.interface.db')

class DB_Window(gobject.GObject):
    __gsignals__ = {
                    'db-reset' : (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                        (gobject.TYPE_STRING,)
                                        )
                    }
    def __init__(self):
        gobject.GObject.__init__(self)
        
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/db.glade')
        self.builder.connect_signals(self)
        
        self.window = self.builder.get_object('db_window')
        # Make sure window isn't destroyed if checkbox hit.
        self.window.connect('delete-event', self.on_delete_event)
        self.db_control_table = self.builder.get_object('db_control_table')
        
        ui_keys = ['exp_id_entry',
                   'measure_id_entry',
                   'patient_id_entry',
                   'measure_name_entry',
                   'db_path_entry',
                   'db_apply_button',
                   'exp_id_autogen_button',
                   'db_enable_checkbutton'
                   ]
        self.persistent_keys = ['db_path_entry','db_enable_checkbutton']
        self.ui = {}
        for i in ui_keys:
            self.ui[i] = self.builder.get_object(i)
        
        self.metadata_map = [('experiment_uuid', 'exp_id_entry'),
                             ('patient_id', 'patient_id_entry'),
                             ('name', 'measure_name_entry')]
        
        self._params = {}
    
    @property
    def persistent_params(self):
        """Dict of parameters that should be saved."""
        self._get_params()
        return {k:self._params[k] for k in self.persistent_keys}
        
    @property
    def params(self):
        """Dict of parameters."""
        self._get_params()      
        return self._params
    
    def _get_params(self):
        """Updates self._params from UI."""
        for i in self.ui:
            if i.endswith('checkbutton'):
                self._params[i] = self.ui[i].get_active()
            elif i.endswith('entry'):
                text = self.ui[i].get_text()
                if text == "":
                    text = None
                self._params[i] = text
    
    @params.setter
    def params(self, params):
        if self._params is {}:
            self._params = dict.fromkeys(self.ui.keys())
    
        for i in self._params:
            if i in params:
                self._params[i] = params[i]
        self._set_params()

    def _set_params(self):
        """Updates UI with new parameters."""
        for i in self.ui:
            if i.endswith('checkbutton'):
                self.ui[i].set_active(self._params[i])
            elif i.endswith('entry'):
                if self._params[i] is not None:
                    self.ui[i].set_text(self._params[i])
                else:
                    self.ui[i].set_text("")
    
    def update_from_metadata(self, metadata):
        params = {k : metadata[j] for j, k in self.metadata_map
                    if j in metadata}
        self.params = params
    
    def show(self):
        self.window.show_all()
        self.on_db_enable_checkbutton_toggled()
    
    def on_db_enable_checkbutton_toggled(self, *args):
        if self.ui['db_enable_checkbutton'].get_active():
            self.db_control_table.show()
        else:
            self.db_control_table.hide()
            
    def on_exp_id_autogen_button_clicked(self, *args):
        self.ui['exp_id_entry'].set_text(uuid4().hex)
        
    def on_db_apply_button_clicked(self, widget=None, *data):
        self.emit('db-reset', self.params['db_path_entry'])
        
    def on_delete_event(self, widget=None, *data):
        widget.hide()
        return True
        
gobject.type_register(DB_Window)