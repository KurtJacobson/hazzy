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
import gi

import sys

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk
from utilities.command import issue_mdi


class MDI(Gtk.Box):

    title = 'MDI'
    author = 'TurBoss'
    version = '0.1.0'
    date = '5/11/2017'
    description = 'MDI Prompt'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.set_hexpand(True)
        self.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        self.vadj = scrolled.get_vadjustment()
        self.pack_start(scrolled, True, True, 0)

        self.cmd_history = Gtk.ListBox()
        self.cmd_history.set_activate_on_single_click(True)
        scrolled.add(self.cmd_history)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text('MDI')
        self.pack_start(self.entry, False, False, 0)

        self.scrolled_to_bottom = False

        self.cmd_history.connect('size-allocate', self.scroll_to_bottom)
        self.entry.connect('activate', self.on_entry_acitvated)

    # Use MDIHistoryRow
    def submit_to_history(self, command):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(box)
        row.connect('activate', self.on_row_activated, command)
        box.pack_start(Gtk.Label(command, xalign=0), True, True, 0)
        btn = Gtk.Button.new_from_icon_name('process-stop', Gtk.IconSize.BUTTON)
        btn.connect('clicked', self.remove_from_history, row)
        btn.get_style_context().add_class('flat')
        btn.get_style_context().add_class('no_padding')
        box.pack_end(btn, False, False, 0)
        self.cmd_history.add(row)
        row.show_all()

    def on_row_activated(self, widegt, command):
        self.entry.set_text(command)

    def remove_from_history(self, widegt, row):
        self.cmd_history.remove(row)

    def on_entry_acitvated(self, widget):
        cmd = widget.get_text()
        if cmd == '':
            return
        widget.set_text('')
        self.submit_to_history(cmd)
        self.scrolled_to_bottom = False

    def scroll_to_bottom(self, widget, event):
        if not self.scrolled_to_bottom:
            self.vadj.set_value(self.vadj.get_upper() - self.vadj.get_page_size())
            self.scrolled_to_bottom = True

# Not done
class MDIHistoryRow(Gtk.ListBoxRow):
    def __init__(self, cmd):
        Gtk.ListBoxRow.__init__(self)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(box)

        label = Gtk.Label(command, xalign=0)
        box.pack_start(label, True, True, 0)

        btn = Gtk.Button.new_from_icon_name('process-stop', Gtk.IconSize.BUTTON)
        btn.connect('clicked', self.remove_from_history, row)
        btn.get_style_context().add_class('flat')
        btn.get_style_context().add_class('no_padding')
        box.pack_end(btn, False, False, 0)

        row.connect('activate', self.on_row_activated, command)
        row.show_all()
