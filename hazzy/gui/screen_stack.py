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
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_transition_duration(300)

        self.current_screen = None
        self.screen_count = 0

        self.show_all()

    def add_screen(self, title=None, switch_to=False):

        screen = WidgetArea()
        screen.show_all()

        name = "screen{}".format(self.screen_count)

        self.add_titled(screen, name, title or '')

        if switch_to:
            self.set_visible_child(self.current_screen)

        self.current_screen = screen
        self.screen_count += 1

    def remove_current_screen(self):
        self.current_screen.destroy()

    def set_current_title(self, title):
        self.child_set_property(self.current_screen, 'title', title)

    def set_position(self, position):
        self.child_set_property(self.current_screen, 'position', position)

    def place_widget(self, widget, x, y, w, h):
        self.current_screen.put(widget, x, y)
        widget.set_size_request(w, h)

    def show_screen(self, name):
        self.set_visible_child_name(name)
        self.get_child_by_name(name).set_visible(True)
