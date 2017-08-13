#!/usr/bin/env python

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

UIDIR = os.path.join(PYDIR)
STYLEDIR = os.path.join(HAZZYDIR, 'themes')

from utilities.status import Status

# Setup logging

from utilities import logger
log = logger.get("HAZZY.ACTIVE_CODES_WIDGET")

VERTICAL = Gtk.Orientation.VERTICAL
HORIZONTAL = Gtk.Orientation.HORIZONTAL


class ActiveCodesWidget(Gtk.Box):

    def __init__(self):
        Gtk.Box.__init__(self, orientation=VERTICAL)

        self.status = Status

        self.status.on_value_changed('formated-gcodes', self.update_gcodes)
        self.status.on_value_changed('formated-mcodes', self.update_mcodes)

        self.gcodes_box = Gtk.Box(orientation=HORIZONTAL)
        self.mcodes_box = Gtk.Box(orientation=HORIZONTAL)

        self.gcodes_label = Gtk.Label()
        self.mcodes_label = Gtk.Label()

        self.gcodes_label.set_text("Active GCode:")
        self.mcodes_label.set_text("Active MCode:")

        self.pack_start(self.gcodes_box,  True, True, 0)
        self.pack_start(self.mcodes_box,  True, True, 0)

        self.gcodes_box.pack_start(self.gcodes_label,  True, True, 0)
        self.mcodes_box.pack_start(self.mcodes_label,  True, True, 0)

        self.show_all()

    def update_gcodes(self, widget, codes):

        for code in codes:
            code_label = Gtk.Label()
            code_label.set_text(code)
            self.gcodes_box.pack_start(code_label, True, True, 0)

        self.gcodes_box.show_all()

    def update_mcodes(self, widget, codes):

        for code in codes:
            code_label = Gtk.Label()
            code_label.set_text(code)
            self.mcodes_box.pack_start(code_label, True, True, 0)

        self.mcodes_box.show_all()