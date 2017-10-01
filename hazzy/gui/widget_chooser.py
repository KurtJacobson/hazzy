#!/usr/bin/env python

import os
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

        self.get_widgets()




    def get_widgets(self):
        categories = os.listdir(WIDGET_DIR)
        for category in categories:
            print category

            if category.startswith('_'):
                continue

            if not os.path.isdir(os.path.join(WIDGET_DIR, category)):
                print "not dir"
                continue
            section = self.add_section(category)

            packages = os.listdir(os.path.join(WIDGET_DIR, category))

            for package in packages:
                print package

                path = os.path.join(WIDGET_DIR, package, 'widget.info')
                info_dict = {}
                if os.path.exists(path):
                    with open(path, 'r') as fh:
                        lines = fh.readlines()
                    for line in lines:
                        if line.startswith('#'):
                            continue
                        key, value = line.split(':')
                        value = ast.literal_eval(value.strip())
                        info_dict[key] = value


                    self.widget_data[package] = info_dict
                section.add_item(package)



    def populate(self):
        data = self.widget_manager.get_widgets()



    def add_section(self, section_name):
        section = Section(section_name)
        self.box.pack_start(section, False, False, 0)
        return section


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

    def add_item(self, item):
        print "adding section item ", item
        self.view.add_item(item, "test", 'test')


class WidgetView(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)

        # Add style class
        style_context = self.get_style_context()
        style_context.add_class("WidgetChooser")

        self.set_text_column(0)
        self.set_pixbuf_column(1)
        self.set_item_width(200)
        self.set_columns(1)

        self.model = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str)
        self.set_model(self.model)

        # Enable DnD
        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)
        self.connect("drag-data-get", self.on_drag_data_get)
        self.drag_source_set_target_list(None)
        self.drag_source_add_text_targets()

        self.image_missing = Gtk.IconTheme.get_default().load_icon('image-missing', 48, 0)


    def add_item(self, name, image_path, package):
        if os.path.exists(image_path):
            image = GdkPixbuf.Pixbuf.new_from_file(image_path)
            w, h = image.get_width(), image.get_height()
            scale = 200 / float(w)
            image = image.scale_simple(w * scale, h * scale, GdkPixbuf.InterpType.BILINEAR)
        else:
            image = self.image_missing

        self.model.append([name, image, package])


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
