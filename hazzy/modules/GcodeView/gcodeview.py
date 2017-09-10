#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#       <kurtcjacobson@gmail.com>
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
gi.require_version('GtkSource', '3.0')

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


class GcodeViewWidget(Gtk.Box):

    def __init__(self):
        Gtk.Box.__init__(self)

        self.set_size_request(200, 160)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI)
        self.builder.connect_signals(self)

        self.add(self.builder.get_object('main'))
        self.scrolled = self.builder.get_object('gcode_scroller')

        self.gcode_view = GcodeView(preview=True)
        buf = self.gcode_view.get_buffer()
        buf.set_text('''(TEST OF G-CODE HIGHLIGHTING)\n\nG1 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0\n\nM3''')
        self.gcode_view.highlight_line(3, 'motion')

        self.scrolled.add(self.gcode_view)

        self.show_all()


