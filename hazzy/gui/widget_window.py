#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk


# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

# Actions
MOVE = 0
RESIZE_X = 1
RESIZE_Y = 2
RESIZE_XY = 3


class WidgetWindow(Gtk.Box):

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
        self.widget_overlay = builder.get_object('widget_overlay')

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
            self.widget_overlay.show()
        else:
            self.widget_overlay.hide()

#===================================
#  Drag to Move / Resize
#===================================

    def on_drag_begin(self, widget, event):
        self.parent = self.get_parent()
        w = widget.get_allocation().width
        h = widget.get_allocation().height

        if event.y <= 50:
            self.action = MOVE
            self.parent.move_begin(self, event)
        elif event.x >= w - 50 and event.y >= h -50:
            self.action = RESIZE_XY
            self.parent.resize_begin(self, event)
        elif event.x >= w - 50:
            self.action = RESIZE_X
            self.parent.resize_begin(self, event)
        elif event.y >= h -50:
            self.action = RESIZE_Y
            self.parent.resize_begin(self, event)
        else:
            self.action = None

    def on_drag_motion(self, widget, event):
        if self.action == MOVE:
            self.parent.move_motion(self, event)
        elif self.action >= RESIZE_X:
            self.parent.resize_motion(self, event, self.action)

    def on_drag_end(self, widget, event):
        if self.action == MOVE:
            self.parent.move_end(self)
        elif self.action >= RESIZE_X:
            self.parent.resize_end(self)
