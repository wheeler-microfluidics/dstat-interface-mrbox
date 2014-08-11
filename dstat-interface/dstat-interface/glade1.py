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

    def on_sfm_button_clicked(self, button, data=None):
        # create an instance of the entry objects
        # so we can get and set the text values
        self.entry1 = self.builder.get_object("entry1")
        self.entry2 = self.builder.get_object("entry2")
        self.result1 = self.builder.get_object("result1")

        # get the text from the GtkEntry widget and convert
        # it to a float value so we can calculate the result
        self.sfm = float(self.entry1.get_text())
        self.diameter = float(self.entry2.get_text())

        # calculate the result convert to an int to round the number
        # then convert to a string to set the text in our label
        # notice the math.pi constant is used in the calculation
        self.rpm = str(int(self.sfm * ((12/math.pi)/self.diameter)))

        # debugging print
        print "calculate rpm clicked"

        # set the result label with our results
        self.result1.set_text(self.rpm)

    def on_gtk_new_activate(self, menuitem, data=None):
        # debugging message
        print 'File New selected'
        
        # create a label for the tab and using get_n_pages() to find out how
        # many pages there is so the next page has a sequential number.
        self.label1 = gtk.Label('Page ' + str(self.notebook.get_n_pages() + 1))
        
        # create a label to put into the page
        self.label2 = gtk.Label('Hello World')
        # If you don't show the contents of the tab it won't show up
        self.label2.show()
        
        # append a page with label5 as the contents and label5 as the tab
        self.notebook.append_page(self.label2, self.label1)

    def on_notebook1_switch_page(self,  notebook, page, page_num, data=None):
        self.tab = notebook.get_nth_page(page_num)
        self.label = notebook.get_tab_label(self.tab).get_label()
        self.message_id = self.statusbar.push(0, self.label)



    # This is our init part where we connect the signals
    def __init__(self):
        self.gladefile = "test1.glade" # store the file name
        self.builder = gtk.Builder() # create an instance of the gtk.Builder
        self.builder.add_from_file(self.gladefile) # add the xml file to the Builder
        
        # This line does the magic of connecting the signals created in the Glade3
        # builder to our defines above. You must have one def for each signal if
        # you use this line to connect the signals.
        self.builder.connect_signals(self)
        
        #get widgets
        self.window = self.builder.get_object("window1")
        self.aboutdialog = self.builder.get_object("aboutdialog1")
        self.statusbar = self.builder.get_object("statusbar")
        self.notebook = self.builder.get_object("notebook1")
        
        self.window.show() # this shows the 'window1' object

        self.context_id = self.statusbar.get_context_id("status") #register and get statusbar context_id for description "status"
        self.status_count = 0 #count of messages pushed

# If this is run stand alone execute the following after the 'if'
# If this class is imported into another program the code after the 'if' will
# not run. This makes the code more flexible.
if __name__ == "__main__":
    main = Buglump() # create an instance of our class
    gtk.main() # run the darn thing