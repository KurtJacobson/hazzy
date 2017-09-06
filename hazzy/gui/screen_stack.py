#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))


class ScreenStack(Gtk.Stack):
    def __init__(self):
        Gtk.Stack.__init__(self)

        self.name = None

        # Add style class
        context = self.get_style_context()
        context.add_class("widget_stack")

        self.set_homogeneous(True)
        self.set_transition_type(Gtk.StackTransitionType.NONE)
        self.set_transition_duration(150)

        self.show_all()


    def add_screen(self, screen, name):
        self.name = name
        # self.add_named(screen, name)
        self.add_titled(screen, name, "screen 1")

    def show_screen(self, name):
        self.set_visible_child_name(name)
        self.get_child_by_name(name).set_visible(True)

