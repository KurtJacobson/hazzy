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

import threading

from video import VideoDev
from stream import HttpServer
from gui import CamViewer


class ControlThread(threading.Thread):
    def __init__(self, thread_id, name, counter, callback, args=None):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.counter = counter
        self.callback = callback
        self.args = args

    def run(self):
        self.callback.run()


def main():

    http = True
    gui = True

    video_device = VideoDev(videodevice=0, frame_width=640, frame_height=480)
    video_thread = ControlThread(1, "VideoThread", 1, video_device)
    video_thread.start()

    if http:
        video_streamer = HttpServer("HAZZY stream", '0.0.0.0', 8080, video_device.get_jpeg_frame)
        stream_thread = ControlThread(1, "StreamThread", 1, video_streamer)
        stream_thread.start()

    if gui:
        video_new_gui = CamViewer(video_device)
        video_new_gui.run()

if __name__ == '__main__':
    main()
