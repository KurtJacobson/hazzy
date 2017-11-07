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
#   Does some magic with info gleaned from the INI file to determine the machine
#   confiuration. Mostly needed for gantry or non trivial kinematics machines.

# ToDo:
#   Should this become part of ini_info.py????

from utilities import ini_info
from utilities import logger

# Set up logging
log = logger.get(__name__)

AXIS_LETTERS = 'xyzabcuvw'

# These are useful
num_axes = 0           # Total number of Axes
num_joints = 0         # Total number of Joints
coordinates = []       # [TRAJ] COORDINATES
axis_letter_list = []  # Axes letters [X, Y, Z, B], no duplicates
joint_axis_dict = {}   # Joint:Axis correspondence {0:0, 1:1, 2:2, 3:4}

# These might be useful
double_aletter = ""
aletter_jnum_dict = {}
jnum_aletter_dict = {}

coordinates = ini_info.get_coordinates()
num_joints = ini_info.get_num_joints()

# Axis letter list (Ex. ['X', 'Y', 'Z', 'B'])
for joint, axis_letter in enumerate(coordinates):
    if axis_letter in axis_letter_list:
        continue
    axis_letter_list.append(axis_letter)

num_axes = len(axis_letter_list)

# Joint:Axis dict (Ex. {0:0, 1:1, 2:2, 3:4})
for jnum, aletter in enumerate(coordinates):
    anum = AXIS_LETTERS.index(aletter)
    joint_axis_dict[jnum] = anum

for aletter in AXIS_LETTERS:
    if coordinates.count(aletter) > 1:
        double_aletter += aletter
if double_aletter != "":
    log.info("Machine appearers to be a gantry config having a double {0} axis"
          .format(double_aletter))

if num_joints == len(coordinates):
    log.info("The machine has {0} axes and {1} joints".format(num_axes, num_joints))
    log.info("The Axis/Joint mapping is:")
    count = 0
    for jnum, aletter in enumerate(coordinates):
        if aletter in double_aletter:
            aletter = aletter + str(count)
            count += 1
        aletter_jnum_dict[aletter] = jnum
        jnum_aletter_dict[jnum] = aletter
        log.info("Axis {0} --> Joint {1}".format(aletter.upper(), jnum))
else:
    log.info("The number of joints ({0}) is not equal to the number of coordinates ({1})"
          .format(num_joints, len(coordinates)))
    log.info("It is highly recommended that you update your config.")
    log.info("Reverting to old style. This could result in incorrect behavior...")
    log.info("\nGuessing Axes/Joints mapping:")
    for jnum, aletter in enumerate(AXIS_LETTERS):
        if aletter in coordinates:
            aletter_jnum_dict[aletter] = jnum
            log.info("Axis {0} --> Joint {1}".format(aletter, jnum))
