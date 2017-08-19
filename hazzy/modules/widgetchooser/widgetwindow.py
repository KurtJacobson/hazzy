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

    def __init__(self, widget, size, label, menu_callback):
        Gtk.Box.__init__(self)

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(PYDIR, 'ui', 'widgetwindow.ui'))
        builder.connect_signals(self)

        self.menu_btn = builder.get_object('menu_button')
        self.label = builder.get_object('label')
        self.box = builder.get_object('box')
        self.wwindow = builder.get_object('widgetwindow')

        self.set_size_request(size[0], size[1])
        self.label.set_text(label)
        self.box.add(widget)
        self.add(self.wwindow)

        self.parent = None
        self.grid_size = 20 # px

        self.offsetx = 0
        self.offsety = 0
        self.px = 0
        self.py = 0
        self.maxx = 0
        self.maxy = 0

        self.initial_x = 0
        self.initial_y = 0
        self.initial_w = 0
        self.initial_h = 0
        self.dx_max = 0
        self.dy_max = 0


        self.menu_btn.connect('pressed', menu_callback, self)

        self.ha = HighLight(self)

        #ha.Show()

        self.show_all()


#==============
#  Drag Move
#==============

    def on_drag_begin(self, w, event):
        self.parent = self.get_parent()
        if event.button == 1:
            # offset = distance of parent widget from edge of screen ...
            self.offsetx, self.offsety = self.get_window().get_position()
            # plus distance from pointer to edge of widget
            self.offsetx += event.x
            self.offsety += event.y
            # maxx, maxy both relative to the parent
            self.maxx = self.parent.get_allocation().width - self.get_allocation().width
            self.maxy = self.parent.get_allocation().height - self.get_allocation().height


    def on_drag_motion(self, widget, event):
        # get starting values for x,y
        x = event.x_root - self.offsetx
        y = event.y_root - self.offsety
        # make sure the potential coordinates x,y:
        # will not push any part of the widget outside of its parent container
        x = max(min(x, self.maxx), 0)
        y = max(min(y, self.maxy), 0)
        if x != self.px or y != self.py:
            self.px = x
            self.py = y
            self.parent.child_set_property(self, 'x', x)
            self.parent.child_set_property(self, 'y', y)


    def on_drag_end(self, widget, event):
        # Snap to 20 x 20 px grid on drag drop
        x = int(round(self.px / self.grid_size)) * self.grid_size
        y = int(round(self.py / self.grid_size)) * self.grid_size
        self.parent.child_set_property(self, 'x', x)
        self.parent.child_set_property(self, 'y', y)


#==============
#  Drag Resize
#==============

    def on_resize_begin(self, widget, event):
        self.parent = self.get_parent()
        pw = self.parent.get_allocation().width
        ph = self.parent.get_allocation().height

        x = self.parent.child_get_property(self, 'x')
        y = self.parent.child_get_property(self, 'y')
        w = self.get_allocation().width
        h = self.get_allocation().height

        self.dx_max = pw - (x + w)
        self.dy_max = ph - (y + h)

        self.initial_x = event.x_root
        self.initial_y = event.y_root
        self.initial_w = self.get_allocation().width
        self.initial_h = self.get_allocation().height


    def on_resize_x_motion(self, widget, event):
        dx = event.x_root - self.initial_x
        if dx <= self.dx_max:
            w = self.initial_w + dx
            h = self.initial_h
            self.set_size_request(w, h)


    def on_resize_y_motion(self, widget, event):
        dy = event.y_root - self.initial_y
        if dy <= self.dy_max:
            w = self.initial_w
            h = self.initial_h + dy
            self.set_size_request(w, h)


    def on_resize_motion(self, widget, event):
        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y
        if dx > self.dx_max:
            dx = self.dx_max
        if dy > self.dy_max:
            dy = self.dy_max
        w = self.initial_w + dx
        h = self.initial_h + dy
        self.set_size_request(w, h)


    def on_resize_end(self, widget, event):
        w = self.get_allocation().width
        h = self.get_allocation().height
        # Snap to 20 x 20 px grid
        w = int(round(float(w) / self.grid_size)) * self.grid_size
        h = int(round(float(h) / self.grid_size)) * self.grid_size
        self.set_size_request(w, h)



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
