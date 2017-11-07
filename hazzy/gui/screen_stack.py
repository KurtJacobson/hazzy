#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   Subclass of Gtk.Stack. This is the main child in the HazzyWindow and
#   provides the ability to add/remove 'screens' to paged thru them.

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

        self.set_homogeneous(True)
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_transition_duration(300)

        self.screen_count = 0

        self.show_all()

    def add_screen(self, title=None):
        screen = WidgetArea()
        screen.show_all()

        name = "screen{}".format(self.screen_count)
        self.add_titled(screen, name, title or 'New Screen')
        self.screen_count += 1
        return screen

    def remove_visible_child(self):
        self.get_visible_child().destroy()
        # If no screens left, add a blank one
        if len(self.get_children()) == 0:
            self.add_screen()

    def add_screen_interactive(self):
        screen = self.add_screen()
        self.set_visible_child(screen)

    def set_visible_child_title(self, title):
        self.child_set_property(self.get_visible_child(), 'title', title)

    def set_visible_child_position(self, position):
        self.child_set_property(self.get_visible_child(), 'position', position)

    def place_widget(self, screen, widget, x, y, w, h):
        screen.put(widget, x, y)
        widget.set_size_request(w, h)
