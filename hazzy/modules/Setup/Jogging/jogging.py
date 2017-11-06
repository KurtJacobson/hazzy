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
#   TBA

import os
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR, 'ui')


class Jogging(Gtk.Bin):

    title = 'Jogging'
    author = 'Kurt Jacobson'
    version = '0.1.0'
    date = '5/11/2017'
    description = 'Basic jogging controls'

    def __init__(self, widget_window):
        Gtk.Bin.__init__(self)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'jogging.ui'))
        # self.builder.connect_signals(SignalHandler)

        main = self.builder.get_object('main')
        self.add(main)

