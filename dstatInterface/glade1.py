#!/usr/bin/env python

import gtk

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
    
    # This is our init part where we connect the signals
    def __init__(self):
        self.gladefile = "test1.glade" # store the file name
        self.builder = gtk.Builder() # create an instance of the gtk.Builder
        self.builder.add_from_file(self.gladefile) # add the xml file to the Builder
        
        # This line does the magic of connecting the signals created in the Glade3
        # builder to our defines above. You must have one def for each signal if
        # you use this line to connect the signals.
        self.builder.connect_signals(self)
        
        #get windows
        self.window = self.builder.get_object("window1")
        self.aboutdialog = self.builder.get_object("aboutdialog1")
        
        self.window.show() # this shows the 'window1' object

# If this is run stand alone execute the following after the 'if'
# If this class is imported into another program the code after the 'if' will
# not run. This makes the code more flexible.
if __name__ == "__main__":
    main = Buglump() # create an instance of our class
    gtk.main() # run the darn thing