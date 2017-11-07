#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
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

# Description:
#   This is used for each of the ScreenStack's children, and is what contains
#   the individual Widgets. It implements what is need to for being able to
#   move/resize the Widgets via dragging with the mouse or via the arrow keys.

# ToDo:
#   Make the widgets expand to the window border if they are within GRID_SIZE / 2

import os
import importlib

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from widget_window import WidgetWindow

# Grid size in pixels used for "Snap to Grid"
GRID_SIZE = 20


class WidgetArea(Gtk.Fixed):

    # Drag action definitions
    class Drag:
        MOVE = 0
        RESIZE_X = 1
        RESIZE_Y = 2
        RESIZE_XY = 3

    # Incremental action definitions
    class Incremental:
        class Move:
            UP = 4
            DOWN = 5
            LEFT = 6
            RIGHT = 7

        class Resize:
            class Width:
                BIGGER = 8
                SMALLER = 9
            class Height:
                BIGGER = 10
                SMALLER = 11

    def __init__(self):
        Gtk.Fixed.__init__(self)

        # Set up drag 'n drop
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.connect("drag-data-received", self.on_drag_data_received)

        self.drag_dest_set_target_list(None)
        self.drag_dest_add_text_targets()

        # Initial event positions
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
        '''Add widget when receive drag to WidgetArea from the WidgetChooser.'''

        # Get the widget package name from the drop data
        package = data.get_text()

        # Create a new WidgetWindow object containing the widget
        widget_window = WidgetWindow(package)

        # Determine reasonable values for the initial size
        size = widget_window.get_preferred_size()[0]

        w = size.width + GRID_SIZE / 2 
        h = size.height + GRID_SIZE / 2 

        # Calculate position so widget drops "centered" under cursor
        x = x - w / 2
        y = y - h / 2

        # Add widget_window to WidgetArea (self)
        self.put(widget_window, x, y)

        # "Snap to Grid"
        widget_window.set_size_request(w, h)

        # Snap to closest grid
        self.child_snap_to_grid(widget_window)

        # ToDo Don't let widget be resized small then
        min_w = widget_window.get_size_request().width
        min_h = widget_window.get_size_request().height


    def child_snap_to_grid(self, widget):
        '''Snap widget position and size to closest grid.'''

        # Get initial widget position
        x = self.child_get_property(widget, 'x')
        y = self.child_get_property(widget, 'y')

        # Get initial widget height
        w = widget.get_size_request().width  #+ GRID_SIZE / 2
        h = widget.get_size_request().height #+ GRID_SIZE / 2

        # Calculate the closest position that is a multiple of GRID_SIZE
        x = int(round(float(x) / GRID_SIZE)) * GRID_SIZE
        y = int(round(float(y) / GRID_SIZE)) * GRID_SIZE

        # "Snap to Grid"
        self.child_set_property(widget, 'x', x)
        self.child_set_property(widget, 'y', y)

        # Calculate the closest size that is a multiple of GRID_SIZE
        w = int(round(float(w) / GRID_SIZE)) * GRID_SIZE
        h = int(round(float(h) / GRID_SIZE)) * GRID_SIZE

        # "Snap to Grid"
        widget.set_size_request(w, h)


#===================================
#  Child Arrow Key Move and Resize
#===================================

    def child_incremental_move(self, widget, direction):
        '''Move or Resize widget by one grid increment.'''

        # Get WidgetArea dimensions
        pw = self.get_allocation().width
        ph = self.get_allocation().height

        # Get the initial widget position within WidgetArea
        x = self.child_get_property(widget, 'x')
        y = self.child_get_property(widget, 'y')

        # Get the initial widget dimensions
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        # Convert WidgetArea dimensions to closest number of "grids"
        pw = int(round(float(pw) / GRID_SIZE))
        ph = int(round(float(ph) / GRID_SIZE))

        # Convert widget position to closest number of "grids"
        x = int(round(float(x) / GRID_SIZE))
        y = int(round(float(y) / GRID_SIZE))

        # Convert widget size to closest number of "grids"
        w = int(round(float(w) / GRID_SIZE))
        h = int(round(float(h) / GRID_SIZE))

        # Increment one "grid" in specified direction, making sure
        # not to exceed WidgetArea bounds
        if direction == self.Incremental.Move.UP:
            y = max(y - 1, 0)
        elif direction == self.Incremental.Move.DOWN:
            y = min(y + 1, ph - h)
        elif direction == self.Incremental.Move.LEFT:
            x = max(x - 1, 0)
        elif direction == self.Incremental.Move.RIGHT:
            x = min(x + 1, pw -w)
        elif direction == self.Incremental.Resize.Width.BIGGER:
            w = min(w + 1, pw - x)
        elif direction == self.Incremental.Resize.Width.SMALLER:
            w = max(w - 1, 0)
        elif direction == self.Incremental.Resize.Height.BIGGER:
            h = min(h + 1, ph - y)
        elif direction == self.Incremental.Resize.Height.SMALLER:
            h = max(h - 1, 0)

        # Convert back to pixels and reposition the widget
        self.child_set_property(widget, 'x', x * GRID_SIZE)
        self.child_set_property(widget, 'y', y * GRID_SIZE)
        widget.set_size_request(w * GRID_SIZE, h * GRID_SIZE)


#===================================
#  Child Drag Move
#===================================

    def child_move_begin(self, widget, event):

        # Get the WidgetArea dimensions
        pw = self.get_allocation().width
        ph = self.get_allocation().height

        # Get the initial widget position within WidgetArea
        x = self.child_get_property(widget, 'x')
        y = self.child_get_property(widget, 'y')

        # Get the initial widget dimensions
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        # Determine the maximum change in position so that the widget will
        # not exceed the bounds of the WidgetArea.
        # Subtract GRID_SIZE/2 to cause position to round down if near max.
        # Prevents window from expanding if size rounds up on resize_end.
        self.dx_max = pw - (x + w) - GRID_SIZE / 2
        self.dy_max = ph - (y + h) - GRID_SIZE / 2

        # Initial cursor position
        self.initial_x = event.x_root
        self.initial_y = event.y_root

        # Initial widget position
        self.initial_pos_x = x
        self.initial_pos_y = y


    def child_move_motion(self, widget, event):

        # Determine how far the cursor has moved since drag start
        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y

        # Determine a "safe" new position for the widget
        x = self.initial_pos_x + max(min(dx, self.dx_max), -self.initial_pos_x)
        y = self.initial_pos_y + max(min(dy, self.dy_max), -self.initial_pos_y)

        # Move the widget to the new position
        self.child_set_property(widget, 'x', x)
        self.child_set_property(widget, 'y', y)


    def child_move_end(self, widget):
        self.child_snap_to_grid(widget)

#===================================
#  Child Drag Resize
#===================================

    def child_resize_begin(self, widget, event):

        # Get the WidgetArea dimensions
        pw = self.get_allocation().width
        ph = self.get_allocation().height

        # Get initial widget position within WidgetArea
        x = self.child_get_property(widget, 'x')
        y = self.child_get_property(widget, 'y')

        # Get initial widget size
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        # Determine the maximum change in size so that the widget will
        # not exceed the bounds of the WidgetArea.
        # Subtract GRID_SIZE/2 to cause size to round down if near max.
        # Prevents window from expanding if size rounds up on resize_end.
        self.dx_max = pw - (x + w) - GRID_SIZE / 2
        self.dy_max = ph - (y + h) - GRID_SIZE / 2

        # Initial cursor position
        self.initial_x = event.x_root
        self.initial_y = event.y_root

        # Initial widget width and height
        self.initial_w = w
        self.initial_h = h


    def child_resize_motion(self, widget, event, action):

        # Determine how far the cursor has moved since resize start
        dx = event.x_root - self.initial_x
        dy = event.y_root - self.initial_y

        # The original with and hight before resize began
        w = self.initial_w
        h = self.initial_h

        # Limit change in size to max so will not exceed WidgetArea bounds
        dx = min(dx, self.dx_max)
        dy = min(dy, self.dy_max)

        # Calculate the new w and h, ensure non negative
        if action == self.Drag.RESIZE_X or action == self.Drag.RESIZE_XY:
            w = max(w + dx, 0)
        if action == self.Drag.RESIZE_Y or action == self.Drag.RESIZE_XY:
            h = max(h + dy, 0)

        # Resize the widget
        widget.set_size_request(w, h)


    def child_resize_end(self, widget):
        self.child_snap_to_grid(widget)
