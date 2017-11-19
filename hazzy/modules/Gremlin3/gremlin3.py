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
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.gl_area = GremlinGLArea(self)

        self.pack_start(self.gl_area, False, False, 0)
        self.show_all()


class GremlinGLArea(Gtk.GLArea):
    def __init__(self, parent):
        Gtk.GLArea.__init__(self)
        self.set_hexpand(True)

        self.parent = parent

        screen = Gdk.Screen.get_default()
        visual = Gdk.Screen.get_rgba_visual(screen)

        print('is composite %s' % Gdk.Screen.is_composited(screen))

        Gtk.Widget.set_visual(self.parent, visual)
        self.set_required_version(3, 3)
        self.test_features()

        self.vertices = [
            0.6, 0.6, 0.0, 1.0,
            -0.6, 0.6, 0.0, 1.0,
            0.0, -0.6, 0.0, 1.0]

        self.vertices = np.array(self.vertices, dtype=np.float32)

        # self.connect("resize", self.reshape_window)
        # self.connect("render", self.render)
        # self.connect("key-press-event", self.key_pressed)
        # self.connect("key-release-event", self.key_released)
        # self.connect("scroll-event", self.mouse_scroll)
        # self.connect("button-press-event", self.mouse_pressed)
        # self.connect("motion-notify-event", self.mouse_motion)
        # self.connect("button-release-event", self.mouse_released)
        self.grab_focus()
        self.set_events(self.get_events() | Gdk.EventMask.SCROLL_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK
                        | Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.KEY_RELEASE_MASK)

        self.connect('realize', self.on_configure_event)
        self.connect('render', self.on_draw)
        self.set_double_buffered(False)

    def test_features(self):
        print('Testing features')
        print('glGenVertexArrays Available {}'.format(bool(glGenVertexArrays)))
        print('Alpha Available {}'.format(bool(self.get_has_alpha())))
        print('Depth buffer Available {}'.format(bool(self.get_has_depth_buffer())))

    def on_configure_event(self, widget):
        print('realize event')
        widget.make_current()
        print(widget.get_error())

        vs = shaders.compileShader(VERTEX_SHADER, GL.GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, GL.GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)

        # Create a new Vertex Array Object
        self.vertex_array_object = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vertex_array_object)

        # Generate a new array buffers for our vertices
        self.vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vertex_buffer)

        # Get position variable form the shader and store
        self.position = GL.glGetAttribLocation(self.shader, 'position')
        GL.glEnableVertexAttribArray(self.position)

        # describe the data layout
        GL.glVertexAttribPointer(self.position, 4, GL.GL_FLOAT, False, 0, ctypes.c_void_p(0))

        # Copy data to the buffer
        GL.glBufferData(GL.GL_ARRAY_BUFFER, 48, self.vertices, GL.GL_STATIC_DRAW)

        # Unbind buffers once done
        GL.glBindVertexArray(0)
        GL.glDisableVertexAttribArray(self.position)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        return True

    def on_draw(self, widget, *args):
        print('render event')
        print('Error: {}'.format(widget.get_error()))

        self.width = 300
        self.height = 200

        # clear screen and select shader for drawing
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glUseProgram(self.shader)

        # bind and draw vertices
        GL.glBindVertexArray(self.vertex_array_object)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
        GL.glBindVertexArray(0)

        GL.glUseProgram(0)
        GL.glFlush()
        return True