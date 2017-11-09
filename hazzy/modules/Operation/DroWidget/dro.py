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
#   Multi function DRO. Displays REL, ABS and DTG positions
#   for all active axes and allows homing/unhoming of each axis.
#   The current G5x position can be set by typing into the REL DRO.

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

from utilities import status
from utilities import machine_info
from widget_factory.dros import DroType, DroEntry, G5xEntry

class Dro(Gtk.Grid):

    title = 'DRO'
    author = 'Kurt Jacobson'
    version = '0.1.0'
    date = '9/12/2017'
    description = '''DRO:
    Multi function DRO. Displays REL, ABS and DTG positions
    for all active axes and allows homing/unhoming of each axis.
    The current G5x position can be set by typing into the REL DRO.
    '''

    def __init__(self, widget_window):
        Gtk.Grid.__init__(self)

        self.widget_window = widget_window

        self.set_size_request(60, 60)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.set_row_spacing(5)
        self.set_column_spacing(5)

        axes = machine_info.axis_letter_list

        status.on_changed('stat.g5x_index', self.on_g5x_state_changed)

        # Column labels
        self.g5x_label = Gtk.Label('G5x')
        self.attach(self.g5x_label, 2, 0, 1, 1)

        self.abs_label = Gtk.Label('ABS')
        self.attach(self.abs_label, 3, 0, 1, 1)

        self.dtg_label = Gtk.Label('DTG')
        self.attach(self.dtg_label, 4, 0, 1, 1)

        count = 1
        for axis in axes:
            # Axis Lables
            label = Gtk.Label(axis.upper())
            self.attach(label, 1, count, 1, 1)

            # G5x DRO
            entry = G5xEntry(axis, DroType.REL)
            self.attach(entry, 2, count, 1, 1)

            # ABS DRO
            label = DroEntry(axis, DroType.ABS)
            self.attach(label, 3, count, 1, 1)

            # DTG DRO
            label = DroEntry(axis, DroType.DTG)
            self.attach(label, 4, count, 1, 1)

            count += 1

    def on_g5x_state_changed(self, stat, g5x_index):
        work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
        self.g5x_label.set_text(work_cords[g5x_index])
