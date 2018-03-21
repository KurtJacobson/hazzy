#!/usr/bin/env python
#  -*- coding: UTF-8 -*-

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

import os
import json

from linuxcnc import stat
from linuxcnc import error

from linuxcnc import command

from linuxcnc import (
    STATE_ESTOP,
    STATE_ESTOP_RESET,
    STATE_ON,
    STATE_OFF,
    MODE_MANUAL,
    MODE_AUTO,
    MODE_MDI,
    INTERP_WAITING,
    INTERP_READING,
    INTERP_PAUSED,
    INTERP_IDLE,
    TRAJ_MODE_COORD,
    TRAJ_MODE_FREE,
    TRAJ_MODE_TELEOP)

PYDIR = os.path.join(os.path.dirname(__file__))

# from utilities import logger
# from utilities import notifications

# log = logger.get(__name__)

try:
    from flask import Flask, request, jsonify
    from flask_restful import Resource, Api
except ValueError as e:
    # log.exception(e)
    msg = "You don't seem to have Flask installed."
    # notifications.show_error(msg, summary='Import Error!', timeout=0)
    raise ImportError('Flask is not installed or cannot be imported')

STATES = {
    STATE_ESTOP: 'ESTOP',
    STATE_ESTOP_RESET: 'RESET',
    STATE_ON: 'ON',
    STATE_OFF: 'OFF'
}

MODES = {
    MODE_MANUAL: 'MAN',
    MODE_AUTO: 'AUTO',
    MODE_MDI: 'MDI'
}

INTERP = {
    INTERP_WAITING: 'WAIT',
    INTERP_READING: 'READ',
    INTERP_PAUSED: 'PAUSED',
    INTERP_IDLE: 'IDLE'
}

MOTION = {
    TRAJ_MODE_COORD: 'COORD',
    TRAJ_MODE_FREE: 'FREE',
    TRAJ_MODE_TELEOP: 'TELEOP'
}

app = Flask("HAZZY")
api = Api(app)


class LcncStats(Resource):
    def __init__(self):
        super(LcncStats, self).__init__()
        self.stat = stat()
        """
        try:
            self.stat = stat()  # create a connection to the status channel
            self.stat.poll()  # get current values
        except error, detail:
            print "error", detail
        """

    def get(self):
        self.stat.poll()

        a_dict = dict()
        for a in dir(self.stat):
            if not a.startswith('_') and not callable(getattr(self.stat, a)):
                val = getattr(self.stat, a)
                jdic = jsonify(val)

        return jdic


api.add_resource(LcncStats, '/stats')

if __name__ == '__main__':
    app.run(port='5002')
