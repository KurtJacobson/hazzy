#!/usr/bin/python
# noqa: E402
import gi

gi.require_version('Gtk', '3.0')
import numpy as np
from gi.repository import Gtk, Gdk
from OpenGL.GLU import *
from OpenGL import GL as GL

from OpenGL.GL import shaders
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, \
    glBindVertexArray

# from numpy import array

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


class application_gui:
    """Tutorial 01 Create and destroy a window"""

    # glwrap = gtkglarea()
    def __init__(self):
        screen = Gdk.Screen.get_default()
        visual = Gdk.Screen.get_rgba_visual(screen)

        print('is composite %s' % Gdk.Screen.is_composited(screen))

        self.window = Gtk.Window()
        Gtk.Widget.set_visual(self.window, visual)
        self.canvas = Gtk.GLArea()
        self.canvas.set_required_version(3, 3)
        self.test_features()

        self.vertices = [
            0.6, 0.6, 0.0, 1.0,
            -0.6, 0.6, 0.0, 1.0,
            0.0, -0.6, 0.0, 1.0]

        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.canvas.connect('realize', self.on_configure_event)
        self.canvas.connect('render', self.on_draw)
        self.canvas.set_double_buffered(False)

        self.window.connect('delete_event', Gtk.main_quit)
        self.window.connect('destroy', lambda quit: Gtk.main_quit())

        self.window.add(self.canvas)
        self.window.show_all()

    def test_features(self):
        print('Testing features')
        print('glGenVertexArrays Available %s' % bool(glGenVertexArrays))
        print('Alpha Available %s' % bool(self.canvas.get_has_alpha()))
        print('Depth buffer Available %s' % bool(self.canvas.get_has_depth_buffer()))

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
        print(widget.get_error())

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


application = application_gui()
Gtk.main()
