#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   PopOver keyboard emulator for use on all alphanumeric entries

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR, 'ui')

#from utilities import logger

## Setup logging
#log = logger.get(__name__)

import logging

log = logging.getLogger(__name__)


_keymap = Gdk.Keymap.get_default()

class Keyboard():

    def __init__(self):

        self.entry = None
        self.parent = None
        self.persistent = False

        self.focus_out_sig = None
        self.key_press_sig = None

        # Glade setup
        gladefile = os.path.join(UIDIR, 'keyboard.ui')

        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.keyboard = self.builder.get_object('keyboard')

        self.wait_counter = 0

        self.letters = 'abcdefghijklmnopqrstuvwxyz' # Now I've said my abc's
        self.numbers = '`1234567890-='              # Now I've said my 1 2 3's

        # Relate special character to their glade names.
        self.characters = {'`':'~', '1':'!', '2':'@', '3':'#', '4':'$',
                           '5':'%', '6':'^', '7':'&', '8':'*', '9':'(',
                           '0':')', '-':'_', '=':'+', '[':'{', ']':'}',
                           '\\':'|', ';':':', "'":'"', ',':'<', '.':'>',
                           '/':'?'} # Now I've said my @#$%^%!

        self.letter_btn_dict = dict((l, self.builder.get_object(l)) for l in self.letters)

        self.number_btn_dict = dict((n, self.builder.get_object(n)) for n in self.characters)

        # Connect letter button press events
        for l, btn in self.letter_btn_dict.iteritems():
            btn.connect("pressed", self.emulate_key) #self.on_button_pressed)

        # Connect number button press events
        for l, btn in self.number_btn_dict.iteritems():
            btn.connect("pressed", self.emulate_key) #self.on_button_pressed)


        print "Initializing the keyboard"


# =========================================================
# Keyboard Settings
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
# Keyboard Emulation
# =========================================================

    def emulate_key(self, widget, key=None):
        try:
            event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)

            if key:
                event.keyval = int(key)
            else:
                event.keyval = ord(widget.get_label())

            event.hardware_keycode = _keymap.get_entries_for_keyval(event.keyval)[1][0].keycode

            # add control mask if ctrl is active
            if self.builder.get_object('ctrl').get_active():
                event.state = Gdk.ModifierType.CONTROL_MASK
                self.builder.get_object('ctrl').set_active(False)

            #self.entry.get_parent_window()
            # FIXME This is a kludge to get the window for both Entry and TextView
            try:
                event.window = self.entry.get_window()
            except TypeError:
                event.window = self.entry.get_window(Gtk.TextWindowType.TEXT)

            self.entry.event(event)    # Do the initial event

            # Call key repeat function every 50ms
            self.wait_counter = 0      # Set counter for repeat timeout
            GObject.timeout_add(50, self.key_repeat, widget, event)

        except Exception as e:
            print(e)
            print("HAZZY KEYBOARD ERROR: key emulation error - " + str(e))


        # Unshift if left shift is active, right shift is "sticky"
        if self.builder.get_object('left_shift').get_active():
            self.shift(False)


    def key_repeat(self, widget, event):
        if widget.get_state() == Gtk.StateType.ACTIVE:
            # 250ms initial repeat delay
            if self.wait_counter < 5:
                self.wait_counter += 1
            else:
                try:
                    self.entry.event(event)    # Repeat the event
                except:
                    pass
            return True
        return False


# =========================================================
# Button Handlers
# =========================================================

    # Space
    def on_space_pressed(self, widget):
        self.emulate_key(widget, Gdk.KEY_space)

    # Backspace
    def on_backspace_pressed(self, widget):
        self.emulate_key(widget, Gdk.KEY_BackSpace)

    # Tab
    def on_tab_pressed(self, widget):
        self.emulate_key(widget, Gdk.KEY_Tab)

    # Return
    def on_return_pressed(self, widget):
        self.enter(widget)
        return

    # Escape
    def on_escape_clicked(self, widget, data=None):
        self.escape()

    # Left arrow
    def on_arrow_left_pressed(self, widget):
        self.emulate_key(widget, Gdk.KEY_Left)

    # Right arrow
    def on_arrow_right_pressed(self, widget):
        self.emulate_key(widget, Gdk.KEY_Right)

    # Up Arrow
    def on_arrow_up_pressed(self, widget):
        self.emulate_key(widget,  Gdk.KEY_Up)

    # Down Arrow
    def on_arrow_down_pressed(self, widget):
        self.emulate_key(widget,  Gdk.KEY_Down)

    # TODO add persistence mode on double click
    def on_ctrl_toggled(self, widget):
        pass

    # Catch real ESC or ENTER key presses
    def on_window_key_press_event(self, widget, event, data=None):
        kv = event.keyval
        if kv == Gdk.KEY_Escape:
            self.escape() # Close the keyboard
        elif kv == Gdk.KEY_Return or kv == Gdk.KEY_KP_Enter:
            self.enter(widget)
        else: # Pass other keypresses on to the entry widget
            try:
                self.entry.emit("key-press-event", event)
            except:
                pass

    # Escape action
    def escape(self):
        try:
            event = Gdk.Event(Gdk.KEY_PRESS)
            event.keyval = Gdk.KEY_Escape
            event.window = self.entry.window
            self.entry.event(event)
            self.entry.emit("key-press-event", event)
        except:
            pass
        self.entry.disconnect(self.focus_out_sig)
        self.entry.disconnect(self.key_press_sig)
        self.keyboard.hide()

    def enter(self, widget):
        self.emulate_key(widget, Gdk.KEY_Return)
        if not self.persistent:
            self.keyboard.hide()

    def on_entry_loses_focus(self, widget, data=None):
        self.escape()

    def on_entry_key_press(self, widget, event, data=None):
        kv = event.keyval
        if kv == Gdk.KEY_Escape:
            self.keyboard.hide() # Close the keyboard

# ==========================================================
# Show the keyboard
# ==========================================================

    def show(self, entry, persistent=False):
        self.entry = entry
        self.persistent = persistent
        self.focus_out_sig = self.entry.connect('focus-out-event', self.on_entry_loses_focus)
        self.key_press_sig = self.entry.connect('key-press-event', self.on_entry_key_press)
        self.keyboard.set_relative_to(entry)
        self.keyboard.popup()

    def on_button_press(self, widget, event):
        # Needed to prevent closing the PopOver on activate
        return True


# ==========================================================
# For use without having to initialize
# ==========================================================

keyboard = Keyboard()

def show(entry, data=None):
    keyboard.show(entry)


# ==========================================================
# For standalone testing
# ==========================================================


def demo():
    keyboard = Keyboard()

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

    entry = Gtk.Entry()
    entry.set_hexpand(False)
    entry.set_vexpand(False)
    entry.connect('focus-in-event', show)
    box.pack_start(entry, False, False, 5)

    button = Gtk.Button()
    box.pack_start(button, False, False, 5)

    window = Gtk.Window(title="Test Keyboard")
    window.connect('destroy', Gtk.main_quit)
    window.add(box)

    window.set_size_request(1000, 400)
    window.show_all()

    Gtk.main()

if __name__ == "__main__":
    demo()
