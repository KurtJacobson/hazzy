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
from hazzy.widgets.widget_area import WidgetArea

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

        view = ScreenView()
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

        self.connect('item-activated', self.on_screen_clicked)
        self.set_activate_on_single_click(True)

        self.set_text_column(0)
        self.set_pixbuf_column(1)

        self.set_columns(3)
        self.set_item_width(120)

        self.do_unselect_all(self)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        self.set_model(model)

        self.widget_manager = WidgetManager()
        self.fill_iconview(self.widget_manager.get_widgets())

    def fill_iconview(self, data):
        names = ['Screen 1',]
        icon = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)
        for name in names:
            self.get_model().append([name, icon])

        icon = Gtk.IconTheme.get_default().load_icon('list-add', 100, 0)
        self.get_model().append(['Add Screen', icon])

    def on_screen_clicked(self, widget, path):
        text = self.get_model()[path][0]
        stack = self.get_parent().get_parent().get_child()
        print text
        if text == "Add Screen":
            text = 'Screen {}'.format(len(stack.get_children()))
            stack.add_screen(WidgetArea(), text)
            stack.show_screen(text)
            icon = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)
            self.get_model().append([text, icon])
        else:
            stack.show_screen(text)
        stack.set_visible_child_name(text)
        print stack.get_children()
        print stack.get_visible_child_name()
