#!/usr/bin/env python
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from hazzy.dashboard import HazzyWindow


def main():
    hazzy_window = HazzyWindow()
    hazzy_window.show_all()

    Gtk.main()

if __name__ == "__main__":
    main()