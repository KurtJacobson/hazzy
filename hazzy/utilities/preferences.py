#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#   It is a class from Gmoccapy that has been heavily modified to support sections.
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


#                   ***USEAGE***

# Setting Preference
#    set_pref("section", "option", "value", type)
#    set_pref("DROs", "dec_places", 4 , int)

# Getting Preference
#    get_pref("section", "option", "default_val", type)
#    dro_places = get_pref("DROs", "dec_places", 3, int)

import os
import ConfigParser

from utilities import ini_info

from utilities import logger
log = logger.get(__name__)


class Preferences(ConfigParser.RawConfigParser):

    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)

        self.types = {
            bool: self.getboolean,
            float: self.getfloat,
            int: self.getint,
            str: self.get,
            repr: lambda section, option: eval(self.get(section, option)),
        }

        self.optionxform = str  # Needed to maintain options case

        self.fn = ini_info.get_preference_file()
        if not os.path.isfile(self.fn):
            log.info("No preference file exists, creating: {}".format(self.fn))

        self.read(self.fn)

    def get_pref(self, section, option, default_val = False, opt_type = bool):
        rtn_type = self.types.get(opt_type)
        try:
            value = rtn_type(section, option)
            return value
        except ConfigParser.NoSectionError:
            # Add the section and the option
            log.debug("Adding missing section [{0}]".format(section))
            self.add_section(section)
            log.debug('Adding missing option [{0}] "{1}"'.format(section, option))
            self.set(section, option, default_val)
        except ConfigParser.NoOptionError:
            # Add the option
            log.debug('Adding missing option [{0}] "{1}"'.format(section, option))
            self.set(section, option, default_val)

        with open(self.fn, "w") as fh:
            self.write(fh)

        return default_val

    def set_pref(self, section, option, value, opt_type=bool):
        try:
            self.set(section, option, opt_type(value))
        except ConfigParser.NoSectionError:
            # Add the section and the option
            log.debug('Adding missing option [{0}] "{1}"'.format(section, option))
            self.add_section(section)
            self.set(section, option, opt_type(value))

        with open(self.fn, "w") as fh:
            self.write(fh)

prefs = Preferences()

def set_pref(section, option, value, opt_type=bool):
    prefs.set_pref(section, option, value, opt_type)

def get_pref(section, option, value, opt_type=bool):
    return prefs.get_pref(section, option, value, opt_type)
