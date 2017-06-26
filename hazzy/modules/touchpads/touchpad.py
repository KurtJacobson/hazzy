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
IMAGEDIR = os.path.join(pydir, "ui")

_keymap = gtk.gdk.keymap_get_default()  # Needed for keypress emulation


class Touchpad():

    def __init__(self, kind='float'):

        self.dro = None
        self.original_text = None

        # Glade setup
        if kind == 'float':
            gladefile = os.path.join(IMAGEDIR, 'float_numpad.glade')
        else:
            gladefile = os.path.join(IMAGEDIR, 'int_numpad.glade')

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")
        self.window.set_keep_above(True)

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

    # Change sign
    def on_change_sign_clicked(self, widget):
        val = self.dro.get_text()
        pos = self.dro.get_position()
        if val == "": # or self.keypad:
            self.dro.insert_text("-", pos)
            self.dro.set_position(pos + 1)
        else:
            if val[0] == '-':
                self.dro.delete_text(0, 1)
            else:
                self.dro.insert_text("-", 0)

    # Change units
    # Note: We don't set the cursor to end to keep the user from
    # being able to backspace and leave a partial units string
    def on_change_units_clicked(self, widget):
        pos = self.dro.get_position()
        val = self.dro.get_text()
        if self.units == 'in' and not 'mm' in val:
            self.dro.set_text(val + 'mm')
            self.dro.set_position(pos)
        elif self.units == 'mm' and not 'in' in val:
            self.dro.set_text(val + 'in')
            self.dro.set_position(pos)
        elif 'mm' in val and self.units == 'in':
            val = val.replace('mm', '')
            self.dro.set_text(val)
            self.dro.set_position(pos)
        elif 'in' in val and self.units == 'mm':
            val = val.replace('in', '')
            self.dro.set_text(val)
            self.dro.set_position(pos)


    # Left arrow
    def on_arrow_left_clicked(self, widget):
        pos = self.dro.get_position()
        if pos > 0: # Can't have -1 or we'd loop to the right
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
    def on_enter_clicked(self, widget):
        self.enter()

    # Catch real ESC or ENTER keypresses, send the rest on to the DRO
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
                self.window.hide()

    # Enter action
    def enter(self):
        try:
            # If entry is nothing escape
            if self.dro.get_text() == "" or self.dro.get_text() == "-":
                self.escape()
            else:
                self.dro.emit('activate')
        except:
            pass
        self.window.hide()

    # Escape action
    def escape(self):
        self.dro.set_text(self.original_text)
        try:
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = int(gtk.gdk.keyval_from_name("Escape"))
            event.hardware_keycode = _keymap.get_entries_for_keyval(event.keyval)[0][0]
            event.window = self.dro.window
            self.dro.emit("key-press-event", event)
        except:
            pass
        self.window.hide()


    # Escape on entry focus out 
    def on_entry_loses_focus(self, widget, data=None):
        self.escape()


    def show(self, widget, units='in', position=None):
        self.dro = widget
        self.dro.connect('focus-out-event', self.on_entry_loses_focus)
        self.units = units

        self.original_text = self.dro.get_text()

        if position is not None:
            self.window.move(position[0], position[1])

        self.window.show()


def main():
    gtk.main()

if __name__ == "__main__":
    ui = Touchpad()
    main()

