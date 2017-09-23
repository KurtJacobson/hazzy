#!/usr/bin/env python

from utilities import ini_info

# Setup logging
from utilities import logger
log = logger.get(__name__)

AXIS_LETTERS = 'xyzabcuvw'

num_axes = 0           # Total number of Axes
num_joints = 0         # Total number of Joints
coordinates = []       # [TRAJ] COORDINATES
axis_letter_list = []  # Axes letters [X, Y, Z, B]
joint_axis_dict = {}   # Joint:Axis correspondence {0:0, 1:1, 2:2, 3:4}

def init():
    _get_axis_list()


def _get_axis_list():

    global coordinates, num_joints, axis_letter_list, joint_axis_dict

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

    double_aletter = ""
    for aletter in AXIS_LETTERS:
        if coordinates.count(aletter) > 1:
            double_aletter += aletter
    if double_aletter != "":
        log.info("Machine appearers to be a gantry config having a double {0} axis"
              .format(double_aletter))

    aletter_jnum_dict = {}
    jnum_aletter_dict = {}
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

init()
