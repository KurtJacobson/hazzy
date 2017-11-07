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
#   Display active G-codes and M-codes


import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from utilities.status import Status

# Setup logging
from utilities import logger
log = logger.get(__name__)

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR)

VERTICAL = Gtk.Orientation.VERTICAL
HORIZONTAL = Gtk.Orientation.HORIZONTAL


class ActiveCodesWidget(Gtk.Box):

    def __init__(self):
        Gtk.Box.__init__(self, orientation=VERTICAL)

        self.status = Status

        self.status.on_value_changed('formated-gcodes', self.update_gcodes)
        self.status.on_value_changed('formated-mcodes', self.update_mcodes)

        self.gcodes_box = None
        self.mcodes_box = None

        self.gcodes_label = Gtk.Label()
        self.gcodes_label.set_text("Active GCode:")

        self.mcodes_label = Gtk.Label()
        self.mcodes_label.set_text("Active MCode:")

        self.show_all()

    def update_gcodes(self, widget, codes):

        self.gcodes_box = Gtk.Box(orientation=HORIZONTAL)
        self.gcodes_box.pack_start(self.gcodes_label, True, True, 0)

        for code in codes:
            code_label = Gtk.Label()
            code_label.set_text(code)
            self.gcodes_box.pack_start(code_label, True, True, 0)

        self.gcodes_box.show_all()
        self.pack_start(self.gcodes_box,  True, True, 0)

    def update_mcodes(self, widget, codes):

        self.mcodes_box = Gtk.Box(orientation=HORIZONTAL)
        self.mcodes_box.pack_start(self.mcodes_label, True, True, 0)

        for code in codes:
            code_label = Gtk.Label()
            code_label.set_text(code)
            self.mcodes_box.pack_start(code_label, True, True, 0)

        self.mcodes_box.show_all()
        self.pack_start(self.mcodes_box,  True, True, 0)

