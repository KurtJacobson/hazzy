#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from math import ceil as fceil

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

# Actions
MOVE = 0
RESIZE_X = 1
RESIZE_Y = 2
RESIZE_XY = 3


def ceil(f):
    return int(fceil(f))


class WidgetWindow(Gtk.Box):

    def __init__(self, widget, size, label, menu_callback=None):
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

        if menu_callback:
            self.menu_btn.connect('pressed', menu_callback, self)

        self.show_all()


#===================================
#  Drag to Move / Resize
#===================================

    def on_drag_begin(self, widget, event):

        self.parent = self.get_parent()

        w = widget.get_allocation().width
        h = widget.get_allocation().height

        if event.y <= 50:
            self.action = MOVE
            self.on_move_begin(event)
        elif event.x >= w - 50 and event.y >= h -50:
            self.action = RESIZE_XY
            self.on_resize_begin(event)
        elif event.x >= w - 50:
            self.action = RESIZE_X
            self.on_resize_begin(event)
        elif event.y >= h -50:
            self.action = RESIZE_Y
            self.on_resize_begin(event)
        else:
            self.action = None


    def on_drag_motion(self, widget, event):
        if self.action == MOVE:
            self.on_move_motion(event)
        elif self.action >= RESIZE_X:
            self.on_resize_motion(event)


    def on_drag_end(self, widget, event):
        if self.action == MOVE:
            self.on_move_end()
        elif self.action >= RESIZE_X:
            self.on_resize_end()

#==============
#  Move
#==============

    def on_move_begin(self, event):
        if event.button == 1:
            # offset = distance of parent widget from edge of screen ...
            self.offsetx, self.offsety = self.get_window().get_position()
            # plus distance from pointer to edge of widget
            self.offsetx += event.x
            self.offsety += event.y
            # maxx, maxy both relative to the parent
            self.maxx = self.parent.get_allocation().width - self.get_allocation().width
            self.maxy = self.parent.get_allocation().height - self.get_allocation().height
            print self.maxx, self.maxy


    def on_move_motion(self, event):
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


    def on_move_end(self):
        # Snap to 20 x 20 px grid on drag drop
        x = int(round(self.px / self.grid_size)) * self.grid_size
        y = int(round(self.py / self.grid_size)) * self.grid_size
        self.parent.child_set_property(self, 'x', x)
        self.parent.child_set_property(self, 'y', y)


#==============
#  Resize
#==============

    def on_resize_begin(self, event):

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


    def on_resize_motion(self, event):

        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y
        w = self.initial_w
        h = self.initial_h

        # Limit size to maximum
        if dx > self.dx_max:
            dx = self.dx_max
        if dy > self.dy_max:
            dy = self.dy_max

        if self.action == RESIZE_X or self.action == RESIZE_XY:
            w += dx
        if self.action == RESIZE_Y or self.action == RESIZE_XY:
            h += dy
        self.set_size_request(w, h)


    def on_resize_end(self):
        w = self.get_allocation().width
        h = self.get_allocation().height
        # Snap to 20 x 20 px grid
        w = int(round(float(w) / self.grid_size)) * self.grid_size
        h = int(round(float(h) / self.grid_size)) * self.grid_size
        self.set_size_request(w, h)
