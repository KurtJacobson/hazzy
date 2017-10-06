#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from utilities import preferences as prefs

from widget_factory.TouchPads import keyboard


class TextEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)

        self.previous_value = ""

        self.connect('focus-in-event', self.on_focus_in)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('key-press-event', self.on_key_press)
        self.connect('activate', self.on_activate)

    def on_focus_in(self, widegt, event):
        self.previous_value = self.get_text()
        #keyboard.show(self)

    def on_focus_out(self, widegt, event):
        pass

    def on_activate(self, widget):
        print "got activate"
        self.get_toplevel().set_focus(None)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.set_text(self.previous_value) # Revert
            self.get_toplevel().set_focus(None)
