#!/usr/bin/env python

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Gdk
from gi.repository import Vte, GLib

PYDIR = os.path.join(os.path.dirname(__file__))

class Terminal(Gtk.ScrolledWindow):

    def __init__(self, widget_window):
        Gtk.ScrolledWindow.__init__(self)

        self.terminal=Vte.Terminal()
        self.terminal.spawn_sync(
                Vte.PtyFlags.DEFAULT,   # depreciated, does nothing?
                os.environ['HOME'],     # where to start the command?
                ["/bin/bash"],          # where is the emulator?
                [],                     # it's ok to leave this list empty
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,                   # at least None is required
                None,
                )

        self.terminal.set_font_scale(1.1)

        self.terminal.connect('key-press-event', self.on_key_press)

        self.set_size_request(200, 200)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.add(self.terminal)

    def on_key_press(self, widget, event):

        # Determine the actively pressed modifier
        modifier = event.get_state() & Gtk.accelerator_get_default_mod_mask()

        # Bool of Control or Shift modifier states
        control = modifier == Gdk.ModifierType.CONTROL_MASK
        shift = modifier == Gdk.ModifierType.SHIFT_MASK

        # Reset terminal instead of exiting
        kv = event.keyval
        if control or shift or (control and shift):
            if kv == Gdk.KEY_d:
                self.terminal.feed_child("reset\n", -1)
                return True

def main():
    win = Gtk.Window()
    win.connect('delete-event', Gtk.main_quit)
    win.add(Terminal())
    win.show_all()

    Gtk.main()

if __name__ == '__main__':
    main()
