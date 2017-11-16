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
#   Entry widgets that suport popup keyboard.

# ToDo:
#   Finish and add numeric netry widgets.

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from utilities import preferences as prefs

from widget_factory.TouchPads import keyboard



class ValidatableEntry(Gtk.Entry, Gtk.Editable):
    __gtype_name__ = 'ValidatableEntry'
    __gsignals__ = {
        'validate-text': (GObject.SignalFlags.RUN_FIRST, None, (str, int, int)),
    }

    # Many of the entries used in Hazzy listen to the `insert-text` signal and
    # then validate the entry before actually setting the text.  The problem is
    # that PyGI signals do not properly handle return values from methods called
    # by a signal, resulting in incorrect cursor positions and the message:
    # `Warning: g_value_get_int: assertion 'G_VALUE_HOLDS_INT (value)' failed Gtk.main()`

    # The solution is to inherent Gtk.Editable and Gtk.Entry and override the
    # default `do_insert_text` method so that is returns the popper pointer position.

    # References:
    #   https://stackoverflow.com/questions/38815694/gtk-3-position-attribute-on-insert-text-signal-from-gtk-entry-is-always-0
    #   https://stackoverflow.com/questions/40074977/how-to-format-the-entries-in-gtk-entry/40163816

    def __init__(self):
        super(ValidatableEntry, self).__init__()

    # This can be overridden to perform validation, or in cases were the cursor
    # pos is not effected by the validation the, `validate-text` signal can be
    # used to call a method to perform the validation without having to subclass.
    def do_insert_text(self, new_text, length, position):
        self.get_buffer().insert_text(position, new_text, length)
        self.emit('validate-text', new_text, length, position)
        return position + length


class TextEntry(ValidatableEntry):
    def __init__(self):
        super(ValidatableEntry, self).__init__()

        self.use_vertual_keyboard = True
        self.activate_on_focus_out = False
        self._was_activated = False

        self.previous_value = ""

        self.connect('focus-in-event', self.on_focus_in)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('key-press-event', self.on_key_press)
        self.connect('activate', self.on_activate)

    def on_focus_in(self, widegt, event):
        self.previous_value = self.get_text()
        if self.use_vertual_keyboard:
            keyboard.show(self)

    def on_focus_out(self, widegt, event):
        if self._was_activated:
            return
        if self.activate_on_focus_out:
            self.do_activate(widegt)
        else:
            # Revert
            self.set_text(self.previous_value)
        # Reset flag
        self._was_activated = False

    def on_activate(self, widget):
        self._was_activated = True
        self.get_toplevel().set_focus(None)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.set_text(self.previous_value) # Revert
            self.get_toplevel().set_focus(None)

    def set_activate_on_focus_out(self, setting):
        self.activate_on_focus_out = setting

    def set_use_vertual_keyboard(self, setting):
        self.use_vertual_keyboard = setting
