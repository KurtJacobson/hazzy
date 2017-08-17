#!/usr/bin/env python

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from gcodeview.gcodeview import GcodeViewWidget
from widgetchooser.widgetwindow import WidgetWindow


class Grid(Gtk.Grid):

    def __init__(self):
        GObject.GObject.__init__(self)

        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_column_homogeneous(True)
        self.set_row_homogeneous(True)

        columns = 10

        lbl = Gtk.Label.new('0')
        self.attach(lbl, 0, 0, 1, 1)

        for i in range(1, columns):
            lbl = Gtk.Label.new('{}'.format(i))
            self.attach(lbl, 0, i, 1, 1)

        for i in range(1, columns):
            lbl = Gtk.Label.new('{}'.format(i))
            self.attach(lbl, i, 0, 1, 1)

        lbl = Gtk.Button.new_with_label('Test1')
        lbl.connect('pressed', self.add)
        self.attach(lbl, 10, 1, 1, 1)

        win = Gtk.Window()
        win.set_size_request(500, 400)
        win.add(self)
        win.connect('destroy', Gtk.main_quit)
        win.connect('button-press-event', self.on_button_press)
        win.show_all()


    def add(self, widget):
        view = GcodeViewWidget()
        wwindow = WidgetWindow(view, 'G-code View')
        self.attach(wwindow, 0, 0, 5, 5)


    def on_button_press(self, widget, position):
        w, h = self.get_size_request()
        x = (position.x / w) / 10
        print x
        print self.get_child_at(x , position.y)


    def refresh_placholders(self):
        pass


def main():
    Gtk.main()

if __name__ == "__main__":
    ui = Grid()
    main()
