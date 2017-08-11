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


import linuxcnc
from gi.repository import GObject

import getiniinfo
import machineinfo


# Setup logging
import logger
log = logger.get("HAZZY.STATUS")


STATES = { linuxcnc.STATE_ESTOP:       'ESTOP'
         , linuxcnc.STATE_ESTOP_RESET: 'RESET'
         , linuxcnc.STATE_ON:          'ON'
         , linuxcnc.STATE_OFF:         'OFF'
         }

MODES  = { linuxcnc.MODE_MANUAL: 'MAN'
         , linuxcnc.MODE_AUTO:   'AUTO'
         , linuxcnc.MODE_MDI:    'MDI'
         }

INTERP = { linuxcnc.INTERP_WAITING: 'WAIT'
         , linuxcnc.INTERP_READING: 'READ'
         , linuxcnc.INTERP_PAUSED:  'PAUSED'
         , linuxcnc.INTERP_IDLE:    'IDLE'
         }

MOTION = { linuxcnc.TRAJ_MODE_COORD:  'COORD'
         , linuxcnc.TRAJ_MODE_FREE:   'FREE'
         , linuxcnc.TRAJ_MODE_TELEOP: 'TELEOP'
         }


def singleton(cls):
    return cls()

@singleton
class Status(GObject.GObject):
    __gtype_name__ = 'Status'
    __gsignals__ = {
        'task_state_changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'task_mode_changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'interp_state_changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'motion_mode_changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),

        'work-cord-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'metric-mode-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        'active-codes-changed': (GObject.SignalFlags.RUN_FIRST, None, (object, object)),

        'update-joint-positions': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'update-axis-positions': (GObject.SignalFlags.RUN_FIRST, None, (object, object, object))
    }



    def __init__(self, stat=None):

        GObject.GObject.__init__(self)

        self.stat = stat or linuxcnc.stat()
        self.error = linuxcnc.error_channel()


        # Get INI settings
        iniinfo = getiniinfo.GetIniInfo
        self.report_actual_position = False # iniinfo.get_position_feedback_actual()

        self.machineinfo = machineinfo.MachineInfo

        self.task_state = None
        self.task_mode = None
        self.interp_state = None
        self.motion_mode = None

        self.g5x_index = None
        self.program_units = None
        self.gcodes = None
        self.mcodes = None
        self.formated_gcodes = None
        self.formated_mcodes = None

        self.tool_in_spindle = None
        self.spindle_brake = None
        self.spindle_enabled = None
        self.spindle_override_enabled = None
        self.spindle_speed = None
        self.spindle_override = None

        self.registry = []
        self.old = {}


        self.tool_in_spindle = None

        GObject.timeout_add(50, self.periodic)


    # This allows monitoring any of the linuxcnc.stat attributes
    # and connecting a callback for a value change
    def monitor(self, attribute, callback):

        if attribute not in GObject.signal_list_names(Status) \
            and attribute not in self.registry:

            GObject.signal_new(attribute, self, GObject.SignalFlags.RUN_FIRST, None, (object,))
            self.registry.append(attribute)
            self.old[attribute] = None

        self.connect(attribute, callback)
        log.info('"{}" connected to "stat.{}" value changed' \
            .format(str(callback.__name__), attribute))


    def periodic(self):
        try:
            self.stat.poll()
            self.update()
        except Exception as e:
            log.exception(e)
        return True


    def update(self):

        for attribute in self.registry:
            old = self.old[attribute]
            new = getattr(self.stat, attribute)
            if old != new:
                self.old[attribute] = new
                self.emit(attribute, new)
                #log.debug('"{}" changed from "{}" to "{}"'.format(attribute, old, new))

        # Current axis possitions
        pos, rel, dtg = self._get_axis_position()
        self.emit('update-axis-positions', pos, rel, dtg)

        # Current joint possitions
        self.emit('update-joint-positions', self._get_joint_position())


        if self.task_state != self.stat.task_state:
            self.task_state = self.stat.task_state
            self.emit('task-state-changed', STATES.get(self.task_state, 'UNKNOWN'))
            log.debug("Machine is in state: {0}".format(STATES.get(self.task_state, 'UNKNOWN')))


        if self.task_mode != self.stat.task_mode:
            self.task_mode = self.stat.task_mode
            self.emit('task-mode-changed', MODES.get(self.task_mode, 'UNKNOWN'))
            log.debug("Machine is in mode: {0}".format(MODES.get(self.task_mode, 'UNKNOWN')))


        if self.interp_state != self.stat.interp_state:
            self.interp_state = self.stat.interp_state
            self.emit('interp-state-changed', INTERP.get(self.interp_state, 'UNKNOWN'))
            log.debug("Interpreter is in state: {0}".format(INTERP.get(self.interp_state, 'UNKNOWN')))


        if self.motion_mode != self.stat.motion_mode:
            self.motion_mode = self.stat.motion_mode
            self.emit('motion-mode-changed', MOTION.get(self.motion_mode, 'UNKNOWN'))
            log.debug("Machine is in mode: {0}".format(MOTION.get(self.motion_mode, 'UNKNOWN')))


        if self.g5x_index != self.stat.g5x_index:
            self.g5x_index = self.stat.g5x_index
            work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
            self.emit('work-cord-changed', work_cords[self.g5x_index])
            log.debug("Work coordinate system: {}".format(work_cords[self.g5x_index]))


        # self.stat.program_units returns 1 for inch, 2 for mm and 3 for cm
        if self.program_units != self.stat.program_units:
            self.program_units = self.stat.program_units
            self.emit('metric-mode-changed', self.program_units != 1)
            log.debug("G21 active: {}".format(str(self.program_units != 1)))


        if self.gcodes != self.stat.gcodes or self.mcodes != self.stat.mcodes:
            gcodes, mcodes = self._get_active_codes()
            self.emit('active-codes-changed', gcodes, mcodes)



    def _get_axis_position(self):

        if self.report_actual_position:
            pos = self.stat.actual_position
        else:
            pos = self.stat.position

        dtg = self.stat.dtg
        g5x_offset = self.stat.g5x_offset
        g92_offset = self.stat.g92_offset
        tool_offset = self.stat.tool_offset

        rel = [0]*9
        for axis in self.machineinfo.axis_number_list:
            rel[axis] = pos[axis] - g5x_offset[axis] - tool_offset[axis]

        if self.stat.rotation_xy != 0:
            t = math.radians(-self.stat.rotation_xy)
            xr = rel[0] * math.cos(t) - rel[1] * math.sin(t)
            yr = rel[0] * math.sin(t) + rel[1] * math.cos(t)
            rel[0] = xr
            rel[1] = yr

        for axis in self.machineinfo.axis_number_list:
            rel[axis] -= g92_offset[axis]

        return pos, tuple(rel), tuple(dtg)


    def _get_joint_position(self):
        if self.report_actual_position:
            pos = self.stat.joint_actual_position
        else:
            pos = self.stat.joint_position
        return pos


    def _get_active_codes(self):

            self.gcodes = self.stat.gcodes
            self.mcodes = self.stat.mcodes

            gcodes = []
            for gcode in sorted(self.gcodes[1:]):
                if gcode == -1:
                    continue
                if gcode % 10 == 0:
                    gcodes.append("G{0}".format(gcode / 10))
                else:
                    gcodes.append("G{0}.{1}".format(gcode / 10, gcode % 10))

            mcodes = []
            for mcode in sorted(self.mcodes[1:]):
                if mcode == -1: 
                    continue
                mcodes.append("M{0}".format(mcode))

            self.formated_gcodes = gcodes
            self.formated_mcodes = mcodes

            return gcodes, mcodes

