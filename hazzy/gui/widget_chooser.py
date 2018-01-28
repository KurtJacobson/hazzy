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
#   This is the popover used for adding/editing screens and widgets 
#   It display an IconView containing all the valid widegt pagakes found
#   in the hazzy widget dir and in the maichine config directory.

import os
import sys
import ast

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

        self.screen_stack = screen_stack

        self.set_can_focus(False)
        self.set_can_default(False)
        self.set_vexpand(True)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Screen title / position editor
        self.screen_editor = ScreenEditor(self.screen_stack)
        self.screen_editor_expander = Expander('Screen Settings')
        self.screen_editor_expander.add(self.screen_editor)
        self.box.pack_start(self.screen_editor_expander, False, False, 0)

        # Scrolled Window for widgets
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_propagate_natural_width(True)
        self.scrolled.set_overlay_scrolling(True)
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.scrolled.add(self.box)

        self.add(self.scrolled)

        self.image_missing = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)
        self.get_widgets()

        self.connect('notify::visible', self.on_popup)

        # FixMe this is needed to keep the popover from showing at start
        # but make it so the children will show when it pops up
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

#        import json
#        print json.dumps(categories, sort_keys=True, indent=4)

        self.populate(categories)


    def populate(self, categories):

        for category, packages in sorted(categories.items()):
            expander = Expander(category)
            icon_vew = WidgetView()
            expander.add(icon_vew)
            self.box.pack_start(expander, False, False, 0)

            count = 0
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

                icon_vew.add_item(name, image, import_str)
                count += 1
            expander.set_item_count(count)

    def on_popup(self, widget, data):
        child = self.screen_stack.get_visible_child()
        if child is None:
            return
        title = self.screen_stack.child_get_property(child, 'title')
        pos = self.screen_stack.child_get_property(child, 'position')
        self.screen_editor.title_entry.set_text(title)
        self.screen_editor.pos_adj.set_value(pos)


class Expander(Gtk.Box):
    def __init__(self, title=''):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.title = title

        self.arrow = Gtk.Arrow.new(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        self.title_label = Gtk.Label(label=self.title)

        # The section button
        self.button = Gtk.Button()
        self.button.get_style_context().add_class('flat')
        self.button.connect('clicked', self.on_button_clicked)
        self.num_label = Gtk.Label()

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(self.arrow, False, False, 0)
        box.set_center_widget(self.title_label)
        box.pack_end(self.num_label, False, False, 0)

        self.button.add(box)

        self.revealer = Gtk.Revealer()
        self.revealer.get_style_context().add_class('expander')

        self.pack_start(self.button, False, False, 0)
        self.pack_start(self.revealer, False, False, 0)

    def add(self, widegt):
        self.revealer.add(widegt)

    def set_item_count(self, count):
        self.num_label.set_text("({})".format(count))

    def on_button_clicked(self, widget):
        revealed = self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(not revealed)
        if revealed:
            self.arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        else:
            self.arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE)


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
        self.connect("drag-begin", self.on_drag_begin)
        self.connect("drag-end", self.on_drag_end)
        self.drag_source_set_target_list(None)
        self.drag_source_add_text_targets()
        self.drag = False

        self.connect('focus-out-event', self.on_focus_out)

    def add_item(self, name, image, import_str):
        self.model.append([name, image, import_str])

    def on_focus_out(self, widget, event):
        if not self.drag:
            self.unselect_all()

    def on_drag_begin(self, widget, event):
        self.drag = True

    def on_drag_end(self, widget, event):
        self.drag = False

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

        grid = Gtk.Grid()
        grid. set_row_spacing(5)

        grid.attach(Gtk.Label(label='Title', hexpand=True), 0, 0, 1, 1)
        self.title_entry = entry_widgets.TextEntry()
        self.title_entry.set_activate_on_focus_out(True)
        self.title_entry.connect('validate-text', self.on_title_entry_validate_text)
        self.title_entry.connect_after('delete-text', self.on_title_entry_delete_text)
        grid.attach(self.title_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label='Position', hexpand=True), 0, 1, 1, 1)
        self.pos_adj = Gtk.SpinButton.new_with_range(0, 10, 1)
        self.pos_adj.connect('value_changed', self.on_position_changed)
        grid.attach(self.pos_adj, 1, 1, 1, 1)

        self.pack_start(grid, False, False, 0)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_spacing(5)

        # Add screen button
        add_btn = Gtk.Button.new_from_stock('gtk-add')
        add_btn.connect('clicked', self.on_add_screen_clicked)

        # Remove screen button
        delete_btn = Gtk.Button.new_from_stock('gtk-remove')
        delete_btn.connect('clicked', self.on_delete_screen_clicked)

        box.pack_start(add_btn, True, True, 0)
        box.pack_start(delete_btn, True, True, 0)
        box.set_homogeneous(True)

        self.pack_start(box, False, False, 0)
        self.show_all()

    def on_add_screen_clicked(self, widegt):
        screen = self.screen_stack.add_screen_interactive()
        title = self.screen_stack.child_get_property(screen, 'title')
        pos = self.screen_stack.child_get_property(screen, 'position')
        self.title_entry.set_text(title)
        self.pos_adj.set_value(pos)

    def on_delete_screen_clicked(self, widegt):
        self.screen_stack.remove_visible_child()
        screen = self.screen_stack.get_visible_child()
        title = self.screen_stack.child_get_property(screen, 'title')
        pos = self.screen_stack.child_get_property(screen, 'position')
        self.title_entry.set_text(title)
        self.pos_adj.set_value(pos)

    # Used to dynamicaly set the tile of the screen while typing
    def on_title_entry_validate_text(self, editable, new_text, new_length, pos):
        title = editable.get_text()
        self.screen_stack.set_visible_child_title(title)

    def on_title_entry_delete_text(self, editable, start_pos, end_pos):
        title = editable.get_text()
        self.screen_stack.set_visible_child_title(title)

    def on_position_changed(self, widegt):
        pos = widegt.get_value_as_int()
        self.screen_stack.set_visible_child_position(pos)
