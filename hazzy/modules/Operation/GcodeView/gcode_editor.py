#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk

# Set up paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if not HAZZYDIR in sys.path:
    sys.path.insert(1, HAZZYDIR)

UI = os.path.join(PYDIR, 'ui', 'gcode_view.ui')

# Import our own modules
from gcode_view import GcodeView

# Setup logger
#log = logger.get("HAZZY.GCODEVIEW")


class GcodeEditor(Gtk.Box):

    def __init__(self):
        Gtk.Box.__init__(self)

        self.set_size_request(200, 160)

        view = GcodeView()
        buf = view.get_buffer()
        buf.set_text('''(TEST OF G-CODE HIGHLIGHTING)\n\nG1 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0\n\nM3''')
        view.highlight_line(3, 'motion')

        scrolled = Gtk.ScrolledWindow()
        scrolled.add(view)

        scrolled.connect('button-press-event', self.on_button_press)

        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)

        self.add(scrolled)
        self.show_all()

    # The GtkSource deos not return True after handaling and button
    # press, so we have to do so here so the hanler in the WidgetWindow
    # and in the HazzyWindow do not remove the focus
    def on_button_press(self, widget, event):
        return True
