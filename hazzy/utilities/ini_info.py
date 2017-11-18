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
#   This module is used to get information from the machine's INI file.
#   It does some sanity checking to ensure it returns valid values.
#   If an INI entry does not exist, it may return a default value.

import os
import sys

from linuxcnc import ini
from constants import Units

# Setup logging
from utilities import logger
log = logger.get(__name__)

CONFIG_DIR = os.environ.get('CONFIG_DIR', None)
PYDIR = os.path.abspath(os.path.dirname(__file__))

inipath = os.environ["INI_FILE_NAME"]
ini = ini(inipath)
if not ini:
    log.critical("Could not find INI file")
    sys.exit()

MACHINE_NAME = ini.find('EMC', 'MACHINE') or "hazzy"

def get_machine_name():
    return MACHINE_NAME

def get_log_file():
    temp = ini.find('DISPLAY', 'LOG_FILE')
    if not temp:
        path = os.path.expanduser('~/hazzy.log')
    elif temp.startswith('~'):
        path = os.path.expanduser(temp)
    elif not os.path.isabs(temp):
        path = os.path.join(CONFIG_DIR, temp)
    else:
        path = os.path.realpath(temp)
    return path

def get_preference_file():
    temp = ini.find('DISPLAY', 'PREFERENCE_FILE')
    if not temp:
        path = os.path.expanduser('~/hazzy.pref')
    elif temp.startswith('~'):
        path = os.path.expanduser(temp)
    elif not os.path.isabs(temp):
        path = os.path.join(CONFIG_DIR, temp)
    else:
        path = os.path.realpath(temp)
    return path

def get_xml_file():
    temp = ini.find('DISPLAY', 'XML_FILE')
    if not temp:
        path = os.path.expanduser('~/hazzy.xml')
    elif temp.startswith('~'):
        path = os.path.expanduser(temp)
    elif not os.path.isabs(temp):
        path = os.path.join(CONFIG_DIR, temp)
    else:
        path = os.path.realpath(temp)
    return path

def get_mdi_history_file():
    temp = ini.find('DISPLAY', 'MDI_HISTORY_FILE')
    if not temp:
        path = os.path.expanduser('~/.axis_mdi_history')
    elif temp.startswith('~'):
        path = os.path.expanduser(temp)
    elif not os.path.isabs(temp):
        path = os.path.join(CONFIG_DIR, temp)
    else:
        path = os.path.realpath(temp)
    return path

def get_coordinates():
    '''Returns [TRAJ] COORDINATES or xyz'''
    temp = ini.find('TRAJ', 'COORDINATES')
    temp = temp.replace(' ','')
    if not temp:
        log.warning("No [TRAJ] COORDINATES entry in INI, using XYZ")
        temp = "xyz"
    return temp.lower()

def get_num_joints():
    '''Returns value of [KINS] JOINTS or 3'''
    temp = ini.find('KINS', 'JOINTS')
    if not temp:
        log.warning("No [KINS] JOINTS entry in INI file, using 3")
        return (3)
    return int(temp)

def get_axis_list():
    '''Returns a list of the Cartesian axes.'''
    axis_list = []
    coordinates = get_coordinates()
    for axis_letter in coordinates:
        if axis_letter in axis_list:
            continue
        axis_list.append(axis_letter)
    return axis_list

def get_machine_units():
    temp = ini.find('TRAJ', 'LINEAR_UNITS')
    if not temp:
        # Then get the X axis units
        temp = ini.find('AXIS_X', 'UNITS')
    if temp in ['mm', 'metric']:
        return Units.MM
    else:
        return Units.IN

def get_no_force_homing():
    temp = ini.find('TRAJ', 'NO_FORCE_HOMING')
    if temp and temp == '1':
        return True
    return False

def get_position_feedback():
    temp = ini.find('DISPLAY', 'POSITION_FEEDBACK')
    if not temp or temp == "0":
        return True
    if temp.lower() == "actual":
        return True
    else:
        return False

def get_is_lathe():
    temp = ini.find('DISPLAY', 'LATHE')
    if not temp or temp == "0":
        return False
    return True

def is_backtool_lathe():
    temp = ini.find('DISPLAY', 'BACK_TOOL_LATHE')
    if not temp or temp == "0":
        return False
    return True

def get_jog_vel():
    # get default jog velocity
    # must convert from INI's units per second to hazzys's units per minute
    temp = ini.find('DISPLAY', 'DEFAULT_LINEAR_VELOCITY')
    if not temp:
        temp = 3.0
    return float(temp) * 60

def get_max_jog_vel():
    # get max jog velocity
    # must convert from INI's units per second to hazzy's units per minute
    temp = ini.find('DISPLAY', 'MAX_LINEAR_VELOCITY')
    if not temp:
        temp = 10.0
    return float(temp) * 60

# ToDo : This may not be needed, as it could be recieved from linuxcnc.stat
def get_max_velocity():
    # max velocity settings: more then one place to check
    # This is the maximum velocity of the machine
    temp = ini.find('TRAJ', 'MAX_VELOCITY')
    if  temp == None:
        log.warning("No MAX_VELOCITY found in [TRAJ] of INI file. Using 15ipm")
        temp = 15.0
    return float(temp) * 60

def get_default_spindle_speed():
    # check for default spindle speed settings
    temp = ini.find('DISPLAY', 'DEFAULT_SPINDLE_SPEED')
    if not temp:
        temp = 300
        log.warning("No DEFAULT_SPINDLE_SPEED entry found in [DISPLAY] of INI file. Using 300rpm")
    return float(temp)

def get_max_spindle_override():
    # check for override settings
    temp = ini.find('DISPLAY', 'MAX_SPINDLE_OVERRIDE')
    if not temp:
        temp = 1.0
        log.warning("No MAX_SPINDLE_OVERRIDE entry found in [DISPLAY] of INI file. Using 1.0")
    return float(temp)

def get_min_spindle_override():
    temp = ini.find('DISPLAY', 'MIN_SPINDLE_OVERRIDE')
    if not temp:
        temp = 0.1
        log.warning("No MIN_SPINDLE_OVERRIDE entry found in [DISPLAY] of INI file. Using 0.1")
    return float(temp)

def get_max_feed_override():
    temp = ini.find('DISPLAY', 'MAX_FEED_OVERRIDE')
    if not temp:
        temp = 1.0
        log.warning("No MAX_FEED_OVERRIDE entry found in [DISPLAY] of INI file. Using 1.0")
    return float(temp)

def get_parameter_file():
    temp = ini.find('RS274NGC', 'PARAMETER_FILE')
    if not temp:
        return False
    return temp

def get_program_prefix():
    path = ini.find('DISPLAY', 'PROGRAM_PREFIX')

    if path:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path
        else:
            log.warning("Path '{}' given in [DISPLAY] PROGRAM_PREFIX does not exist, "
            "trying '~/linuxcnc/nc_files'".format(path))

    path = os.path.expanduser("~/linuxcnc/nc_files")
    if os.path.exists(path):
        return path
    else:
        log.warning("Default path '~/linuxcnc/nc_files' does not exist, using '~/' as path")
        path = os.path.expanduser('~/')
        return path

def get_file_extentions():
    file_ext = ini.findall('FILTER', 'PROGRAM_EXTENSION')
    if file_ext:
        ext_list = ["*.ngc"]
        for data in file_ext:
            raw_ext = data.split(",")
            for extension in raw_ext:
                ext = extension.split()
                ext_list.append(ext[0].replace(".", "*."))
    else:
        log.error("Error converting file extensions in [FILTER] PROGRAM_EXTENSION, using default '*.ngc'")
        ext_list = ["*.ngc"]
    return ext_list

def get_increments():
    jog_increments = []
    increments = ini.find('DISPLAY', 'INCREMENTS')
    if increments:
        if "," in increments:
            for i in increments.split(","):
                jog_increments.append(i.strip())
        else:
            jog_increments = increments.split()
        jog_increments.insert(0, 0)
    else:
        jog_increments = [ "0", "1.000", "0.100", "0.010", "0.001" ]
        log.warning("No default jog increments entry found in [DISPLAY] of INI file")
    return jog_increments

def get_tool_table():
    temp = ini.find('EMCIO', 'TOOL_TABLE')
    if not temp:
        return False
    return temp

def get_subroutine_paths():
    subroutines_paths = ini.find('RS274NGC', 'SUBROUTINE_PATH')
    if not subroutines_paths:
        log.info("No subroutine folder or program prefix given in ini file")
        subroutines_paths = program_prefix()
    if not subroutines_paths:
        return False
    return subroutines_paths

def get_RS274_start_code():
    temp = ini.find('RS274NGC', 'RS274NGC_STARTUP_CODE')
    if not temp:
        return False
    return  temp

def get_startup_notification():
    return ini.find('DISPLAY', 'STARTUP_NOTIFICATION')

def get_startup_warning():
    return ini.find('DISPLAY', 'STARTUP_WARNING')
