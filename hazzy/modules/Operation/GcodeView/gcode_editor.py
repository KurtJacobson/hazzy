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


from Setup.FileChooser.filechooser import FileChooser

# Import our own modules
from gcode_view import GcodeView, GcodeMap

# Setup logger
#log = logger.get("HAZZY.GCODEVIEW")


class GcodeEditor(Gtk.Bin):

    def __init__(self):
        Gtk.Bin.__init__(self)

        self.set_size_request(200, 160)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI)
        self.builder.connect_signals(self)

        main = self.builder.get_object('main')
        self.add(main)

        self.stack = self.builder.get_object('stack')

        self.file_chooser = FileChooser()
        self.file_chooser.connect('file-activated', self.on_file_activated)
        self.file_chooser.show_all()
        self.stack.add_named(self.file_chooser, 'file_chooser_page')

        self.gcode_view_page = self.builder.get_object('gcode_view_page')

        self.gcode_view = GcodeView()
        self.buf = self.gcode_view.get_buffer()
        self.buf.set_text('''(TEST OF G-CODE HIGHLIGHTING)\n\nG1 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0\n\nM3''')
        self.gcode_view.highlight_line(3, 'motion')

        self.scroll_window = self.builder.get_object('scrolled_window')
        self.scroll_window.add(self.gcode_view)

        self.map_scrolled = self.builder.get_object('source_map_scrolled_window')
        self.source_map = GcodeMap()
        self.source_map.set_view(self.gcode_view)
        self.map_scrolled.add(self.source_map)

        self.open_radiobutton = self.builder.get_object('open_radiobutton')
        self.edit_radiobutton = self.builder.get_object('edit_radiobutton')

    def on_run_button_toggled(self, widegt):
        self.gcode_view.set_editable(False)
        print 'Run Button toggled'

    def on_edit_button_toggled(self, widegt):
        self.stack.set_visible_child(self.gcode_view_page)
        self.gcode_view.set_editable(True)
        print 'Edit Button Toggled'

    def on_open_button_toggled(self, widegt):
        self.stack.set_visible_child(self.file_chooser)
        print 'Open Button Toggled'

    def on_file_activated(self, widegt, path):
        self.gcode_view.load_file(path)
        self.stack.set_visible_child(self.gcode_view_page)
        self.edit_radiobutton.set_active(True)

    # The GtkSource deos not return True after handaling and button
    # press, so we have to do so here so the hanler in the WidgetWindow
    # and in the HazzyWindow do not remove the focus
    def on_scrolled_window_button_press(self, widget, event):
        return True
