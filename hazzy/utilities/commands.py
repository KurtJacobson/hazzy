#!/usr/bin/env python

import linuxcnc

class Commands():
    def __init__(self):
        self.stat = linuxcnc.stat()
        self.command = linuxcnc.command()

    def estop(self):
        self.set_state(linuxcnc.STATE_ESTOP)

    def estop_reset(self):
        self.set_state(linuxcnc.STATE_ESTOP_RESET)

    def machine_off(self):
        self.set_state(linuxcnc.STATE_OFF)

    def machine_on(self):
        self.set_state(linuxcnc.STATE_ON)

    def mist_on(self):
        self.command.mist(1)

    def mist_off(self):
        self.command.mist(0)

    def flood_on(self):
        self.command.flood(1)

    def flood_off(self):
        self.command.flood(0)

    def set_mode(self, mode):
        self.stat.poll()
        if self.stat.task_mode == mode:
            return
        self.command.mode(mode)
        self.command.wait_complete()

    def set_state(self, state):
        self.stat.poll()
        if self.stat.state == state:
            return
        self.command.state(state)
        self.command.wait_complete()

    def set_motion_mode(self, mode):
        self.stat.poll()
        if self.stat.motion_mode == mode:
            return
        self.command.teleop_enable(0)
        self.command.traj_mode(mode)
        self.command.wait_complete()

    def issue_mdi(self, mdi_command):
        if self.set_mode(linuxcnc.MODE_MDI):
            log.info("Issuing MDI command: {}".format(mdi_command))
            self.command.mdi(mdi_command)

    def set_work_offset(self, axis, value):
        offset_command = 'G10 L20 P%d %s%.12f' % (self.stat.g5x_index, axis, value)
        self.issue_mdi(offset_command)
        self.set_mode(linuxcnc.MODE_MANUAL)

    def is_moving(self):
        '''Check if machine is moving due to MDI, program execution, etc.'''
        if self.stat.state == linuxcnc.RCS_EXEC:
            return True
        else:
            return self.stat.task_mode == linuxcnc.MODE_AUTO \
                and self.stat.interp_state != linuxcnc.INTERP_IDLE
