import os
import sys
import gi
import cairo


from math import ceil as fceil

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))


def ceil(f):
    return int(fceil(f))


class WidgetWindow(Gtk.Box):

    def __init__(self, widget, label, menu_callback):
        Gtk.Box.__init__(self)

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(PYDIR, 'ui', 'widgetwindow.ui'))
        builder.connect_signals(self)

        self.menu_btn = builder.get_object('menu_button')
        self.label = builder.get_object('label')
        self.box = builder.get_object('box')
        self.wwindow = builder.get_object('widgetwindow')

        self.label.set_text(label)
        self.box.add(widget)
        self.add(self.wwindow)


        self.offsetx = 0
        self.offsety = 0
        self.px = 0
        self.py = 0
        self.maxx = 0
        self.maxy = 0


        self.menu_btn.connect('pressed', menu_callback, self)

        self.ha = HighLight(self)

        #ha.Show()

        self.show_all()


    def drag_move(self, widget, event):
        # get starting values for x,y
        x = event.x_root - self.offsetx
        y = event.y_root - self.offsety
        # make sure the potential coordinates x,y:
        #   1) will not push any part of the widget outside of its parent container
        #   2) is a multiple of SENSITIVITY
        x = max(min(x, self.maxx), 0)
        y = max(min(y, self.maxy), 0)

        print self.offsetx, self.offsety
        print x, y

        if x != self.px or y != self.py:
            self.px = x
            self.py = y
            p = self.get_parent()
            a = p.get_allocation()
            xf, yf = a.width / 50, a.height / 35
            x, y = int(x / xf), int(y / yf)
            p.child_set_property(self, 'left_attach', x)
            p.child_set_property(self, 'top_attach', y)


    def resize_in_x(self, widget, event):
        # get starting values for x,y
        x = event.x_root - self.offsetx
        y = event.y_root - self.offsety
        # make sure the potential coordinates x,y:
        #   1) will not push any part of the widget outside of its parent container
        #   2) is a multiple of SENSITIVITY
        x = max(min(x, self.maxx), 0)
        y = max(min(y, self.maxy), 0)
        if x != self.px or y != self.py:
            self.px = x
            self.py = y
            p = self.get_parent()
            a = p.get_allocation()
            xf, yf = a.width / 50, a.height / 35
            x, y = int(x / xf), int(y / yf)
            p.child_set_property(self, 'width', x)

    def resize_in_y(self, widget, event):
        print 'got resize_in_y'


    def drag_start(self, w, event):
        self.ha.Show()
        print "drag started"

        if event.button == 1:
            # offset = distance of parent widget from edge of screen ...
            self.offsetx, self.offsety =  w.get_toplevel().get_position()
            # plus distance from pointer to edge of widget
            self.offsetx += event.x
            self.offsety += event.y
            # maxx, maxy both relative to the parent
            p = self.get_parent()
            self.maxx = p.get_allocation().width - self.get_allocation().width
            self.maxy = p.get_allocation().height - self.get_allocation().height

    def drag_end(self, widget, event):
        self.ha.hide()


    def motion_notify_event(self, widget, event):

        # x_root,x_root relative to screen
        # x,y relative to parent (fixed widget)
        # px,py stores previous values of x,y

        # get starting values for x,y
        x = event.x_root - self.offsetx
        y = event.y_root - self.offsety
        # make sure the potential coordinates x,y:
        #   1) will not push any part of the widget outside of its parent container
        #   2) is a multiple of SENSITIVITY
        x = max(min(x, self.maxx), 0)
        y = max(min(y, self.maxy), 0)
        if x != self.px or y != self.py:
            self.px = x
            self.py = y
            print x, y
            fixed.move(widget, x, y)



class HighLight(Gtk.Window):

    def __init__(self, parent):
        Gtk.Window.__init__(self, Gtk.WindowType.POPUP)

        self.connect_after("draw", self.__onExpose)

        # set RGBA visual for the window so transparency works
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.myparent = parent



    def Show(self):
        alloc = self.myparent.get_allocation()
        width = alloc.width
        height = alloc.height
        x_loc = alloc.x
        y_loc = alloc.y

        print width, height, x_loc, y_loc

        x_loc, y_loc = self.translateCoords(int(x_loc), int(y_loc))
        self.move(x_loc, y_loc)

        self.resize(ceil(width), ceil(height))
        self.show()


    def __onExpose(self, self_, ctx):

        print "exposed"
        context = self.get_window().cairo_create()
        a = self_.get_allocation()
        context.rectangle(a.x, a.y, a.width, a.height)
        sc = self.get_style_context()
        color = Gdk.Color(.5, .5, 1)

        if self.is_composited():
            print "Composited"
            context.set_operator(cairo.OPERATOR_CLEAR)
            context.set_source_rgba(0, 0, 0, 0.0)
            context.fill_preserve()
            context.set_operator(cairo.OPERATOR_OVER)
            context.set_source_rgba(color.red, color.green, color.blue, 0.5)
            context.fill()
        else:
            context.set_source_rgba(color.red, color.green, color.blue)
            context.set_operator(cairo.OPERATOR_OVER)
            context.fill()


    def translateCoords(self, x, y):
        top_level = self.myparent.get_toplevel()
        window = top_level.get_window()
        if window is None:
            print("   !!! get_window() returned None for", self.myparent, top_level)
        else:
            x_loc1, y_loc1 = window.get_position()
            translate_x = self.myparent.translate_coordinates(top_level, x, y)
            x = x_loc1 + translate_x[0]
            y = y_loc1 + translate_x[1]
            return x, y
