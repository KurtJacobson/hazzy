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
#   This modules handles the creation of the main window. If the file specified
#   in the INI's entry [DISPLAY] XML_FILE exists, it will attempt to populate
#   the window based on that description. If that file does not exist or is not
#   valid, a window containing one blank screen will be displayed.

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from lxml import etree
from datetime import datetime

from utilities.constants import Paths
from gui import about

# Import our own modules
from widget_chooser import WidgetChooser
from widget_window import WidgetWindow
from screen_stack import ScreenStack
from widget_area import WidgetArea
from header_bar import HeaderBar

from utilities import ini_info

# Set up logging
from utilities import logger
log = logger.get(__name__)

class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        # Get the XML file path
        self.xml_file = ini_info.get_xml_file()

        self.connect('button-press-event', self.on_button_press)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        self.header_bar = HeaderBar(self, title='Hazzy')
        self.set_titlebar(self.header_bar)

        self.overlay = Gtk.Overlay()
        self.box.pack_start(self.overlay, True, True, 0)

        self.screen_stack = ScreenStack()
        self.overlay.add(self.screen_stack)

        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.screen_stack)
        self.header_bar.set_custom_title(self.stack_switcher)

        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_popover(self.make_menu_popover())
        self.header_bar.pack_start(self.menu_button)

        self.system_menu_button = Gtk.MenuButton()
        self.system_menu_button.set_popover(self.make_system_menu_popover())
        self.header_bar.pack_start(self.system_menu_button)

        self.edit_button = Gtk.Button()
        self.edit_button.connect('clicked', self.on_edit_button_clicked)
        self.edit_button.set_can_focus(False)
        icon = Gtk.Image.new_from_icon_name('view-list-symbolic', Gtk.IconSize.MENU)
        self.edit_button.set_image(icon)
        self.header_bar.pack_start(self.edit_button)

        self.widget_chooser = WidgetChooser(self.screen_stack)
        self.widget_chooser.set_relative_to(self.edit_button)

        self.set_size_request(900, 600)

        self.get_gtk_theme()

    def on_show_halscope_clicked(self, widget):
        p = os.popen("halscope &")

    def on_show_halmeter_clicked(self, widget):
        p = os.popen("halmeter &")

    def on_show_halshow_clicked(self, widget):
        p = os.popen("halshow &")

    def on_button_press(self, widget, event):
        # Remove focus when clicking on non focusable area
        self.get_toplevel().set_focus(None)

    def on_edit_button_clicked(self, widget):
        self.widget_chooser.popup_()

    def on_edit_layout_toggled(self, widget):
        edit = widget.get_active()
        # Hide eventbox used for drag/resize
        screens = self.screen_stack.get_children()
        for screen in screens:
            widgets = screen.get_children()
            for widget in widgets:
                widget.show_overlay(edit)

    def on_show_about_clicked(self, widget):
        about.About(self)

# =========================================================
#  XML handlers for saving/loading screen layout
# =========================================================

    def load_from_xml(self):

        if not os.path.exists(self.xml_file):
            # Add an initial screen to get started
            self.screen_stack.add_screen()
            return

        try:
            tree = etree.parse(self.xml_file)
        except etree.XMLSyntaxError as e:
            error_str = e.error_log.filter_from_level(etree.ErrorLevels.FATAL)
            log.error(error_str)
            return

        root = tree.getroot()

        # Windows (Might support multiple windows in future, so iterate)
        for window in root.iter('window'):
            window_name = window.get('name')
            window_title = window.get('title')

            props = self.get_properties(window)

            self.set_default_size(int(props['w']), int(props['h']))
            self.move(int(props['x']), int(props['y']))
            self.set_maximized(props['maximize'])
            self.set_fullscreen(props['fullscreen'])
            self.set_gtk_theme(props['gtk-theme'])
            self.set_icon_theme(props['icon-theme'])

            # Add screens
            for screen in window.iter('screen'):

                screen_title = screen.get('title')
                screen_obj = self.screen_stack.add_screen(screen_title)

                # Add all the widgets
                for widget in screen.iter('widget'):
                    package = widget.get('package')
                    props = self.get_properties(widget)
                    try:
                        widget_obj = WidgetWindow(package)
                        self.screen_stack.place_widget(screen_obj,
                                                    widget_obj,
                                                    int(props['x']),
                                                    int(props['y']),
                                                    int(props['w']),
                                                    int(props['h']))
                    except ImportError:
                        log.error('The package "{}" could not be imported'.format(package))
                        continue

        if not self.screen_stack.get_children():
            # Add an initial screen to get started
            self.screen_stack.add_screen()

    def save_to_xml(self):

        # Create XML root element & comment
        root = etree.Element("hazzy_interface")
        root.append(etree.Comment('Interface for: {}'.format(Paths.MACHINE_NAME)))

        # Add time stamp
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        root.append(etree.Comment('Last modified: {}'.format(time_str)))

        # Main window size & position 
        #    ToDO: need to iterate to support multi window
        win = etree.SubElement(root, "window")
        win.set('name', 'Window 1')
        win.set('title', 'Main Window')

        self.set_property(win, 'maximize', self.header_bar.window_maximized)
        self.set_property(win, 'fullscreen', self.header_bar.window_fullscreen)
        self.set_property(win, 'gtk-theme', self.get_gtk_theme())
        self.set_property(win, 'icon-theme', self.get_icon_theme())

        x = self.get_position().root_x
        y = self.get_position().root_y
        w, h = self.get_size()

        for prop, value in zip(['x','y','w','h'], [x,y,w,h]):
            self.set_property(win, prop, value)

        # Screens
        screens = self.screen_stack.get_children()
        for screen in screens:
            screen_title = self.screen_stack.child_get_property(screen, 'title')

            scr = etree.SubElement(win, "screen")
            scr.set('title', screen_title)

            # Widgets
            widgets = screen.get_children()
            for widget in widgets:
                wid = etree.SubElement(scr, "widget")
                wid.set('package', widget.package)

                x = screen.child_get_property(widget, 'x')
                y = screen.child_get_property(widget, 'y')
                w = widget.get_size_request().width
                h = widget.get_size_request().height

                for prop, value in zip(['x','y','w','h'], [x,y,w,h]):
                    self.set_property(wid, prop, value)

        with open(self.xml_file, 'w') as fh:
            fh.write(etree.tostring(root, pretty_print=True))

# =========================================================
#  Helper functions
# =========================================================

    def set_property(self, parent, name, value):
        prop = etree.SubElement(parent, 'property')
        prop.set('name', name)
        prop.text = str(value)

    def get_properties(self, parent):
        props = {}
        for prop in parent.iterchildren('property'):
            props[prop.get('name')] = prop.text
        return props

    def set_maximized(self, maximized):
        if maximized == 'True':
            self.maximize()
        else:
            self.unmaximize()

    def set_fullscreen(self, fullscreen):
        if fullscreen == 'True':
            self.fullscreen()
        else:
            self.unfullscreen()

    def get_gtk_theme(self):
        settings = self.get_settings()
        theme = settings.get_property("gtk-theme-name")
        if not theme:
            theme = settings.get_default().get_property("gtk-theme-name")
        return theme

    # ToDo: Verify that theme exists
    def set_gtk_theme(self, theme=None):
        settings = self.get_settings()
        if not theme:
            theme = settings.get_default().get_property("gtk-theme-name")
        settings.set_string_property("gtk-theme-name", theme, "")

    def get_icon_theme(self):
        settings = self.get_settings()
        theme = settings.get_property("gtk-icon-theme-name")
        if not theme:
            theme = settings.get_default().get_property("gtk-icon-theme-name")
        return theme

    # ToDo: Verify that theme exists
    def set_icon_theme(self, theme=None):
        settings = self.get_settings()
        if not theme:
            theme = settings.get_default().get_property("gtk-icon-theme-name")
        settings.set_string_property("gtk-icon-theme-name", theme, "")

    def make_menu_popover(self):
        #Create a menu popover - very temporary, need to do something neater
        popover = Gtk.PopoverMenu.new()

        pbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        pbox.set_property('margin', 10)
        popover.add(pbox)

        edit = Gtk.CheckButton.new()
        edit.set_label("Edit Layout")
        edit.set_active(True)
        edit.connect('toggled', self.on_edit_layout_toggled)
        pbox.pack_start(edit, False, False, 5)

        about = Gtk.ModelButton.new()
        about.set_label("About")
        about.connect('clicked', self.on_show_about_clicked)
        pbox.pack_start(about, False, False, 5)

        quit = Gtk.ModelButton.new()
        quit.set_label("Quit")
        quit.connect('clicked', Gtk.main_quit)

        pbox.pack_start(quit, False, False, 5)
        pbox.show_all()

        return popover

    def make_system_menu_popover(self):
        #Create a menu popover - very temporary, need to do something neater
        popover = Gtk.PopoverMenu.new()

        pbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        pbox.set_property('margin', 10)
        popover.add(pbox)

        halscope = Gtk.ModelButton.new()
        halscope.set_label("Hal Scope")
        halscope.connect('clicked', self.on_show_halscope_clicked)
        pbox.pack_start(halscope, False, False, 5)

        halmeter = Gtk.ModelButton.new()
        halmeter.set_label("Hal Meter")
        halmeter.connect('clicked', self.on_show_halmeter_clicked)
        pbox.pack_start(halmeter, False, False, 5)

        halshow = Gtk.ModelButton.new()
        halshow.set_label("Hal Configuration")
        halshow.connect('clicked', self.on_show_halshow_clicked)
        pbox.pack_start(halshow, False, False, 5)

        pbox.show_all()

        return popover
