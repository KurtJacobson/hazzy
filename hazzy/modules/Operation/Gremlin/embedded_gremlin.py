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
#   MDI entry with command history and completion. Uses the MDIEntry from
#   the Widget Factory as a base.

import os
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

HERE = os.path.dirname(os.path.abspath(__file__))

class EmbededGremlin(Gtk.Socket):

    title = 'Gremlin Backplot'
    author = 'Kurt Jacobson'
    version = '0.1.0'
    date = '11/29/2017'
    description = 'Gremlin g-code backplot'

    def __init__(self, widget_window):
        Gtk.Socket.__init__(self)

        self.connect("plug-added", self.plugged_event)
        self.connect('realize', self.on_realized)

    def plugged_event(self, widget):
        print "I have just had a plug inserted!"

    def on_realized(self, widget):
        xid = self.get_id()
        grem = os.path.join(HERE, 'hazzygremlin', 'hazzygremlin.py')
        subprocess.Popen([grem, str(xid)])
