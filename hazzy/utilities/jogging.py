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
#   Basic keyboard jogging handlers

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

import linuxcnc

from utilities import preferences as prefs
from utilities.command import is_homed
from utilities import logger

log = logger.get(__name__)

stat = linuxcnc.stat()
command = linuxcnc.command()


KEYBINDINGS = {
    'Up'           : '+y',
    'Down'         : '-y',
    'Right'        : '+x',
    'Left'         : '-x',
    'Page_Up'      : '+z',
    'Page_Down'    : '-z',
    'bracketleft'  : '+b',
    'bracketright' : '-b'
}

is_pressed = {}

def on_key_press_event(widget, event):

    keyname = Gdk.keyval_name(event.keyval)

    if not keyname in KEYBINDINGS.keys():
        return False

    if is_pressed.get(keyname, False):
        return True

    is_pressed[keyname] = True

    if not prefs.get('JOGGING', 'USE_KEYBOARD', 'YES', bool):
        return

    stat.poll()
    if stat.task_mode != linuxcnc.MODE_MANUAL \
        or not stat.enabled \
        or not is_homed():
        return

    jog_start(KEYBINDINGS[keyname])
    is_pressed[keyname] = True
    return True

def on_key_release_event(widget, event):

    keyname = Gdk.keyval_name(event.keyval)
    is_pressed[keyname] = False

    stat.poll()
    if stat.task_mode != linuxcnc.MODE_MANUAL \
        or not stat.enabled \
        or not is_homed():
        return

    jog_stop(KEYBINDINGS[keyname])
    return True

def jog_start(axis):
    JOGMODE = 0
    dir = axis[0]
    vel = prefs.get("JOGGING", "VELOCITY", 1, int)
    axis_num = "xyzabcuvw".index(axis[1])
    log.debug("green$STARTED jogging {} axis".format(axis))
    command.jog(linuxcnc.JOG_CONTINUOUS, JOGMODE, axis_num, float('{}{}'.format(dir, vel)))

def jog_stop(axis):
    JOGMODE = 0
    axis_num = "xyzabcuvw".index(axis[1])
    log.debug("red$STOPED jogging {} axis".format(axis))
    command.jog(linuxcnc.JOG_STOP, JOGMODE, axis_num)
