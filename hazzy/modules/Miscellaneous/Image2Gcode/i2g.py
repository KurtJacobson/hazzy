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

import os
import json

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GdkPixbuf

from image2gcode import Image2Gcode


# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

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

        self.widget_window = widget_window
        self.main_window = None  # Current Window can no be known until it is realized

        self.config_stack = False

        self.set_size_request(1024, 768)

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)

        # I2G module

        self.i2g = Image2Gcode()

        # Boxes

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Image Properties

        self.image_properties = None

        self.image_pixel_size = 0.0

        self.image_error_label = Gtk.Label()
        self.image_dpi_label = Gtk.Label()
        self.image_depth_label = Gtk.Label()
        self.image_pixels_label = Gtk.Label()
        self.image_pixel_size_label = Gtk.Label()
        self.image_size_label = Gtk.Label()

        self.properties_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dpi_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        depth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        pixels_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        pixel_size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        image_size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        dpi_box.pack_start(Gtk.Label(label="dpi:"), False, False, 0)
        dpi_box.pack_start(self.image_dpi_label, False, False, 0)

        depth_box.pack_start(Gtk.Label(label="bit depth:"), False, False, 0)
        depth_box.pack_start(self.image_depth_label, False, False, 0)

        pixels_box.pack_start(Gtk.Label(label="pixels:"), False, False, 0)
        pixels_box.pack_start(self.image_pixels_label, False, False, 0)

        pixel_size_box.pack_start(Gtk.Label(label="pixel size:"), False, False, 0)
        pixel_size_box.pack_start(self.image_pixel_size_label, False, False, 0)

        image_size_box.pack_start(Gtk.Label(label="image size:"), False, False, 0)
        image_size_box.pack_start(self.image_size_label, False, False, 0)

        self.properties_box.pack_start(self.image_error_label, False, False, 0)
        self.properties_box.pack_start(dpi_box, False, False, 0)
        self.properties_box.pack_start(depth_box, False, False, 0)
        self.properties_box.pack_start(pixels_box, False, False, 0)
        self.properties_box.pack_start(pixel_size_box, False, False, 0)
        self.properties_box.pack_start(image_size_box, False, False, 0)

        # Image

        self.image_view = None

        self.image_file = None

        self.image = Gtk.Image()

        self.load_image(self.image_file)

        self.image_box.set_size_request(320, 320)

        self.image_box.set_hexpand(True)
        self.image_box.set_vexpand(True)

        # Settings

        self.settings = None

        # Unit System

        self.unit_system_combo = self.combobox_3_constructor(label_text="Unit System",
                                                             list_options=[
                                                                 [0, "Inches", "G20"],
                                                                 [1, "Millimeters", "G21"]
                                                             ])

        # Invert BW

        self.invert_bw_check = self.checkbox_constructor(label_text="Invert BW",
                                                         default_value=False)

        # Normalize

        self.normalize_image_check = self.checkbox_constructor(label_text="Normalize Image",
                                                               default_value=False)

        # Extend

        self.extend_combo = self.combobox_2_constructor(label_text="Extend",
                                                        list_options=[
                                                            [0, "None"],
                                                            [1, "White"],
                                                            [2, "Black"]
                                                        ])

        # Tolerance

        self.tolerance_entry = self.entry_constructor(label_text="Tolerance (Unit)", default_value=0.0001)

        # Feed

        self.feed_entry = self.entry_constructor(label_text="Feed (Units per minute)", default_value=1000)

        # Plunge

        self.plunge_entry = self.entry_constructor(label_text="Plunge (Units per minute)", default_value=300)

        # Spindle

        self.spindle_entry = self.entry_constructor(label_text="Spindle (RPM)", default_value=24000)

        # Scan Pattern

        self.scan_pattern_combo = self.combobox_2_constructor(label_text="Scan Pattern",
                                                              list_options=[
                                                                  [0, "Rows"],
                                                                  [1, "Columns"],
                                                                  [2, "Rows Columns"],
                                                                  [3, "Columns Rows"]
                                                              ])

        # Path Direction

        self.path_direction_combo = self.combobox_2_constructor(label_text="Path Direction",
                                                                list_options=[
                                                                    [0, "Positive"],
                                                                    [1, "Negative"],
                                                                    [2, "Alternating"],
                                                                    [3, "Up Milling"],
                                                                    [3, "Down Milling"]
                                                                ])

        # Angle

        self.angle_entry = self.entry_constructor(label_text="Angle (Degrees)", default_value=90)

        # Depth

        self.depth_entry = self.entry_constructor(label_text="Depth (Unit)", default_value=2.0)

        # Step-over

        self.step_over_scale = self.scale_constructor(label_text="Step-over (pixels)", lower_value=0, upper_value=100)

        # Tool diameter

        self.tool_diameter_entry = self.entry_constructor(label_text="Tool Diameter (Unit)", default_value=1.5)

        # Security Height

        self.security_height_entry = self.entry_constructor(label_text="Security Height (Unit)", default_value=10.0)

        # Tool type

        self.tool_type_combo = self.combobox_2_constructor(label_text="Tool type",
                                                           list_options=[
                                                               [0, "Ball End"],
                                                               [1, "Flat End"],
                                                               [2, "30 Degree"],
                                                               [3, "45 Degree"],
                                                               [4, "60 Degree"]
                                                           ])

        # Lace Bounding

        self.lace_bounding_combo = self.combobox_2_constructor(label_text="Lace Bounding",
                                                               list_options=[
                                                                   [0, "None"],
                                                                   [1, "Secondary"],
                                                                   [2, "Full"]
                                                               ])

        # Contact Angle

        self.contacnt_angle_entry = self.entry_constructor(label_text="Contact Angle (degrees)", default_value=45)

        # Rough Offset

        self.rough_offset_entry = self.entry_constructor(label_text="Rough Offset (Units, 0 = none)", default_value=0.0)

        # Rough Depth

        self.rough_depth_entry = self.entry_constructor(label_text="Rough Depth per pass (Units)", default_value=0.25)

        # Buttons

        self.open_button = Gtk.Button(label="Open File")
        self.open_button.connect("clicked", self.on_open_file_clicked)

        self.close_button = Gtk.Button(label="Close File")
        self.close_button.connect("clicked", self.on_close_file_clicked)

        self.load_button = Gtk.Button(label="Load Preset")
        self.load_button.connect("clicked", self.on_load_preset_clicked)

        self.save_button = Gtk.Button(label="Save Preset")
        self.save_button.connect("clicked", self.on_save_preset_clicked)

        self.execute_button = Gtk.Button(label="Execute Program")
        self.execute_button.set_sensitive(False)
        self.execute_button.connect("clicked", self.on_execute_program_clicked)

        # pack all

        self.button_box.pack_start(self.open_button, True, True, 0)
        self.button_box.pack_start(self.close_button, True, True, 0)
        self.button_box.pack_start(self.save_button, True, True, 0)
        self.button_box.pack_start(self.load_button, True, True, 0)
        self.button_box.pack_start(self.execute_button, True, True, 0)

        self.main_box.pack_start(self.image_box, False, False, 0)
        self.main_box.pack_start(self.options_box, False, False, 0)

        self.widget_box.pack_start(self.main_box, False, False, 0)
        self.widget_box.pack_start(self.button_box, True, True, 0)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)

        self.load_settings(os.path.join(PYDIR, "default.i2g"))

        # Need current window to pass to file dialog, but can't
        # find until the window is realized.
        self.connect('realize', self.on_realized)

    def on_realized(self, widget):
        if self.widget_window.get_parent():
            self.main_window = self.widget_window.get_parent().get_toplevel()

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

        return combo

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

        return combo

    def checkbox_constructor(self, label_text=None, default_value=False):
        check_button = Gtk.CheckButton(label=label_text)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(check_button, True, False, 0)
        self.options_box.pack_start(box, False, False, 0)

        return check_button

    def entry_constructor(self, label_text, default_value):

        label = Gtk.Label(label=label_text)

        entry = Gtk.Entry()
        entry.set_text(str(default_value))

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        box.pack_start(label, True, False, 0)
        box.pack_start(entry, False, True, 0)

        self.options_box.pack_start(box, False, False, 0)

        return entry

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

        box.pack_start(label, True, False, 0)
        box.pack_start(scale, True, True, 0)
        self.options_box.pack_start(box, False, False, 0)

        return scale

    def on_open_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Choose an image",
            transient_for=self.main_window,
            modal=True,
            destroy_with_parent=True,
            action=Gtk.FileChooserAction.OPEN
        )

        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.add_image_filters(dialog)

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

    def on_save_preset_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Save settings preset",
            transient_for=self.main_window,
            modal=True,
            destroy_with_parent=True,
            action=Gtk.FileChooserAction.SAVE
        )

        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.add_i2g_filters(dialog)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.save_settings(dialog.get_filename())

        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

        return True

    def on_load_preset_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Load settings preset",
            transient_for=self.main_window,
            modal=True,
            destroy_with_parent=True,
            action=Gtk.FileChooserAction.SAVE
        )

        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.add_i2g_filters(dialog)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.load_settings(dialog.get_filename())

        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

        return True

    def on_execute_program_clicked(self, widget):

        dialog = Gtk.FileChooserDialog(
            title="Save GCODE",
            transient_for=self.main_window,
            modal=True,
            destroy_with_parent=True,
            action=Gtk.FileChooserAction.SAVE
        )

        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.add_ngc_filters(dialog)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.i2g.set_output(dialog.get_filename())

            self.get_settings()

            self.i2g.execute(self.settings)

        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

        return True

    def get_settings(self):

        self.settings = {
            "unit_system": self.unit_system_combo.get_active(),
            "invert_bw": self.invert_bw_check.get_active(),
            "normalize_image": self.normalize_image_check.get_active(),
            "extend": self.extend_combo.get_active(),
            "tolerance": float(self.tolerance_entry.get_text()),
            "feed": float(self.feed_entry.get_text()),
            "plunge": float(self.plunge_entry.get_text()),
            "spindle": float(self.spindle_entry.get_text()),
            "scan_pattern": self.scan_pattern_combo.get_active(),
            "path_direction": self.path_direction_combo.get_active(),
            "angle": float(self.angle_entry.get_text()),
            "depth": float(self.depth_entry.get_text()),
            "step_over": float(self.step_over_scale.get_value()),
            "tool_diameter": float(self.tool_diameter_entry.get_text()),
            "security_height": float(self.security_height_entry.get_text()),
            "tool_type": self.tool_type_combo.get_active(),
            "lace_bounding": self.lace_bounding_combo.get_active(),
            "contacnt_angle": self.contacnt_angle_entry.get_text(),
            "rough_offset": float(self.rough_offset_entry.get_text()),
            "rough_depth": float(self.rough_depth_entry.get_text()),
            "pixel_size": self.image_pixel_size
        }

    def set_settings(self):

        self.unit_system_combo.set_active(self.settings["unit_system"])
        self.invert_bw_check.set_active(self.settings["invert_bw"])
        self.normalize_image_check.set_active(self.settings["normalize_image"])
        self.extend_combo.set_active(self.settings["extend"])
        self.tolerance_entry.set_text(self.settings["tolerance"])
        self.feed_entry.set_text(self.settings["feed"])
        self.plunge_entry.set_text(self.settings["plunge"])
        self.spindle_entry.set_text(self.settings["spindle"])
        self.scan_pattern_combo.set_active(self.settings["scan_pattern"])
        self.path_direction_combo.set_active(self.settings["path_direction"])
        self.angle_entry.set_text(self.settings["angle"])
        self.depth_entry.set_text(self.settings["depth"])
        self.step_over_scale.set_value(self.settings["step_over"])
        self.tool_diameter_entry.set_text(self.settings["tool_diameter"])
        self.security_height_entry.set_text(self.settings["security_height"])
        self.tool_type_combo.set_active(self.settings["tool_type"])
        self.lace_bounding_combo.set_active(self.settings["lace_bounding"])
        self.contacnt_angle_entry.set_text(self.settings["contacnt_angle"])
        self.rough_offset_entry.set_text(self.settings["rough_offset"])
        self.rough_depth_entry.set_text(self.settings["rough_depth"])

    def save_settings(self, file_name):
        self.get_settings()
        with open(file_name, "wb") as i2g_file:
            i2g_file.write(json.dumps(self.settings, indent=4, sort_keys=True))

    def load_settings(self, file_name):
        with open(file_name, "rb") as i2g_file:
            self.settings = json.load(i2g_file)
            self.set_settings()

    def load_image(self, image_file):

        image_loaded = False

        self.image_file = image_file
        self.image_properties = None

        self.image_box.remove(self.image)
        self.image_box.remove(self.properties_box)
        if image_file:
            self.image_properties = self.i2g.load_file(file_name=image_file)
            image_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=image_file,
                                                                   width=600,
                                                                   height=400,
                                                                   preserve_aspect_ratio=True)

            self.image = Gtk.Image.new_from_pixbuf(image_pixbuf)

            image_loaded = True

            if self.image_properties:

                dpi = self.image_properties["properties"]["dpi"][0]

                self.get_settings()
                if self.settings["unit_system"]:  # MM
                    pixel_size = 25.4 / float(dpi)
                    print("pixel size mm = {}".format(pixel_size))
                else:  # INCH
                    pixel_size = 0.1 / float(dpi)
                    print("pixel size inchs = {}".format(pixel_size))

                self.image_pixel_size = pixel_size

                self.image_properties["properties"]["size"][0] = pixel_size * self.image_properties["properties"]["pixels"][
                    0]
                self.image_properties["properties"]["size"][1] = pixel_size * self.image_properties["properties"]["pixels"][
                    1]
                self.draw_image_properties()

                self.execute_button.set_sensitive(True)
            else:
                self.image = Gtk.Image.new_from_stock(Gtk.STOCK_MISSING_IMAGE, Gtk.IconSize.BUTTON)
                self.draw_image_properties()

                self.execute_button.set_sensitive(False)

        else:
            self.image = Gtk.Image.new_from_stock(Gtk.STOCK_MISSING_IMAGE, Gtk.IconSize.BUTTON)
            self.draw_image_properties()

        self.image.show()
        self.image_box.pack_start(self.image, True, False, 0)
        self.image_box.pack_start(self.properties_box, False, False, 0)

        return image_loaded

    def draw_image_properties(self):

        if self.image_properties:
            self.image_error_label.set_text("")
            self.image_dpi_label.set_text("\t{0[0]}:{0[1]}".format(self.image_properties["properties"]["dpi"]))
            self.image_depth_label.set_text("\t{0}".format(self.image_properties["properties"]["depth"]))
            self.image_pixels_label.set_text("\t{0[0]} x {0[1]}".format(self.image_properties["properties"]["pixels"]))
            self.image_pixel_size_label.set_text("\t{0}".format(self.settings["pixel_size"]))
            self.image_size_label.set_text(
                "\t{0[0]:.3f} x {0[1]:.3f}".format(self.image_properties["properties"]["size"]))
        else:
            self.image_error_label.set_text("NOT VALID IMAGE LOADED")
            self.image_dpi_label.set_text("")
            self.image_depth_label.set_text("")
            self.image_pixels_label.set_text("")
            self.image_pixel_size_label.set_text("")
            self.image_size_label.set_text("")

    @staticmethod
    def add_image_filters(dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Image files")
        filter_text.add_mime_type("image/*")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    @staticmethod
    def add_i2g_filters(dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("I2G files")
        filter_text.add_pattern("*.i2g")
        dialog.add_filter(filter_text)

    @staticmethod
    def add_ngc_filters(dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("LinuxCNC Gcode")
        filter_text.add_pattern("*.ngc")
        dialog.add_filter(filter_text)


def main():
    window = Gtk.Window()

    w_box = I2GWidget(window)

    window.add(w_box)

    window.show_all()

    window.connect("destroy", Gtk.main_quit)

    Gtk.main()


if __name__ == "__main__":
    main()
