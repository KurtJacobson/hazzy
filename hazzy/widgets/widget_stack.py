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

        self.set_homogenious(True)


    def add_by_name(self, name):
        pass


    def show_child(self, name):
        self.set_visible_child_name(name)

