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

import os
import numpy as np
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk

from OpenGL.GLU import *
from OpenGL import GL as GL

from OpenGL.GL import shaders
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, \
                                                  glBindVertexArray

PYDIR = os.path.join(os.path.dirname(__file__))


VERTEX_SHADER = """
    #version 330
    in vec4 position;
    void main()
    {
        gl_Position = position;
    }"""

FRAGMENT_SHADER = """
    #version 330
    out vec4 fragColor;
    void main()
    {
        fragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
    """


class Gremlin3(Gtk.Box):

    title = 'Gremlin3'
    author = ''
    version = '0.1.0'
    date = '5/11/2017'
    description = 'Basic module skeleton'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self)

        screen = Gdk.Screen.get_default()
        visual = Gdk.Screen.get_rgba_visual(screen)

        Gtk.Widget.set_visual(self, visual)

        self.canvas = Gtk.GLArea()
        self.canvas.set_required_version(3, 3)

        print(self.test_features())

        # gl_area.connect('render', self.area_render)

        # self.pack_end(gl_area, True, True, 0)

    def area_render(self, gl_area, gl_context):
        print gl_area
        print gl_context
        return True

    def test_features(self):
        print('Testing features')
        print('glGenVertexArrays Available %s' % bool(glGenVertexArrays))
        print('Alpha Available %s' % bool(self.canvas.get_has_alpha()))
        print('Depth buffer Available %s' % bool(self.canvas.get_has_depth_buffer()))