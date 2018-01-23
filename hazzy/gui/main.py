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
#   This handles the initialization of the application and the creation of the
#   the main window.  The window will be populated based on the layout defined
#   in the XML file specified in [DISPLAY] XML_FILE in the INI.  If that file
#   does not exist or is not valid, one window containing one blank screen will
#   be created for the user to add widgets to.

import time

from utilities import logger
log = logger.get('MAIN')

def log_time(task, times=[time.time(), time.time()]):
    now = time.time()
    log.debug("yellow<Time:> {:.3f} (green<{:+.3f}>) - {}".format(now - times[0], now - times[1], task))
    times[1] = now

log_time("in script")

import os
import sys
import datetime
import linuxcnc, hal
import traceback

from lxml import etree
from datetime import datetime

log_time('python imports done')

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib

log_time('Gtk imports done')

# Log exceptions
def excepthook(exc_type, exc_value, exc_traceback):
    message = traceback.format_exception(exc_type, exc_value, exc_traceback)
    log.critical("".join(message))

# Connect our excepthook handler
sys.excepthook = excepthook

# Check LinuxCNC Version
major, minor, micro = os.environ.get('LINUXCNCVERSION').split('.')
if (int(major), int(minor)) < (2, 8):
    log.critical("LinuxCNC is version {}.{}.{} but hazzy requires LinuxCNC 2.8 or above"
        .format(major, minor, micro))
    sys.exit()

# Check GTK+ Version
major, minor, micro = Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION
if (major, minor) < (3, 20):
    log.critical("GTK+ is version {}.{}.{} but hazzy requires GTK+ 3.20 or above"
        .format(major, minor, micro))
    sys.exit()

log_time('done checking requirements')

from utilities.constants import Paths
from utilities import notifications
from utilities import ini_info
from utilities import jogging

# Import our own modules
from widget_chooser import WidgetChooser
from widget_window import WidgetWindow
from screen_stack import ScreenStack
from widget_area import WidgetArea
from header_bar import HeaderBar
from about import About

log_time('module imports done')


class Hazzy(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)

        # Get the XML file path
        self.xml_file = ini_info.get_xml_file()

        self.settings = Gtk.Settings.get_default()
        self.set_gtk_theme('Adwaita')

        log_time('done initializing')

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.start_time = datetime.now()
        log.info("green<Starting>")

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(os.path.join(Paths.STYLEDIR, "style.css"))

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(Paths.UIDIR, 'menu.ui'))

        self.app_menu = self.builder.get_object('appmenu')
        self.set_app_menu(self.app_menu)

        actions = ['new_window', 'about', 'quit', 'launch_hal_meter', 'launch_hal_scope',
            'launch_hal_configuration', 'launch_classicladder', 'launch_status']

        for action in actions:
            self.add_simple_action(action)

        toggle_actions = ['edit_layout', 'dark_theme']
        for action in toggle_actions:
            self.add_toggle_action(action)

        # Show any Startup Notifications given in INI
        startup_notification = ini_info.get_startup_notification()
        if startup_notification:
            notifications.show_info(startup_notification, timeout=0)

        startup_warning = ini_info.get_startup_warning()
        if startup_warning:
            notifications.show_warning(startup_warning, timeout=0)

        log_time('app startup done')

    def do_activate(self):
        Gtk.Application.do_activate(self)

        self.load_from_xml()

        GLib.idle_add(log_time, "in main loop")
        log_time("app activate done")

    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)

        log.info("red<Quitting>")
        run_time = datetime.now() - self.start_time
        log.info("Total session duration: {}".format(run_time))

        self.save_to_xml()

    def on_window_delete_event(self, window, event):
        # If only one window quit hazzy, else just close window.
        # TODO: Add a dialog asking to quit app or close window.  
        if len(self.get_windows()) > 1:
            window.destroy()
        else:
            self.quit()
            return True

# =========================================================
# App menu action handlers
# =========================================================

    def on_edit_layout_toggled(self, action, state):
        action.set_state(state)
        for window in self.get_windows():
            window.set_edit_layout(state)

    def on_dark_theme_toggled(self, action, state):
        action.set_state(state)
        self.set_dark_theme(state)

    def on_new_window(self, action, data):
        self.new_window(True).screen_stack.add_screen()

    def on_launch_hal_scope(self, action, data):
        p = os.popen("halscope &")

    def on_launch_hal_meter(self, action, data):
        p = os.popen("halmeter &")

    def on_launch_hal_configuration(self, action, data):
        p = os.popen("tclsh {0}/bin/halshow.tcl &".format(Paths.TCLPATH))

    def on_launch_classicladder(self, action, data):
        if hal.component_exists("classicladder_rt"):
            p = os.popen("classicladder  &", "w")
        else:
            text = "Classicladder real-time component not detected"
            self.error_dialog.run(text)

    def on_launch_status(self, action, data):
        p = os.popen("linuxcnctop &")

    def on_about(self, action, data):
        About(self.get_active_window())

    def on_quit(self, action, data):
        log_time('quit requested')
        self.quit()

# =========================================================
# Menu helper functions
# =========================================================

    def add_simple_action(self, action_name):
        action = Gio.SimpleAction.new(action_name)
        setattr(self, '{}_action'.format(action_name.replace('-', '_')), action)
        callback = getattr(self, 'on_{}'.format(action_name))
        action.connect("activate", callback)
        self.add_action(action)

    def add_toggle_action(self, action_name, state=False):
        toggle = Gio.SimpleAction.new_stateful(action_name,
                            None, GLib.Variant.new_boolean(state))
        setattr(self, '{}_action'.format(action_name.replace('-', '_')), toggle)
        callback = getattr(self, 'on_{}_toggled'.format(action_name))
        toggle.connect("change-state", callback)
        self.add_action(toggle)


# =========================================================
#  XML handlers for saving/loading screen layout
# =========================================================

    def load_from_xml(self):

        if not os.path.exists(self.xml_file):
            # Add an initial screen to get started
            self.new_window(True).screen_stack.add_screen()
            return

        try:
            tree = etree.parse(self.xml_file)
        except etree.XMLSyntaxError as e:
            error_str = e.error_log.filter_from_level(etree.ErrorLevels.FATAL)
            log.error(error_str)
            self.new_window(True).screen_stack.add_screen()
            return

        root = tree.getroot()

        # FixMe don't need to iterate here
        for app in root.iter('application'):
            props = self.get_properties(app)

            self.set_gtk_theme(props.get('gtk-theme'))
            self.set_icon_theme(props.get('icon-theme'))
            dark = props.get('dark-theme', 'False') == 'True'
            self.dark_theme_action.set_state(GLib.Variant.new_boolean(dark))
            self.set_dark_theme(dark)

        # Windows
        win = None
        for win in root.iter('window'):
            window_name = win.get('name')
            window_title = win.get('title')

            props = self.get_properties(win)

            window = self.new_window()

            window.set_default_size(int(props['w']), int(props['h']))
            window.move(int(props['x']), int(props['y']))
            window.set_maximized(props['maximize'])
            window.set_fullscreen(props['fullscreen'])

            # Screens
            scr = None
            for scr in win.iter('screen'):

                screen_title = scr.get('title')
                screen_obj = window.screen_stack.add_screen(screen_title)

                # Widgets
                for widget in scr.iter('widget'):
                    package = widget.get('package')
                    props = self.get_properties(widget)
                    try:
                        widget_obj = WidgetWindow(package)
                        widget_obj.overlay.set_visible(False)
                        window.screen_stack.place_widget(screen_obj,
                                                        widget_obj,
                                                        int(props['x']),
                                                        int(props['y']),
                                                        int(props['w']),
                                                        int(props['h']))
                    except ImportError:
                        log.error('The package "{}" could not be imported'.format(package))
                        continue

            if scr is None:
                # There were no screens, add an initial one
                window.screen_stack.add_screen()

        if win is None:
            # There were no windows, add an initial one
            window = self.new_window()
            window.screen_stack.add_screen()

    def save_to_xml(self):

        # Create XML root element & comment
        root = etree.Element("hazzy")
        root.append(etree.Comment('Interface for: {}'.format(ini_info.get_machine_name())))

        # Add time stamp
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        root.append(etree.Comment('Last modified: {}'.format(time_str)))

        app = etree.SubElement(root, "application")

        self.set_property(app, 'gtk-theme', self.get_gtk_theme())
        self.set_property(app, 'dark-theme', self.get_dark_theme())
        self.set_property(app, 'icon-theme', self.get_icon_theme())

        # Window size & position
        for window in self.get_windows():

            win = etree.SubElement(root, "window")
            win.set('name', 'Window 1')
            win.set('title', 'Main Window')

            self.set_property(win, 'maximize', window.header_bar.window_maximized)
            self.set_property(win, 'fullscreen', window.header_bar.window_fullscreen)

            x = window.get_position().root_x
            y = window.get_position().root_y
            w, h = window.get_size()

            for prop, value in zip(['x','y','w','h'], [x,y,w,h]):
                self.set_property(win, prop, value)

            # Screens
            screens = window.screen_stack.get_children()
            for screen in screens:
                screen_title = window.screen_stack.child_get_property(screen, 'title')

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

#        print etree.tostring(root, pretty_print=True)

# =========================================================
#  XML helper functions
# =========================================================

    def new_window(self, begin_editing=False):
        window = HazzyWindow(self)
        window.connect('delete-event', self.on_window_delete_event)
        self.edit_layout_action.set_state(GLib.Variant.new_boolean(begin_editing))
        window.chooser_button.set_visible(begin_editing)
        window.check_button.set_visible(begin_editing)
        self.add_window(window)
        return window

    def set_property(self, parent, name, value):
        prop = etree.SubElement(parent, 'property')
        prop.set('name', name)
        prop.text = str(value)

    def get_properties(self, parent):
        props = {}
        for prop in parent.iterchildren('property'):
            props[prop.get('name')] = prop.text
        return props

    def get_gtk_theme(self):
        return self.settings.get_property("gtk-theme-name")

    # ToDo: Verify that theme exists
    def set_gtk_theme(self, theme):
        self.settings.set_string_property("gtk-theme-name", theme, "")

    def get_icon_theme(self):
        return self.settings.get_property("gtk-icon-theme-name")

    # ToDo: Verify that theme exists
    def set_icon_theme(self, theme):
        self.settings.set_string_property("gtk-icon-theme-name", theme, "")

    def get_dark_theme(self):
        return self.settings.get_property("gtk-application-prefer-dark-theme")

    def set_dark_theme(self, dark):
        self.settings.set_property("gtk-application-prefer-dark-theme", dark)


class HazzyWindow(Gtk.ApplicationWindow):
    def __init__(self, app, *args, **kwargs):
        Gtk.ApplicationWindow.__init__(self, application=app, *args, **kwargs)

        self.app = app
        self.set_show_menubar(False) # Use a menu button instead

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        self.header_bar = HeaderBar(self)
        self.header_bar.set_title('Hazzy')
        self.header_bar.set_subtitle('Machine: ' + ini_info.get_machine_name())
        self.set_titlebar(self.header_bar)

        # The overlay is not used anymore, should we remove it, or leave
        # it in case somebody wants to use it for a InfoBar or the like??
        self.overlay = Gtk.Overlay()
        self.box.pack_start(self.overlay, True, True, 0)

        self.screen_stack = ScreenStack()
        self.screen_stack.connect_after('add', self.on_screen_stack_children_changed)
        self.screen_stack.connect_after('remove', self.on_screen_stack_children_changed)
        self.overlay.add(self.screen_stack)

        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.screen_stack)
        self.stack_switcher.show_all()

        self.menu_button = Gtk.MenuButton()
        icon = Gtk.Image.new_from_icon_name('applications-system-symbolic', # 'open-menu-symbolic'
                                            Gtk.IconSize.MENU)
        self.menu_button.add(icon)
        self.menu_button.get_style_context().add_class('flat')
        self.menu_button.set_menu_model(self.app.app_menu)
        self.header_bar.pack_start(self.menu_button)

        self.header_bar.pack_start(Gtk.Separator())

        self.widget_chooser = WidgetChooser(self.screen_stack)
        self.chooser_button = Gtk.MenuButton()
        self.chooser_button.set_popover(self.widget_chooser)
        self.header_bar.pack_start(self.chooser_button)

        self.check_button = Gtk.EventBox()
        self.check_button.set_tooltip_text('Finish editing')
        icon = Gtk.Image.new_from_icon_name('emblem-default',
                                            Gtk.IconSize.LARGE_TOOLBAR)
        self.check_button.add(icon)
        self.check_button.connect('button-press-event', lambda w, e: self.set_edit_layout(False))
        self.check_button.set_margin_top(10)
        self.check_button.set_margin_right(10)
        self.check_button.set_halign(Gtk.Align.END)
        self.check_button.set_valign(Gtk.Align.START)
        self.overlay.add_overlay(self.check_button)

        self.connect('button-press-event', self.on_button_press) # Clear focus
        self.connect('key-press-event', self.on_key_press)       # Jog start
        self.connect('key-release-event', self.on_key_release)   # Jog stop

        self.set_size_request(500, 300)
        self.show_all()

    # Only show the StackSwitcher if there are 2 or more screens
    def on_screen_stack_children_changed(self, stack, child):
        if len(self.screen_stack.get_children()) > 1:
            # Display the StackSwitcher
            self.header_bar.set_custom_title(self.stack_switcher)
        else:
            # Display the Title / Subtitle
            self.header_bar.set_custom_title(None)

    def set_edit_layout(self, edit):
        self.app.edit_layout_action.set_state(GLib.Variant.new_boolean(edit))
        screens = self.screen_stack.get_children()
        self.chooser_button.set_visible(edit)
        self.check_button.set_visible(edit)
        for screen in screens:
            widgets = screen.get_children()
            for widget in widgets:
                widget.show_overlay(edit)

    # Remove focus when clicking on any non focusable area
    def on_button_press(self, widget, event):
        self.get_toplevel().set_focus(None)

    # If no widget has focus, then assume the user wants
    # to jog the machine. Need to fine a way to make this safer.
    def on_key_press(self, widget, event):
        if not self.get_focus():
            jogging.on_key_press_event(widget, event)
            return True

    # Stop jogging, whenever a key is released, otherwise we
    # might miss the key release and continue jogging if some
    # other widget got focus while the jog was in progress, NOT safe!
    def on_key_release(self, widget, event):
        jogging.on_key_release_event(widget, event)
        return True

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
