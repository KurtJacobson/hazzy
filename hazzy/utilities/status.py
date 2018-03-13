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
#   emit GObject signals for changes to LinuxCNC status or joint attributes.

# ToDo:
#   Clean up and possibly rethink


import math
import linuxcnc
import time
import gi

from gi.repository import GObject
from gi.repository import GLib

from utilities import ini_info
from utilities import notifications

# Setup logging
from utilities import logger

log = logger.get(__name__)


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


# These signals should cause an update
# when they are connected to a callback
SIGNALS = {
    'formated-gcodes': 'gcodes',
    'formated-mcodes': 'mcodes',
    'file-loaded': 'file'
}

class Status(GObject.GObject):
    __gtype_name__ = 'Status'
    __gsignals__ = {
        'formated-gcodes': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'formated-mcodes': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'file-loaded': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'joint-positions': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'axis-positions': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'error': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, stat=None):
        GObject.GObject.__init__(self)

        self.signals = GObject.signal_list_names(self)

        self.stat = stat or linuxcnc.stat()
        self.error = linuxcnc.error_channel()

        self.report_actual_position = ini_info.get_position_feedback()
        axes = ini_info.get_axis_list()
        self.axis_list = ['xyzabcuvw'.index(axis) for axis in axes]
        self.num_joints = ini_info.get_num_joints()

        self.file = None

        self.registry = []
        self.old = {}

        self.old['joint'] = getattr(self.stat, 'joint')

        # Setup joint dict signals
        self.joint_keys = self.old['joint'][0].keys() # keys() is slow, but we only use it on init
        for key in self.joint_keys:
            key = 'joint-{}'.format(key)
            GObject.signal_new(key.replace('_', '-'), self, GObject.SignalFlags.RUN_FIRST, None, (int, object))

        self.max_time = 0
        self.counter = 0

        # Connect internally used signal callbacks
        self.on_changed('stat.gcodes', self._update_active_gcodes)
        self.on_changed('stat.mcodes', self._update_active_mcodes)
        self.on_changed('stat.file', self._update_file)

        GLib.timeout_add(50, self._periodic)

    # This allows monitoring any of the linuxcnc.stat attributes
    # and connecting a callback to be called on attribute value change
    def _connect_stat_callback(self, attribute, callback):

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

        else:
            log.error('linuxcnc.stat object has no attribute "{}"'.format(attribute))

    def _connect_joint_callback(self, attribute, callback):
        if attribute in self.joint_keys:
            sig_name = 'joint-{}'.format(attribute)
            self.connect(sig_name, callback)
        else:
            log.error('linuxcnc.stat.joint object has no attribute "{}"'.format(attribute))

    def on_changed(self, attribute, callback):
        kind, name = attribute.split('.')
        if kind == 'stat':
            self._connect_stat_callback(name, callback)
        elif kind == 'joint':
            self._connect_joint_callback(name, callback)


    def _periodic(self):
#        start_time = time.time()
        try:

            self.stat.poll()

            # Status updates
            for attribute in self.registry:
                old = self.old[attribute]

                new = getattr(self.stat, attribute)

                if old != new:
                    self.old[attribute] = new
                    self.emit(attribute, new)

            # Joint updates
            new = getattr(self.stat, 'joint')
            old = self.old['joint']
            self.old['joint'] = new

#            start = time.time()
            for joint in range(self.num_joints):
                if new[joint] != old[joint]:
                    #print '\nJoint {}'.format(joint)
                    changed_items = tuple(set(new[joint].items())-set(old[joint].items()))
                    for item in changed_items:
#                        print 'JOINT_{0} {1}: {2}'.format(joint, item[0], item[1])
                        key = 'joint-{}'.format(item[0].replace('_', '-'))
                        self.emit(key, joint, item[1])

#            print start - time.time()

#            # Always update joint/axis positions
            calc = time.time()
            self._update_axis_positions()
            self._update_joint_positions()
#            print 'Calc time: ', time.time() - calc

            # Check for errors
            error = self.error.poll()
            if error:
                self._on_error(error)

        except Exception as e:
            log.exception(e)

#        print 'Loop time: ', time.time() - start_time

        return True

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

        self.emit('axis-positions', tuple([pos, tuple(rel), tuple(dtg)]))

    def _update_joint_positions(self):

        if self.report_actual_position:
            pos = self.stat.joint_actual_position
        else:
            pos = self.stat.joint_position

        self.emit('joint-positions', pos)

    def _on_error(self, error):
        kind, msg = error

        if msg == "" or msg is None:
            msg = "Unknown error!"

        if kind == linuxcnc.NML_ERROR:
            notifications.show_error(msg, "NML_ERROR!", timeout=0)
            log.error("NML_ERROR: {}".format(msg))
        elif kind == linuxcnc.OPERATOR_ERROR:
            notifications.show_error(msg, "OPERATOR_ERROR!", timeout=0)
            log.error("OPERATOR_ERROR: {}".format(msg))
        elif kind == linuxcnc.NML_TEXT:
            notifications.show_info(msg, "NML_TEXT!", timeout=0)
            log.info("NML_TEXT: {}".format(msg))
        elif kind == linuxcnc.OPERATOR_TEXT:
            notifications.show_info(msg, "OPERATOR_TEXT!", timeout=0)
            log.info("OPERATOR_TEXT: {}".format(msg))
        elif kind == linuxcnc.NML_DISPLAY:
            notifications.show_info(msg, "NML_DISPLAY!", timeout=0)
            log.info("NML_DISPLAY: {}".format(msg))
        elif kind == linuxcnc.OPERATOR_DISPLAY:
            notifications.show_info(msg, "OPERATOR_DISPLAY!", timeout=0)
            log.info("OPERATOR_DISPLAY: {}".format(msg))

        else:
            notifications.show_error("UNKNOWN ERROR!", msg)
            log.error("UNKNOWN ERROR: {}".format(msg))

        # ToDo Set HAL error pin
#        self.emit('error', (kind, msg))


status = Status()

def on_changed(attribute, callback):
    status.on_changed(attribute, callback)

# These are used only for logging purposes
def _log_task_state(widget, task_state):
    state_str = STATES.get(task_state, 'UNKNOWN')
    log.debug("Machine state: {0}".format(state_str))

def _log_task_mode(widget, task_mode):
    mode_str = MODES.get(task_mode, 'UNKNOWN')
    log.debug("Machine mode: {0}".format(mode_str))

def _log_interp_state(widget, interp_state):
    interp_str = INTERP.get(interp_state, 'UNKNOWN')
    log.debug("Interp state: {0}".format(interp_str))

def _log_motion_mode(widget, motion_mode):
    motion_str = MOTION.get(motion_mode, 'UNKNOWN')
    log.debug("Motion mode: {0}".format(motion_str))

def _log_work_corordinate(widget, g5x_index):
    work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
    work_cord_str = work_cords[g5x_index]
    log.debug("Work coord: {}".format(work_cord_str))

# Connect signals to log callbacks
on_changed('stat.task_state', _log_task_state)
on_changed('stat.task_mode', _log_task_mode)
on_changed('stat.interp_state', _log_interp_state)
on_changed('stat.motion_mode', _log_motion_mode)
on_changed('stat.g5x_index', _log_work_corordinate)
