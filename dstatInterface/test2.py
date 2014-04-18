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
try:
    import math
except:
    print('math lib missing')
    sys.exit(1)

# we can call it just about anything we want
class Buglump:
    
    # This first define is for our on_window1_destroy signal we created in the
    # Glade designer. The print message does just that and prints to the terminal
    # which can be useful for debugging. The 'object' if you remember is the signal
    # class we picked from GtkObject.
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
    
    def on_push_status_activate(self, menuitem, data=None): #adds message to top of stack
        self.status_count += 1 #increment status_count
        self.statusbar.push(self.context_id, "Message number %s" % str(self.status_count))
    
    def on_pop_status_activate(self, menuitem, data=None): #removes top message from stack
        self.status_count -= 1
        self.statusbar.pop(self.context_id)
    
    def on_clear_status_activate(self, menuitem, data=None): #clears status stack
        self.statusbar.remove_all(self.context_id)
        self.status_count = 0
    #        while (self.status_count > 0):
    #            self.statusbar.pop(self.context_id)
    #            self.status_count -= 1
    
    def on_expcombobox_changed(self, widget, data=None):
        # get the index of the changed row
        self.index = widget.get_active()
        
        # get the model
        self.model = widget.get_model()
        
        # retrieve the item from column 1
        self.item = self.model[self.index][1]
        
        # debugging print statements
        print "ComboBox Active Text is", self.item
        print "ComboBox Active Index is", self.index
    
    # This is our init part where we connect the signals
    def __init__(self):
        self.gladefile = "dstatInterface.glade" # store the file name
        self.builder = gtk.Builder() # create an instance of the gtk.Builder
        self.builder.add_from_file(self.gladefile) # add the xml file to the Builder
        
        # This line does the magic of connecting the signals created in the Glade3
        # builder to our defines above. You must have one def for each signal if
        # you use this line to connect the signals.
        self.builder.connect_signals(self)
        
        #expcombobox
        self.expcombobox = self.builder.get_object("expcombobox")
        self.cell = gtk.CellRendererText()
        self.expcombobox.pack_start(self.cell, True) #pack CellRenderer into beginning of combobox cell
        self.expcombobox.add_attribute(self.cell, 'text', 1) # text in column 1
        self.expcombobox.set_active(0) #set initial value

        
        
        #get widgets
        self.window = self.builder.get_object("window1")
        self.aboutdialog = self.builder.get_object("aboutdialog1")
        self.statusbar = self.builder.get_object("statusbar")

        
        self.window.show() # this shows the 'window1' object
        
        self.context_id = self.statusbar.get_context_id("status") #register and get statusbar context_id for description "status"
        self.status_count = 0 #count of messages pushed

# If this is run stand alone execute the following after the 'if'
# If this class is imported into another program the code after the 'if' will
# not run. This makes the code more flexible.
if __name__ == "__main__":
    main = Buglump() # create an instance of our class
    gtk.main() # run the darn thing