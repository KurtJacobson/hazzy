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

        self.activate_on_focus_out = False
        self._was_activated = False

        self.previous_value = ""

        self.connect('focus-in-event', self.on_focus_in)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('key-press-event', self.on_key_press)
        self.connect('activate', self.on_activate)

    def on_focus_in(self, widegt, event):
        self.previous_value = self.get_text()
        keyboard.show(self)

    def on_focus_out(self, widegt, event):
        if self._was_activated:
            return
        if self.activate_on_focus_out:
            # FixMe This does not work :(
            self.do_activate(widegt)
        else:
            # Revert
            self.set_text(self.previous_value)
        # Reset flag
        self._was_activated = False

    def on_activate(self, widget):
        self._was_activated = True
        self.get_toplevel().set_focus(None)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.set_text(self.previous_value) # Revert
            self.get_toplevel().set_focus(None)
