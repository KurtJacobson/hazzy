#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from lxml import etree

from utilities.constants import Paths

# Import our own modules
from widget_manager import WidgetManager
from widget_chooser import WidgetChooser
from screen_chooser import ScreenChooser
from widget_window import WidgetWindow
from screen_stack import ScreenStack
from widget_area import WidgetArea



class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        self.widget_manager = WidgetManager()

        gladefile = os.path.join(os.path.dirname(__file__), 'ui', 'hazzy.ui')
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



    def load_from_xml(self):

        if not os.path.exists(Paths.XML_FILE):
            return

        tree = etree.parse(Paths.XML_FILE)
        root = tree.getroot()

        screens = []

        for screen in root.iter('screen'):
            screen_obj = WidgetArea()
            screen_name = screen.get('name')
            self.screen_stack.add_screen(screen_obj, screen_name)
            screens.append(screen_name)

            for widget in screen.iter('widget'):
                package = widget.get('name')
                obj, title, size = self.widget_manager.get_widget(package)
                wwindow = WidgetWindow(package, obj, title)

                props = {}
                for prop in widget.iter('property'):
                    props[prop.get('name')] = prop.text

                screen_obj.put(wwindow, int(props['x']), int(props['y']))
                wwindow.set_size_request(int(props['w']), int(props['h']))

        self.screen_chooser.view.fill_iconview(screens)


    def save_to_xml(self):
        screens = self.screen_stack.get_children()
        data = []

        root = etree.Element("hazzy_interface")
        root.append(etree.Comment('Interface for: RF45 Milling Machine'))
        root.append(etree.Comment('Last modified: 8/5/2017'))

        for screen in screens:
            screen_name = self.screen_stack.child_get_property(screen, 'name')
            screen_pos = self.screen_stack.child_get_property(screen, 'position')

            scr = etree.SubElement(root, "screen")
            scr.set('name', screen_name)
            scr.set('position', str(screen_pos))

            widgets = screen.get_children()
            for widget in widgets:

                wid = etree.SubElement(scr, "widget")
                wid.set('name', widget.package)

                x = screen.child_get_property(widget, 'x')
                y = screen.child_get_property(widget, 'y')
                w = widget.get_size_request().width
                h = widget.get_size_request().height

                for prop_name, prop_value in zip(['x','y','w','h'], [x,y,w,h]):
                    prop = etree.SubElement(wid, 'property')
                    prop.set('name', prop_name)
                    prop.text = str(prop_value)

        with open(Paths.XML_FILE, 'wb') as fh:
            fh.write(etree.tostring(root, pretty_print=True))
