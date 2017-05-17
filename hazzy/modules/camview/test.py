#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
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

import gobject
import gtk
import gio
import sys
import os
import shutil

from video import VideoDev

pydir = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(pydir, 'ui')


class VideoStream(gobject.GObject):
    __gtype_name__ = 'CamView'
    __gproperties__ = {
        'camera': (gobject.TYPE_INT, 'Camera Number', 'if you have several cameras, select the one to use',
                   0, 8, 0, gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'draw_color': (gtk.gdk.Color.__gtype__, 'draw color', 'Sets the color of the drawn lines and circles',
                       gobject.PARAM_READWRITE),
        'frame_width': (gobject.TYPE_INT, 'Width of captured frame',
                        'The width of the captured frame, see your camera settings for supported values',
                        320, 2560, 640, gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'frame_height': (gobject.TYPE_INT, 'Height of captured frame',
                         'The height of the captured frame, see your camera settings for supported values',
                         240, 1920, 480, gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'circle_size': (gobject.TYPE_INT, 'Circle Size', 'The size of the largest circle',
                        8, 1000, 150, gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'number_of_circles': (gobject.TYPE_INT, 'Number Of Circles', 'The number of circles to be drawn',
                              1, 25, 5, gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'autosize': (
            gobject.TYPE_BOOLEAN, 'Autosize Image', 'If checked the image will be autosized to fit best the place',
            False, gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'cam_settings': (gobject.TYPE_STRING, 'settings', 'Sets special camera options with a valid v4l2-ctl command',
                         "", gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),

    }
    __gproperties = __gproperties__

    __gsignals__ = {
        'clicked': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)),
        'exit': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):

        gobject.GObject.__init__(self)

        # Glade setup
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, "video_stream.glade"))
        self.builder.connect_signals(self)

        self.video_tab = self.builder.get_object('VideoNoteBook')

        video_device = VideoDev()
        self.frame = video_device.get_frame()
        self.img_pixbuf = gtk.gdk.pixbuf_new_from_array(self.frame, gtk.gdk.COLORSPACE_RGB, 8)

        self.video_tab.set_from_pixbuff(self.img_pixbuf)


def main():
    stream = VideoStream()
    window = gtk.Window()
    window.add(stream.video_tab)
    window.show_all()
    gtk.main()

if __name__ == "__main__":
    main()
