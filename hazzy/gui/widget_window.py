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
#   The window which contains the widgets added to the WidgetArea
#   This could use a LOT of clean up


import os
import sys
import cairo
import importlib

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from message_bar import MessageBar
from utilities.constants import MessageType

# Set up paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
UI_FILE = os.path.join(PYDIR, 'ui', 'widget_window.ui')


class WidgetWindow(Gtk.EventBox):

    def __init__(self, package):
        Gtk.EventBox.__init__(self)

        self.package = package
        self.action = None
        self.drag_active = False

        # Add style class
        self.style_context = self.get_style_context()
        self.style_context.add_class("WidgetWindow")

        # Used to remove focus when clicking a non focusable widget
        self.connect('button-press-event', self.on_button_press)

        builder = Gtk.Builder()
        builder.add_from_file(UI_FILE)
        builder.connect_signals(self)

        # WidgetWindow - the whole thing
        self.widget_window = builder.get_object('widget_window')

        # Overlay - covers the whole window to catch event for drag/resize
        self.overlay = builder.get_object('overlay')
        self.overlay.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.overlay_style_context = self.overlay.get_style_context()

        # The inner window, used only for getting the icon image
        self.window = builder.get_object('window')

        # TitleBar - the title bar at the top of the window
        self.title_bar = builder.get_object('title_bar')
        self.title_bar_label = builder.get_object('title_bar_label')
        self.title_bar_button = builder.get_object('title_bar_button')

        #  WidgetBox - the box that the widget actually gets added to
        self.widget_box = builder.get_object('widget_box')

        # MessageBar
        self.message_bar = MessageBar()
        self.widget_box.add_overlay(self.message_bar)


        # Import the Widget and add to WidgetWindow
        module = importlib.import_module(self.package)
        widget = getattr(module, 'Widget')(self)

        self.widget_dir = os.path.abspath(os.path.dirname(module.__file__))

        if hasattr(widget, 'title'):
            # Use widget title attribute if specified
            title = widget.title
        else:
            # Use the package name
            title = self.package.split('.')[-1]

        # Set up the WidgetWindow
        self.title_bar_label.set_text(title)

        widget.set_margin_right(5)
        widget.set_margin_left(5)
        widget.set_margin_top(5)
        widget.set_margin_bottom(5)

        self.widget_box.add(widget)
        self.add(self.widget_window)

        if hasattr(widget, 'on_settings_button_pressed'):
            self.title_bar_button.connect('clicked', widget.on_settings_button_pressed)

        self.show_all()

    def set_title(self, title):
        self.title_bar_label.set_text(title)

    def show_info(self, *args, **kwargs):
        self.message_bar.show_info(*args, **kwargs)

    def show_warning(self, *args, **kwargs):
        self.message_bar.show_warning(*args, **kwargs)

    def show_error(self, *args, **kwargs):
        self.message_bar.show_error(*args, **kwargs)

    def show_question(self, *args, **kwargs):
        self.message_bar.show_question(*args, **kwargs)

    def on_button_press(self, widget, event):
        # Remove focus when clicking on WidgetWindow
        self.get_toplevel().set_focus(None)

    def on_delete_clicked(self, widget):
        # Remove self from the WidgetArea
        self.destroy()

    def show_overlay(self, visible):
        self.overlay.set_visible(visible)

    def get_widget_image(self):
        # Gets an image for use as an icon in the WidgetChooser
        # Need to implement some way to call from a GUI menu.

        window = self.window.get_window()

        if window is None:
            return

        width, height = window.get_width(), window.get_height()

        surface = Gdk.Window.create_similar_surface(window,
                                                    cairo.CONTENT_COLOR,
                                                    width, height)
        cairo_context = cairo.Context(surface)
        Gdk.cairo_set_source_window(cairo_context, window, 0, 0)
        cairo_context.paint()

        surface.write_to_png(os.path.join(self.widget_dir, 'widget.png'))

    def on_key_press(self, widget, event):

        # Events that don't need to know about modifiers
        if event.keyval == Gdk.KEY_Escape:
            self.get_toplevel().set_focus(None)
            return True
        if event.keyval == Gdk.KEY_Delete:
            self.destroy()  # Remove the widget
            return True
        if event.keyval == Gdk.KEY_Tab:
            # TODO Implement move focus to next widget
            pass

        # Get any active, but not pressed modifiers, like CapsLock and NumLock
        persistant_modifiers = Gtk.accelerator_get_default_mod_mask()

        # Determine the actively pressed modifier
        modifier = event.get_state() & persistant_modifiers

        # Bool of Control or Shift modifier states
        control = modifier == Gdk.ModifierType.CONTROL_MASK
        shift = modifier == Gdk.ModifierType.SHIFT_MASK

        # If neither Shift or Control we want to move the Widget
        if event.keyval == Gdk.KEY_Up and not (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Move.UP)
        elif event.keyval == Gdk.KEY_Down and not (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Move.DOWN)
        elif event.keyval == Gdk.KEY_Left and not (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Move.LEFT)
        elif event.keyval == Gdk.KEY_Right and not (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Move.RIGHT)

        # If either Shift or Control we want to resize the Widget
        elif event.keyval == Gdk.KEY_Up and (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Resize.Height.SMALLER)
        elif event.keyval == Gdk.KEY_Down and (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Resize.Height.BIGGER)
        elif event.keyval == Gdk.KEY_Left and (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Resize.Width.SMALLER)
        elif event.keyval == Gdk.KEY_Right and (shift or control):
            self.parent.child_incremental_move(self, self.parent.Incremental.Resize.Width.BIGGER)

        # Indicate the event was handled
        return True


#===================================
#  Drag to Move / Resize
#===================================

    def on_drag_begin(self, widget, event):

        self.drag_active = True

        self.overlay.grab_focus()

        # Bring self to top of z-order
        # FIXME this does not work. Why??????
        # https://stackoverflow.com/questions/1066012/stacking-widgets-in-gtk
        # https://lazka.github.io/pgi-docs/#Gdk-3.0/classes/Window.html#Gdk.Window.raise_
        self.get_window().raise_()

        # Get the WidgetArea that self is a child of
        self.parent = self.get_parent()

        # Get dimensions of self
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        # Determine what drag action based on position of event
        if event.y <= 50:
            self.action = self.parent.Drag.MOVE
            self.parent.child_move_begin(self, event)
        elif event.x >= w - 50 and event.y >= h -50:
            self.action = self.parent.Drag.RESIZE_XY
            self.parent.child_resize_begin(self, event)
        elif event.x >= w - 50:
            self.action = self.parent.Drag.RESIZE_X
            self.parent.child_resize_begin(self, event)
        elif event.y >= h -50:
            self.action = self.parent.Drag.RESIZE_Y
            self.parent.child_resize_begin(self, event)
        else:
            self.action = None

        # Indicate the event was handled
        return True

    def on_drag_motion(self, widget, event):
        if self.action == self.parent.Drag.MOVE:
            self.parent.child_move_motion(self, event)
        elif self.action >= self.parent.Drag.RESIZE_X:
            self.parent.child_resize_motion(self, event, self.action)

    def on_drag_end(self, widget, event):
        if not self.drag_active:
            return
        if self.action == self.parent.Drag.MOVE:
            self.parent.child_move_end(self)
        elif self.action >= self.parent.Drag.RESIZE_X:
            self.parent.child_resize_end(self)

        self.drag_active = False
