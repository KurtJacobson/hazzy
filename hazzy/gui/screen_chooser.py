#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from widget_manager import WidgetManager
from widget_area import WidgetArea

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

        self.set_transition_type(Gtk.RevealerTransitionType.NONE)

        self.view = ScreenView()
        self.add(self.view)

    def get_visible(self):
        return self.get_reveal_child()

    def set_visible(self, visible):
        self.set_reveal_child(visible)


class ScreenView(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        # Add style class
        context = self.get_style_context()
        context.add_class("WidgetChooser")

        self.connect('item-activated', self.on_icon_clicked)
        self.set_activate_on_single_click(True)

        self.set_text_column(0)
        self.set_pixbuf_column(1)

        self.set_columns(3)
        self.set_item_width(120)

        self.do_unselect_all(self)

        self.model = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        self.set_model(self.model)
        self.fill_iconview(None)

    def fill_iconview(self, screens):
        self.model.clear()
        theme = Gtk.IconTheme.get_default()
        icon = theme.load_icon('image-missing', 56, 0)
        if screens:
            for screen in screens:
                self.model.append([screen, icon])

        icon = theme.load_icon('list-add', 56, Gtk.IconLookupFlags.FORCE_SIZE)
        self.get_model().append(['Add Screen', icon])

    def on_icon_clicked(self, widget, path):
        name = self.model[path][0]
        stack = self.get_parent().get_parent().get_child()
        if name == "Add Screen":
            name = 'Screen {}'.format(len(stack.get_children()) + 1)
            icon = Gtk.IconTheme.get_default().load_icon('image-missing', 56, 0)
            self.get_model().append([name, icon])
            stack.add_screen(WidgetArea(), name, name)
        stack.show_screen(name)
        self.get_parent().set_reveal_child(False)
