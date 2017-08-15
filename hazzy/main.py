#!/usr/bin/env python

#   An attempt at a new UI for LinuxCNC that can be used
#   on a touch screen without any lost of functionality.
#   The code is written in python and glade and is almost a
#   complete rewrite, but was influenced mainly by Gmoccapy
#   and Touchy, with some code adapted from the HAL VCP widgets.

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
import linuxcnc
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject


# Setup paths to files
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
INIFILE = sys.argv[2]                               # Path to .ini file
CONFIGDIR = os.path.dirname(INIFILE)                # Path to config dir
TCLPATH = os.environ['LINUXCNC_TCL_DIR']

# Path to TCL for external programs eg. halshow
if sys.argv[1] != "-ini":
    raise SystemExit("-ini must be first argument")

# Get actual paths so we can run from any location
HAZZYDIR = os.path.dirname(os.path.realpath(__file__))
UIDIR = os.path.join(HAZZYDIR, 'ui')
MODULEDIR = os.path.join(HAZZYDIR, 'modules')
MAINDIR = os.path.dirname(HAZZYDIR)

# Set system path so we can find our own modules
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

# Import our own modules
from hazzy.utilities import logger
from hazzy.utilities import status
from hazzy.modules.dro.dro import Dro


log = logger.get('HAZZY')


class LinuxCNC:

    def __init__(self):

        # UI setup
        gladefile = os.path.join(UIDIR, 'hazzy_3.ui')

        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        panel = self.builder.get_object('panel')
        titlebar = self.builder.get_object('titlebar')

        self.window = Gtk.Window()

        self.window.set_titlebar(titlebar)
        self.window.add(panel)

        btn = self.builder.get_object('btn1')

        self.revealer = self.builder.get_object('revealer')
        self.infobar = self.builder.get_object('infobar')

        self.dro = Dro()

        self.status = status.Status

        self.status.on_value_changed('tool_in_spindle', self.test)
        self.status.on_value_changed('tool_in_spindle', self.test2)
        self.status.on_value_changed('g92_offset', self.g92)
        self.status.on_value_changed('file', self.on_file_changed)

        # Connect stat
        self.status.connect('axis-positions', self.update_position)
        self.status.connect('formated-gcodes', self.update_codes)

        self.window.connect("delete-event", Gtk.main_quit)

        self.window.show()

    def reveal(self, widget, data=None):
        print Gtk.MessageType.WARNING
        self.infobar.set_message_type(Gtk.MessageType.WARNING)
        self.revealer.set_reveal_child(True)

    def infobar_response(self, widget, data=None):
        self.revealer.set_reveal_child(False)

    def test(self, widget, data=None):
        pass

    def test2(self, widget, data=None):
        pass

    def g92(self, widget, data):
        pass

    def on_file_changed(self, widget, data):
        print data

    def update_position(self, widget, pos, rel, dtg):
        label = self.builder.get_object('label')
        label.set_text(str(rel[1]))

    def update_codes(self, widget, gcodes):
        print gcodes


def main():
    LinuxCNC()
    Gtk.main()

if __name__ == "__main__":
    main()
