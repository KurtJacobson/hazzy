#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#     <kurtjacobson@bellsouth.net>
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

# [SETTING PREFERENCE]
# self.prefs.setpref("section", "option", "value", type)
# self.prefs.setpref("DROs", "dec_places", 4 , int)

# [RETREVING PREFERENCE] 
# self.prefs.getpref("section", "option", "default_val", type)
# dro_places = self.prefs.getpref("DROs", "dec_places", 3, int)

# If the file specified by path does not exist it will be created using default values

import os
import ConfigParser
import logging

log = logging.getLogger("HAZZY.PREFS")

cp = ConfigParser.RawConfigParser
cp.optionxform = str  # Needed to maintain option case

def singleton(cls):
    return cls()

@singleton
class Preferences(cp):
    types = {
        bool: cp.getboolean,
        float: cp.getfloat,
        int: cp.getint,
        str: cp.get,
        repr: lambda self, section, option: eval(cp.get(self, section, option)),
    }

    def __init__(self, path = None):
        cp.__init__(self)

    def set_file_path(self, path):
        if not path:
            path = "~/.hazzy_preferences"
        self.fn = os.path.expanduser(path)    
        if not os.path.isfile(self.fn):
            log.info("No preference file found, creating one...")
            log.info("Preference file: {}".format(self.fn))
        self.read(self.fn)


    # Get the pref form the section
    def getpref(self, section, option, default_val = False, opt_type = bool):
        self.read(self.fn)
        rtn_type = self.types.get(opt_type)
        try:
            value = rtn_type(self, section, option)
        # If the section does not exist add it and the option
        except ConfigParser.NoSectionError:
            log.debug("[getpref] Adding missing section [%s]" % section)
            self.add_section(section)
            log.debug('[getpref] Adding missing option [%s] "%s"' % (section, option))
            self.set(section, option, default_val)
            self.write(open(self.fn, "w"))
            if type in(bool, float, int):
                value = type(default_val)
            else:
                value = default_val
        # If the option does not exist in the section add it
        except ConfigParser.NoOptionError:
            log.debug('[getpref] Adding missing option [%s] "%s"' % (section, option))
            self.set(section, option, default_val)
            self.write(open(self.fn, "w"))
            if type in(bool, float, int):
                value = type(default_val)
            else:
                value = default_val
        return value


    # Set the pref in the specified section, if not section add it
    def setpref(self, section, option, value, opt_type = bool):
        try:
            self.set(section, option, opt_type(value))
            self.write(open(self.fn, "w"))
        except ConfigParser.NoSectionError:
            log.debug('[setpref] Adding missing option [%s] "%s"' % (section, option))
            self.add_section(section)
            self.set(section, option, opt_type(value))
            self.write(open(self.fn, "w"))

