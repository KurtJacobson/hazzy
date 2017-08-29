#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from hazzy.widgets.widget_manager import WidgetManager

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
WIDGET_DIR = os.path.join(HAZZYDIR, 'hazzy/modules')


class ScreenChooser(Gtk.Revealer):
    def __init__(self):
        Gtk.Revealer.__init__(self)

        self.set_reveal_child(False)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        view = WidgetView()
        self.add(view)

    def get_visible(self):
        return self.get_reveal_child()

    def set_visible(self, visible):
        self.set_reveal_child(visible)


class ScreenView(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        # Add style class
        context = self.get_style_context()
        context.add_class("widget_chooser")

        self.set_text_column(0)
        self.set_pixbuf_column(1)

        self.set_columns(3)
        self.set_item_width(120)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        self.set_model(model)

        self.widget_manager = WidgetManager()
        self.fill_iconview(self.widget_manager.get_widgets())

    def fill_iconview(self, data):
        names = ['Screen 1', 'Screen 2', 'Screen 3', 'Screen 4', 'Screen 5']
        icon = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)
        for name in names:
            self.get_model().append([name, icon])

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)
        text = self.get_model().get_value(selected_iter, 2)
        data.set_text(text, -1)
