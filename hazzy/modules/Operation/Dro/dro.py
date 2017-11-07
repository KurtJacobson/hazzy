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
#   A very basic XYZ DRO. For use mainly as an example.

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from utilities import ini_info
from utilities import machine_info
from utilities import status
from utilities.constants import Paths

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR)

# Setup logging
from utilities import logger
log = logger.get(__name__)

log.info(ini_info.get_xml_file())
log.info(machine_info.axis_letter_list)

class Dro(Gtk.Box):

    title = 'DRO'
    author = 'Kurt Jacobson'
    version = '0.1.0'
    date = '10/01/2017'
    description = 'A very basic XYZ DRO. For use mainly as an example.'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self)

        status.on_changed('stat.axis_positions', self.update_dros)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'dro.ui'))

        self.x = self.builder.get_object('x')
        self.y = self.builder.get_object('y')
        self.z = self.builder.get_object('z')

        self.display = self.builder.get_object('dro')

        self.add(self.display)
        self.show_all()

    def update_dros(self, widget, positions):
        pos, rel, dtg = positions
        self.x.set_text(str(rel[0]))
        self.y.set_text(str(rel[1]))
        self.z.set_text(str(rel[2]))
