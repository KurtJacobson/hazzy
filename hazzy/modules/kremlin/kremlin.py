#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#     <kurtjacobson@bellsouth.net>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.


# Temporary, for silly people who don't use an IDE
import os, sys

from vtk.vtkCommonCorePython import VTK_MAJOR_VERSION

PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)


import copy
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from vtk.vtkRenderingCorePython import vtkRenderWindow, vtkCamera
from vtk.vtkRenderingCorePython import vtkGenericRenderWindowInteractor
from vtk.vtkRenderingCorePython import vtkRenderer

from hazzy.modules.pygcode import Line as GLine
from hazzy.modules.pygcode import GCode
from hazzy.modules.pygcode import GCodeMotion
from hazzy.modules.pygcode import GCodeLinearMove
from hazzy.modules.pygcode import GCodeRapidMove
from hazzy.modules.pygcode import GCodeArcMove, GCodeArcMoveCW, GCodeArcMoveCCW
from hazzy.modules.pygcode import Machine

from hazzy.modules.kremlin.vtk_helper import FollowerTool, Cone, Line, Arc, Axes


class GtkVTKRenderWindowInteractor(Gtk.GLArea):
    """ Embeds a vtkRenderWindow into a pyGtk widget and uses
    vtkGenericRenderWindowInteractor for the event handling.  This
    class embeds the RenderWindow correctly.  A __getattr__ hook is
    provided that makes the class behave like a
    vtkGenericRenderWindowInteractor."""

    def __init__(self, *args):

        Gtk.GLArea.__init__(self)

        print("VTK VERSION : {0}".format(VTK_MAJOR_VERSION))

        self._render_window = vtkRenderWindow()

        self.camera = vtkCamera()
        self.camera.SetPosition(0, 0, 100)
        self.camera.SetFocalPoint(0, 0, 0)

        self._renderer = vtkRenderer()
        self._renderer.SetBackground(0, 0, 0)
        self._renderer.SetBackground2(0.1, 0.2, 0.4)
        self._renderer.SetGradientBackground(1)
        self._renderer.SetActiveCamera(self.camera)

        self._render_window.AddRenderer(self._renderer)

        # private attributes
        self.__Created = 0

        self._iren = vtkGenericRenderWindowInteractor()
        self._iren.SetRenderWindow(self._render_window)

        self._iren.AddObserver('CreateTimerEvent', self.create_timer)
        self._iren.AddObserver('DestroyTimerEvent', self.destroy_timer)

        self.connect_signals()

        # need this to be able to handle key_press events.
        self.set_can_focus(True)
        # default size
        self.set_usize(800, 600)


    def set_usize(self, w, h):
        self.set_size_request(w, h)
        self._render_window.SetSize(w, h)
        self._iren.SetSize(w, h)
        self._iren.ConfigureEvent()

    def connect_signals(self):
        self.connect('realize', self.on_realize)
        self.connect('render', self.on_render)
        self.connect('configure-event', self.on_configure)
        self.connect('button-press-event', self.on_button_down)
        self.connect('button-release-event', self.on_button_up)
        self.connect('scroll-event', self.on_scroll)
        self.connect('motion-notify-event', self.on_mouse_move)
        self.connect('enter-notify-event', self.on_enter)
        self.connect('leave-notify-event', self.on_leave)
        self.connect('key-press-event', self.on_key_press)
        self.connect('key-release-event', self.on_key_release)
        self.connect('scroll-event', self.on_scroll)
        self.connect('delete-event', self.on_destroy)

        self.add_events(Gdk.EventMask.EXPOSURE_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.SCROLL_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                        Gdk.EventMask.ENTER_NOTIFY_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK)

    def __getattr__(self, attr):
        """Makes the object behave like a
        vtkGenericRenderWindowInteractor"""
        if attr == '__vtk__':
            return lambda t=self._iren: t
        elif hasattr(self._iren, attr):
            return getattr(self._iren, attr)
        else:
            raise AttributeError("{0}  has no attribute named {1}".format(
                self.__class__.__name__, attr))

    def create_timer(self, obj, event):
        GLib.timeout_add(10, self._iren.TimerEvent)

    def destroy_timer(self, obj, event):
        """The timer is a one shot timer so will expire automatically."""
        return True

    def get_render_window(self):
        return self._render_window

    def get_renderer(self):
        return self._renderer

    def render(self):
        if self.__Created:
            self._render_window.Render()

    def on_realize(self, *args):
        if self.__Created == 0:
            # you can't get the xid without the window being realized.
            self.realize()
            win_id = str(self.get_window().get_xid())
            self._render_window.SetWindowInfo(win_id)
            self._iren.Initialize()
            self.__Created = 1
        return True

    def on_configure(self, wid, event=None):
        sz = self._render_window.GetSize()
        if (event.width != sz[0]) or (event.height != sz[1]):
            self._iren.SetSize(event.width, event.height)
            self._iren.ConfigureEvent()
        return True

    def on_render(self, *args):
        self.render()
        return True

    def on_destroy(self, event=None):
        self.hide()
        del self._render_window
        self.destroy()
        return True

    def _get_ctrl_shift(self, event):
        ctrl, shift = 0, 0
        if (event.state & Gdk.ModifierType.CONTROL_MASK) == Gdk.ModifierType.CONTROL_MASK:
            ctrl = 1
        if (event.state & Gdk.ModifierType.SHIFT_MASK) == Gdk.ModifierType.SHIFT_MASK:
            shift = 1
        return ctrl, shift

    def on_button_down(self, wid, event):
        """Mouse button pressed."""
        m = self.get_pointer()
        ctrl, shift = self._get_ctrl_shift(event)
        self._iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift, chr(0), 0, None)
        button = event.button
        if button == 3:
            self._iren.RightButtonPressEvent()
            return True
        elif button == 1:
            self._iren.LeftButtonPressEvent()
            return True
        elif button == 2:
            self._iren.MiddleButtonPressEvent()
            return True
        else:
            return False

    def on_button_up(self, wid, event):
        """Mouse button released."""
        m = self.get_pointer()
        ctrl, shift = self._get_ctrl_shift(event)
        self._iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift, chr(0), 0, None)
        button = event.button
        if button == 3:
            self._iren.RightButtonReleaseEvent()
            return True
        elif button == 1:
            self._iren.LeftButtonReleaseEvent()
            return True
        elif button == 2:
            self._iren.MiddleButtonReleaseEvent()
            return True

        return False

    def on_scroll(self, wid, event):
        """Mouse scroll wheel changed position"""
        if event.direction == Gdk.ScrollDirection.UP:
            self.camera.Zoom(1.5)
            self._render_window.Render()
            return True
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.camera.Zoom(.5)
            self._render_window.Render()
            return True
        else:
            return False

    def on_mouse_move(self, wid, event):
        """Mouse has moved."""
        m = self.get_pointer()
        ctrl, shift = self._get_ctrl_shift(event)
        self._iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift, chr(0), 0, None)
        self._iren.MouseMoveEvent()
        return True

    def on_enter(self, wid, event):
        """Entering the vtkRenderWindow."""
        self.grab_focus()
        m = self.get_pointer()
        ctrl, shift = self._get_ctrl_shift(event)
        self._iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift, chr(0), 0, None)
        self._iren.EnterEvent()
        return True

    def on_leave(self, wid, event):
        """Leaving the vtkRenderWindow."""
        m = self.get_pointer()
        ctrl, shift = self._get_ctrl_shift(event)
        self._iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift, chr(0), 0, None)
        self._iren.LeaveEvent()
        return True

    def on_key_press(self, wid, event):
        """Key pressed."""
        m = self.get_pointer()
        ctrl, shift = self._get_ctrl_shift(event)
        keycode, keysym = event.keyval, event.string
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)
        self._iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift, key, 0, keysym)
        self._iren.KeyPressEvent()
        self._iren.CharEvent()
        return True

    def on_key_release(self, wid, event):
        "Key released."
        m = self.get_pointer()
        ctrl, shift = self._get_ctrl_shift(event)
        keycode, keysym = event.keyval, event.string
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)
        self._iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift, key, 0, keysym)
        self._iren.KeyReleaseEvent()
        return True

    def add_actor(self, actor):
        ren = self.get_renderer()
        ren.AddActor(actor)


class Kremlin(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)

        self.vtk_window = GtkVTKRenderWindowInteractor()

        # self.vtk_window.SetDesiredUpdateRate(1000)
        self.vtk_window.set_usize(800, 600)
        self.pack_start(self.vtk_window, True, True, 0)

        self.vtk_window.show_all()
        self.show_all()

        # prevents 'q' from exiting the app.
        self.vtk_window.AddObserver('ExitEvent', lambda o, e, x=None: x)

        self.gcode_path = []

        self.tool = None

    def load_file(self, ngc_filename):
        buf_size = 65536
        with open(ngc_filename, 'r') as ngc_file:
            while True:
                lines = ngc_file.readlines(buf_size)
                if not lines:
                    break
                for line in lines:
                    gcode_line = GLine(str(line))
                    self.gcode_path.append(gcode_line)

    def draw_path(self):

        position = [0, 0, 0, None]
        prev_postion = [0, 0, 0, None]

        active_modal = None

        for i, line in enumerate(self.gcode_path):
            if line.block.gcodes:
                for code in line.block.gcodes:
                    active_modal = code
                    if prev_postion is not None:
                        if isinstance(code, GCodeLinearMove):
                            color = (1, 1, 1)

                            position = self.get_pos(line, position)

                            self.draw_line(prev_postion, position, color=color)

                        elif isinstance(code, GCodeRapidMove):
                            color = (1, 0, 0)

                            position = self.get_pos(line, position)

                            self.draw_line(prev_postion, position, color=color)

                        elif isinstance(code, GCodeArcMoveCW):
                            color = (1, 1, 1)

                            position = self.get_pos(line, position)
                            self.draw_arc(prev_postion, position, True, color=color)

                        elif isinstance(code, GCodeArcMoveCCW):
                            color = (1, 1, 1)
                            position = self.get_pos(line, position)
                            self.draw_arc(prev_postion, position, False, color=color)
                    prev_postion = copy.copy(position)

            elif line.block.modal_params:
                if prev_postion is not None:
                    if isinstance(active_modal, GCodeLinearMove):
                        color = (1, 1, 1)
                        position = self.get_pos(line, position)

                        self.draw_line(prev_postion, position, color=color)

                    elif isinstance(active_modal, GCodeRapidMove):
                        color = (1, 0, 0)

                        position = self.get_pos(line, position)

                        self.draw_line(prev_postion, position, color=color)

                    elif isinstance(active_modal, GCodeArcMoveCW):
                        color = (1, 1, 1)

                        position = self.get_pos(line, position)
                        self.draw_arc(prev_postion, position, True)

                    elif isinstance(active_modal, GCodeArcMoveCCW):
                        color = (1, 1, 1)
                        position = self.get_pos(line, position)
                        self.draw_arc(prev_postion, position, False)
                prev_postion = copy.copy(position)

    def draw_axes(self, x, y, z):
        center = (x, y, z)
        color = (1, 0, 0)
        axes = Axes(center=center, color=color)
        self.vtk_window.add_actor(axes)

    def draw_tool(self, x, y, z):

        color = (0, 0.5, 1)

        self.tool = Cone(center=(x, y, z), radius=1, angle=-90, height=1.5, color=color, resolution=100)

        self.vtk_window.add_actor(self.tool)

    def draw_line(self, pt1, pt2, color=(1, 1, 1)):

        point_1 = pt1[0], pt1[1], pt1[2]
        point_2 = pt2[0], pt2[1], pt2[2]

        line = Line(point_1, point_2, color=color)
        self.vtk_window.add_actor(line)

    def draw_arc(self, pt1, pt2, cw, color=(1, 1, 1)):

        point_1 = pt1[0], pt1[1], pt1[2]
        point_2 = pt2[0], pt2[1], pt2[2]
        r = pt2[3]

        arc = Arc(point_1, point_2, r=r, cen=None, cw=cw, arc_color=color)
        self.vtk_window.add_actor(arc)

    def get_pos(self, line, position):

        for code in line.block.gcodes:

            if isinstance(code, GCodeMotion):
                pos = code.get_param_dict("RXYZ")

                position[0] = pos.get("X", position[0])
                position[1] = pos.get("Y", position[1])
                position[2] = pos.get("Z", position[2])

                position[3] = pos.get("R", None)

        for j, modal in enumerate(line.block.modal_params):
            position[j] = modal.value

        return position

    def move_tool(self, x, y, z):
        if self.tool is not None:
            self.tool.SetPosition(x, y, z)


def main():
    window = Gtk.Window(title="HAZZY VTK")
    window.connect('destroy', Gtk.main_quit)
    window.connect('delete-event', Gtk.main_quit)

    kremlin = Kremlin()
    kremlin.draw_axes(x=0, y=0, z=0)
    kremlin.draw_tool(x=0, y=0, z=0)
    kremlin.load_file("hazzy.ngc")
    kremlin.draw_path()
    kremlin.move_tool(0, 0, 0)

    window.add(kremlin)

    window.show()
    Gtk.main()


if __name__ == "__main__":
    main()
