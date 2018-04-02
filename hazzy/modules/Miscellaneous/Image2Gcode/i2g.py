#!/usr/bin/env python

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
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

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

        self.combobox_3_constructor(label_text="Unit System",
                                    list_options=[
                                        [0, "Inches", "G20"],
                                        [1, "Millimeters", "G21"]
                                    ])

        # Invert

        self.checkbox_constructor(label_text="Invert Color",
                                  default_value=False,
                                  callback=None)

        # Normalize

        self.checkbox_constructor(label_text="Normalize Image",
                                  default_value=False,
                                  callback=None)

        # Extend

        self.combobox_2_constructor(label_text="Extend",
                                    list_options=[
                                        [0, "None"],
                                        [1, "White"],
                                        [2, "Black"]
                                    ])

        # Tolerance

        self.entry_constructor(label_text="Tolerance (Unit)", default_value=0.0001)

        # Pixel size

        self.entry_constructor(label_text="Pixel Size (Units)", default_value=0.08)

        # Feed

        self.entry_constructor(label_text="Feed (Units per minute)", default_value=1000)

        # Plunge

        self.entry_constructor(label_text="Plunge (Units per minute)", default_value=300)

        # Spindle

        self.entry_constructor(label_text="Spindle (RPM)", default_value=24000)

        # Scan Pattern

        self.combobox_2_constructor(label_text="Scan Pattern",
                                    list_options=[
                                        [0, "Rows"],
                                        [1, "Columns"],
                                        [2, "Rows Columns"],
                                        [3, "Columns Rows"]
                                    ])

        # Path Direction

        self.combobox_2_constructor(label_text="Path Direction",
                                    list_options=[
                                        [0, "Positive"],
                                        [1, "Negative"],
                                        [2, "Alternating"],
                                        [3, "Up Milling"],
                                        [3, "Down Milling"]
                                    ])

        # Angle

        self.entry_constructor(label_text="Angle (Degrees)", default_value=90)

        # Depth

        self.entry_constructor(label_text="Depth (Unit)", default_value=2.0)

        # Step-over

        self.scale_constructor(label_text="Step-over (pixels)", lower_value=0, upper_value=100)

        # Tool diameter

        self.entry_constructor(label_text="Tool Diameter (Unit)", default_value=1.5)

        # Security

        self.entry_constructor(label_text="Security Height (Unit)", default_value=10.0)

        # Tool type

        self.combobox_2_constructor(label_text="Path Direction",
                                    list_options=[
                                        [0, "Ball End"],
                                        [1, "Flat End"],
                                        [2, "30 Degree"],
                                        [3, "45 Degree"],
                                        [4, "60 Degree"]
                                    ])

        # Lace Bounding

        self.combobox_2_constructor(label_text="Path Direction",
                                    list_options=[
                                        [0, "None"],
                                        [1, "Secondary"],
                                        [2, "Full"]
                                    ])

        # Contact Angle

        self.entry_constructor(label_text="Contact Angle (degrees)", default_value=45)

        # Roughing Offset

        self.entry_constructor(label_text="Roughing Offset (Units, 0 = none)", default_value=0.0)

        # Roughing Depth

        self.entry_constructor(label_text="Roughing Depth per pass (Units)", default_value=0.25)

        # Open Close Buttons

        self.open_button = Gtk.Button(label="Open")
        self.open_button.connect("clicked", self.on_open_file_clicked)

        self.close_button = Gtk.Button(label="Close")
        self.close_button.connect("clicked", self.on_close_file_clicked)

        self.button_box.pack_start(self.open_button, False, False, 0)
        self.button_box.pack_start(self.close_button, False, False, 0)
        self.options_box.pack_start(self.button_box, False, False, 0)

        # End

        self.main_box.pack_start(self.image_box, False, False, 0)
        self.main_box.pack_start(self.options_box, False, False, 0)

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

    def combobox_2_constructor(self,
                               label_text=None,
                               list_options=None):

        label = Gtk.Label(label=label_text)
        label.set_hexpand(True)

        store = Gtk.ListStore(int, str)

        for i in range(len(list_options)):
            store.append(list_options[i])

        combo = Gtk.ComboBox.new_with_model(store)
        combo.set_entry_text_column(1)

        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, "text", 1)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        box.pack_start(label, True, False, 0)
        box.pack_start(combo, True, True, 0)

        self.options_box.pack_start(box, False, False, 0)

    def combobox_3_constructor(self,
                               label_text=None,
                               list_options=None):

        label = Gtk.Label(label=label_text)
        label.set_hexpand(True)

        store = Gtk.ListStore(int, str, str)

        for i in range(len(list_options)):
            store.append(list_options[i])

        combo = Gtk.ComboBox.new_with_model(store)
        combo.set_entry_text_column(1)

        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, "text", 1)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        box.pack_start(label, True, False, 0)
        box.pack_start(combo, True, True, 0)

        self.options_box.pack_start(box, False, False, 0)

    def checkbox_constructor(self, label_text=None, default_value=False, callback=None):
        check_button = Gtk.CheckButton(label=label_text)

        if callback:
            check_button.connect("toggled", callback)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(check_button, True, False, 0)
        self.options_box.pack_start(box, False, False, 0)

    def entry_constructor(self, label_text, default_value):

        label = Gtk.Label(label=label_text)

        entry = Gtk.Entry()
        entry.set_text(str(default_value))

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        box.pack_start(label, True, False, 0)
        box.pack_start(entry, False, True, 0)

        self.options_box.pack_start(box, False, False, 0)

    def scale_constructor(self, label_text, lower_value=0, upper_value=100):

        label = Gtk.Label(label=label_text)

        adjustment = Gtk.Adjustment(value=0,
                                    lower=lower_value,
                                    upper=upper_value,
                                    step_increment=1,
                                    page_increment=10,
                                    page_size=0)

        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        box.pack_start(label, False, False, 0)
        box.pack_start(scale, False, False, 0)
        self.options_box.pack_start(box, False, False, 0)

    def on_open_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose an image",
            transient_for=self.get_parent(),
            modal=True,
            destroy_with_parent=True,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )

        self.add_filters(dialog)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.load_image(dialog.get_filename())

        elif response == Gtk.ResponseType.CANCEL:
            self.load_image(None)

        dialog.destroy()

        return True

    def on_close_file_clicked(self, widget):
        self.load_image(None)

        return True

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
