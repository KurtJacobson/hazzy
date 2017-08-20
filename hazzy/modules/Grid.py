#!/usr/bin/env python

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from gcodeview.gcodeview import GcodeViewWidget
from widgetchooser.widgetwindow import WidgetWindow


class Grid(Gtk.Fixed):

    def __init__(self):
        GObject.GObject.__init__(self)

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.add()


    def add(self):

        # Widget No.1
        widget = GcodeViewWidget()
        size = [400, 300]
        name = 'G-code'
        wwindow = WidgetWindow(widget, size, name)
        self.put(wwindow, 0, 0)

        # Widget No.2
        widget = GcodeViewWidget()
        size = [400, 300]
        name = 'G-code'
        wwindow = WidgetWindow(widget, size, name)
        self.put(wwindow, 400, 0)


def main():
    ui = Grid()
    win = Gtk.Window()
    win.set_default_size(1000, 700)
    win.add(ui)
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
