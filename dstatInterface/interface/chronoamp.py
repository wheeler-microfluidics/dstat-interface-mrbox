#!/usr/bin/env python

import gtk

class chronoamp:
    def label_set_func(self, tree_column, cell, model, iter):
        info = model.get_value(iter, 1)
        cell.set_property("text", info)
    
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file('interface/chronoamp.glade')
        self.builder.connect_signals(self)
        
        self.statusbar = self.builder.get_object('statusbar')
        self.potential = self.builder.get_object('potential_entry')
        self.time = self.builder.get_object('time_entry')
        self.model = self.builder.get_object('ca_list')
        self.treeview = self.builder.get_object('treeview')

        self.cell_renderer = gtk.CellRendererText()
        
        self.treeview.insert_column_with_attributes(-1, "Time", self.cell_renderer, text=1).set_expand(True)
        self.treeview.insert_column_with_attributes(-1, "Potential", self.cell_renderer, text=0).set_expand(True)
        
        self.treeviewselection = self.treeview.get_selection()
        self.treeviewselection.set_mode(gtk.SELECTION_MULTIPLE)

    def on_add_button_clicked(self, widget):
        self.statusbar.remove_all(0)
        
        try:
            potential = int(self.potential.get_text())
            time = int(self.time.get_text())
            
            if (potential > 1499 or potential < -1500):
                raise ValueError("Potential out of range")
            if (time < 1 or time > 65535):
                raise ValueError("Time out of range")
        
            self.model.append([potential, time])
        
        except ValueError as e:
            self.statusbar.push(0, str(e))
        except TypeError as e:
            self.statusbar.push(0, str(e))

    def on_remove_button_clicked(self, widget):
        self.selected_rows = list(self.treeviewselection.get_selected_rows()[1]) #returns 2-tuple: treemodel, list of paths selected rows
        
        self.referencelist = []
        
        for i in self.selected_rows:
            x=gtk.TreeRowReference(self.model, i)
            self.referencelist.append(x)
        
        for i in self.referencelist:
            self.model.remove(self.model.get_iter(i.get_path()))
