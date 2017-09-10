#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

import linuxcnc

from utilities.status import Status, STATES, MODES, INTERP, MOTION
from utilities.commands import Commands

PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR, 'ui')

class BasicControls(Gtk.Box):

    def __init__(self):
        Gtk.Box.__init__(self)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, 'basic_controls.ui'))
        self.builder.connect_signals(self)

        self.controls = self.builder.get_object('basic_controls')
        self.add(self.controls)

        self.command = Commands()
        self.status = Status

        self.status.on_value_changed('task_state', self.on_task_state_changed)
        self.status.on_value_changed('task_mode', self.on_task_mode_changed)
        self.status.on_value_changed('interp_state', self.on_interp_state_changed)
        self.status.on_value_changed('motion_mode', self.on_motion_mode_changed)

        self.show_all()

    def on_reset_btn_clicked(self, widget):
        self.command.estop_reset()
        self.builder.get_object('power_sw').set_sensitive(True)

    def on_power_switch_activated(self, widget, event):
        if widget.get_active():
            self.command.machine_on()
        else:
            self.command.machine_off()

    def on_task_state_changed(self, widget, task_state):
        state_str = STATES.get(task_state, 'UNKNOWN')
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
        mode_str = MODES.get(task_mode, 'UNKNOWN')
        self.builder.get_object('mode_lbl').set_text(mode_str)

    def on_interp_state_changed(self, widget, interp_state):
        interp_str = INTERP.get(interp_state, 'UNKNOWN')
        self.builder.get_object('interp_lbl').set_text(interp_str)

    def on_motion_mode_changed(self, widget, motion_mode):
        motion_str = MOTION.get(motion_mode, 'UNKNOWN')
        self.builder.get_object('motion_lbl').set_text(motion_str)
