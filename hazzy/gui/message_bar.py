#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from utilities.constants import MessageType


class MessageBar(Gtk.Revealer):

    def __init__(self):
        Gtk.Revealer.__init__(self)

        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.START)

        # Main Bar
        self.bar = Gtk.Box(Gtk.Orientation.HORIZONTAL)
        self.bar_style_context = self.bar.get_style_context()
        self.add(self.bar)

        # Message Icon
        self.icon = Gtk.Image()
        self.bar.pack_start(self.icon, False, False, 0)

        # Message Label
        self.label = Gtk.Label('Info')
        self.label.set_margin_left(5)
        self.bar.pack_start(self.label, False, False, 0)

        # Close button
        self.button = Gtk.Button()
        close_icon = Gtk.Image.new_from_icon_name('window-close-symbolic',
                                                        Gtk.IconSize.MENU)
        self.button_style_context = self.button.get_style_context()
        self.button.add(close_icon)
        self.button.connect('clicked', self.close)
        self.bar.pack_end(self.button, False, False, 0)

    def close(self, widget=None):
        self.set_reveal_child(False)

    def show_info(self, message='Undefined', timeout=None):
        self.label.set_text(message)
        self.bar_style_context.add_class('blue_bar')
        self.button_style_context.add_class('blue_button')
        self.set_reveal_child(True)
        self.set_timout(timeout)

    def show_warning(self, message='Undefined', timeout=None):
        self.label.set_text(message)
        self.bar_style_context.add_class('yellow_bar')
        self.button_style_context.add_class('yellow_button')
        self.set_reveal_child(True)
        self.set_timout(timeout)

    def show_error(self, message='Undefined', timeout=None):
        self.label.set_text(message)
        self.bar_style_context.add_class('red_bar')
        self.button_style_context.add_class('red_button')
        self.set_reveal_child(True)
        self.set_timout(timeout)

    def show_question(self, message='Undefined'):
        raise NotImplemented

    def show_confirmation(selfm, message='Undefined'):
        raise NotImplemented

    def set_timout(self, timeout):
        if timeout:
            GObject.timeout_add(timeout * 1000, self.close)
