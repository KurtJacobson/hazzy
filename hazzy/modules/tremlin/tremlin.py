"""
Description:

  Provides a pyGtk vtkRenderWindowInteractor widget.  This embeds a
  vtkRenderWindow inside a Gtk widget and uses the
  vtkGenericRenderWindowInteractor for the event handling.  This is
  based on vtkTkRenderWindow.py.

  The class uses the Gtkgl.GtkGLArea widget (Gtkglarea).  This avoids
  a lot of problems with flicker.

  There is a working example at the bottom.

Created by Prabhu Ramachandran, April 2002.

Bugs:

  (*) There is a focus related problem.  Tkinter has a focus object
  that handles focus events.  I don't know of an equivalent object
  under Gtk.  So, when an 'enter_notify_event' is received on the
  GtkVTKRenderWindow I grab the focus but I don't know what to do when
  I get a 'leave_notify_event'.

  (*) Will not work under Win32 because it uses the XID of a window in
  OnRealize.  Suggestions to fix this will be appreciated.

"""

import math

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from vtk.vtkRenderingCorePython import vtkRenderWindow, vtkCamera
from vtk.vtkRenderingCorePython import vtkGenericRenderWindowInteractor
from vtk.vtkRenderingCorePython import vtkPolyDataMapper
from vtk.vtkRenderingCorePython import vtkActor
from vtk.vtkRenderingCorePython import vtkRenderer

from vtk.vtkFiltersSourcesPython import vtkConeSource

from vtk.vtkCommonCorePython import vtkPoints, VTK_MAJOR_VERSION
from vtk.vtkCommonDataModelPython import vtkPolyData, vtkCellArray

from hazzy.modules.pygcode import Line
from hazzy.modules.pygcode import GCodeLinearMove
from hazzy.modules.pygcode import GCodeRapidMove
from hazzy.modules.pygcode import Machine


class GtkVTKRenderWindowInteractor(Gtk.GLArea):
    """ Embeds a vtkRenderWindow into a pyGtk widget and uses
    vtkGenericRenderWindowInteractor for the event handling.  This
    class embeds the RenderWindow correctly.  A __getattr__ hook is
    provided that makes the class behave like a
    vtkGenericRenderWindowInteractor."""

    def __init__(self, *args):

        Gtk.GLArea.__init__(self)

        self.camera = vtkCamera()
        self.camera.SetPosition(0, 0, 100)
        self.camera.SetFocalPoint(0, 0, 0)

        self._renderer = vtkRenderer()
        self._renderer.SetActiveCamera(self.camera)
        self._renderer.SetBackground(0.1, 0.2, 0.4)

        self._render_window = vtkRenderWindow()
        self._render_window.AddRenderer(self._renderer)

        # private attributes
        self.__Created = 0
        self._active_button = 0

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
        self.connect("realize", self.on_realize)
        self.connect("render", self.on_render)
        self.connect("configure-event", self.on_configure)
        self.connect("button-press-event", self.on_button_down)
        self.connect("button-release-event", self.on_button_up)
        self.connect('scroll-event', self.on_scroll)
        self.connect("motion-notify-event", self.on_mouse_move)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("leave-notify-event", self.on_leave)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        self.connect('scroll-event', self.on_scroll)
        self.connect("delete-event", self.on_destroy)

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
        self.Render()
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


class Tremlin(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)

        self.gvtk = GtkVTKRenderWindowInteractor()

        # gvtk.SetDesiredUpdateRate(1000)
        self.gvtk.set_usize(800, 600)
        self.pack_start(self.gvtk, True, True, 0)

        self.gvtk.show_all()
        self.show_all()

        # prevents 'q' from exiting the app.
        self.gvtk.AddObserver("ExitEvent", lambda o, e, x=None: x)

        self.machine = Machine()

        self.gcode_path = []

    def load_file(self, ngc_filename):

        with open(ngc_filename, "r") as ngc_file:
            ngc_code = ngc_file.readlines()
            for code_line in ngc_code:
                line = Line(code_line)

                if line.block.gcodes:
                    self.gcode_path.append(line.block.gcodes)

    def draw_cone(self):
        cone = vtkConeSource()
        cone.SetResolution(100)

        cone_mapper = vtkPolyDataMapper()
        cone_mapper.SetInputConnection(cone.GetOutputPort())

        cone_actor = vtkActor()
        cone_actor.SetMapper(cone_mapper)
        cone_actor.GetProperty().SetColor(0.5, 0.5, 1.0)

        self.add_actor(cone_actor)

    def draw_polyline(self):

        num_gcode_blocks = len(self.gcode_path)

        points = vtkPoints()
        points.SetNumberOfPoints(num_gcode_blocks)

        lines = vtkCellArray()
        lines.InsertNextCell(num_gcode_blocks)

        for i, line in enumerate(self.gcode_path):
            line_type = type(line[0])
            if line_type == GCodeLinearMove:
                coord = self.proces_line(line[0])
                # print("{0} Linear Move {1}".format(i, coord.values))
                points.SetPoint(i,
                                coord.values["X"],
                                coord.values["Y"],
                                coord.values["Z"])

            elif line_type == GCodeRapidMove:
                coord = self.proces_line(line[0])
                # print("{0} Rapid Move {1}".format(i, coord.values))
                points.SetPoint(i,
                                coord.values["X"],
                                coord.values["Y"],
                                coord.values["Z"])

            lines.InsertCellPoint(i)

        path = vtkPolyData()

        path.SetPoints(points)
        path.SetLines(lines)

        path_mapper = vtkPolyDataMapper()

        if VTK_MAJOR_VERSION <= 5:
            path_mapper.SetInputConnection(path.GetProducerPort())
        else:
            path_mapper.SetInputData(path)
            path_mapper.Update()

        path_actor = vtkActor()

        path_actor.SetMapper(path_mapper)
        path_actor.GetProperty().SetColor(1, 1, 1)  # (R,G,B)

        self.add_actor(path_actor)

    def add_actor(self, actor):
        ren = self.gvtk.get_renderer()
        ren.AddActor(actor)

    def proces_line(self, line):
        self.machine.process_gcodes(line)
        return self.machine.pos



def main():
    window = Gtk.Window(title="HAZZY VTK")
    window.connect("destroy", Gtk.main_quit)
    window.connect("delete-event", Gtk.main_quit)

    tremlin = Tremlin()
    tremlin.draw_cone()
    tremlin.load_file("hazzy.ngc")
    tremlin.draw_polyline()

    window.add(tremlin)

    window.show()
    Gtk.main()


if __name__ == "__main__":
    main()
