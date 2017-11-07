#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   MessageBar for use in the WidgetWindow. Useful for displaying general
#   widget specific messages and for use as a basic YES/NO dialog.

# Note:
#    This scrip can be run by itself for demonstration or testing.

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

class MessageBar(Gtk.Revealer):

    def __init__(self):
        Gtk.Revealer.__init__(self)

        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.START)

        self.style_context = self.get_style_context()
        self.time_out_id = None
        self.signal_1_id = None
        self.signal_2_id = None

        # Main Bar
        self.bar = Gtk.Box(Gtk.Orientation.HORIZONTAL)
        self.add(self.bar)

        # Message Icon
        self.icon = Gtk.Image()
        self.bar.pack_start(self.icon, False, False, 0)

        # Message Label
        self.label = Gtk.Label('Info')
        self.label.set_margin_left(5)
        self.label.set_line_wrap(True)
        self.bar.pack_start(self.label, False, False, 0)

        # Close button
        self.close_button = Gtk.Button()
        close_icon = Gtk.Image.new_from_icon_name('window-close-symbolic',
                                                        Gtk.IconSize.MENU)
        self.close_button.add(close_icon)
        self.close_button.connect('clicked', self.close)
        self.bar.pack_end(self.close_button, False, False, 0)

        self.button_2 = Gtk.Button('No')
        self.bar.pack_end(self.button_2, False, False, 0)

        self.button_1 = Gtk.Button('Yes')
        self.bar.pack_end(self.button_1, False, False, 0)

    def close(self, widget=None):
        self.reveal(False)
        # Ether the message timed out or user closed, either way, no timeout
        self.time_out_id = None
        self.disconnect_signals()

    def show_info(self, message='Undefined', timeout=2):
        self.button_1.hide()
        self.button_2.hide()
        self.close_button.show()
        self.label.set_text(message)
        self.set_style('blue')
        self.reveal(True)
        self.set_timout(timeout)

    def reveal(self, reveal):
        self.set_reveal_child(reveal)
        self.disconnect_signals()

    def show_warning(self, message='Undefined', timeout=10):
        self.button_1.hide()
        self.button_2.hide()
        self.close_button.show()
        self.label.set_text(message)
        self.set_style('yellow')
        self.reveal(True)
        self.set_timout(timeout)

    def show_error(self, message='Undefined', timeout=None):
        self.button_1.hide()
        self.button_2.hide()
        self.close_button.show()
        self.label.set_text(message)
        self.set_style('red')
        self.reveal(True)
        self.set_timout(timeout)

    def show_question(self, message='Undefined', callback=None, *args, **kwargs):
        self.close_button.hide()
        self.button_1.show()
        self.button_2.show()

        self.label.set_text(message)
        self.set_style('blue')

        self.reveal(True)

        if not callback:
            callback = self.default_callback

        self.signal_1_id = self.button_1.connect('clicked',
                                                    self.on_yes_clicked,
                                                    callback, *args, **kwargs)
        self.signal_2_id = self.button_2.connect('clicked',
                                                    self.on_no_clicked,
                                                    callback, *args, **kwargs)

    def show_confirmation(selfm, message='Undefined'):
        raise NotImplemented

    def set_style(self, style_class):
        for klass in self.style_context.list_classes():
            self.style_context.remove_class(klass)
        self.style_context.add_class(style_class)

    def set_timout(self, timeout):
        if self.time_out_id:
            # Remove any active timeout
            GObject.source_remove(self.time_out_id)
            self.time_out_id = None
        if timeout:
            self.time_out_id = GObject.timeout_add(timeout * 1000, self.close)

    def on_yes_clicked(self, widget, callback, *args, **kwargs):
        callback(Gtk.ResponseType.YES, *args, **kwargs)
        self.close()

    def on_no_clicked(self, widget, callback, *args, **kwargs):
        callback(Gtk.ResponseType.NO, *args, **kwargs)
        self.close()

    def on_ok_clicked(self, widget, callback, *args, **kwargs):
        callback(Gtk.ResponseType.OK, *args, **kwargs)
        self.close()

    def on_cancel_clicked(self, widget, callback, *args, **kwargs):
        callback(Gtk.ResponseType.CANCEL, *args, **kwargs)
        self.close()

    def disconnect_signals(self):
        if self.signal_1_id:
            self.button_1.disconnect(self.signal_1_id)
            self.signal_1_id = None
        if self.signal_2_id:
            self.button_2.disconnect(self.signal_2_id)
            self.signal_2_id = None

    def default_callback(self, response, *args, **kwargs):
        print('MessageBar response: {}'.format(response))


class Demo(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='MessageBar Demo')

        self.set_default_size(400, 200)
        self.connect('destroy', Gtk.main_quit)

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(os.path.join('..', "themes/style.css"))

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.overlay = Gtk.Overlay()
        self.add(self.overlay)

        button_box = Gtk.ButtonBox()
        button_box.set_halign(Gtk.Align.FILL)
        button_box.set_valign(Gtk.Align.END)
        button_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        button_box.set_margin_bottom(5)

        # Show info message button
        btn = Gtk.Button('Info')
        btn.connect('clicked', self.show_info)
        button_box.add(btn)

        # Show warning message button
        btn = Gtk.Button('Warning')
        btn.connect('clicked', self.show_warning)
        button_box.add(btn)

        # Show error message button
        btn = Gtk.Button('Error')
        btn.connect('clicked', self.show_error)
        button_box.add(btn)

        # Show question message button
        btn = Gtk.Button('Question')
        btn.connect('clicked', self.show_question)
        button_box.add(btn)

        self.overlay.add(button_box)

        self.message_bar = MessageBar()
        self.overlay.add_overlay(self.message_bar)

        self.show_all()
        Gtk.main()

    def show_info(self, widegt):
        self.message_bar.show_info('This is an info message')

    def show_warning(self, widegt):
        self.message_bar.show_warning('This is an warning message')

    def show_error(self, widegt):
        self.message_bar.show_error('This is an error message')

    def show_question(self, widget):
        self.message_bar.show_question('This is a question. Do you like it?')

if __name__ == '__main__':
    Demo()
