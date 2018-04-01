#!/usr/bin/env python

#   Copyright (C) 2005 Chris Radek
#      <chris@timeguy.com>
#   Copyright (C) 2006 Jeff Epler
#      <jepler@unpy.net>
#   Copyright (C) 2018 TurBoss
#      <j.l.toledano.l@gmail.com>
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

"""
from rs274.author import Gcode
import rs274.options

from math import *
import operator
"""

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

"""
from widget_factory import pref_widgets
from utilities import preferences as prefs
from utilities import logger
"""


# Setup paths
# PYDIR = os.path.abspath(os.path.dirname(__file__))

# Setup logging
# log = logger.get(__name__)


class I2GWidget(Gtk.Box):
    title = 'Image 2 g-code'
    author = 'TurBoss'
    version = '0.1.0'
    date = '13/07/2018'
    description = 'converts images to gcode'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        # Create buffer
        self.double_buffer = None

        self.config_stack = False

        self.set_size_request(600, 800)

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)

        # Boxes

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.option_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.unit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.invert_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.normalize_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.extend_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.tolerance_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.pixel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.feed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.plunge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.spindle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.pattern_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.direction_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.angle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.depth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.step_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.tool_dia_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.security_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.tool_type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.lace_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.contact_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.roughing_offset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.roughing_depth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Image

        self.image_view = None

        self.image_file = None

        self.image = Gtk.Image()

        self.load_image(self.image_file)

        self.image_box.set_size_request(320, 320)

        self.image_box.set_hexpand(True)
        self.image_box.set_vexpand(True)

        # Unit

        self.unit_label = Gtk.Label(label="Unit System")

        self.unit_box.pack_start(self.unit_label, False, False, 0)

        self.unit_store = Gtk.ListStore(int, str, str)

        self.unit_store.append([0, "Inches", "G20"])
        self.unit_store.append([1, "Millimeters", "G21"])

        self.unit_combo = Gtk.ComboBox.new_with_model(self.unit_store)
        self.unit_combo.set_entry_text_column(1)

        self.unit_renderer_text = Gtk.CellRendererText()
        self.unit_combo.pack_start(self.unit_renderer_text, True)
        self.unit_combo.add_attribute(self.unit_renderer_text, "text", 1)

        self.unit_box.pack_start(self.unit_combo, False, False, 0)
        self.option_box.pack_start(self.unit_box, False, False, 0)

        # Invert

        self.invert = Gtk.CheckButton("Invert Color")
        # self.invert_image.connect("toggled", self.on_invert_toggled)

        self.invert_box.pack_start(self.invert, False, False, 0)
        self.option_box.pack_start(self.invert_box, False, False, 0)

        # Normalize

        self.normalize = Gtk.CheckButton("Normalize Image")
        # self.normalize.connect("toggled", self.on_normalize_toggled)

        self.normalize_box.pack_start(self.normalize, False, False, 0)
        self.option_box.pack_start(self.normalize_box, False, False, 0)

        # Extend

        self.extend_label = Gtk.Label(label="Extend")

        self.extend_box.pack_start(self.extend_label, False, False, 0)

        self.extend_store = Gtk.ListStore(int, str)

        self.extend_store.append([0, "None"])
        self.extend_store.append([1, "White"])
        self.extend_store.append([2, "Black"])

        self.extend_combo = Gtk.ComboBox.new_with_model(self.extend_store)
        self.extend_combo.set_entry_text_column(1)

        self.extend_renderer_text = Gtk.CellRendererText()
        self.extend_combo.pack_start(self.extend_renderer_text, True)
        self.extend_combo.add_attribute(self.extend_renderer_text, "text", 1)

        self.extend_box.pack_start(self.extend_combo, False, False, 0)
        self.option_box.pack_start(self.extend_box, False, False, 0)

        # Tolerance

        self.tolerance_label = Gtk.Label(label="Tolerance (Unit)")

        self.tolerance_box.pack_start(self.tolerance_label, False, False, 0)

        self.tolerance_entry = Gtk.Entry()
        self.tolerance_entry.set_text("0.001")

        self.tolerance_box.pack_start(self.tolerance_entry, False, False, 0)
        self.option_box.pack_start(self.tolerance_box, False, False, 0)

        # Pixel size

        self.pixel_label = Gtk.Label(label="Pixel Size (Units)")

        self.pixel_box.pack_start(self.pixel_label, False, False, 0)

        self.pixel_entry = Gtk.Entry()
        self.pixel_entry.set_text("0.08")

        self.pixel_box.pack_start(self.pixel_entry, False, False, 0)
        self.option_box.pack_start(self.pixel_box, False, False, 0)

        # Feed

        self.feed_label = Gtk.Label(label="Feed (Units per minute)")

        self.feed_box.pack_start(self.feed_label, False, False, 0)

        self.feed_entry = Gtk.Entry()
        self.feed_entry.set_text("1000")

        self.feed_box.pack_start(self.feed_entry, False, False, 0)
        self.option_box.pack_start(self.feed_box, False, False, 0)

        # Plunge

        self.plunge_label = Gtk.Label(label="Plunge (Units per minute)")

        self.plunge_box.pack_start(self.plunge_label, False, False, 0)

        self.plunge_entry = Gtk.Entry()
        self.plunge_entry.set_text("300")

        self.plunge_box.pack_start(self.plunge_entry, False, False, 0)
        self.option_box.pack_start(self.plunge_box, False, False, 0)

        # Spindle

        self.spindle_label = Gtk.Label(label="Spindle (RPM)")

        self.spindle_box.pack_start(self.spindle_label, False, False, 0)

        self.spindle_entry = Gtk.Entry()
        self.spindle_entry.set_text("10000")

        self.spindle_box.pack_start(self.spindle_entry, False, False, 0)
        self.option_box.pack_start(self.spindle_box, False, False, 0)

        # Scan Pattern

        self.pattern_label = Gtk.Label(label="Scan Pattern")

        self.pattern_box.pack_start(self.pattern_label, False, False, 0)

        self.pattern_store = Gtk.ListStore(int, str)

        self.pattern_store.append([0, "Rows"])
        self.pattern_store.append([1, "Cols"])
        self.pattern_store.append([2, "Test"])

        self.pattern_combo = Gtk.ComboBox.new_with_model(self.pattern_store)
        self.pattern_combo.set_entry_text_column(1)

        self.pattern_renderer_text = Gtk.CellRendererText()
        self.pattern_combo.pack_start(self.pattern_renderer_text, True)
        self.pattern_combo.add_attribute(self.pattern_renderer_text, "text", 1)

        self.pattern_box.pack_start(self.pattern_combo, False, False, 0)
        self.option_box.pack_start(self.pattern_box, False, False, 0)

        # Scan Direction

        self.direction_label = Gtk.Label(label="Scan Direction")

        self.direction_box.pack_start(self.direction_label, False, False, 0)

        self.direction_store = Gtk.ListStore(int, str)

        self.direction_store.append([0, "Positive"])
        self.direction_store.append([1, "Negative"])
        self.direction_store.append([2, "Test"])

        self.direction_combo = Gtk.ComboBox.new_with_model(self.direction_store)
        self.direction_combo.set_entry_text_column(1)

        self.direction_renderer_text = Gtk.CellRendererText()
        self.direction_combo.pack_start(self.direction_renderer_text, True)
        self.direction_combo.add_attribute(self.direction_renderer_text, "text", 1)

        self.direction_box.pack_start(self.direction_combo, False, False, 0)
        self.option_box.pack_start(self.direction_box, False, False, 0)

        # Angle

        self.angle_label = Gtk.Label(label="Angle (Degrees)")

        self.angle_box.pack_start(self.angle_label, False, False, 0)

        self.angle_entry = Gtk.Entry()
        self.angle_entry.set_text("90")

        self.angle_box.pack_start(self.angle_entry, False, False, 0)
        self.option_box.pack_start(self.angle_box, False, False, 0)

        # Depth

        self.depth_label = Gtk.Label(label="Depth (Unit)")

        self.depth_box.pack_start(self.depth_label, False, False, 0)

        self.depth_entry = Gtk.Entry()
        self.depth_entry.set_text("90")

        self.depth_box.pack_start(self.depth_entry, False, False, 0)
        self.option_box.pack_start(self.depth_box, False, False, 0)

        # Step-over

        self.step_label = Gtk.Label(label="Step-over (pixels)")

        self.step_box.pack_start(self.step_label, False, False, 0)

        self.step_adjustment = Gtk.Adjustment(0, 0, 100, 1, 10, 0)
        self.step_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.step_adjustment)

        self.step_box.pack_start(self.step_scale, False, False, 0)
        self.option_box.pack_start(self.step_box, False, False, 0)

        # Tool diameter

        self.tool_dia_label = Gtk.Label(label="Tool Diameter (Unit)")

        self.tool_dia_box.pack_start(self.tool_dia_label, False, False, 0)

        self.tool_dia_entry = Gtk.Entry()
        self.tool_dia_entry.set_text("1.5")

        self.tool_dia_box.pack_start(self.tool_dia_entry, False, False, 0)
        self.option_box.pack_start(self.tool_dia_box, False, False, 0)

        # Security

        self.security_label = Gtk.Label(label="Security Height (Unit)")

        self.security_box.pack_start(self.security_label, False, False, 0)

        self.security_entry = Gtk.Entry()
        self.security_entry.set_text("5")

        self.security_box.pack_start(self.security_entry, False, False, 0)
        self.option_box.pack_start(self.security_box, False, False, 0)

        # Tool type

        self.tool_type_label = Gtk.Label(label="Tool Type")

        self.tool_type_box.pack_start(self.tool_type_label, False, False, 0)

        self.tool_type_store = Gtk.ListStore(int, str)

        self.tool_type_store.append([0, "Ball"])
        self.tool_type_store.append([1, "Flat"])
        self.tool_type_store.append([2, "V-Carve"])

        self.tool_type_combo = Gtk.ComboBox.new_with_model(self.direction_store)
        self.tool_type_combo.set_entry_text_column(1)

        self.tool_type_renderer_text = Gtk.CellRendererText()
        self.tool_type_combo.pack_start(self.tool_type_renderer_text, True)
        self.tool_type_combo.add_attribute(self.tool_type_renderer_text, "text", 1)

        self.tool_type_box.pack_start(self.tool_type_combo, False, False, 0)
        self.option_box.pack_start(self.tool_type_box, False, False, 0)

        # Lace Bounding

        self.lace_label = Gtk.Label(label="Lace Bounding")

        self.lace_box.pack_start(self.lace_label, False, False, 0)

        self.lace_store = Gtk.ListStore(int, str)

        self.lace_store.append([0, "Ball"])
        self.lace_store.append([1, "Flat"])
        self.lace_store.append([2, "V-Carve"])

        self.lace_combo = Gtk.ComboBox.new_with_model(self.direction_store)
        self.lace_combo.set_entry_text_column(1)

        self.lace_renderer_text = Gtk.CellRendererText()
        self.lace_combo.pack_start(self.lace_renderer_text, True)
        self.lace_combo.add_attribute(self.lace_renderer_text, "text", 1)

        self.lace_box.pack_start(self.lace_combo, False, False, 0)
        self.option_box.pack_start(self.lace_box, False, False, 0)

        # Contact Angle

        self.contact_label = Gtk.Label(label="Contact Angle (degrees)")

        self.contact_box.pack_start(self.contact_label, False, False, 0)

        self.contact_entry = Gtk.Entry()
        self.contact_entry.set_text("45")

        self.contact_box.pack_start(self.contact_entry, False, False, 0)
        self.option_box.pack_start(self.contact_box, False, False, 0)

        # Roughing Offset

        self.roughing_offset_label = Gtk.Label(label="Roughing Offset (Units, 0 = none)")

        self.roughing_offset_box.pack_start(self.roughing_offset_label, False, False, 0)

        self.roughing_offset_entry = Gtk.Entry()
        self.roughing_offset_entry.set_text("0.00")

        self.roughing_offset_box.pack_start(self.roughing_offset_entry, False, False, 0)
        self.option_box.pack_start(self.roughing_offset_box, False, False, 0)

        # Roughing Depth

        self.roughing_depth_label = Gtk.Label(label="Roughing Depth per pass (Units)")

        self.roughing_depth_box.pack_start(self.roughing_depth_label, False, False, 0)

        self.roughing_depth_entry = Gtk.Entry()
        self.roughing_depth_entry.set_text("0.25")

        self.roughing_depth_box.pack_start(self.roughing_depth_entry, False, False, 0)
        self.option_box.pack_start(self.roughing_depth_box, False, False, 0)

        # Open Close Buttons

        self.open_button = Gtk.Button(label="Open")
        self.open_button.connect("clicked", self.on_open_file_clicked)

        self.close_button = Gtk.Button(label="Close")
        self.close_button.connect("clicked", self.on_close_file_clicked)

        self.button_box.pack_start(self.open_button, False, False, 0)
        self.button_box.pack_start(self.close_button, False, False, 0)
        self.option_box.pack_start(self.button_box, False, False, 0)

        # End

        self.main_box.pack_start(self.image_box, False, False, 0)
        self.main_box.pack_start(self.option_box, False, False, 0)

        self.widget_box.pack_start(self.main_box, False, False, 0)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)

    def load_image(self, image_file):
        self.image_file = image_file
        print(image_file)

        self.image_box.remove(self.image)

        if image_file:
            self.image = Gtk.Image.new_from_file(image_file)
        else:
            self.image = Gtk.Image.new_from_stock(Gtk.STOCK_MISSING_IMAGE, Gtk.IconSize.BUTTON)

        self.image_box.pack_start(self.image, False, False, 0)
        self.image.show()

    def on_open_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please choose an image",
            self.get_parent(),
            Gtk.FileChooserAction.OPEN, (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK)
        )

        self.add_filters(dialog)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("OK")
            self.load_image(dialog.get_filename())

        elif response == Gtk.ResponseType.CANCEL:
            print("CANCEL")
            self.load_image(None)

        dialog.destroy()

    def on_close_file_clicked(self, widget):
        self.load_image(None)

    @staticmethod
    def add_filters(dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Image files")
        filter_text.add_mime_type("image/*")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)


def main():
    window = Gtk.Window()
    w_box = I2GWidget(window)
    window.add(w_box)
    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
