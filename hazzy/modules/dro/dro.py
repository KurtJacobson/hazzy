#!/usr/bin/env python

import os
import sys
import importlib
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

status = importlib.import_module('utilities.status')

# Setup logging
from utilities import logger
log = logger.get("HAZZY.KEYBOARD")

class Dro():

    def __init__(self):

        self.stat = status.Status

        self.stat.connect('update_axis_positions', self.update_dros)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'dro.ui'))

        self.window = self.builder.get_object('window')

        self.x = self.builder.get_object('x')
        self.y = self.builder.get_object('y')
        self.z = self.builder.get_object('z')
        self.window.show()


    def update_dros(self, widget, pos, rel, dtg):
        self.x.set_text(str(rel[0]))
        self.y.set_text(str(rel[1]))
        self.z.set_text(str(rel[2]))

