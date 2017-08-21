#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from constants import Paths

# Import our own modules
from hazzy.utilities import logger
from hazzy.modules.widgetchooser.widgetchooser import DragSourcePanel

from hazzy.modules.gcodeview.gcodeview import GcodeViewWidget
from hazzy.modules.widgetchooser.widgetwindow import WidgetWindow

log = logger.get('HAZZY.DASHBOARD')


(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)


class HazzyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        gladefile = os.path.join(Paths.UIDIR, 'hazzy_3.ui')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.hazzy_window = self.builder.get_object('hazzy_window')
        self.titlebar = self.builder.get_object('titlebar')
        self.revealer_area = self.builder.get_object('revealer_area')
        self.widget_area = self.builder.get_object('widget_area')
        self.builder.connect_signals(self)
        self.add(self.hazzy_window)
        self.set_titlebar(self.titlebar)

        self.iconview = DragSourcePanel()
        self.revealer_area.add(self.iconview)

        self.widget_area.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.widget_area.connect("drag-data-received", self.on_drag_data_received)
        self.add_targets()

        # Widget No.1
        widget = GcodeViewWidget()
        size = [400, 300]
        name = 'G-code'
        wwindow = WidgetWindow(widget, size, name)
        self.widget_area.put(wwindow, 0, 0)

        self.show_all()


    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        dro_widget = GcodeViewWidget()
        label = data.get_text()
        widget = GcodeViewWidget()
        size = [400, 300]
        name = 'G-code'
        wwindow = WidgetWindow(widget, size, name)
        self.widget_area.put(wwindow, 0, 0)


    def on_reveal_clicked(self, button):
        reveal = self.revealer_area.get_reveal_child()
        self.revealer_area.set_reveal_child(not reveal)

    def add_targets(self):
        self.widget_area.drag_dest_set_target_list(None)
        self.iconview.drag_source_set_target_list(None)

        self.widget_area.drag_dest_add_text_targets()
        self.iconview.drag_source_add_text_targets()




class DragSourcePanel(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        self.set_text_column(COLUMN_TEXT)
        self.set_pixbuf_column(COLUMN_PIXBUF)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        self.set_model(model)

        self.add_item("Dro", "image-missing")
        self.add_item("Code View", "help-about")
        self.add_item("Code Editor", "edit-copy")

        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)

        self.connect("drag-data-get", self.on_drag_data_get)


    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)

        if True:  # info == TARGET_ENTRY_TEXT:
            text = self.get_model().get_value(selected_iter, COLUMN_TEXT)
            data.set_text(text, -1)
        elif info == TARGET_ENTRY_PIXBUF:
            pixbuf = self.get_model().get_value(selected_iter, COLUMN_PIXBUF)
            data.set_pixbuf(pixbuf)

    def add_item(self, text, icon_name):
        pixbuf = Gtk.IconTheme.get_default().load_icon(icon_name, 16, 0)
        self.get_model().append([text, pixbuf])
