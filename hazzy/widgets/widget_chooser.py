#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from widgets.widget_manager import WidgetManager

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
WIDGET_DIR = os.path.join(HAZZYDIR, 'hazzy/modules')


class WidgetChooser(Gtk.Revealer):
    def __init__(self):
        Gtk.Revealer.__init__(self)

        self.set_reveal_child(False)
        self.set_valign(Gtk.Align.START)

        # Scrolled Window
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_propagate_natural_height(True)
        self.scrolled.set_overlay_scrolling(False)
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)

        view = WidgetView()
        self.scrolled.add(view)
        self.add(self.scrolled)

    def get_visible(self):
        return self.get_reveal_child()

    def set_visible(self, visible):
        self.set_reveal_child(visible)


class WidgetView(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        # Add style class
        context = self.get_style_context()
        context.add_class("widget_chooser")

        self.set_text_column(0)
        self.set_pixbuf_column(1)

        self.set_item_width(120)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str)
        self.set_model(model)

        # Enable DnD
        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)
        self.connect("drag-data-get", self.on_drag_data_get)
        self.drag_source_set_target_list(None)
        self.drag_source_add_text_targets()

        self.widget_manager = WidgetManager()
        self.fill_iconview(self.widget_manager.get_widgets())

    def fill_iconview(self, data):
        self.set_columns(len(data))
        for pakage, i in data.iteritems():
            icon = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)
            if i.get('image'):
                path = os.path.join(WIDGET_DIR, pakage, i.get('image'))
                if os.path.exists(path):
                    icon = GdkPixbuf.Pixbuf.new_from_file(path)
                    w, h = icon.get_width(), icon.get_height()
                    scale = 200 / float(w)
                    icon = icon.scale_simple(w * scale, h * scale, GdkPixbuf.InterpType.BILINEAR)
            name = i.get('name')
            self.get_model().append([name, icon, pakage])

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)
        text = self.get_model().get_value(selected_iter, 2)
        data.set_text(text, -1)
