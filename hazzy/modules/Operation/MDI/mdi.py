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
#   MDI entry with command history and completion. Uses the MDIEntry from
#   the Widget Factory as a base.

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from widget_factory.entry_widgets import MDIEntry

class MDI(Gtk.Box):

    title = 'MDI'
    author = 'TurBoss'
    version = '0.1.2'
    date = '5/11/2017'
    description = 'MDI Prompt'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.set_hexpand(True)
        self.set_vexpand(True)

        # Widget Factories MDI entry widget
        self.entry = MDIEntry()
        self.pack_end(self.entry, False, False, 0)

        # Scrolled window for the MDI history view
        scrolled = Gtk.ScrolledWindow()
        self.vadj = scrolled.get_vadjustment()
        self.pack_start(scrolled, True, True, 0)

        # MDI history TreeView
        self.view = Gtk.TreeView(self.entry.model)
        self.view.set_activate_on_single_click(True)
        self.view.set_headers_visible(False)
        scrolled.add(self.view)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Command", renderer, text=0)
        self.view.append_column(column)

        self.selection = self.view.get_selection()
        self.scrolled_to_bottom = False

        self.view.connect('size-allocate', self.scroll_to_bottom)
        self.view.connect('row-activated', self.on_view_row_activated)
        self.view.connect('cursor-changed', self.on_view_cursor_changed)
        self.entry.connect('activate', self.on_entry_activated)
        self.entry.connect('focus-in-event', self.on_entry_gets_focus)
        self.entry.connect('key-press-event', self.on_entry_keypress)

    # On history item clicked set the cmd in the MDI entry
    def on_view_row_activated(self, widget, row, column):
        cmd = self.entry.model[row][0]
        self.set_entry_text(cmd)

    # On history item selected (via arrow keys) set the cmd in the MDI entry
    def on_view_cursor_changed(self, widget):
        row = widget.get_cursor()[0]
        if row is not None:
            cmd = self.entry.model[row][0]
            self.view.set_search_entry(None)
            self.set_entry_text(cmd)

    # Just a little helper
    def set_entry_text(self, cmd):
        self.entry.set_text(cmd)
        self.entry.set_position(-1)

    # While MDI entry has focus, use UP/DOWN arrow keys to move through history
    # setting the selected cmd in the entry.
    def on_entry_keypress(self, widegt, event):
        kv = event.keyval
        if kv == Gdk.KEY_Up:
            row = self.get_row() # Highlighted row path, or the last row's path
            if row.prev():
                self.view.set_cursor([row,], None, False)
            else:
                Gdk.beep() # Complain if we are already on the top row
            return True
        elif kv == Gdk.KEY_Down:
            # For some odd reason row.next() returns None, instead of a bool
            # indication if the row is valid like row.prev() does, so we have
            # to do our own validation here.
            row = self.get_row() # Highlighted row path, or the last row's path
            last_row = Gtk.TreePath.new_from_indices([len(self.entry.model),])
            row.next()
            if row != last_row:
                self.view.set_cursor([row,], None, False)
            else:
                Gdk.beep() # Complain if we are already on the last row
            return True

    def get_row(self):
        try: # If no row is selected the list of rows will be empty resulting in IndexError
            row = self.selection.get_selected_rows()[1][0]
        except IndexError: # If IndexError then default to the last row
            row = Gtk.TreePath.new_from_indices([len(self.entry.model),])
        return row

    # Clear any selection when the entry gets focus. This may not be needed/wanted
    def on_entry_gets_focus(self, widget, event):
        selection = self.view.get_selection()
        selection.unselect_all()

    def on_entry_activated(self, widget):
        self.scrolled_to_bottom = False # Reset the flag

    # Since the TreeView row is added after a sort delay, we have to listen for
    # the TreeView `size-allocate` and scroll to the end on that.
    # See the SO question here:  https://stackoverflow.com/a/5235358/7798639
    def scroll_to_bottom(self, widget, event):
        # We only want to scroll to bottom when a new row is added, so use a flag
        if not self.scrolled_to_bottom:
            self.vadj.set_value(self.vadj.get_upper() - self.vadj.get_page_size())
            self.scrolled_to_bottom = True
