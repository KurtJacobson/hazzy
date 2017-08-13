#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.


import math
import linuxcnc

from gi.repository import GObject

# Setup logging
import logger

log = logger.get("HAZZY.STATUS")

STATES = {
    linuxcnc.STATE_ESTOP: 'ESTOP',
    linuxcnc.STATE_ESTOP_RESET: 'RESET',
    linuxcnc.STATE_ON: 'ON',
    linuxcnc.STATE_OFF: 'OFF'
}

MODES = {
    linuxcnc.MODE_MANUAL: 'MAN',
    linuxcnc.MODE_AUTO: 'AUTO',
    linuxcnc.MODE_MDI: 'MDI'
}

INTERP = {
    linuxcnc.INTERP_WAITING: 'WAIT',
    linuxcnc.INTERP_READING: 'READ',
    linuxcnc.INTERP_PAUSED: 'PAUSED',
    linuxcnc.INTERP_IDLE: 'IDLE'
}

MOTION = {
    linuxcnc.TRAJ_MODE_COORD: 'COORD',
    linuxcnc.TRAJ_MODE_FREE: 'FREE',
    linuxcnc.TRAJ_MODE_TELEOP: 'TELEOP'
}

SIGNALS = {
    'formated-gcodes': 'gcodes',
    'formated-mcodes': 'mcodes',
    'file-loaded': 'file'
}

def singleton(cls):
    return cls()


@singleton
class Status(GObject.GObject):
    __gtype_name__ = 'Status'
    __gsignals__ = {
        'formated-gcodes': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'formated-mcodes': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'file-loaded': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'joint-positions': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'axis-positions': (GObject.SignalFlags.RUN_FIRST, None, (object, object, object)),
    }

    def __init__(self, stat=None):

        GObject.GObject.__init__(self)

        self.signals = GObject.signal_list_names(self)

        self.stat = stat or linuxcnc.stat()
        self.error = linuxcnc.error_channel()

        self.report_actual_position = False

        self.axis_list = []
        self.file = None

        self.registry = []
        self.old = {}

        self.on_value_changed('axis_mask', self._update_axis_list, False)

        self.on_value_changed('task_state', self._update_task_state, False)
        self.on_value_changed('task_mode', self._update_task_mode, False)
        self.on_value_changed('interp_state', self._update_interp_state, False)
        self.on_value_changed('motion_mode', self._update_motion_mode, False)
        self.on_value_changed('g5x_index', self._update_work_corordinate, False)

        self.on_value_changed('gcodes', self._update_active_gcodes, False)
        self.on_value_changed('mcodes', self._update_active_mcodes, False)

        self.on_value_changed('file', self._update_file, True)

        GObject.timeout_add(50, self.periodic)

    # This allows monitoring any of the linuxcnc.stat attributes
    # and connecting a callback to be called on attribute value change
    def on_value_changed(self, attribute, callback, print_info=True):

        if hasattr(self.stat, attribute) \
                or attribute.replace('_', '-') in self.signals:

            if attribute.replace('_', '-') not in self.signals \
                    and attribute not in self.registry:
                GObject.signal_new(attribute, self, GObject.SignalFlags.RUN_FIRST, None, (object,))
                self.registry.append(attribute)

            self.connect(attribute, callback)

            # Cause update
            if attribute in SIGNALS.keys():
                self.old[SIGNALS[attribute]] = None
            else:
                self.old[attribute] = None

            if print_info:
                log.info('"{}" connected to "stat.{}" value changed' \
                         .format(str(callback.__name__), attribute))

        else:
            log.warning('linuxcnc.stat does not have attribute "{}"'.format(attribute))

    def periodic(self):
        try:
            self.stat.poll()

            for attribute in self.registry:
                old = self.old[attribute]
                new = getattr(self.stat, attribute)
                if old != new:
                    self.old[attribute] = new
                    self.emit(attribute, new)

            # Always update joint/axis positions
            self._update_axis_positions()
            self._update_joint_positions()

        except Exception as e:
            log.exception(e)

        return True

    def _update_task_state(self, widget, task_state):
        state_str = STATES.get(task_state, 'UNKNOWN')
        log.debug("Machine state: {0}".format(state_str))

    def _update_task_mode(self, widget, task_mode):
        mode_str = MODES.get(task_mode, 'UNKNOWN')
        log.debug("Machine mode: {0}".format(mode_str))

    def _update_interp_state(self, widget, interp_state):
        interp_str = INTERP.get(interp_state, 'UNKNOWN')
        log.debug("Interp state: {0}".format(interp_str))

    def _update_motion_mode(self, widget, motion_mode):
        motion_str = MOTION.get(motion_mode, 'UNKNOWN')
        log.debug("Motion mode: {0}".format(motion_str))

    def _update_work_corordinate(self, widget, g5x_index):
        work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
        work_cord_str = work_cords[g5x_index]
        log.debug("Work coord: {}".format(work_cord_str))

    def _update_active_gcodes(self, widget, gcodes):
        formated_gcodes = []
        for gcode in sorted(gcodes[1:]):
            if gcode == -1:
                continue
            if gcode % 10 == 0:
                formated_gcodes.append("G{0}".format(gcode / 10))
            else:
                formated_gcodes.append("G{0}.{1}".format(gcode / 10, gcode % 10))
        self.emit('formated-gcodes', formated_gcodes)

    def _update_active_mcodes(self, widget, mcodes):
        formated_mcodes = []
        for mcode in sorted(mcodes[1:]):
            if mcode == -1:
                continue
            formated_mcodes.append("M{0}".format(mcode))
        self.emit('formated-mcodes', formated_mcodes)

    def _update_file(self, widget, file):
        if self.stat.interp_state == linuxcnc.INTERP_IDLE \
                and self.stat.call_level == 0:
            self.emit('file-loaded', file)
            log.debug('File loaded: "{}"'.format(file))

    def _update_axis_list(self, widget, axis_mask):
        mask = '{0:09b}'.format(axis_mask)

        self.axis_list = []
        for anum, enabled in enumerate(mask[::-1]):
            if enabled == '1':
                self.axis_list.append(anum)

    def _update_axis_positions(self):

        if self.report_actual_position:
            pos = self.stat.actual_position
        else:
            pos = self.stat.position

        dtg = self.stat.dtg
        g5x_offset = self.stat.g5x_offset
        g92_offset = self.stat.g92_offset
        tool_offset = self.stat.tool_offset

        rel = [0] * 9
        for axis in self.axis_list:
            rel[axis] = pos[axis] - g5x_offset[axis] - tool_offset[axis]

        if self.stat.rotation_xy != 0:
            t = math.radians(-self.stat.rotation_xy)
            xr = rel[0] * math.cos(t) - rel[1] * math.sin(t)
            yr = rel[0] * math.sin(t) + rel[1] * math.cos(t)
            rel[0] = xr
            rel[1] = yr

        for axis in self.axis_list:
            rel[axis] -= g92_offset[axis]

        self.emit('axis-positions', pos, tuple(rel), tuple(dtg))

    def _update_joint_positions(self):

        if self.report_actual_position:
            pos = self.stat.joint_actual_position
        else:
            pos = self.stat.joint_position

        self.emit('joint-positions', pos)
