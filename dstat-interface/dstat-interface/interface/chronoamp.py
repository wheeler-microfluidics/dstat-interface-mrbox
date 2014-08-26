#!/usr/bin/env python

import gtk

class Chronoamp:
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/chronoamp.glade')
        self.builder.connect_signals(self)
        
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