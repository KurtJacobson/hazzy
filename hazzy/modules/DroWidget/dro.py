#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

PYDIR = os.path.join(os.path.dirname(__file__))

from utilities import ini_info
from utilities import machine_info
from utilities import status
from utilities import entry_eval
from utilities import preferences as prefs
from gui import widgets

class AxisDro(Gtk.Grid):

    def __init__(self):
        Gtk.Grid.__init__(self)

        self.set_size_request(60, 60)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.set_row_spacing(5)
        self.set_column_spacing(5)

        axes = machine_info.axis_letter_list

        status.on_value_changed('g5x_index', self.update_g5x_label, False)

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
            label = Gtk.Label(axis)
            self.attach(label, 1, count, 1, 1)

            # G5x DRO
            entry = G5xEntry(axis, DroEntry.DroType.REL)
            self.attach(entry, 2, count, 1, 1)

            # ABS DRO
            label = DroEntry(axis, DroEntry.DroType.ABS)
            self.attach(label, 3, count, 1, 1)

            # DTG DRO
            label = DroEntry(axis, DroEntry.DroType.DTG)
            box = LabelCover()
            self.attach(box, 4, count, 1, 1)
            self.attach(label, 4, count, 1, 1)

            count += 1

    def update_g5x_label(self, widget, g5x_index):
        work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
        self.g5x_label.set_text(work_cords[g5x_index])



class LabelCover(Gtk.EventBox):
    def __init__(self):
        Gtk.EventBox.__init__(self)
        self.connect('button-press-event', self.on_button_press)

    def on_button_press(self, widget, event):
        widget.get_toplevel().set_focus(None)


class DroEntry(Gtk.Entry):
    ''' Base DRO entry class '''

    class DroType:
        REL = 0
        ABS = 1
        DTG = 2

    def __init__(self, axis_letter, dro_type=DroType.REL):
        Gtk.Entry.__init__(self)

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.set_alignment(1)
        self.set_width_chars(8)

        self.set_name('dro')

        font = Pango.FontDescription('16')
        self.modify_font(font)

        self.axis_letter = axis_letter
        self.axis_num = 'xyzabcuvw'.index(self.axis_letter.lower())

        self.dro_type = dro_type

        self.has_focus = False

        self.connect('button-release-event', self.on_button_release)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('key-press-event', self.on_key_press)
        self.connect('activate', self.on_activate)

        status.on_value_changed('axis-positions', self._update_dro, False)

    def _update_dro(self, widget, positions):
        if not self.has_focus: # Don't step on user trying to enter value
            pos = positions[self.dro_type][self.axis_num]
            pos_str = '{:.{dec_plcs}f}'.format(pos, dec_plcs=4)
            self.set_text(pos_str)

    def on_button_release(self, widget, data=None):
        if not self.has_focus:
            self.select()
            return True

    def on_focus_out(self, widget, data=None):
        self.unselect()

    def on_activate(self, widget, data=None):
        self.unselect()

    def on_key_press(self, widget, event, data=None):
        if event.keyval == Gdk.KEY_Escape:
            self.unselect()

    def select(self):
        self.select_region(0, -1)
        self.has_focus = True

    def unselect(self):
        self.select_region(0, 0)
        self.get_toplevel().set_focus(None)
        self.has_focus = False


class G5xEntry(DroEntry):
    ''' G5x DRO entry class. Allows setting work offset by typing into DRO '''

    def __init__(self, axis_letter, dro_type):
        DroEntry.__init__(self, axis_letter, dro_type)

        self.on_icon_toggled(True)

    def on_icon_toggled(self, setting):
        if setting:
            icon_name = "go-home-symbolic"
        else:
            icon_name = None
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, icon_name)

    def on_activate(self, widget):
        expr = self.get_text().lower()
        val = entry_eval.eval(expr)
        if val is not None:
            self.set_text(str(val))
            #cmd.set_work_offset(axis_letter, val)
        print val
