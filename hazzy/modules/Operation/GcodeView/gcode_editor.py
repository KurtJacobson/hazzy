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
UI = os.path.join(PYDIR, 'ui', 'gcode_view.ui')

# Import our own modules
from utilities import command
from utilities import logger
from utilities import ini_info
from utilities.constants import MessageType

# Import FileChooser
from Setup.FileChooser.filechooser import FileChooser

from gcode_view import GcodeView, GcodeMap

# Setup logger
log = logger.get(__name__)


class GcodeEditor(Gtk.Bin):

    def __init__(self, widget_window=None):
        Gtk.Bin.__init__(self)

        self.widget_window = widget_window

        self.set_size_request(200, 160)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI)
        self.builder.connect_signals(self)

        main = self.builder.get_object('main')
        self.add(main)

        self.open_radiobutton = self.builder.get_object('open_radiobutton')
        self.edit_radiobutton = self.builder.get_object('edit_radiobutton')
        self.run_radiobutton = self.builder.get_object('run_radiobutton')
        self.edit_button_box = self.builder.get_object('edit_button_box')
        self.line_count_label = self.builder.get_object('line_count_label')
        self.stack = self.builder.get_object('stack')

        self.file_chooser = FileChooser(widget_window)
        self.file_chooser.connect('file-activated', self.on_filechooser_file_activated)
        self.file_chooser.connect('selection-changed', self.on_filechooser_selection_changed)
        self.file_chooser.show_all()
        self.file_chooser.add_filter('ini', ini_info.get_file_extentions())
        self.file_chooser.set_filter('ini')

        self.stack.add_named(self.file_chooser, 'file_chooser')
        self.stack.set_visible_child(self.file_chooser)

        self.gcode_view_page = self.builder.get_object('gcode_view_page')

        self.gcode_view = GcodeView()

        self.scroll_window = self.builder.get_object('scrolled_window')
        self.scroll_window.add(self.gcode_view)

        self.map_scrolled = self.builder.get_object('source_map_scrolled_window')
        self.source_map = GcodeMap()
        self.source_map.set_view(self.gcode_view)
        self.map_scrolled.add(self.source_map)

    def on_open_button_toggled(self, widegt):
        if not widegt.get_active():
            return
        self.stack.set_visible_child(self.file_chooser)

    def on_edit_button_toggled(self, widegt):
        if not widegt.get_active():
            return
        path = self.get_selected_file()
        if path is None:
            return

        self.stack.set_visible_child(self.gcode_view_page)
        self.edit_button_box.show()
        self.gcode_view.set_editable(True)

        self.check_modified_and_load_editor(path)

    def on_run_button_toggled(self, widegt):
        if not widegt.get_active():
            return

        if self.stack.get_visible_child() == self.file_chooser:
            path = self.get_selected_file()
            self.stack.set_visible_child(self.gcode_view_page)
        else:
            path = self.gcode_view.current_file

        self.check_modified_and_load_editor(path)

        self.edit_button_box.hide()
        self.gcode_view.set_editable(False)
        command.load_file(self.gcode_view.current_file)

    def on_filechooser_file_activated(self, widegt, path):
        self.edit_radiobutton.set_active(True)
        self.stack.set_visible_child(self.gcode_view_page)
        self.edit_button_box.show()
        self.gcode_view.set_editable(True)
        self.check_modified_and_load_editor(path)

    def on_filechooser_selection_changed(self, widget, path):
        self.widget_window.set_title(path)
        is_file = os.path.isfile(path)
        self.edit_radiobutton.set_sensitive(is_file)
        self.run_radiobutton.set_sensitive(is_file)

        if is_file:
            line_count = self.file_chooser.count_lines(path)
            self.line_count_label.set_text(str(line_count))
        else:
            self.line_count_label.set_text('0')

# Helpers
#============================

    def get_selected_file(self):
        path = self.file_chooser.get_selected()
        if not path or len(path) != 1:
            self.widget_window.show_error('Please select exactly one file to edit', 1.5)
            self.open_radiobutton.set_active(True)
            return None
        else:
            return path[0]

    def check_modified_and_load_editor(self, path):
        if self.gcode_view.get_modified():
            fname = os.path.split(self.gcode_view.current_file)[1]
            msg = '"{}" has been modified, save changes?'.format(fname)
            self.widget_window.show_question(msg, self.on_save_changes_response, path)
        else:
            if path != self.gcode_view.current_file:
                self.gcode_view.load_file(path)

    def on_save_changes_response(self, response, path):
        if response == Gtk.ResponseType.YES:
            self.gcode_view.save()
            self.gcode_view.load_file(path)
        else:
            self.gcode_view.load_file(path)

    # The GtkSource deos not return True after handaling a button
    # press, so we have to do so here so the hanler in the WidgetWindow
    # and in the HazzyWindow do not remove the focus
    def on_scrolled_window_button_press(self, widget, event):
        return True
