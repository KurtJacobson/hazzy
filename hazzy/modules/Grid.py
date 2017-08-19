#!/usr/bin/env python

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from gcodeview.gcodeview import GcodeViewWidget
from widgetchooser.widgetwindow import WidgetWindow

ROWS = 35
COLUMNS = 50

class Grid(Gtk.Grid):

    def __init__(self):
        GObject.GObject.__init__(self)

        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_column_homogeneous(True)
        self.set_row_homogeneous(True)

        # Add row placeholders
        for i in range(1, ROWS):
            lbl = Gtk.Label()
            self.attach(lbl, 0, i, 1, 1)

        # Add column placeholders
        for i in range(1, COLUMNS):
            lbl = Gtk.Label()
            self.attach(lbl, i, 0, 1, 1)

        self.add()

        self.popover = Popover(self)

        win = Gtk.Window()
        win.set_default_size(1000, 700)
        win.add(self)
        win.connect('destroy', Gtk.main_quit)
        win.show_all()

    def add(self):
        view = GcodeViewWidget()
        wwindow = WidgetWindow(view, 'G-code', self.on_menu_btn_pressed)
        self.attach(wwindow, 0, 0, 15, 10)

        view2 = GcodeViewWidget()
        wwindow2 = WidgetWindow(view2, 'G-code', self.on_menu_btn_pressed)
        self.attach_next_to(wwindow2, wwindow, Gtk.PositionType.RIGHT, 15, 10)

    def set_x(self, widget, x):
        self.child_set_property(widget, 'top_attach', x)

    def set_y(self, widget, y):
        self.child_set_property(widget, 'left_attach', y)

    def set_w(self, widget, width):
        self.child_set_property(widget, 'width', width)

    def set_h(self, widget, height):
        self.child_set_property(widget, 'height', height)

    def get_x(self, widget):
        return self.child_get_property(widget, 'top_attach')

    def get_y(self, widget):
        return self.child_get_property(widget, 'left_attach')

    def get_w(self, widget):
        return self.child_get_property(widget, 'width')

    def get_h(self, widget):
        return self.child_get_property(widget, 'height')

    def on_menu_btn_pressed(self, btn, widget):
        self.popover.show(btn, widget)


class Popover(Gtk.Popover):

    def __init__(self, grid):
        GObject.GObject.__init__(self)

        self.grid = grid
        self.wid = None

        builder = Gtk.Builder()
        builder.add_from_file('popover.ui')
        popover = builder.get_object('popover')

        self.x = builder.get_object('x_pos_adj')
        self.y = builder.get_object('y_pos_adj')

        self.w = builder.get_object('width_adj')
        self.h = builder.get_object('height_adj')

        self.x.connect('value-changed', self.on_x_changed)
        self.y.connect('value-changed', self.on_y_changed)
        self.w.connect('value-changed', self.on_w_changed)
        self.h.connect('value-changed', self.on_h_changed)

        popover.reparent(self)


    def show(self, btn, widget):
        self.set_relative_to(btn)
        self.wid = widget

        self.x.set_value(self.grid.get_x(widget))
        self.y.set_value(self.grid.get_y(widget))
        self.w.set_value(self.grid.get_w(widget))
        self.h.set_value(self.grid.get_h(widget))

        self.popup()

    def on_x_changed(self, widget):
        value = self.x.get_value()
        self.grid.set_x(self.wid, value)

    def on_y_changed(self, widget):
        value = self.y.get_value()
        self.grid.set_y(self.wid, value)

    def on_w_changed(self, widget):
        value = self.w.get_value()
        self.grid.set_w(self.wid, value)

    def on_h_changed(self, widget):
        value = self.h.get_value()
        self.grid.set_h(self.wid, value)


def main():
    Gtk.main()

if __name__ == "__main__":
    ui = Grid()
    main()
