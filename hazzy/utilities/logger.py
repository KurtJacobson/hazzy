#!/usr/bin/env python

#   Base logging module

#   Copyright (c) 2017 Kurt Jacobson
#        <kcjengr@gmail.com>
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

import os
import logging

from hazzy.utilities.colored_log import ColoredFormatter

PYDIR = os.path.dirname(os.path.realpath(__file__))
HAZZYDIR = os.path.dirname(PYDIR)

# TODO Get log file path from INI
log_file = os.path.join(HAZZYDIR, 'hazzy.log')


# Get logger for module with name 'name'
def get(name):
    return logging.getLogger(name)

# Set global logging level
def set_level(level):
    base_log.setLevel(getattr(logging, level))
    log.info('Base log level set to {}'.format(level))

# Create base logger
base_log = logging.getLogger("HAZZY")
base_log.setLevel(logging.DEBUG)

# Add console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
cf = ColoredFormatter("[%(name)s][%(levelname)s]  %(message)s (%(filename)s:%(lineno)d)")
ch.setFormatter(cf)
base_log.addHandler(ch)

# Add file handler 
# TODO add support for setting log file path
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
ff = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(ff)
base_log.addHandler(fh)

# Get logger for logger
log = get('HAZZY.LOGGER')
log.info('Logging to "{}"'.format(log_file))
