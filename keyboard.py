#!/usr/bin/env python

#   Popup keyboard emulator for use on all alphanumeric entries

#   Copyright (c) 2017 Kurt Jacobson
#        <kcjengr@gmail.com>
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

import pygtk
import gtk
import os
import sys
import gobject

pydir = os.path.abspath(os.path.dirname(__file__))
IMAGEDIR = os.path.join(pydir, "images") 

_keymap = gtk.gdk.keymap_get_default()


class keyboard(object):

    def __init__(self, entry, pos, persistent=False ):
        
        self.keyboard = keyboard
        self.entry_buf = entry.get_buffer()
        self.entry = entry
        self.persistent = persistent
        
        # Glade setup
        gladefile = os.path.join(IMAGEDIR, 'keyboard.glade')

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")
        
        self.window.move(pos[0]+105, pos[1]+440) #545, 650)
        self.window.show()
        
        gobject.timeout_add(50, self.repeat_event)  # Keypress repeat function
        
        # FIXME this is messy
        self.event = None
        self.widget = self.builder.get_object('a')
        self.wait_counter = 0
        
        
        self.window.set_keep_above(True)
    
        self.letters = 'abcdefghijklmnopqrstuvwxyz ' # Now I've said my abc's
#                Don't remove the space character ^ It's named ' ' in glade too!
                                                
        self.numbers = '`1234567890-=' # Now I've said my 1 2 3's
        
        # Relate special character to their glade names.
        self.characters = {'`':'~', '1':'!', '2':'@', '3':'#', '4':'$', 
                           '5':'%', '6':'^', '7':'&', '8':'*', '9':'(', 
                           '0':')', '-':'_', '=':'+', '[':'{', ']':'}', 
                           '\\':'|', ';':':', "'":'"', ',':'<', '.':'>',
                           '/':'?'} # Now I've said my @#$%^%!
        
        self.letter_btn_dict = dict((l, self.builder.get_object(l)) for l in self.letters)
        
        self.number_btn_dict = dict((n, self.builder.get_object(n)) for n in self.characters)
        
        # Connet letter button press events
        for l, btn in self.letter_btn_dict.iteritems():
            btn.connect("pressed", self.on_button_pressed)
            
        # Connet number button press events
        for l, btn in self.number_btn_dict.iteritems():
            btn.connect("pressed", self.on_button_pressed)
        
        
# =========================================================
## BEGIN - Keyboard Settings
# =========================================================
  
    # Caps Lock        
    def on_caps_lock_toggled(self, widget):
        if widget.get_active():
            self.caps(True)
        else:
            self.caps(False)
            

    # Left shift unshifts after keypress           
    def on_left_shift_toggled(self, widget):
        if widget.get_active():
            self.shift(True)
        else:
            self.shift(False)
            
            
    # Right shift is "sticky"
    def on_right_shift_toggled(self, widget):
        if widget.get_active():
            self.shift(True)
        else:
            self.shift(False)
            
            
    # Caps lock action           
    def caps(self, data = False):
        if data:
            for l, btn in self.letter_btn_dict.iteritems():
                btn.set_label(l.upper())
        else:
            for l, btn in self.letter_btn_dict.iteritems():
                btn.set_label(l.lower())
                
                
    # Shift action, inverts caps lock setting 
    def shift(self, data = False):
        if data:
            for n, btn in self.number_btn_dict.iteritems():
                btn.set_label(self.characters[n])
            if self.builder.get_object('caps_lock').get_active():
                self.caps(False)
            else:
                self.caps(True)
        else:
            for n, btn in self.number_btn_dict.iteritems():
                btn.set_label(n)
            if self.builder.get_object('caps_lock').get_active():
                self.caps(True)
            else:
                self.caps(False)
            self.builder.get_object('left_shift').set_active(False)
            
            
            
# =========================================================
## BEGIN - Keyboard Emulation
# =========================================================

        
    def emulate_key(self, widget, key):
        try:
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = int(gtk.gdk.keyval_from_name(key))
            event.hardware_keycode = _keymap.get_entries_for_keyval(event.keyval)[0][0]
            event.window = self.entry.window
            self.event = event
            self.widget = widget
            self.wait_counter = 0           # Set counter for repeat timeout
            self.entry.event(self.event)    # Do the initial event
        except:
            self.window.hide()

            
    def repeat_event(self):
        if self.widget.get_state() == gtk.STATE_ACTIVE:
            if self.wait_counter < 5:
                self.wait_counter += 1
            else:
                try:
                    self.entry.event(self.event)    # Do an initial event
                except:
                    pass
        return True
        
        
# =========================================================
## BEGIN - Button Handlers
# =========================================================


#    # This would work for letters but not for the special characters        
#    def on_button_pressed(self, widget):
#        self.emulate_key(widget, widget.get_label())
#        # Unshift if left shift is active, right shift is "sticky" 
#        if self.builder.get_object('left_shift').get_active():
#            self.shift(False)
            
            
    # This handles all the character entry        
    def on_button_pressed(self, widget):
        try: # Needed since the widget may not have focus anymore
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = ord(widget.get_label())
            event.hardware_keycode = -1    # For some reason don't need a keycode...
            event.window = self.entry.window
            self.event = event
            self.widget = widget
            self.wait_counter = 0           # Set counter for repeat timout
            self.entry.event(self.event)    # Do the initial event
        except:
            self.window.hide()
            pass
        
        # Unshift if left shift is active, right shift is "sticky" 
        if self.builder.get_object('left_shift').get_active():
            self.shift(False)
    
        
    # Backspace    
    def on_backspace_pressed(self, widget): 
        self.emulate_key(widget, "BackSpace")
        
    # Tab 
    def on_tab_pressed(self, widget):
        self.emulate_key(widget, "Tab")
        
    # Return    
    def on_return_pressed(self, widget):
        self.enter(widget)
        
    # Left arrow
    def on_arrow_left_pressed(self, widget):
        self.emulate_key(widget, "Left")  
      
    # Right arrow    
    def on_arrow_right_pressed(self, widget):
        self.emulate_key(widget, "Right")
        
    # Up Arrow    
    def on_arrow_up_pressed(self, widget):
        self.emulate_key(widget, "Up")

    # Down Arrow
    def on_arrow_down_pressed(self, widget):
        self.emulate_key(widget, "Down")
     
    # FIXME    
    def ctrl_pressed(self, widget):
        print "Control_L" #Control_L\
        event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        event.keyval = int(gtk.gdk.keyval_from_name('Control_L'))
        event.hardware_keycode = _keymap.get_entries_for_keyval(event.keyval)[0][0]
        event.window = self.entry.window
        self.entry.emit("key-press-event", event)
        
    # Catch real ESC or ENTER key presses
    def on_window_key_press_event(self, widget, event, data=None):
        kv = event.keyval
        if kv == gtk.keysyms.Escape:
            self.escape() # Close the keyboard
        elif kv == gtk.keysyms.Return or kv == gtk.keysyms.KP_Enter:
            self.enter(widget)
        else: # Pass other keypresses on to the entry widget
            #print _keymap.get_entries_for_keyval(kv)
            try:
                self.entry.emit("key-press-event", event)
            except:
                pass
    
    def on_esc_pressed(self, widget, data=None):
        self.escape()
        
    # Escape action
    def escape(self):
        try:
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS) 
            event.keyval = gtk.keysyms.Escape
            event.window = self.entry.window
            self.entry.event(event)
            self.entry.emit("key-press-event", event)
        except:
            pass
        #self.window.destroy()
        self.window.hide()
        
        
    def enter(self, widget):
        self.emulate_key(widget, "Return")
        if not self.persistent:
            self.window.hide()
        
        
    def on_window_focus_out_event(self, widget, data=None):
        print "Focus out"
        self.escape()
        
        
def main():
    gtk.main()
    

if __name__ == "__main__":
    ui = keyboard()
    main()

