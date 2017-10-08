#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from widget_area import WidgetArea

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))


class ScreenStack(Gtk.Stack):
    def __init__(self):
        Gtk.Stack.__init__(self)

        # Add style class
        context = self.get_style_context()
        context.add_class("widget_stack")

        self.set_homogeneous(True)
        self.set_transition_type(Gtk.StackTransitionType.NONE)
        self.set_transition_duration(150)

        self.current_screen = None

        self.show_all()

    def add_screen(self, name=None, title=None):
        if name is None:
            screens = self.get_children()
            for screen in screens:
                print screen.name

        new_screen = WidgetArea()
        self.add_titled(new_screen, name, title or '')
        self.current_screen = new_screen

    def place_widget(self, widget, x, y, w, h):
        self.current_screen.put(widget, x, y)
        widget.set_size_request(w, h)

    def set_position(self, name, position):
        screen = self.get_child_by_name(name)
        self.child_set_property(screen, 'position', position)

    def show_screen(self, name):
        self.set_visible_child_name(name)
        self.get_child_by_name(name).set_visible(True)
