#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

HERE = os.path.abspath(os.path.dirname(__file__))
print HERE


class Icons(Gtk.Window):
    def __init__(self):
        super(Icons, self).__init__()

        self.connect('destroy', Gtk.main_quit)

        self.theme = Gtk.IconTheme.get_default()
        self.theme.prepend_search_path(HERE)
        icon = self.theme.load_icon('tab-symbolic', 48, Gtk.IconLookupFlags.FORCE_SYMBOLIC)
        image = Gtk.Image.new_from_pixbuf(icon)

        btn = Gtk.Button(image=image)

        self.add(btn)

def demo():
    win = Icons()
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    demo()
