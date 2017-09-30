#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk

PYDIR = os.path.join(os.path.dirname(__file__))

from utilities import ini_info
from utilities import machine_info
from utilities.status import Status
from utilities import entry_eval

class AxisDro(Gtk.Grid):

    def __init__(self):
        Gtk.Grid.__init__(self)

        self.set_size_request(60, 60)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.set_row_spacing(5)
        self.set_column_spacing(5)

        axes = machine_info.axis_letter_list

        self.stat = Status
        self.stat.on_value_changed('g5x_index', self.update_g5x_label)

        # Column labels
        self.g5x_label = Gtk.Label()
        self.attach(self.g5x_label, 2, 0, 1, 1)

        self.abs_label = Gtk.Label('Machine')
        self.attach(self.abs_label, 3, 0, 1, 1)

        count = 1
        for axis in axes:
            # Axis Lables
            label = Gtk.Label(axis)
            self.attach(label, 1, count, 1, 1)

            # G5x entry
            entry = G5xEntry(axis)
            self.attach(entry, 2, count, 1, 1)

            #
            label = Gtk.Entry()
            label.set_text("0.00000")
            label.set_editable(False)
            self.attach(label, 3, count, 1, 1)

            count += 1

    def update_g5x_label(self, widget, g5x_index):
        work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
        self.g5x_label.set_text(work_cords[g5x_index])


class G5xEntry(Gtk.Entry):
    def __init__(self, axis_letter):
        Gtk.Entry.__init__(self)

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.axis_letter = axis_letter

        self.has_focus = False

        self.connect('focus-in-event', self.on_focus_in)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('key-press-event', self.on_key_press)
        self.connect('activate', self.on_activate)

    def on_focus_in(self, widget, event):
        if not self.has_focus:
            widget.select_region(0, -1)
            self.has_focus = True

    def on_focus_out(self, widget, data=None):
        self.has_focus = False

    def on_key_press(self, widget, event, data=None):
        if event.keyval == Gdk.KEY_Escape:
            self.dro_has_focus = False
            self.get_toplevel().set_focus(None)

    def on_activate(self, widget):
        expr = self.get_text().lower()
        val = entry_eval.eval(expr)
        if val is not None:
            self.set_text(str(val))
            #cmd.set_work_offset(axis_letter, val)
        print val
