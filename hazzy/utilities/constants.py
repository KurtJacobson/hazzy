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
#   Collection of constants.
#   Needs to be cleaned up. Get rid on INI reading, do that with ini_info.py


import os
from linuxcnc import ini

class MessageType(enumerate):
    INFO = 0
    WARNING = 1
    ERROR = 2

class Paths(enumerate):
    # Hazzy Paths
    HAZZYDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    MAINDIR = os.path.dirname(HAZZYDIR)

    UIDIR = os.path.join(HAZZYDIR, 'ui')
    MODULEDIR = os.path.join(HAZZYDIR, 'modules')
    STYLEDIR = os.path.join(HAZZYDIR, 'themes')

    # LinuxCNC Paths
    INI_FILE = os.environ['INI_FILE_NAME']
    CONFIGDIR = os.environ['CONFIG_DIR']
    NC_FILE_DIR = os.environ['LINUXCNC_NCFILES_DIR']
    TCLPATH = os.environ['LINUXCNC_TCL_DIR']
