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
#   Various DRO widegts.

# ToDo:
#   Add DRO label widgets.

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from utilities import ini_info
from utilities import machine_info
from utilities import status
from utilities import command
from utilities import entry_eval
from utilities import preferences as prefs
from utilities.constants import Units

from widget_factory.TouchPads import keyboard

class DroType:
    ABS = 0
    REL = 1
    DTG = 2

class DroEntry(Gtk.EventBox):
    '''Base DRO entry class'''
    # Uses a Gtk.EventBox placed over a Gtk.Entry so that when the entry
    # is insensitive we can still catch button press events and remove
    # focus, needed for touchscreen use were no escape key is handy.

    coords = machine_info.coordinates
    machine_units = ini_info.get_machine_units()

    # Set the conversions used for changing the DRO units
    # Only convert linear axes (XYZUVW), use factor of unity for ABC
    if machine_units == Units.MM: 
        # List of factors for converting from mm to inches
        conversion_list = [1.0/25.4]*3+[1]*3+[1.0/25.4]*3
    else:
        # List of factors for converting from inches to mm
        conversion_list = [25.4]*3+[1]*3+[25.4]*3

    def __init__(self, axis_letter, dro_type=DroType.REL):
        Gtk.EventBox.__init__(self)

        self.axis_letter = axis_letter
        self.axis_num = 'xyzabcuvw'.index(self.axis_letter.lower())
        self.joint_num = self.coords.index(self.axis_letter.lower())
        self.dro_type = dro_type

        # Don't let the EventBox hide the entry
        self.set_visible_window(False)

        # Make expand to fill space allocated space
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Add the actual DRO display
        self.entry = Gtk.Entry()
        self.add(self.entry)

        self.set_editable(False) # Default to not editable

        self.entry.set_alignment(1)   # Move text to far right
        self.entry.set_width_chars(7) # 6 digits and a decimal point (99.9999)

        # Add style class
        self.style_context = self.entry.get_style_context()
        self.style_context.add_class("DroEntry")

        # Could set font like this, but CSS better
#        font = Pango.FontDescription('16')
#        self.modify_font(font)

        self.in_decimal_places = prefs.get('DROs', 'IN_DEC_PLCS', 4, int)
        self.mm_decimal_places = prefs.get('DROs', 'MM_DEC_PLCS', 3, int)
        self.conversion_factor = self.conversion_list[self.axis_num]
        self.dec_plcs = self.in_decimal_places
        self.factor = 1
        self.has_focus = False
        self.selected = False

        self.connect('button-press-event', self.on_eventbox_clicked)
        self.entry.connect('button-press-event', self.on_button_press)
        self.entry.connect('button-release-event', self.on_button_release)
        self.entry.connect('focus-in-event', self.on_focus_in)
        self.entry.connect('focus-out-event', self.on_focus_out)
        self.entry.connect('key-press-event', self.on_key_press)
        self.entry.connect('activate', self.on_activate)

        status.on_changed('stat.axis-positions', self._update_dro)
        status.on_changed('stat.program_units', self._update_units)

    def _update_dro(self, widget, positions):
        if not self.has_focus: # Don't step on user trying to enter value
            pos = positions[self.dro_type][self.axis_num] * self.factor

            pos_str = '{:.{dec_plcs}f}'.format(pos, dec_plcs=self.dec_plcs)
            self.entry.set_text(pos_str)

    def _update_units(self, status, units):
        if units == self.machine_units:
            self.factor = 1
        else:
            self.factor = self.conversion_factor
        if units == Units.IN:
            self.dec_plcs = self.in_decimal_places
        else:
            self.dec_plcs = self.mm_decimal_places

    def on_button_press(self, widegt, event, data=None):
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS \
            or event.type == Gdk.EventType.TRIPLE_BUTTON_PRESS:
            return True

    def on_button_release(self, widget, data=None):
        if not self.selected:
            self.selected = True
            return True

    def on_focus_in(self, widegt, data=None):
        self.select()

    def on_focus_out(self, widget, data=None):
        self.style_context.remove_class('error')
        self.unselect()

    def on_activate(self, widget, data=None):
        self.unselect()

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.unselect()

    def on_eventbox_clicked(self, widget, event):
        self.unselect()

    def select(self):
        self.entry.select_region(0, -1)
        self.has_focus = True
        self.selected = False
        keyboard.show(self.entry)

    def unselect(self):
        self.entry.select_region(0, 0)
        self.get_toplevel().set_focus(None)
        self.has_focus = False

    def set_editable(self, editable):
        self.entry.set_sensitive(editable) # For rendering insensitive colors
        self.set_above_child(not editable) # Move EventBox to top so catches events


class G5xEntry(DroEntry):
    ''' G5x DRO entry class. Allows setting work offset by typing into DRO '''

    no_force_homing = ini_info.get_no_force_homing()

    def __init__(self, axis_letter, dro_type):
        DroEntry.__init__(self, axis_letter, dro_type)

        self.entry.set_width_chars(9)

        icon_name = "go-home-symbolic"
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, icon_name)

        self.entry.set_sensitive(True)
        self.entry.set_icon_activatable(1, True)
        self.entry.connect("icon-press", self.home)

        status.on_changed('joint.homing', self.on_homing)
        status.on_changed('joint.homed', self.on_homed)

        # Only indicate unhomed if require homing
        if not self.no_force_homing:
            self.style_context.add_class('unhomed')

        status.on_changed('stat.enabled', self.on_enebled_state_changed)

    def home(self, widget, icon, event):
        command.home_joint(self.joint_num)

    def on_homing(self, widget, joint, homing):
        if joint == self.joint_num:
            if homing == 1:
                self.style_context.remove_class('unhomed')
                self.style_context.add_class('homing')
            else:
                self.style_context.remove_class('homing')

    def on_homed(self, widget, joint, homed):
        if joint == self.joint_num:
            if homed == 1:
                self.style_context.remove_class('unhomed')
            else:
                self.style_context.add_class('unhomed')

    def on_enebled_state_changed(self, stat, enabled):
        self.set_editable(enabled)

    def on_activate(self, widget):
        '''Evaluate entry and set axis position to value.'''
        expr = self.entry.get_text().lower()
        val = entry_eval.eval(expr)
        print "DRO entry value: ", val
        if val is not None:
            command.set_work_coordinate(self.axis_letter, val)
            self.unselect()
        else:
            self.style_context.add_class('error')
            Gdk.beep()
