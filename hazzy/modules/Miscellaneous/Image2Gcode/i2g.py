#!/usr/bin/env python

#   Copyright (C) 2005 Chris Radek
#      <chris@timeguy.com>
#   Copyright (C) 2006 Jeff Epler
#      <jepler@unpy.net>
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

import sys
import os

import gettext

from PIL import Image

import numpy.core

plus_inf = numpy.core.Inf

from rs274.author import Gcode
import rs274.options

from math import *
import operator

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk
from gi.repository import Gst

from widget_factory import pref_widgets
from utilities import preferences as prefs
from utilities import logger

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

# Setup logging
log = logger.get(__name__)

Gst.init(None)


class I2GWidget(Gtk.Box):
    title = 'Image2Gcode'
    author = 'TurBoss'
    version = '0.1.0'
    date = '13/07/2018'
    description = 'converts images to gcode'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.config_stack = False

        self.set_size_request(320, 240)

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.unit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.unit_label = Gtk.Label(label="Unit system")

        self.unit_store = Gtk.ListStore(int, str, str)

        self.unit_store.append([0, "Inches", "G20"])
        self.unit_store.append([1, "Milimeters", "G21"])

        self.unit_combo = Gtk.ComboBox.new_with_model(self.unit_store)
        self.unit_combo.set_entry_text_column(1)

        self.unit_renderer_text = Gtk.CellRendererText()
        self.unit_combo.pack_start(self.unit_renderer_text, True)
        self.unit_combo.add_attribute(self.unit_renderer_text, "text", 1)

        self.unit_box.pack_start(self.unit_label, False, False, 0)
        self.unit_box.pack_start(self.unit_combo, False, False, 0)

        self.widget_box.pack_start(self.unit_box, False, False, 0)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)