#!/usr/bin/env python

import os
import gi
import ast
import importlib

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from constants import Paths

# Import our own modules
from hazzy.utilities import logger
from hazzy.modules.widgetchooser.widgetwindow import WidgetWindow

log = logger.get('HAZZY.DASHBOARD')

PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '..'))
WIDGET_DIR = os.path.join(HAZZYDIR, 'hazzy/modules')

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)


class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        gladefile = os.path.join(Paths.UIDIR, 'hazzy.ui')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.hazzy_window = self.builder.get_object('hazzy_window')
        self.titlebar = self.builder.get_object('titlebar')
        self.widget_area = self.builder.get_object('widget_area')
        self.revealer_area = self.builder.get_object('revealer_area')

        self.iconview_scroller = self.builder.get_object('iconview_scroller')
        self.builder.connect_signals(self)
        self.add(self.hazzy_window)
        self.set_titlebar(self.titlebar)

        self.widgetchooser = WidgetChooserView()
        self.iconview_scroller.add(self.widgetchooser)

        self.widget_data = {}

        self.widgetchooser.fill(self.get_widgets())

        self.widget_area.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.widget_area.connect("drag-data-received", self.on_drag_data_received)
        self.add_targets()

        self.set_size_request(900, 600)
        self.show_all()


    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):

        pakage = data.get_text()
        info = self.widget_data[pakage]

        name = info.get('name')
        module = info.get('module')
        clas = info.get('class')
        size = info.get('size')

        module = importlib.import_module('.' + module, 'hazzy.modules.' + pakage)
        widget = getattr(module, clas)

        wwindow = WidgetWindow(widget(), size, name)
        self.widget_area.put(wwindow, x-size[0]/2, y-size[1]/2)

    def get_widgets(self):
        pakages = os.listdir(WIDGET_DIR)
        for pakage in pakages:
            path = os.path.join(WIDGET_DIR, pakage, 'widget.info')
            info_dict = {}
            if os.path.exists(path):
                #print "exists", path
                with open(path, 'r') as fh:
                    lines = fh.readlines()
                for line in lines:
                    if line.startswith('#'):
                        continue
                    key, value = line.split(':')
                    value = ast.literal_eval(value.strip())
                    #print key, value
                    info_dict[key] = value
                self.widget_data[pakage] = info_dict
        return self.widget_data

    def on_reveal_clicked(self, button):
        reveal = self.revealer_area.get_reveal_child()
        self.revealer_area.set_reveal_child(not reveal)


    def on_edit_layout_toggled(self, widget):
        edit = widget.get_active()
        # Hide eventbox used for drag/resize
        widgets = self.widget_area.get_children()
        for widget in widgets:
            widget.show_overlay(edit)

    def add_targets(self):
        self.widget_area.drag_dest_set_target_list(None)
        self.widgetchooser.drag_source_set_target_list(None)

        self.widget_area.drag_dest_add_text_targets()
        self.widgetchooser.drag_source_add_text_targets()



class WidgetChooser(Gtk.ScrolledWindow):
    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        pass



class WidgetChooserView(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        context = self.get_style_context()
        context.add_class("widget_chooser");

        self.set_text_column(0)
        self.set_pixbuf_column(1)

        self.set_item_width(120)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str)
        self.set_model(model)

        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)
        self.connect("drag-data-get", self.on_drag_data_get)


    def fill(self, data):
        self.set_columns(len(data))
        for pakage, i in data.iteritems():
            icon = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)
            if i.get('image'):
                path = os.path.join(WIDGET_DIR, pakage, i.get('image'))
                icon = GdkPixbuf.Pixbuf.new_from_file(path)
                w, h = icon.get_width(), icon.get_height()
                scale = 200 / float(w)
                icon = icon.scale_simple(w * scale, h * scale, GdkPixbuf.InterpType.BILINEAR)
            name = i.get('name')
            self.get_model().append([name, icon, pakage])


    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)
        text = self.get_model().get_value(selected_iter, 2)
        data.set_text(text, -1)
