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
from gi.repository import Gtk, GObject

from constants import Paths

# Import our own modules
from hazzy.utilities import logger
from hazzy.modules.widgetchooser.widgetchooser import DragSourcePanel
from hazzy.modules.widgetchooser.widgetchooser import DropArea

from hazzy.modules.pydock.StarArrowButton import StarArrowButton
from hazzy.modules.pydock.HighliightArea import HighlightArea

log = logger.get('HAZZY.DASHBOARD')


class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        gladefile = os.path.join(Paths.UIDIR, 'hazzy_3.ui')

        self.dockable = True

        self.iconview = DragSourcePanel()
        self.drop_area = DropArea() #Gtk.Box()

        self.iconview.connect("drag-begin", self.__onDragBegin),
        self.iconview.connect("drag-end", self.__onDragEnd),
        # self.connect_after("switch-page", self.__onPageSwitched),

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

        self.highlightArea = HighlightArea(self.drop_area)

        self.button_cids = []

        self.starButton = StarArrowButton(
            self,
            os.path.join(Paths.UIDIR, "dock_top.svg"),
            os.path.join(Paths.UIDIR, "dock_right.svg"),
            os.path.join(Paths.UIDIR, "dock_bottom.svg"),
            os.path.join(Paths.UIDIR, "dock_left.svg"),
            os.path.join(Paths.UIDIR, "dock_center.svg"),
            os.path.join(Paths.UIDIR, "dock_star.svg")
        )

        self.button_cids += [
            self.starButton.connect("dropped", self.__onDrop),
            self.starButton.connect("hovered", self.__onHover),
            self.starButton.connect("left", self.__onLeave),
        ]


        self.add_targets()

    def on_reveal_clicked(self, button):
        reveal = self.revealer_area.get_reveal_child()
        self.revealer_area.set_reveal_child(not reveal)

    def add_targets(self):
        self.drop_area.drag_dest_set_target_list(None)
        self.iconview.drag_source_set_target_list(None)

        self.drop_area.drag_dest_add_text_targets()
        self.iconview.drag_source_add_text_targets()

    def __onDragBegin(self, widget, context):
        print 'onDragBegin'
        self.starButton.show_all()

    def __onDragEnd(self, widget, context):
        print 'onDragEnd'
        self.starButton.hide()

    def __onDrop(self, starButton, position, sender):
        print 'onDrop'
        self.highlightArea.hide()

        # if the undocked leaf was alone, __onDragEnd may not triggered
        # because leaf was removed
        for instance in self.getInstances(self.perspective):
            instance.hideArrows()

        if self.dockable:
            if sender.get_parent() == self and self.book.get_n_pages() == 1:
                return
            # cp = sender.get_current_page()
            child = sender.get_nth_page(sender.get_current_page())
            title, id = sender.get_parent().undock(child)
            self.dock(child, position, title, id)

    def __onHover(self, starButton, position, widget):
        print 'onHover'
        if self.dockable:
            self.highlightArea.showAt(position)
            starButton.get_window().raise_()

    def __onLeave(self, starButton):
        print "onLeave"
        self.highlightArea.hide()



class DropArea(Gtk.Grid):

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

#        lbl = Gtk.Button.new_with_label('Test1')
#        self.attach(lbl, 1, 1, 1, 1)

#        lbl = Gtk.Button.new_with_label('Test2')
#        self.attach(lbl, 2, 3, 1, 1)
