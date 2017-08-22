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
        self.action = None
        self.grid_size = 20

        # Initial event pos
        self.initial_x = 0
        self.initial_y = 0

        # Initial widget properties
        self.initial_pos_x = 0
        self.initial_pos_y = 0
        self.initial_w = 0
        self.initial_h = 0

        # Maximum change in size/pos
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
        self.initial_pos_x = x
        self.initial_pos_y = y


    def on_move_motion(self, event):
        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y

        x = self.initial_pos_x + max(min(dx, self.dx_max), -self.initial_pos_x)
        y = self.initial_pos_y + max(min(dy, self.dy_max), -self.initial_pos_y)

        self.parent.child_set_property(self, 'x', x)
        self.parent.child_set_property(self, 'y', y)


    def on_move_end(self):
        x = self.parent.child_get_property(self, 'x')
        y = self.parent.child_get_property(self, 'y')

        # Snap to 20 x 20 px grid on drag drop
        x = int(round(float(x) / self.grid_size)) * self.grid_size
        y = int(round(float(y) / self.grid_size)) * self.grid_size

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
        self.initial_w = w
        self.initial_h = h


    def on_resize_motion(self, event):
        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y
        w = self.initial_w
        h = self.initial_h

        # Limit size to maximum
        dx = min(dx, self.dx_max)
        dy = min(dy, self.dy_max)

        if self.action == RESIZE_X or self.action == RESIZE_XY:
            w = max(w + dx, 0)
        if self.action == RESIZE_Y or self.action == RESIZE_XY:
            h = max(h + dy, 0)
        self.set_size_request(w, h)


    def on_resize_end(self):
        w = self.get_allocation().width
        h = self.get_allocation().height

        # Snap to 20 x 20 px grid
        w = int(round(float(w) / self.grid_size)) * self.grid_size
        h = int(round(float(h) / self.grid_size)) * self.grid_size
        self.set_size_request(w, h)
