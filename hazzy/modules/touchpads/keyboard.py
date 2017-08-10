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
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if not HAZZYDIR in sys.path:
    sys.path.insert(1, HAZZYDIR)

UIDIR = os.path.join(PYDIR, 'ui')
STYLEDIR = os.path.join(HAZZYDIR, 'themes')

# Setup logging
from utilities import logger
log = logger.get("HAZZY.KEYBOARD")


_keymap = Gdk.Keymap.get_default()


def singleton(cls):
    return cls()

@singleton
class Keyboard():

    def __init__(self):

        self.entry = None
        self.parent = None
        self.persistent = False

        # Glade setup
        gladefile = os.path.join(UIDIR, 'keyboard.glade')

        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        keyboard = self.builder.get_object('keyboard')
        self.window = self.builder.get_object('window')
        self.window.set_keep_above(True)
        self.window.add(keyboard)

        # Setup CSS themeing
        style_provider = Gtk.CssProvider()

        with open(os.path.join(STYLEDIR, "style.css"), 'rb') as css:
            css_data = css.read()

        style_provider.load_from_data(css_data)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


        self.wait_counter = 0

        self.letters = 'abcdefghijklmnopqrstuvwxyz' # Now I've said my abc's
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

#        # Connect letter button press events
        for l, btn in self.letter_btn_dict.iteritems():
            btn.connect("pressed", self.emulate_key) #self.on_button_pressed)

        # Connect number button press events
        for l, btn in self.number_btn_dict.iteritems():
            btn.connect("pressed", self.emulate_key) #self.on_button_pressed)

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
            event.window = self.entry.get_window()
            self.entry.event(event)    # Do the initial event

            # Call key repeat function every 50ms
            self.wait_counter = 0      # Set counter for repeat timeout
            GObject.timeout_add(50, self.key_repeat, widget, event)

        except Exception as e:
            log.exception(e)
            log.error("HAZZY KEYBOARD ERROR: key emulation error - " + str(e))
            self.window.hide()

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

    # Escape
    def on_esc_pressed(self, widget, data=None):
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
        self.window.hide()

    def enter(self, widget):
        self.emulate_key(widget, Gdk.KEY_Return)
        if not self.persistent:
            self.window.hide()

    def on_entry_loses_focus(self, widget, data=None):
        self.escape()

    def on_entry_key_press(self, widget, event, data=None):
        kv = event.keyval
        if kv == Gdk.KEY_Escape:
            self.window.hide() # Close the keyboard

# ==========================================================
# Show the keyboard
# ==========================================================

    def show(self, entry, persistent=False ):
        self.entry = entry
        self.persistent = persistent
        self.entry.connect('focus-out-event', self.on_entry_loses_focus)
        #self.entry.connect('key-press-event', self.on_entry_key_press)
        if self.parent:
            pos = self.parent.get_position()
            self.window.move(pos[0]+105, pos[1]+440)
        self.window.show()

    def set_parent(self, parent):
        self.parent = parent


# ==========================================================
# For standalone testing
# ==========================================================

def show(widget, event):
    keyboard.show(entry)

def destroy(widget):
    Gtk.main_quit()

def main():
    Gtk.main()

if __name__ == "__main__":
    keyboard = Keyboard
    entry = Gtk.Entry()
    window = Gtk.Window()
    window.add(entry)
    window.connect('destroy', destroy)
    entry.connect('button-press-event', show)
    window.show_all()
    keyboard.set_parent(window)
    keyboard.show(entry)
    main()
