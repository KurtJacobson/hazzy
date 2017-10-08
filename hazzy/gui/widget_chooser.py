#!/usr/bin/env python

import os
import sys
import ast
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

from widget_factory import entry_widgets

class WidgetChooser(Gtk.Popover):
    def __init__(self, screen_stack):
        Gtk.Popover.__init__(self)

        self.set_vexpand(True)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        screen_editor = ScreenEditor(screen_stack)
        self.box.pack_start(screen_editor, False, False, 0)

        # Scrolled Window
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_propagate_natural_width(True)
        self.scrolled.set_overlay_scrolling(True)
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.scrolled.add(self.box)

        self.add(self.scrolled)

        self.image_missing = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)

        self.get_widgets()

        self.show_all()
        self.hide()

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
                else:
                    info['image'] = os.path.join(root, 'widget.png')

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
                name = info.get('name', package)
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
    def __init__(self, section_name='Unnamed'):
        Gtk.HeaderBar.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.section_name = section_name

        self.arrow = Gtk.Arrow.new(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        self.label = Gtk.Label(self.section_name)

        # The section button
        self.button = Gtk.Button()
        self.button.get_style_context().add_class('flat')
        self.button.connect('clicked', self.on_button_clicked)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(self.arrow, False, False, 0)
        box.set_center_widget(self.label)
        self.button.add(box)

        self.label = Gtk.Label()
        box.pack_end(self.label, False, False, 0)

        self.revealer = Gtk.Revealer()

        self.view = WidgetView()
        self.revealer.add(self.view)

        self.pack_start(self.button, False, False, 0)
        self.pack_start(self.revealer, False, False, 0)

        self.count = 0


    def on_button_clicked(self, widget):
        revealed = self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(not revealed)
        if revealed:
            self.arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        else:
            self.arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE)


    def add_item(self, name, image, import_str):
        self.view.model.append([name, image, import_str])
        self.count += 1
        self.label.set_text('({})'.format(self.count))



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


class ScreenEditor(Gtk.Box):
    def __init__(self, screen_stack):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.screen_stack = screen_stack
        self.visible_child = None

        self.set_spacing(5)

        label = Gtk.Label('Screen Name')
        self.pack_start(label, False, False, 0)

        self.title_entry = entry_widgets.TextEntry()
        self.pack_start(self.title_entry, False, False, 0)
        self.title_entry.connect('activate', self.on_title_entry_activated)

        label = Gtk.Label('Screen Position')
        self.pack_start(label, False, False, 0)

        self.pos_adj = Gtk.SpinButton.new_with_range(0, 10, 1)
        self.pos_adj.connect('value_changed', self.on_position_changed)
        self.pack_start(self.pos_adj, False, False, 0)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_spacing(5)
        add_btn = Gtk.Button.new_from_stock('gtk-add')
        delete_btn = Gtk.Button.new_from_stock('gtk-delete')

        box.pack_start(add_btn, True, True, 0)
        box.pack_start(delete_btn, True, True, 0)
        box.set_homogeneous(True)

        self.pack_start(box, False, False, 0)

        self.screen_stack.connect("notify::visible-child", self.on_stack_changed)

        self.show_all()


    def on_title_entry_activated(self, widegt):
        title = self.title_entry.get_text()
        self.set_title(title)

    def set_title(self, title):
        self.screen_stack.child_set_property(self.visible_child, 'title', title)

    def on_position_changed(self, widegt):
        pos = widegt.get_value_as_int()
        print pos
        self.screen_stack.child_set_property(self.visible_child, 'position', pos)

    def on_stack_changed(self, stack, param):

        self.visible_child = stack.get_visible_child()

        title = self.screen_stack.child_get_property(self.visible_child, 'title')
        self.title_entry.set_text(title)

        pos = stack.child_get_property(self.visible_child, 'position')
        self.pos_adj.set_value(pos)


if __name__ == "__main__":
    main()
