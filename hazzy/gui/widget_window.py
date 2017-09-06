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

    def __init__(self, package, widget, title, menu_callback=None):
        Gtk.Box.__init__(self)

        self.package = package
        self.title = title

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(PYDIR, 'ui', 'widgetwindow.ui'))
        builder.connect_signals(self)

        menu_btn = builder.get_object('menu_button')
        label = builder.get_object('label')
        box = builder.get_object('box')
        wwindow = builder.get_object('widgetwindow')
        self.overlay = builder.get_object('overlay')

        label.set_text(title)
        box.add(widget)

        self.add(wwindow)

        if menu_callback:
            self.menu_btn.connect('pressed', menu_callback, self)

        self.show_all()

    def show_overlay(self, setting):
        if setting:
            self.overlay.show()
        else:
            self.overlay.hide()

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
