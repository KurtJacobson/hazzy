#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

from utilities import status
from utilities import machine_info
from widget_factory.dros import DroType, DroEntry, G5xEntry, DroCover

class Dro(Gtk.Grid):

    def __init__(self, widget_window):
        Gtk.Grid.__init__(self)

        self.widget_window = widget_window

        self.set_size_request(60, 60)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.set_row_spacing(5)
        self.set_column_spacing(5)

        axes = machine_info.axis_letter_list

        status.on_changed('stat.g5x_index', self.update_g5x_label)

        # Column labels
        self.g5x_label = Gtk.Label()
        self.attach(self.g5x_label, 2, 0, 1, 1)

        self.abs_label = Gtk.Label('Absolute')
        self.attach(self.abs_label, 3, 0, 1, 1)

        self.dtg_label = Gtk.Label('Remaining')
        self.attach(self.dtg_label, 4, 0, 1, 1)

        count = 1
        for axis in axes:
            # Axis Lables
            label = Gtk.Label(axis.upper())
            self.attach(label, 1, count, 1, 1)

            # G5x DRO
            entry = G5xEntry(axis, DroType.REL)
            self.attach(entry, 2, count, 1, 1)

            # ABS DRO
            label = DroEntry(axis, DroType.ABS)
            box = DroCover() # Temp kludge to make un-editable/un-selectable
            self.attach(box, 3, count, 1, 1)
            self.attach(label, 3, count, 1, 1)

            # DTG DRO
            label = DroEntry(axis, DroType.DTG)
            box = DroCover() # Temp kludge to make un-editable/un-selectable
            self.attach(box, 4, count, 1, 1)
            self.attach(label, 4, count, 1, 1)

            count += 1

    def update_g5x_label(self, widget, g5x_index):
        work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
        self.g5x_label.set_text(work_cords[g5x_index])
