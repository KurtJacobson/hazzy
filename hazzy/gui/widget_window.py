#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk


# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))


class WidgetWindow(Gtk.Box):

    selected = []

    def __init__(self, package, widget, title):
        Gtk.Box.__init__(self)

        self.module_package = package
        self.module_widget = widget
        self.module_title = title

        self.action = None

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(PYDIR, 'ui', 'widget_window.ui'))
        builder.connect_signals(self)

        # WidgetWindow - the whole thing
        self.widget_window = builder.get_object('widget_window')

        # Overlay - covers the whole window to catch event for drag/resize
        self.overlay = builder.get_object('overlay')
        self.overlay.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.overlay_style_context = self.overlay.get_style_context()

        # TitleBar - the title bar at the top of the window
        self.title_bar = builder.get_object('title_bar')
        self.title_bar_label = builder.get_object('title_bar_label')
        self.title_bar_button = builder.get_object('title_bar_button')

        #  WidgetBox - the box that the widget actually gets added to
        self.widget_box = builder.get_object('widget_box')

        self.title_bar_label.set_text(title)
        self.widget_box.add(self.module_widget)
        self.add(self.widget_window)

        if hasattr(self.module_widget, 'on_settings_button_pressed'):
            menu_btn.connect('clicked', self.module_widget.on_settings_button_pressed)

        self.show_all()


    def show_overlay(self, setting):
        if setting:
            self.overlay.show()
        else:
            self.overlay.hide()

    def on_key_press(self, widget, event):

        # Events that don't need to know about modifiers
        if event.keyval == Gdk.KEY_Escape:
            self.unselect()
            return True
        if event.keyval == Gdk.KEY_Delete:
            self.destroy()
            return True
        if event.keyval == Gdk.KEY_Tab:
            print 'Select next'
            return False

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

    def select(self):
        # Bring self to top of z-order
        #self.bring_to_top()

        # Grab focus so can catch key-press events
        self.overlay.grab_focus()

        # If another WidgetWindow was previously selected, remove selected style
        if WidgetWindow.selected:
            WidgetWindow.selected.overlay_style_context.remove_class('selected')

        # Add selected style class to self
        self.overlay_style_context.add_class('selected')

        # Record self as last selected, so can un-select when another gets focus
        WidgetWindow.selected = self

    def unselect(self):
        # Don't have focus anymore
        self.get_toplevel().set_focus(None)

        # Remove selected style class from self
        if WidgetWindow.selected:
            WidgetWindow.selected.overlay_style_context.remove_class('selected')

    def bring_to_top(self):
        # FIXME this causes erratic drags, why????
        # Get the widgets position in the WidgetArea
        x = self.parent.child_get_property(self, 'x')
        y = self.parent.child_get_property(self, 'y')

        # KLUDGE Remove and re-add to bring to top of z-order
        self.parent.remove(self)
        self.parent.put(self, x, y)


#===================================
#  Drag to Move / Resize
#===================================

    def on_drag_begin(self, widget, event):

        # Get the WidgetArea that self is a child of
        self.parent = self.get_parent()

        # Highlight self and give focus
        self.select()

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

    def on_drag_motion(self, widget, event):
        if self.action == self.parent.Drag.MOVE:
            self.parent.child_move_motion(self, event)
        elif self.action >= self.parent.Drag.RESIZE_X:
            self.parent.child_resize_motion(self, event, self.action)

    def on_drag_end(self, widget, event):
        if self.action == self.parent.Drag.MOVE:
            self.parent.child_move_end(self)
        elif self.action >= self.parent.Drag.RESIZE_X:
            self.parent.child_resize_end(self)
