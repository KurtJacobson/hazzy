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
import logging

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk

log = logging.getLogger("HAZZY.TOUCHPAD")

class TouchPad:
    def __init__(self, test=False):
        self.window = TouchPadWindow()
        self.dro = None
        self.original_text = None

        if test:
            self.window.disable_dot()
            self.window.show()

    def show(self, widget, kind="float"):

        if kind != "float":
            self.window.disable_dot()

        self.dro = widget
        self.original_text = self.dro.get_text()

        self.window.show()


class TouchPadWindow(Gtk.Window):
    def __init__(self):
        super(TouchPadWindow, self).__init__()

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join("modules", "touchpads", "ui", "int_numpad_3.glade"))
        builder.connect_signals(TouchPadHandler())

        style_provider = Gtk.CssProvider()

        with open(os.path.join("styles", "style.css"), 'rb') as css:
            css_data = css.read()

        style_provider.load_from_data(css_data)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        numpad = builder.get_object("numpad")

        self.dot_button = builder.get_object("dot")

        self.add(numpad)

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_modal(True)
        self.set_decorated(False)

    def disable_dot(self):
        self.dot_button.set_sensitive(False)


class TouchPadHandler:
    @staticmethod
    def on_numpad_delete_event(*args):
        Gtk.main_quit(*args)

    @staticmethod
    def on_cancel_clicked(*args):
        Gtk.main_quit(*args)

    @staticmethod
    def on_ok_clicked(*args):
        Gtk.main_quit(*args)

    def on_numpad_key_release_event(self, widget, event):
        key_name = Gdk.keyval_name(event.keyval)
        log.debug("key pressed from keyboard: {0}".format(key_name))

    def on_button_clicked(self, button):
        button_name = button.get_name()
        log.debug("button pressed from touchpad :{0}".format(button_name))


def main():
    TouchPad(test=True)
    Gtk.main()

if __name__ == "__main__":
    main()
