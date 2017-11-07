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
#   Provides a temperary meaning of starting/stoping a program.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from utilities import command

class ProgramControls(Gtk.Box):
    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.get_style_context().add_class('red')

        self.run_button = Gtk.Button.new_with_label('Run')
        self.run_button.get_style_context().add_class('blue')
        self.run_button.connect('clicked', self.on_run_button_clicked)
        self.pack_start(self.run_button, True, True, 4)

        self.stop_button = Gtk.Button.new_with_label('Stop')
        self.stop_button.get_style_context().add_class('red')
        self.stop_button.connect('clicked', self.on_stop_button_clicked)
        self.pack_start(self.stop_button, True, True, 4)

    def on_run_button_clicked(self, widget):
        command.auto_run()

    def on_stop_button_clicked(self, widget):
        command.abort()
