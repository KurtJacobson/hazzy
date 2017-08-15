#!/usr/bin/env python

#   An attempt at a new UI for LinuxCNC that can be used
#   on a touch screen without any lost of functionality.
#   The code is written in python and glade and is almost a
#   complete rewrite, but was influenced mainly by Gmoccapy
#   and Touchy, with some code adapted from the HAL VCP widgets.

#   Copyright (c) 2017 Kurt Jacobson
#       <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

import os
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from constants import Paths

# Import our own modules
from hazzy.utilities import logger
from hazzy.utilities.widgetchooser import DragSourcePanel
from hazzy.utilities.widgetchooser import DropArea

log = logger.get('HAZZY')

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)


class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Hazzy")

        gladefile = os.path.join(Paths.UIDIR, 'hazzy_3.ui')

        self.iconview = DragSourcePanel()

        self.drop_area = DropArea()

        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)

        self.panel = self.builder.get_object('panel')
        self.titlebar = self.builder.get_object('titlebar')
        self.revealer_button = self.builder.get_object('revealer_button')
        self.revealer_area = self.builder.get_object('revealer_area')

        self.set_titlebar(self.titlebar)

        self.revealer_area.add(self.iconview)
        self.panel.pack_start(self.drop_area, True, True, 0)

        self.add(self.panel)
        self.panel.show_all()

        self.revealer_button.connect("clicked", self.on_reveal_clicked)

        self.add_targets()

    def on_reveal_clicked(self, button):
        reveal = self.revealer_area.get_reveal_child()
        self.revealer_area.set_reveal_child(not reveal)

    def add_targets(self):

        self.drop_area.drag_dest_set_target_list(None)
        self.iconview.drag_source_set_target_list(None)

        self.drop_area.drag_dest_add_text_targets()
        self.iconview.drag_source_add_text_targets()
