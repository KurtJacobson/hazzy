#!/usr/bin/env python

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

# Path to TCL for external programs eg. halshow
TCLPATH = os.environ['LINUXCNC_TCL_DIR']

# Get actual paths so we can run from any location
HAZZYDIR = os.path.dirname(os.path.realpath(__file__))
UIDIR = os.path.join(HAZZYDIR, 'ui')
MODULEDIR = os.path.join(HAZZYDIR, 'modules')
MAINDIR = os.path.dirname(HAZZYDIR)

# Set system path so we can find our own modules
if not HAZZYDIR in sys.path:
    sys.path.insert(1, HAZZYDIR)

# Import our own modules
from utilities import logger
log = logger.get('HAZZY')

from utilities import status
from modules.dro.dro import Dro


class LinuxCNC():

    def __init__(self):

        # UI setup
        gladefile = os.path.join(UIDIR, 'hazzy_3.ui')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object('window')
        titlebar = self.builder.get_object('titlebar')
        self.window.set_titlebar(titlebar)

        btn = self.builder.get_object('btn1')

        self.dro = Dro()


        self.status = status.Status


        self.status.monitor('tool_in_spindle', self.test)
        self.status.monitor('tool_in_spindle', self.test2)
        self.status.monitor('g92_offset', self.g92)

        # Connect stat
        self.status.connect('update-axis-positions', self.update_position)
        self.status.connect('active-codes-changed', self.update_codes)

        self.window.show()

    def test(self, widget, data=None):
        pass

    def test2(self, widget, data=None):
        pass

    def g92(self, widget, data):
        pass

    def update_position(self, widget, pos, rel, dtg):
        label = self.builder.get_object('label')
        label.set_text(str(rel[1]))

    def update_codes(self, widget, gcodes, mcodes):
        print gcodes
        print mcodes


    def on_window_delete_event(self, widget, data=None):
        print "Quiting"
        Gtk.main_quit()


def main():
    Gtk.main()

if __name__ == "__main__":
    ui = LinuxCNC()
    main()
