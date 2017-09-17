#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk

PYDIR = os.path.join(os.path.dirname(__file__))

class Dro(Gtk.Grid):

    def __init__(self):
        Gtk.Grid.__init__(self)

        axes = os.environ.get('TRAJ_COORDINATES', None)
        print axes



