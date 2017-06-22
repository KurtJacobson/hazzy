#!/usr/bin/env python
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

import gtk
import os
import time

pydir = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(pydir, "ui")


class CamViewer:

    def __init__(self, video_device):

        # Glade setup

        gladefile = os.path.join(UIDIR, 'gui.glade')

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("window1")
        self.video_frame = self.builder.get_object("image1")

        self.get_frame = video_device.get_jpeg_frame
        self.img_pixbuf = None

        self.running = False
        self.result = False

    def show_image(self, frame):

        try:

            loader = gtk.gdk.PixbufLoader('jpeg')
            loader.write(frame)
            loader.close()

            self.img_pixbuf = loader.get_pixbuf()

            self.video_frame.set_from_pixbuf(self.img_pixbuf)
            self.video_frame.show()

        except Exception as e:
            print(e)

    def run(self):
        """ Show the Dialog only if not already running """

        if not self.running:
            self.running = True
            self.window.show()
            while self.running:
                frame = self.get_frame()
                self.show_image(frame)

            self.running = False
