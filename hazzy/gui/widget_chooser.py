#!/usr/bin/env python

import os
import sys
import ast
import importlib
import json

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
WIDGET_DIR = os.path.join(HAZZYDIR, 'hazzy/modules')

WIDGET_DIRS = [WIDGET_DIR, os.environ['CONFIG_DIR']]


class WidgetChooser(Gtk.Revealer):
    def __init__(self):
        Gtk.Revealer.__init__(self)

        self.set_reveal_child(True)
        self.set_halign(Gtk.Align.START)

        # Scrolled Window
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_propagate_natural_width(True)
        self.scrolled.set_overlay_scrolling(True)
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scrolled.add(self.box)

        self.add(self.scrolled)

        self.image_missing = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)

        self.get_widgets()

    def get_widgets(self):

        categories = {}

        for widget_dir in WIDGET_DIRS:

            sys.path.append(widget_dir)

            for root, subdirs, files in os.walk(widget_dir):

                # Ignore directories starting with '_'
                if os.path.split(root)[1].startswith('_'):
                    continue

                # Ignore non widgets. i.e. dirs with no 'widget.info' file
                info_file = os.path.join(root, 'widget.info')
                if not os.path.exists(info_file):
                    continue

                with open(info_file, 'r') as fh:
                    lines = fh.readlines()

                info = {}
                for line in lines:
                    line = line.strip()

                    # Skip blank or comment lines
                    if not line or line[0] in ['#', ';']:
                        continue

                    key, value = line.split(':')
                    info[key.strip()] = ast.literal_eval(value.strip())

                if info.get('image'):
                    info['image'] = os.path.join(root, info['image'])

                path = os.path.relpath(root, widget_dir).split('/')

                # Determine package for import, and category name for display
                if len(path) == 1:
                    category = info.get('category') or 'Uncategorized'
                    package = path[0]
                elif len(path) == 2:
                    category = info.get('category') or path[0]
                    package = path[1]

                info['import_str'] = '.'.join(path)

                if not category in categories.keys():
                    categories[category] = {}

                categories[category][package] = info

#        print json.dumps(categories, sort_keys=True, indent=4)

        self.populate(categories)


    def populate(self, categories):

        for category, packages in sorted(categories.items()):
            section = Section(category)
            self.box.pack_start(section, False, False, 0)

            for package, info in sorted(packages.items()):
                name = info.get('name', 'Unnamed')
                import_str = info['import_str']
                image_path = info.get('image')

                if os.path.exists(image_path):
                    image = GdkPixbuf.Pixbuf.new_from_file(image_path)
                    w, h = image.get_width(), image.get_height()
                    scale = 200 / float(w)
                    image = image.scale_simple(w * scale, h * scale, GdkPixbuf.InterpType.BILINEAR)
                else:
                    image = self.image_missing

                section.add_item(name, image, import_str)


class Section(Gtk.Box):
    def __init__(self, section_name='Section 1'):
        Gtk.HeaderBar.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.section_name = section_name

        self.arrow = Gtk.Arrow.new(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        self.label = Gtk.Label(self.section_name)

        # The section button
        self.button = Gtk.Button()
        self.button.connect('clicked', self.on_button_clicked)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(self.arrow, False, False, 0)
        box.set_center_widget(self.label)
        self.button.add(box)

        self.revealer = Gtk.Revealer()

        self.view = WidgetView()
        self.revealer.add(self.view)

        self.pack_start(self.button, False, False, 0)
        self.pack_start(self.revealer, False, False, 0)


    def on_button_clicked(self, widget):
        revealed = self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(not revealed)
        if revealed:
            self.arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        else:
            self.arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE)


    def add_item(self, name, image, import_str):
        self.view.model.append([name, image, import_str])



class WidgetView(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        # Add style class
        style_context = self.get_style_context()
        style_context.add_class("WidgetChooser")

        self.set_text_column(0)
        self.set_pixbuf_column(1)
        self.set_item_width(130)
        self.set_columns(1)

        self.model = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str)
        self.set_model(self.model)

        # Enable DnD
        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)
        self.connect("drag-data-get", self.on_drag_data_get)
        self.drag_source_set_target_list(None)
        self.drag_source_add_text_targets()

        self.connect('focus-out-event', self.on_focus_out)

    def on_focus_out(self, widget, event):
        self.unselect_all()

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)
        text = self.get_model().get_value(selected_iter, 2)
        data.set_text(text, -1)


def main():
    win = Gtk.Window()
    win.set_size_request(200, 400)
    win.connect('destroy', Gtk.main_quit)
    sec = WidgetChooser()
    win.add(sec)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
