#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from constants import Paths

# Import our own modules
from widgets.widget_chooser import WidgetChooser
from widgets.screen_chooser import ScreenChooser
from widgets.screen_stack import ScreenStack
from widgets.widget_area import WidgetArea


class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        gladefile = os.path.join(Paths.UIDIR, 'hazzy.ui')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.titlebar = self.builder.get_object('titlebar')
        self.set_titlebar(self.titlebar)

        self.overlay = Gtk.Overlay()
        self.add(self.overlay)

        self.screen_stack = ScreenStack()
        self.overlay.add(self.screen_stack)

        self.widget_chooser = WidgetChooser()
        self.overlay.add_overlay(self.widget_chooser)

        self.screen_chooser = ScreenChooser()
        self.overlay.add_overlay(self.screen_chooser)

        self.screen_stack.add_screen(WidgetArea(), 'Screen 1')
        self.screen_stack.show_screen('Screen 1')

        self.set_size_request(900, 600)
        self.show_all()

    def on_show_widget_choser_clicked(self, widget):
        visible = self.widget_chooser.get_visible()
        self.widget_chooser.set_visible(not visible)

    def on_show_screen_choser_clicked(self, widget):
        visible = self.screen_chooser.get_visible()
        self.screen_chooser.set_visible(not visible)

    def on_edit_layout_toggled(self, widget):
        edit = widget.get_active()
        # Hide eventbox used for drag/resize
        screens = self.screen_stack.get_children()
        for screen in screens:
            widgets = screen.get_children()
            for widget in widgets:
                widget.show_overlay(edit)
