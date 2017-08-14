#!/usr/bin/env python


#   This class is used to get information from the machines INI file.
#   It does some sanity cheking and returns valid values. If an entry
#   does not exist it may return a default value.


#   Copyright (c) 2017 Kurt Jacobson
#     <kurtjacobson@bellsouth.net>
#
#   This file is part of Hazzy.
#   It is a slightly modified version of a class from Gmoccapy
#   Original Author: Norbert Schechner
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


from linuxcnc import ini

import os
import sys

from hazzy.utilities import logger

log = logger.get("HAZZY.GETINI")

CONFIGPATH = os.environ.get('CONFIG_DIR', None)
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.join(PYDIR, '../..')


def singleton(cls):
    return cls()

@singleton
class GetIniInfo:

    def __init__(self):
        inipath = os.environ["INI_FILE_NAME"]
        self.inifile = ini(inipath)
        if not self.inifile:
            log.error("No INI File given!")
            sys.exit()

    def get_cycle_time(self):
        temp = self.inifile.find("DISPLAY", "CYCLE_TIME")
        try:
            return int(temp)
        except:
            log.info("Missing entry [DISPLAY] CYCLE_TIME in INI file. Using 50ms")
            return 50

    def get_postgui_halfile(self):
        postgui_halfile = self.inifile.find("HAL", "POSTGUI_HALFILE")
        if not postgui_halfile:
            postgui_halfile = None
        return postgui_halfile

    def get_preference_file_path(self):
        # we get the preference file, if there is none given in the INI
        # we use hazzy.pref in the config dir
        temp = self.inifile.find("DISPLAY", "PREFERENCE_FILE_PATH")
        if not temp:
            machinename = self.inifile.find("EMC", "MACHINE")
            if not machinename:
                temp = os.path.join(CONFIGPATH, "hazzy.pref")
            else:
                machinename = machinename.replace(" ", "_")
                temp = os.path.join(CONFIGPATH, "%s.pref" % machinename)
        log.info("Preference file path: %s" % temp)
        return temp

    def get_log_file_path(self):
        # we get the log file, if there is none given in the INI
        # we use hazzy.log in the config dir
        temp = self.inifile.find("DISPLAY", "LOG_FILE_PATH")
        if not temp:
            machinename = self.inifile.find("EMC", "MACHINE")
            if not machinename:
                temp = os.path.join(CONFIGPATH, "hazzy.log")
            else:
                machinename = machinename.replace(" ", "_")
                temp = os.path.join(CONFIGPATH, "%s.log" % machinename)
        log.info("Log file path: %s" % temp)
        return temp

    def get_open_file(self):
        temp = self.inifile.find("DISPLAY", "OPEN_FILE")
        if not temp:
            temp = os.path.join(MAINDIR, "sim.hazzy/example_gcode/hazzy.ngc")
        if not os.path.exists(temp):
            log.warning("Path given in [DISPLY] OPEN_FILE in INI is not valid")
            return
        return temp

    def get_coordinates(self):
        temp = self.inifile.find("TRAJ", "COORDINATES")
        # Get rid of any spaces
        temp = temp.replace(' ','')

        if not temp:
            log.warning("No coordinates entry found in [TRAJ] of INI file, using XYZ")
            temp = "XYZ"
        return temp.upper()

    def get_joints(self):
        temp = self.inifile.find("KINS", "JOINTS")
        if not temp:
            log.warning("No JOINTS entry found in [KINS] of INI file, using 3")
            return (3)
        return int(temp)

    def get_axis_list(self):
        axis_list = []
        coordinates = self.get_coordinates()
        for joint, axisletter in enumerate(coordinates):
            if axisletter in axis_list:
                continue
            axis_list.append(axisletter)
        return axis_list

    def get_machine_metric(self):
        temp = self.inifile.find("TRAJ", "LINEAR_UNITS")
        if not temp:
            # Then get the X axis units
            temp = self.inifile.find("AXIS_X", "UNITS")
        if temp=="mm" or temp=="metric" or temp == "1.0":
            return True
        else:
            return False

    def get_no_force_homing(self):
        temp = self.inifile.find("TRAJ", "NO_FORCE_HOMING")
        if not temp or temp == "0":
            return False
        return True

    def get_position_feedback_actual(self):
        temp = self.inifile.find("DISPLAY", "POSITION_FEEDBACK")
        if not temp or temp == "0":
            return True
        if temp.lower() == "actual":
            return True
        else:
            return False

    def get_lathe(self):
        temp = self.inifile.find("DISPLAY", "LATHE")
        if not temp or temp == "0":
            return False
        return True

    def get_backtool_lathe(self):
        temp = self.inifile.find("DISPLAY", "BACK_TOOL_LATHE")
        if not temp or temp == "0":
            return False
        return True

    def get_jog_vel(self):
        # get default jog velocity
        # must convert from INI's units per second to hazzys's units per minute
        temp = self.inifile.find("DISPLAY", "DEFAULT_LINEAR_VELOCITY")
        if not temp:
            temp = 3.0
        return float(temp) * 60

    def get_max_jog_vel(self):
        # get max jog velocity
        # must convert from INI's units per second to hazzys's units per minute
        temp = self.inifile.find("DISPLAY", "MAX_LINEAR_VELOCITY")
        if not temp:
            temp = 10.0
        return float(temp) * 60

    # ToDo : This may not be needed, as it could be recieved from linuxcnc.stat
    def get_max_velocity(self):
        # max velocity settings: more then one place to check
        # This is the maximum velocity of the machine
        temp = self.inifile.find("TRAJ", "MAX_VELOCITY")
        if  temp == None:
            log.warning("No MAX_VELOCITY found in [TRAJ] of INI file. Using 15ipm")
            temp = 15.0
        return float(temp) * 60

    def get_default_spindle_speed(self):
        # check for default spindle speed settings
        temp = self.inifile.find("DISPLAY", "DEFAULT_SPINDLE_SPEED")
        if not temp:
            temp = 300
            log.warning("No DEFAULT_SPINDLE_SPEED entry found in [DISPLAY] of INI file. Using 300rpm")
        return float(temp)

    def get_max_spindle_override(self):
        # check for override settings
        temp = self.inifile.find("DISPLAY", "MAX_SPINDLE_OVERRIDE")
        if not temp:
            temp = 1.0
            log.warning("No MAX_SPINDLE_OVERRIDE entry found in [DISPLAY] of INI file. Using 1.0")
        return float(temp)

    def get_min_spindle_override(self):
        temp = self.inifile.find("DISPLAY", "MIN_SPINDLE_OVERRIDE")
        if not temp:
            temp = 0.1
            log.warning("No MIN_SPINDLE_OVERRIDE entry found in [DISPLAY] of INI file. Using 0.1")
        return float(temp)

    def get_max_feed_override(self):
        temp = self.inifile.find("DISPLAY", "MAX_FEED_OVERRIDE")
        if not temp:
            temp = 1.0
            log.warning("No MAX_FEED_OVERRIDE entry found in [DISPLAY] of INI file. Using 1.0")
        return float(temp)

    def get_embedded_tabs(self):
        # Check INI file for embed commands
        # NAME is used as the tab label if a notebook is used
        # LOCATION is the widgets name from the gladefile.
        # COMMAND is the actual program command
        # if no location is specified the main notebook is used

        tab_names = self.inifile.findall("DISPLAY", "EMBED_TAB_NAME")
        tab_location = self.inifile.findall("DISPLAY", "EMBED_TAB_LOCATION")
        tab_cmd = self.inifile.findall("DISPLAY", "EMBED_TAB_COMMAND")

        if len(tab_names) != len(tab_cmd):
            return False, False, False
        if len(tab_location) != len(tab_names):
            for num, i in enumerate(tab_names):
                try:
                    if tab_location[num]:
                        continue
                except:
                    tab_location.append("notebook_mode")
        return tab_names, tab_location, tab_cmd

    def get_parameter_file(self):
        temp = self.inifile.find("RS274NGC", "PARAMETER_FILE")
        if not temp:
            return False
        return temp

    def get_program_prefix(self):
        # and we want to set the default path
        default_path = self.inifile.find("DISPLAY", "PROGRAM_PREFIX")
        if not default_path:
            log.warning("Path %s from DISPLAY , PROGRAM_PREFIX does not exist" % default_path)
            log.info("Trying default path...")
            default_path = "~/linuxcnc/nc_files/"
            if not os.path.exists(os.path.expanduser(default_path)):
                log.warning("Default path to ~/linuxcnc/nc_files does not exist")
                log.info("setting home as path")
                default_path = os.path.expanduser("~/")
        return default_path

    def get_file_ext(self):
        file_ext = self.inifile.findall("FILTER", "PROGRAM_EXTENSION")
        if file_ext:
            ext_list = ["*.ngc"]
            for data in file_ext:
                raw_ext = data.split(",")
                for extension in raw_ext:
                    ext = extension.split()
                    ext_list.append(ext[0].replace(".", "*."))
        else:
            log.error("Error converting file extensions from [FILTER] PROGRAMM_PREFIX, using default '*.ngc'")
            ext_list = ["*.ngc"]
        return ext_list

    def get_increments(self):
        jog_increments = []
        increments = self.inifile.find("DISPLAY", "INCREMENTS")
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

    def get_tool_table(self):
        temp = self.inifile.find("EMCIO", "TOOL_TABLE")
        if not temp:
            return False
        return temp

    def get_tool_sensor_data(self):
        xpos = self.inifile.find("TOOLSENSOR", "X")
        ypos = self.inifile.find("TOOLSENSOR", "Y")
        zpos = self.inifile.find("TOOLSENSOR", "Z")
        maxprobe = self.inifile.find("TOOLSENSOR", "MAXPROBE")
        return xpos, ypos, zpos, maxprobe

    def get_macros(self):
        # lets look in the ini File, if there are any entries
        macros = self.inifile.findall("MACROS", "MACRO")
        # If there are no entries we will return False
        if not macros:
            return False

        # we need the subroutine paths to check where to search for the macro files
        subroutine_paths = self.get_subroutine_paths()
        if not subroutine_paths:
            return False

        # we do check, if the corresponding files to the macros do exist
        checked_macros =[]
        for macro in macros:
            found = False
            for path in subroutine_paths.split(":"):
                file = path + "/" + macro.split()[0] + ".ngc"
                if os.path.isfile(file):
                    checked_macros.append(macro)
                    found = True
                    break
            if not found: # report error!
                message = ("\n**** GMOCCAPY INFO ****\n")
                message += ("File %s of the macro %s could not be found ****\n" %((str(macro.split()[0]) + ".ngc"),[macro]))
                message += ("we searched in subdirectories: %s" %subroutine_paths.split(":"))
                print (message)

        return checked_macros

    def get_subroutine_paths(self):
        subroutines_paths = self.inifile.find("RS274NGC", "SUBROUTINE_PATH")
        if not subroutines_paths:
            log.info("No subroutine folder or program prefix given in ini file")
            subroutines_paths = self.get_program_prefix()
        if not subroutines_paths:
            return False
        return subroutines_paths

    def get_axis_2_min_limit(self):
        temp = self.inifile.find("AXIS_2", "MIN_LIMIT")
        if not temp:
            return False
        return float(temp)

    def get_RS274_start_code(self):
        temp = self.inifile.find("RS274NGC", "RS274NGC_STARTUP_CODE")
        if not temp:
            return False
        return  temp
