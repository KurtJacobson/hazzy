#!/usr/bin/env python


import getiniinfo


# Setup logging
import logger
log = logger.get("HAZZY.MACHINEINFO")

AXIS_LETTERS = ['X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W']


def singleton(cls):
    return cls()

@singleton
class MachineInfo():

    def __init__(self):


        self.get_ini_info = getiniinfo.GetIniInfo

        self.num_axes = 0           # Total number of Cartesian axes
        self.num_joints = 0         # Total number of joints
        self.axis_letter_list = []  # Axes used in the machine [X, Y, Z, B]
        self.axis_number_list = []  # Corresponding axis numbers [0, 1, 2, 4]
        self.joint_axis_dict = {}   # Joint axis correspondence {0:0, 1:1, 2:2, 3:4}


        self._get_axis_list()


    def _get_axis_list(self):
        coordinates = self.get_ini_info.get_coordinates()
        self.num_joints = self.get_ini_info.get_joints()

        # Axis letter list (Ex. ['X', 'Y', 'Z', 'B'])
        for joint, axis_letter in enumerate(coordinates):
            if axis_letter in self.axis_letter_list:
                continue
            self.axis_letter_list.append(axis_letter)

        self.num_axes = len(self.axis_letter_list)

        # Axis number list (Ex. [0, 1, 2, 4])
        for axis in self.axis_letter_list:
            axis_number = AXIS_LETTERS.index(axis)
            self.axis_number_list.append(axis_number)

        # Joint:Axis dict (Ex. {0:0, 1:1, 2:2, 3:4})
        for jnum, aletter in enumerate(coordinates):
            anum = AXIS_LETTERS.index(aletter)
            self.joint_axis_dict[jnum] = anum

        double_aletter = ""
        for aletter in AXIS_LETTERS:
            if coordinates.count(aletter) > 1:
                double_aletter += aletter
        if double_aletter != "":
            log.info("Machine appearers to be a gantry config having a double {0} axis"
                  .format(double_aletter))

        self.aletter_jnum_dict = {}
        self.jnum_aletter_dict = {}
        if self.num_joints == len(coordinates):
            log.info("The machine has {0} axes and {1} joints".format(self.num_axes, self.num_joints))
            log.info("The Axis/Joint mapping is:")
            count = 0
            for jnum, aletter in enumerate(coordinates):
                if aletter in double_aletter:
                    aletter = aletter + str(count)
                    count += 1
                self.aletter_jnum_dict[aletter] = jnum
                self.jnum_aletter_dict[jnum] = aletter
                log.info("Axis {0} --> Joint {1}".format(aletter, jnum))
        else:
            log.info("The number of joints ({0}) is not equal to the number of coordinates ({1})"
                  .format(self.num_joints, len(coordinates)))
            log.info("It is highly recommended that you update your config.")
            log.info("Reverting to old style. This could result in incorrect behavior...")
            log.info("\nGuessing the Axes/Joints mapping is:")
            for jnum, aletter in enumerate(AXIS_LETTERS):
                if aletter in coordinates:
                    self.aletter_jnum_dict[aletter] = jnum
                    log.info("Axis {0} --> Joint {1}".format(aletter, jnum))
