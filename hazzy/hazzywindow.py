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
from widgets.widget_manager import WidgetManager
from widgets.widget_chooser import WidgetChooser
from widgets.widget_window import WidgetWindow
from widgets.widget_stack import WidgetStack
from widgets.widget_area import WidgetArea
from hazzy.utilities import logger

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
        self.revealer_area = self.builder.get_object('revealer_area')
        self.iconview_scroller = self.builder.get_object('iconview_scroller')

        self.builder.connect_signals(self)
        self.add(self.hazzy_window)
        self.set_titlebar(self.titlebar)

        self.widget_chooser = WidgetChooser()
        self.iconview_scroller.add(self.widget_chooser)

        self.widget_stack = WidgetStack()
        self.hazzy_window.add(self.widget_stack)

        self.widget_stack.add_screen(WidgetArea(), 'Screen 1')
        self.widget_stack.show_screen('Screen 1')

        self.set_size_request(900, 600)
        self.show_all()

    def on_reveal_clicked(self, button):
        reveal = self.revealer_area.get_reveal_child()
        self.revealer_area.set_reveal_child(not reveal)

    def on_edit_layout_toggled(self, widget):
        edit = widget.get_active()
        # Hide eventbox used for drag/resize
        screens = self.widget_stack.get_children()
        for screen in screens:
            widgets = screen.get_children()
            for widget in widgets:
                widget.show_overlay(edit)
