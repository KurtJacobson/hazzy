import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))


class WidgetWindow(Gtk.Box):
    def __init__(self, widget, label, menu_callback):
        Gtk.Box.__init__(self)

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(PYDIR, 'ui', 'widgetwindow.ui'))

        self.menu_btn = builder.get_object('menu_button')
        self.label = builder.get_object('label')
        self.box = builder.get_object('box')
        self.wwindow = builder.get_object('widgetwindow')

        self.label.set_text(label)
        self.box.add(widget)
        self.add(self.wwindow)

        self.menu_btn.connect('pressed', menu_callback, self)

        self.show_all()
