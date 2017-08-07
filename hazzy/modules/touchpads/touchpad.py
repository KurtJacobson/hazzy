#!/usr/bin/env python

#   Popup numberpad for use on all numeric only entries
#
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
from gi.repository import Gdk


class TouchpadHandler:

    def on_numpad_delete_event(self, *args):
        Gtk.main_quit(*args)

    def on_cancel_clicked(self, *args):
        Gtk.main_quit(*args)

    def on_ok_clicked(self, *args):
        Gtk.main_quit(*args)

    def on_numpad_key_release_event(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        print(keyname)

    def on_button_clicked(self, button):

        print(button.get_name())

builder = Gtk.Builder()
builder.add_from_file(os.path.join("modules", "touchpads", "ui", "int_numpad_3.glade"))

builder.connect_signals(TouchpadHandler())

style_provider = Gtk.CssProvider()

css = open(os.path.join("styles", "style.css"), 'rb')
css_data = css.read()
css.close()

style_provider.load_from_data(css_data)

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

win = builder.get_object("numpad")
win.show_all()

Gtk.main()
