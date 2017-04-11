#!/usr/bin/env python

#   Popup numberpad for use on all numeric only entries

#   Copyright (c) 2017 Kurt Jacobson
#       <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import os

pydir = os.path.abspath(os.path.dirname(__file__))
IMAGEDIR = os.path.join(pydir, "images") 

_keymap = gtk.gdk.keymap_get_default()  # Needed for keypress emulation

class touchpad(object):

    def __init__(self, widget, position=None, kind='numpad'):
        
        self.dro = widget
        self.original_text = self.dro.get_text() # Save the original entry
        #self.dro.set_text('')                    # Clear the DRO    
        
        # Glade setup
        if kind == 'numpad': 
            gladefile = os.path.join(IMAGEDIR, 'numpad.glade')
            self.keypad = False
        else:
            gladefile = os.path.join(IMAGEDIR, 'keypad.glade')
            self.keypad = True

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")
        
        # Set position if requested
        if position != None:
            self.window.move(position[0], position[1])
            
        self.window.show()
        
    
    # Handles all the character buttons
    def on_button_clicked(self, widget):
        self.dro.delete_selection() 
        pos = self.dro.get_position()                  # Get current cursor pos 
        self.dro.insert_text(widget.get_label(), pos)  # Insert text at cursor pos
        self.dro.set_position(pos + 1)                 # Move cursor one space right
        
        
    # Backspace
    def on_backspace_clicked(self, widget):
        pos = self.dro.get_position()       # Get current cursor pos
        self.dro.delete_text(pos - 1, pos)  # Delete one space to left
        self.dro.set_position(pos - 1)      # Move cursor one space to left

        
    # Change sign / Negative Sign  
    def on_change_sign_clicked(self, widget):
        val = self.dro.get_text()
        pos = self.dro.get_position()
        if self.keypad or val == "":
            self.dro.insert_text("-", pos)
            self.dro.set_position(pos + 1)
        else:
            if val[0] == '-':
                self.dro.delete_text(0, 1)
            else:
                self.dro.insert_text("-", 0)      
                     
        
    # Left arrow
    def on_arrow_left_clicked(self, widget):
        pos = self.dro.get_position()
        if pos > 0: # Can't have -1 or we loop to the right
            self.dro.set_position(pos - 1)
            
            
    # Right arrow    
    def on_arrow_right_clicked(self, widget):
        pos = self.dro.get_position()  
        self.dro.set_position(pos + 1)
        
        
    # Up arrow   
    def on_arrow_up_clicked(self, widget):
        event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        event.keyval = gtk.keysyms.Up
        self.dro.emit("key-press-event", event)
        
        
    # Down arrow
    def on_arrow_down_clicked(self, widget):
        event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        event.keyval = gtk.keysyms.Down
        self.dro.emit("key-press-event", event)   
         
        
    # Space    
    def on_space_clicked(self, widget, data=None):
        pos = self.dro.get_position()       # Get current cursor pos 
        self.dro.insert_text("\t", pos)     # Insert tab at cursor pos
        self.dro.set_position(pos + 1)      # Move cursor one tab right
        
        
    # Escape
    def on_esc_clicked(self, widget, data=None):
        self.escape() 
        
        
    # Enter
    def enter_clicked(self, widget):
        self.enter()
        
        
    # Catch real ESC or ENTER keypresses, sent the rest on to the DRO
    def on_window_key_press_event(self, widget, event, data=None):
        kv = event.keyval
        if kv == gtk.keysyms.Return or kv == gtk.keysyms.KP_Enter:
            self.enter()
        elif kv == gtk.keysyms.Escape:
            self.escape()
        else: # Pass it on to the dro entry widget
            try:
                self.dro.emit("key-press-event", event)
            except:
                self.window.destroy()
            
    
    # Enter action    
    def enter(self):
        # If entry is nothing escape
        try:
            if self.dro.get_text() == "" or self.dro.get_text() == "-":
                self.escape()
            else:
                self.dro.emit('activate')
        except:
            pass
        self.window.destroy()
            
            
    # Escape action
    def escape(self):
        try:
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = int(gtk.gdk.keyval_from_name("Escape"))
            event.hardware_keycode = _keymap.get_entries_for_keyval(event.keyval)[0][0]
            event.window = self.dro.window
            self.dro.emit("key-press-event", event)
        except:
            pass
        self.window.destroy()
        
        
    # Escape on focus out
    def on_window_focus_out_event(self, widget, data=None):
        self.escape()
        

def main():
    gtk.main()
    

if __name__ == "__main__":
    ui = touchpad()
    main()

