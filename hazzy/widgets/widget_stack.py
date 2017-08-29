#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))


class WidgetStack(Gtk.Stack):
    def __init__(self):
        Gtk.Stack.__init__(self)

        # Add style class
        context = self.get_style_context()
        context.add_class("widget_stack")

        self.set_homogeneous(True)

        self.show_all()


    def add_screen(self, screen, name):
        self.add_named(screen, name)


    def show_screen(self, name):
        self.set_visible_child_name(name)

