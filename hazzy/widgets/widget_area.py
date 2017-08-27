#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from hazzy.widgets.widget_manager import WidgetManager
from hazzy.widgets.widget_window import WidgetWindow

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

GRID_SIZE = 20

# Actions
MOVE = 0
RESIZE_X = 1
RESIZE_Y = 2
RESIZE_XY = 3


class WidgetArea(Gtk.Fixed):
    def __init__(self):
        Gtk.Fixed.__init__(self)

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.connect("drag-data-received", self.on_drag_data_received)

        self.drag_dest_set_target_list(None)
        self.drag_dest_add_text_targets()

        self.widget_manager = WidgetManager()

        # Initial event pos
        self.initial_x = 0
        self.initial_y = 0

        # Initial child properties
        self.initial_pos_x = 0
        self.initial_pos_y = 0
        self.initial_w = 0
        self.initial_h = 0

        # Maximum change in size/pos
        self.dx_max = 0
        self.dy_max = 0


    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        pakage = data.get_text()

        widget, name, size = self.widget_manager.get_widget(pakage)

        # Snap to grid
        x = int(round(float(x - size[0]/2) / 20)) * 20
        y = int(round(float(y - size[1]/2) / 20)) * 20

        # Snap to 20 x 20 px grid
        w = int(round(float(size[0]) / 20)) * 20
        h = int(round(float(size[1]) / 20)) * 20

        wwindow = WidgetWindow(widget, [w, h], name)
        self.put(wwindow, x, y)

#===================================
#  Child Drag Move
#===================================

    def move_begin(self, widget, event):
        pw = self.get_allocation().width
        ph = self.get_allocation().height

        x = self.child_get_property(widget, 'x')
        y = self.child_get_property(widget, 'y')
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        # Subtract GRID_SIZE/2 to cause size to round down if near max
        # Needed to prevent window from expanding
        self.dx_max = pw - (x + w) - GRID_SIZE / 2
        self.dy_max = ph - (y + h) - GRID_SIZE / 2

        self.initial_x = event.x_root
        self.initial_y = event.y_root
        self.initial_pos_x = x
        self.initial_pos_y = y


    def move_motion(self, widget, event):
        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y

        x = self.initial_pos_x + max(min(dx, self.dx_max), -self.initial_pos_x)
        y = self.initial_pos_y + max(min(dy, self.dy_max), -self.initial_pos_y)

        self.child_set_property(widget, 'x', x)
        self.child_set_property(widget, 'y', y)


    def move_end(self, widget):
        x = self.child_get_property(widget, 'x')
        y = self.child_get_property(widget, 'y')

        # Snap to 20 x 20 px grid on drag drop
        x = int(round(float(x) / GRID_SIZE)) * GRID_SIZE
        y = int(round(float(y) / GRID_SIZE)) * GRID_SIZE

        self.child_set_property(widget, 'x', x)
        self.child_set_property(widget, 'y', y)


#===================================
#  Child Drag Resize
#===================================

    def resize_begin(self, widget, event):
        pw = self.get_allocation().width
        ph = self.get_allocation().height

        x = self.child_get_property(widget, 'x')
        y = self.child_get_property(widget, 'y')
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        # Subtract GRID_SIZE/2 to cause size to round down if near max
        # Needed to prevent window from expanding
        self.dx_max = pw - (x + w) - GRID_SIZE / 2
        self.dy_max = ph - (y + h) - GRID_SIZE / 2

        self.initial_x = event.x_root
        self.initial_y = event.y_root
        self.initial_w = w
        self.initial_h = h


    def resize_motion(self, widget, event, action):
        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y
        w = self.initial_w
        h = self.initial_h

        # Limit size to maximum
        dx = min(dx, self.dx_max)
        dy = min(dy, self.dy_max)

        if action == RESIZE_X or action == RESIZE_XY:
            w = max(w + dx, 0)
        if action == RESIZE_Y or action == RESIZE_XY:
            h = max(h + dy, 0)
        widget.set_size_request(w, h)


    def resize_end(self, widget):
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        # Snap to 20 x 20 px grid
        w = int(round(float(w) / GRID_SIZE)) * GRID_SIZE
        h = int(round(float(h) / GRID_SIZE)) * GRID_SIZE
        widget.set_size_request(w, h)
