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

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

import vtk
import math


class GtkVTKRenderWindowInteractor(Gtk.GLArea):
    """ Embeds a vtkRenderWindow into a pyGtk widget and uses
    vtkGenericRenderWindowInteractor for the event handling.  This
    class embeds the RenderWindow correctly.  A __getattr__ hook is
    provided that makes the class behave like a
    vtkGenericRenderWindowInteractor."""

    def __init__(self, *args):

        Gtk.GLArea.__init__(self)
        self._RenderWindow = vtk.vtkRenderWindow()

        # private attributes
        self.__Created = 0
        self._ActiveButton = 0

        self._Iren = vtk.vtkGenericRenderWindowInteractor()
        self._Iren.SetRenderWindow(self._RenderWindow)

        self._Iren.AddObserver('CreateTimerEvent', self.CreateTimer)
        self._Iren.AddObserver('DestroyTimerEvent', self.DestroyTimer)
        self.ConnectSignals()

        # need this to be able to handle key_press events.
        ## self.set_flags(Gtk.CAN_FOCUS)
        # default size
        self.set_usize(300, 300)

    def set_usize(self, w, h):
        ## Gtk.GLArea.set_usize(self, w, h)
        self._RenderWindow.SetSize(w, h)
        self._Iren.SetSize(w, h)
        self._Iren.ConfigureEvent()

    def ConnectSignals(self):
        self.connect("realize", self.OnRealize)
        ## self.connect("expose_event", self.OnExpose)
        self.connect("configure_event", self.OnConfigure)
        self.connect("button_press_event", self.OnButtonDown)
        self.connect("button_release_event", self.OnButtonUp)
        self.connect("motion_notify_event", self.OnMouseMove)
        self.connect("enter_notify_event", self.OnEnter)
        self.connect("leave_notify_event", self.OnLeave)
        self.connect("key_press_event", self.OnKeyPress)
        self.connect("delete_event", self.OnDestroy)
        """
        self.add_events(Gtk.GLArea.EXPOSURE_MASK | Gtk.GLArea.BUTTON_PRESS_MASK |
                        Gtk.GLArea.BUTTON_RELEASE_MASK |
                        Gtk.GLArea.KEY_PRESS_MASK |
                        Gtk.GLArea.POINTER_MOTION_MASK |
                        Gtk.GLArea.POINTER_MOTION_HINT_MASK |
                        Gtk.GLArea.ENTER_NOTIFY_MASK | Gtk.GLArea.LEAVE_NOTIFY_MASK)
        """
    def __getattr__(self, attr):
        """Makes the object behave like a
        vtkGenericRenderWindowInteractor"""
        if attr == '__vtk__':
            return lambda t=self._Iren: t
        elif hasattr(self._Iren, attr):
            return getattr(self._Iren, attr)
        else:
            raise AttributeError(self.__class__.__name__ + " has no attribute named " + attr)

    def CreateTimer(self, obj, event):
        GLib.timeout_add(10, self._Iren.TimerEvent)

    def DestroyTimer(self, obj, event):
        """The timer is a one shot timer so will expire automatically."""
        return 1

    def GetRenderWindow(self):
        return self._RenderWindow

    def Render(self):
        if self.__Created:
            self._RenderWindow.Render()

    def OnRealize(self, *args):
        if self.__Created == 0:
            # you can't get the xid without the window being realized.
            self.realize()
            win_id = str(self.get_window().xid)
            self._RenderWindow.SetWindowInfo(win_id)
            self._Iren.Initialize()
            self.__Created = 1
        return True

    def OnConfigure(self, wid, event=None):
        sz = self._RenderWindow.GetSize()
        if (event.width != sz[0]) or (event.height != sz[1]):
            self._Iren.SetSize(event.width, event.height)
            self._Iren.ConfigureEvent()
        return True

    def OnExpose(self, *args):
        self.Render()
        return True

    def OnDestroy(self, event=None):
        self.hide()
        del self._RenderWindow
        self.destroy()
        return True

    def _GetCtrlShift(self, event):
        ctrl, shift = 0, 0
        if (event.state & Gtk.GLArea.CONTROL_MASK) == Gtk.GLArea.CONTROL_MASK:
            ctrl = 1
        if (event.state & Gtk.GLArea.SHIFT_MASK) == Gtk.GLArea.SHIFT_MASK:
            shift = 1
        return ctrl, shift

    def OnButtonDown(self, wid, event):
        """Mouse button pressed."""
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            chr(0), 0, None)
        button = event.button
        if button == 3:
            self._Iren.RightButtonPressEvent()
            return True
        elif button == 1:
            self._Iren.LeftButtonPressEvent()
            return True
        elif button == 2:
            self._Iren.MiddleButtonPressEvent()
            return True
        else:
            return False

    def OnButtonUp(self, wid, event):
        """Mouse button released."""
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            chr(0), 0, None)
        button = event.button
        if button == 3:
            self._Iren.RightButtonReleaseEvent()
            return True
        elif button == 1:
            self._Iren.LeftButtonReleaseEvent()
            return True
        elif button == 2:
            self._Iren.MiddleButtonReleaseEvent()
            return True

        return False

    def OnMouseMove(self, wid, event):
        """Mouse has moved."""
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            chr(0), 0, None)
        self._Iren.MouseMoveEvent()
        return True

    def OnEnter(self, wid, event):
        """Entering the vtkRenderWindow."""
        self.grab_focus()
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            chr(0), 0, None)
        self._Iren.EnterEvent()
        return True

    def OnLeave(self, wid, event):
        """Leaving the vtkRenderWindow."""
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            chr(0), 0, None)
        self._Iren.LeaveEvent()
        return True

    def OnKeyPress(self, wid, event):
        """Key pressed."""
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        keycode, keysym = event.keyval, event.string
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            key, 0, keysym)
        self._Iren.KeyPressEvent()
        self._Iren.CharEvent()
        return True

    def OnKeyRelease(self, wid, event):
        "Key released."
        m = self.get_pointer()
        ctrl, shift = self._GetCtrlShift(event)
        keycode, keysym = event.keyval, event.string
        key = chr(0)
        if keycode < 256:
            key = chr(keycode)
        self._Iren.SetEventInformationFlipY(m[0], m[1], ctrl, shift,
                                            key, 0, keysym)
        self._Iren.KeyReleaseEvent()
        return True

    def Initialize(self):
        if self.__Created:
            self._Iren.Initialize()


def main():
    # The main window
    window = Gtk.Window()
    window.set_title("A GtkVTKRenderWindow Demo!")
    window.connect("destroy", Gtk.main_quit)
    window.connect("delete_event", Gtk.main_quit)
    window.set_border_width(10)

    # A VBox into which widgets are packed.
    vbox = Gtk.VBox(spacing=3)
    window.add(vbox)
    vbox.show()

    # The GtkVTKRenderWindow
    gvtk = GtkVTKRenderWindowInteractor()
    # gvtk.SetDesiredUpdateRate(1000)
    gvtk.set_usize(400, 400)
    vbox.pack_start(gvtk, True, True, 0)
    gvtk.show()
    gvtk.Initialize()
    gvtk.Start()
    # prevents 'q' from exiting the app.
    gvtk.AddObserver("ExitEvent", lambda o, e, x=None: x)

    # The VTK stuff.
    cone = vtk.vtkConeSource()
    cone.SetResolution(80)
    coneMapper = vtk.vtkPolyDataMapper()
    coneMapper.SetInputConnection(cone.GetOutputPort())
    # coneActor = vtk.vtkLODActor()
    coneActor = vtk.vtkActor()
    coneActor.SetMapper(coneMapper)
    coneActor.GetProperty().SetColor(0.5, 0.5, 1.0)
    ren = vtk.vtkRenderer()
    gvtk.GetRenderWindow().AddRenderer(ren)
    ren.AddActor(coneActor)

    # A simple quit button
    quit = Gtk.Button("Quit!")
    quit.connect("clicked", Gtk.main_quit)
    vbox.pack_start(quit, True, True, 0)
    quit.show()

    # show the main window and start event processing.
    window.show()
    Gtk.main()


if __name__ == "__main__":
    main()
