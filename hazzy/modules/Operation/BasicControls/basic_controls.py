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
#   Provide a minimal way of clearing E-stop and turning the machine on.
#   This is just to hold us over until something better.


import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

import linuxcnc

from utilities import status
from utilities import command

# Setup logging
from utilities import logger
log = logger.get(__name__)

PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR, 'ui')

class BasicControls(Gtk.Bin):

    def __init__(self, widget_window):
        Gtk.Bin.__init__(self)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'basic_controls.ui'))
        self.builder.connect_signals(self)

        self.controls = self.builder.get_object('basic_controls')
        self.add(self.controls)

        status.on_changed('stat.task_state', self.on_task_state_changed)
        status.on_changed('stat.task_mode', self.on_task_mode_changed)
        status.on_changed('stat.interp_state', self.on_interp_state_changed)
        status.on_changed('stat.motion_mode', self.on_motion_mode_changed)

        self.show_all()

    def on_reset_btn_clicked(self, widget):
        command.estop_reset()
        self.builder.get_object('power_sw').set_sensitive(True)

    def on_power_switch_activated(self, widget, event):
        if widget.get_active():
            command.machine_on()
        else:
            command.machine_off()

    def on_task_state_changed(self, widget, task_state):
        state_str = status.STATES.get(task_state, 'UNKNOWN')
        self.builder.get_object('state_lbl').set_text(state_str)

        if task_state == linuxcnc.STATE_ON:
            self.builder.get_object('power_sw').set_active(True)
        elif task_state == linuxcnc.STATE_ESTOP_RESET \
            or task_state == linuxcnc.STATE_OFF \
            or task_state == linuxcnc.STATE_ESTOP:
            self.builder.get_object('power_sw').set_sensitive(True)
            self.builder.get_object('power_sw').set_active(False)

        if task_state == linuxcnc.STATE_ESTOP:
            self.builder.get_object('power_sw').set_sensitive(False)

    def on_task_mode_changed(self, widget, task_mode):
        mode_str = status.MODES.get(task_mode, 'UNKNOWN')
        self.builder.get_object('mode_lbl').set_text(mode_str)

    def on_interp_state_changed(self, widget, interp_state):
        interp_str = status.INTERP.get(interp_state, 'UNKNOWN')
        self.builder.get_object('interp_lbl').set_text(interp_str)

    def on_motion_mode_changed(self, widget, motion_mode):
        motion_str = status.MOTION.get(motion_mode, 'UNKNOWN')
        self.builder.get_object('motion_lbl').set_text(motion_str)
