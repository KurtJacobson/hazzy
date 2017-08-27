#!/usr/bin/env python

import os
import gi
import ast
import importlib

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from constants import Paths

# Import our own modules
from hazzy.utilities import logger
from widgets.widget_window import WidgetWindow
from widgets.widget_area import WidgetArea
from widgets.widget_manager import WidgetManager
from widgets.widget_chooser import WidgetChooser

log = logger.get('HAZZY.DASHBOARD')


class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        gladefile = os.path.join(Paths.UIDIR, 'hazzy.ui')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.hazzy_window = self.builder.get_object('hazzy_window')
        self.titlebar = self.builder.get_object('titlebar')
        self.widget_stack = self.builder.get_object('widget_stack')
        self.revealer_area = self.builder.get_object('revealer_area')

        self.iconview_scroller = self.builder.get_object('iconview_scroller')
        self.builder.connect_signals(self)
        self.add(self.hazzy_window)
        self.set_titlebar(self.titlebar)

        self.iconview_scroller.add(WidgetChooser())

        self.widget_area = WidgetArea()
        self.widget_stack.add_named(self.widget_area, 'Page 1')
        self.widget_stack.set_visible_child_name('Page 1')

        self.set_size_request(900, 600)
        self.show_all()

    def on_reveal_clicked(self, button):
        reveal = self.revealer_area.get_reveal_child()
        self.revealer_area.set_reveal_child(not reveal)

    def on_edit_layout_toggled(self, widget):
        edit = widget.get_active()
        # Hide eventbox used for drag/resize
        widgets = self.widget_area.get_children()
        for widget in widgets:
            widget.show_overlay(edit)

