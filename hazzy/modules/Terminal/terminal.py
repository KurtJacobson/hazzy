#!/usr/bin/env python

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Vte
from gi.repository import GLib

PYDIR = os.path.join(os.path.dirname(__file__))

print "PYDIR", PYDIR

class Terminal(Vte.Terminal):

    def __init__(self):
        Vte.Terminal.__init__(self)

        self.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            PYDIR,                                  # working directory
            ["/usr/bin/python"],
            None,
            GLib.SpawnFlags.CHILD_INHERITS_STDIN,
            None,
            None,
            )

        self.set_size_request(200, 200)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.set_font_scale(1.25)


def main():
    win = Gtk.Window()
    win.connect('delete-event', Gtk.main_quit)
    win.add(Terminal())
    win.show_all()

    Gtk.main()

if __name__ == '__main__':
    main()
