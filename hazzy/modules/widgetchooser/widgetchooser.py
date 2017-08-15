#!/usr/bin/env python

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

from constants import Paths

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

# Setup logging
from hazzy.utilities import logger
from hazzy.modules.gcodeview.gcodeview import GcodeViewWidget

log = logger.get("HAZZY.WIDGETCHOOSER")

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)


class WidgetChooser(Gtk.Box):
    def __init__(self, drop_area):
        Gtk.Box.__init__(self)

        self.drop_area = drop_area

        self.iconview = DragSourcePanel()
        self.pack_start(self.iconview, True, True, 0)

        self.add_text_targets()

        self.connect("delete-event", Gtk.main_quit)

        self.show_all()

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

        if True:  # info == TARGET_ENTRY_TEXT:
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

        self.set_size_request(100, 300)

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        dro_widget = GcodeViewWidget()

        label = data.get_text()

        wwindow = WidgetWindow(dro_widget, label)

        self.pack_start(wwindow, False, True, 0)


class WidgetWindow(Gtk.Box):
    def __init__(self, widget, label):
        Gtk.Box.__init__(self)

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(PYDIR, 'ui', 'widgetwindow.ui'))

        self.label = builder.get_object('label')
        self.box = builder.get_object('box')
        self.wwindow = builder.get_object('widgetwindow')

        self.label.set_text(label)
        self.box.add(widget)
        self.add(self.wwindow)

        self.show_all()


# Testing Only
def main():
    style_provider = Gtk.CssProvider()

    with open(os.path.join(Paths.STYLEDIR, "style.css"), 'rb') as css:
        css_data = css.read()

    style_provider.load_from_data(css_data)

    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    win = Gtk.Window()
    win.connect('destroy', Gtk.main_quit)

    box = Gtk.Box()

    drop_area = DropArea()

    chooser = WidgetChooser(drop_area)
    box.pack_start(chooser, True, True, 0)

    box.pack_start(drop_area, False, False, 0)

    win.add(box)
    win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
