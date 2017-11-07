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


# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

UIDIR = os.path.join(PYDIR, 'ui')

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
        self.pack_start(scrolled, True, True, 0)

        self.store = Gtk.ListStore(str, str, str)

        view = Gtk.TreeView(self.store)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Instruction", renderer, text=0)
        view.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Remove", renderer, text=1)
        view.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Run", renderer, text=2)
        view.append_column(column)

        scrolled.add(view)

        entry = Gtk.Entry()
        entry.set_placeholder_text('MDI')
        self.pack_start(entry, False, False, 0)

        entry.connect('activate', self.on_entry_acitvated)

    def on_entry_acitvated(self, widget):
        cmd = widget.get_text()
        widget.set_text('')
        self.store.append([cmd, None, None])
