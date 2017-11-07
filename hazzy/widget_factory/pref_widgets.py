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
#   These are convenience widgets for use when developing new widgets.
#   They are used for displaying and setting the various types of
#   preferences that a widget might have.

# ToDo:
#   Add slider pref widgets, rethink how widget groups should be done.

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from utilities import preferences as prefs


class PrefEntry(Gtk.Entry):
    __gtype_name__ = 'PrefEntry'
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        }

    def __init__(self, section, option, default_value=''):
        Gtk.Entry.__init__(self)

        self.section = section
        self.option = option
        self.default_value = default_value

        self.connect('focus-out-event', self.on_focus_out)
        self.connect('key-press-event', self.on_key_press)
        self.connect('activate', self.on_activate)

        self.value = prefs.get(self.section, self.option, self.default_value, str)
        self.set_text(str(self.value))

    def on_activate(self, widget):
        self.set_preference()

    def on_focus_out(self, widget, data=None):
        self.set_preference()

    def on_key_press(self, widget, event, data=None):
        if event.keyval == Gdk.KEY_Escape:
            self.set_text(self.value) # Revert
            self.get_toplevel().set_focus(None)

    def set_preference(self):
        value = self.get_text()
        if value == self.value:
            return
        self.value = value
        prefs.set(self.section, self.option, self.value, str)
        self.emit('value-changed', self.value)
        self.select_region(0, 0)
        self.get_toplevel().set_focus(None)


class PrefComboBox(Gtk.ComboBox):
    __gtype_name__ = 'PrefComboBox'
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        }

    def __init__(self, section, option, items=[], default_item=None):
        Gtk.ComboBox.__init__(self)

        self.section = section
        self.option = option
        self.items = items
        self.default_item = default_item

        self.model = Gtk.ListStore(str)
        self.set_model(self.model)

        for item in self.items:
            self.model.append([item])

        renderer_text = Gtk.CellRendererText()
        self.pack_start(renderer_text, True)
        self.add_attribute(renderer_text, "text", 0)

        self.item = prefs.get(self.section, self.option, self.default_item, str)
        self.set_selected(self.item)

        self.connect("changed", self.on_selection_changed)

    def set_selected(self, item):
        for row in range(len(self.model)):
            if self.model[row][0] == item:
                self.set_active_iter(self.model.get_iter(row))
                self.item = item
                self.emit('value-changed', self.item)
                break

    def on_selection_changed(self, widget):
        tree_iter = widget.get_active_iter()
        if tree_iter != None:
            self.item = self.model[tree_iter][0]
            prefs.set(self.section, self.option, self.item)
            self.emit('value-changed', self.item)


class PrefCheckButton(Gtk.CheckButton):
    __gtype_name__ = 'PrefCheckButton'
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        }

    def __init__(self, section, option, default_value=False):
        Gtk.CheckButton.__init__(self)

        self.section = section
        self.option = option
        self.default_value = default_value

        self.connect('toggled', self.on_toggle)

        self.state = prefs.get(self.section, self.option, self.default_value, bool)
        self.set_active(self.state)

    def on_toggle(self, widget):
        self.state = self.get_active()
        prefs.set(self.section, self.option, self.state)
        self.emit('value-changed', self.state)


class PrefSwitch(Gtk.Switch):
    __gtype_name__ = 'PrefSwitch'
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        }

    def __init__(self, section, option, default_value=False):
        Gtk.Switch.__init__(self)

        self.section = section
        self.option = option
        self.default_value = default_value

        self.connect('state-set', self.on_state_set)

        self.state = prefs.get(self.section, self.option, self.default_value, bool)
        self.set_active(self.state)

    def on_state_set(self, widget, event):
        self.state = not self.get_state() # Don't know why need to invert
        prefs.set(self.section, self.option, self.state)
        self.emit('value-changed', self.state)


class PrefFeild(Gtk.Box):
    def __init__(self, feild, group):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label(feild.option)
        self.pack_start(label, True, True, 0)
        self.pack_start(feild, True, True, 0)
        group.add_widget(label)
        group.add_widget(feild)
