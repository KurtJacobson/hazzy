#!/usr/bin/env python

#   An attempt at a new UI for LinuxCNC that can be used
#   on a touch screen without any lost of functionality.
#   The code is written in python and glade and is almost a
#   complete rewrite, but was influenced mainly by Gmoccapy
#   and Touchy, with some code adapted from the HAL VCP widgets.

#   Copyright (c) 2017 Kurt Jacobson
#       <kurtcjacobson@gmail.com>
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
from gi.repository import GdkPixbuf

# Setup paths to files
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
INIFILE = sys.argv[2]  # Path to .ini file
CONFIGDIR = os.path.dirname(INIFILE)  # Path to config dir
TCLPATH = os.environ['LINUXCNC_TCL_DIR']

# Path to TCL for external programs eg. halshow
if sys.argv[1] != "-ini":
    raise SystemExit("-ini must be first argument")

# Get actual paths so we can run from any location
HAZZYDIR = os.path.dirname(os.path.realpath(__file__))
UIDIR = os.path.join(HAZZYDIR, 'ui')
MODULEDIR = os.path.join(HAZZYDIR, 'modules')
MAINDIR = os.path.dirname(HAZZYDIR)
STYLEDIR = os.path.join(HAZZYDIR, 'themes')

# Set system path so we can find our own modules
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

# Import our own modules
from utilities import logger
from modules.dro.dro import Dro
from modules.gcodeview.gcodeview import GcodeViewWidget

log = logger.get('HAZZY')

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)


class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Hazzy")

        gladefile = os.path.join(UIDIR, 'hazzy_3.ui')

        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)

        self.iconview = DragSourcePanel()
        self.drop_area = DropArea()

        self.panel = self.builder.get_object('panel')
        self.titlebar = self.builder.get_object('titlebar')
        self.revealer_button = self.builder.get_object('revealer')
        self.widget_chooser = self.builder.get_object('widget_chooser')

        self.set_titlebar(self.titlebar)
        self.add(self.panel)

        self.widget_chooser.add(self.iconview)
        self.panel.pack_start(self.drop_area, True, True, 0)

        self.add_image_targets()

        self.revealer_button.connect("clicked", self.on_reveal_clicked)
        self.connect("delete-event", Gtk.main_quit)

    def add_image_targets(self, button=None):
        targets = Gtk.TargetList.new([])
        targets.add_image_targets(TARGET_ENTRY_PIXBUF, True)

        self.drop_area.drag_dest_set_target_list(targets)
        self.iconview.drag_source_set_target_list(targets)

    def add_text_targets(self, button=None):
        self.drop_area.drag_dest_set_target_list(None)
        self.iconview.drag_source_set_target_list(None)

        self.drop_area.drag_dest_add_text_targets()
        self.iconview.drag_source_add_text_targets()

    def on_reveal_clicked(self, button):
        reveal = self.widget_chooser.get_reveal_child()
        self.widget_chooser.set_reveal_child(not reveal)


class DragSourcePanel(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        self.set_text_column(COLUMN_TEXT)
        self.set_pixbuf_column(COLUMN_PIXBUF)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        self.set_model(model)

        self.add_item("Dro", "image-missing")
        self.add_item("Code View", "help-about")
        self.add_item("Code Editor", "edit-copy")

        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)

        self.connect("drag-data-get", self.on_drag_data_get)

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)

        if info == TARGET_ENTRY_TEXT:
            text = self.get_model().get_value(selected_iter, COLUMN_TEXT)
            data.set_text(text, -1)
        elif info == TARGET_ENTRY_PIXBUF:
            pixbuf = self.get_model().get_value(selected_iter, COLUMN_PIXBUF)
            data.set_pixbuf(pixbuf)

    def add_item(self, text, icon_name):
        pixbuf = Gtk.IconTheme.get_default().load_icon(icon_name, 16, 0)
        self.get_model().append([text, pixbuf])


class DropArea(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)

        self.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):

        dro_widget = Dro()
        gcv_widget = GcodeViewWidget()

        self.add(dro_widget)
        self.add(gcv_widget)

def main():
    style_provider = Gtk.CssProvider()

    with open(os.path.join(STYLEDIR, "style.css"), 'rb') as css:
        css_data = css.read()

    style_provider.load_from_data(css_data)

    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    win = HazzyWindow()
    win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
