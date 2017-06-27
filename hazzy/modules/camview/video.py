# -*- coding: UTF-8 -*-

#   Copyright (c) 2017 Kurt Jacobson
#     <kurtjacobson@bellsouth.net>
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

import cv2

# check if opencv3 is used, so we will have to change attribut naming
from pkg_resources import parse_version

OPCV3 = parse_version(cv2.__version__) >= parse_version('3')


class VideoDev:
    def __init__(self, videodevice=0, frame_width=640, frame_height=480):
        # set the selected camera as video device
        self.videodevice = videodevice

        # set the correct camera as video device

        self.cam = cv2.VideoCapture(self.videodevice)

        # set the capture size
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.frame = self.cam.read()[1]

        self.jpeg_frame = cv2.imencode('.jpg', self.frame)[1].tostring()

        if OPCV3:
            self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cam.set(cv2.CAP_PROP_FPS, 30)
        else:
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cam.set(cv2.cv.CV_CAP_PROP_FPS, 30)

    def run(self):
        running = True
        while running:

            success, frame = self.cam.read()
            if success:
                self.frame = frame

            cv2.waitKey(60)

    def get_jpeg_frame(self):
        self.jpeg_frame = cv2.imencode('.jpg', self.frame)[1].tostring()
        return self.jpeg_frame
