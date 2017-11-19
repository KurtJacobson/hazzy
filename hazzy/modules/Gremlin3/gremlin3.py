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

        self.canvas.set_has_depth_buffer(True)
        self.canvas.set_has_alpha(True)
        self.canvas.set_double_buffered(True)
        self.canvas.gl_programs = True

        self.canvas.connect("realize", self.initialize)
        self.canvas.connect("render", self.render)
        self.canvas.connect("resize", self.reshape)
        self.canvas.connect("key-press-event", self.key_pressed)
        self.canvas.connect("key-release-event", self.key_released)
        self.canvas.connect("button-press-event", self.mouse_pressed)
        self.canvas.connect("button-release-event", self.mouse_released)
        self.canvas.connect("motion-notify-event", self.mouse_motion)

        self.canvas.connect("scroll-event", self.mouse_scroll)
        self.pack_end(self.canvas, True, True, 0)

        self.grab_focus()
        self.set_events(self.get_events() | Gdk.EventMask.SCROLL_MASK
                        | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK
                        | Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.KEY_RELEASE_MASK)

        self.test_features()

    def initialize(self, widget):
        """ Enables the buffers and other charasteristics of the OpenGL context.
            sets the initial projection and view matrix

            self.flag -- Needed to only create one OpenGL program, otherwise a bunch of
                         programs will be created and use system resources. If the OpenGL
                         program will be changed change this value to True
        """
        pass

    def reshape(self, widget, width, height):
        """ Resizing function, takes the widht and height of the widget
            and modifies the view in the camera acording to the new values

            Keyword arguments:
            widget -- The widget that is performing resizing
            width -- Actual width of the window
            height -- Actual height of the window
        """
        w = float(width)
        h = float(height)
        # self.vm_widget.resize_window(w, h)

        self.queue_draw()

    def render(self, area, context):
        """ This is the function that will be called everytime the window
            needs to be re-drawed.
        """
        # print area
        # print context
        return True
        # self.vm_widget.render()

    def key_pressed(self, widget, event):
        """ The mouse_button function serves, as the names states, to catch
            events in the keyboard, e.g. letter 'l' pressed, 'backslash'
            pressed. Note that there is a difference between 'A' and 'a'.
            Here I use a specific handler for each key pressed after
            discarding the CONTROL, ALT and SHIFT keys pressed (usefull
            for customized actions) and maintained, i.e. it's the same as
            using Ctrl+Z to undo an action.
        """
        k_name = Gdk.keyval_name(event.keyval)
        print(k_name)

    def key_released(self, widget, event):
        """ Used to indicates a key has been released.
        """
        k_name = Gdk.keyval_name(event.keyval)
        print(k_name)

    def mouse_pressed(self, widget, event):
        """ Function doc
        """
        print(int(event.button), event.x, event.y)

    def mouse_released(self, widget, event):
        """ Function doc
        """
        # self.vm_widget.mouse_released(int(event.button), event.x, event.y)
        print(event, event.x, event.y)

    def mouse_motion(self, widget, event):
        """ Function doc
        """
        print(event.x, event.y)

    def mouse_scroll(self, widget, event):
        """ Function doc
        """
        if event.direction == Gdk.ScrollDirection.UP:
            print("UP")
        if event.direction == Gdk.ScrollDirection.DOWN:
            print("DOWN")

    def test_features(self):
        print('Testing features')
        print('glGenVertexArrays Available {}'.format(glGenVertexArrays))
        print('Alpha Available {}'.format(self.canvas.get_has_alpha()))
        print('Depth buffer Available {}'.format(self.canvas.get_has_depth_buffer()))