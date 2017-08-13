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

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

UIDIR = os.path.join(PYDIR, 'ui')
STYLEDIR = os.path.join(HAZZYDIR, 'themes')

# Setup logging
import logger
log = logger.get("HAZZY.WIDGETCHOOSER")

from modules.gcodeview.gcodeview import GcodeViewWidget

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)


class WidgetChooser(Gtk.Box):

    def __init__(self, dest):
        Gtk.Box.__init__(self)

        self.dest = dest

        self.iconview = DragSourcePanel()
        self.pack_start(self.iconview, True, True, 0)

        self.add_image_targets()

        self.connect("delete-event", Gtk.main_quit)

        self.show_all()


    def add_image_targets(self, button=None):
        targets = Gtk.TargetList.new([])
        targets.add_image_targets(TARGET_ENTRY_PIXBUF, True)

        self.dest.drag_dest_set_target_list(targets)
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

        self.set_size_request(100, 300)

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.connect("drag-data-received", self.on_drag_data_received)


    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):

        dro_widget = GcodeViewWidget()
        self.pack_start(dro_widget, False, True, 10)


# Testing Only
def main():
    win = Gtk.Window()
    win.connect('destroy', Gtk.main_quit)

    box = Gtk.Box()

    droparea = DropArea()

    chooser = WidgetChooser(droparea)
    box.pack_start(chooser, True, True, 0)

    box.pack_start(droparea, False, False, 0)

    win.add(box)
    win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
