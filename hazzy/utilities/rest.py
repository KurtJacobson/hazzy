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

import linuxcnc

from flask import Flask, request
from flask_restful import Resource, Api
from json import dumps

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

app = Flask("HAZZY")
api = Api(app)


class Stats(Resource):
    def __init__(self):
        super(Stats, self).__init__()
        self.stat = linuxcnc.stat()

    def get(self):
        self.stat.poll()
        att_list = list()
        for att in dir(self.stat):
            att_list.append(att)
        return att_list


api.add_resource(Stats, '/stats')  # Route_1

if __name__ == '__main__':
    app.run(port='5002')
