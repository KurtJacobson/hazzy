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


class MDI(Gtk.Box):

    title = 'MDI'
    author = 'TurBoss'
    version = '0.1.0'
    date = '5/11/2017'
    description = 'MDI Prompt'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'mdi.glade'))
        self.builder.connect_signals(SignalHandler())

        self.mdi_liststore = self.builder.get_object('mdi_liststore')

        self.mdi_box = self.builder.get_object('mdi_box')

        self.pack_start(self.mdi_box, True, True, 0)


class SignalHandler:

    def on_mdi_prompt_activate(self, widget):

        mdi_buffer = widget.get_text()
        widget.set_text("")
        print(mdi_buffer)

        #store.append(mdi_command)
