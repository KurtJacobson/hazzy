#!/usr/bin/env python
import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from constants import Paths
from hazzy.dashboard import HazzyWindow

BASE = None
INIFILE = None


def main(argv):

    BASE = os.path.abspath(os.path.dirname(argv[0]))

    if sys.argv[1] != "-ini":
        raise SystemExit("-ini must be first argument")

    INIFILE = argv[2]

    style_provider = Gtk.CssProvider()

    with open(os.path.join(Paths.STYLEDIR, "style.css"), 'rb') as css:
        css_data = css.read()

    style_provider.load_from_data(css_data)

    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    hazzy_window = HazzyWindow()
    hazzy_window.show_all()

    hazzy_window.connect('delete-event', Gtk.main_quit)

    Gtk.main()


if __name__ == "__main__":
    main(sys.argv)
