#!/usr/bin/env python

# For stand-alone testing of the filechooser

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)

# Imoport our own modules
import filechooser
from modules.touchpads.keyboard import Keyboard


class FileChooser(object):

    def __init__(self):

        # Glade setup
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/standalone_3.glade")

        self.window = Gtk.Window()
        box = self.builder.get_object('box')
        self.window.add(box)
        header = self.builder.get_object('header')
        self.window.set_titlebar(header)
        self.window.connect('delete_event', self.on_delete_event)


        # Filechooser setup
        self.filechooser = filechooser.FileChooser()
        box = self.builder.get_object("box")
        box.add(self.filechooser)

        # Initialize keyboard
        self.keyboard = Keyboard

        # Connect signals emited by filechooser
        self.filechooser.connect('file-activated', self.on_file_activated)
        self.filechooser.connect('selection-changed', self.on_file_selection_changed)
        self.filechooser.connect('filename-editing-started', self.on_file_name_editing_started)
        self.filechooser.connect('error', self.on_error)

        # Set up file ext filters
        self.filechooser.add_filter('gcode', ['.ngc', '.TAP', '.txt'])
        self.filechooser.add_filter('all', ['*'])
        self.filechooser.set_filter('all')

        # Set show hidden (defaults to False if not set)
        self.filechooser.set_show_hidden(False)

        #print self.filechooser.get_filter()
        #print self.filechooser.get_filters()

        # Show the whole shebang
        self.window.show()


    def on_error(self, obj, type, text):
        print type, text

    def on_cut_clicked(self, widget, data=None):
        if self.filechooser.cut_selected():
            self.builder.get_object('paste').set_sensitive(True)

    def on_copy_clicked(self, widget, data=None):
        if self.filechooser.copy_selected():
            self.builder.get_object('paste').set_sensitive(True)

    def on_paste_clicked(self, widget, data=None):
        if self.filechooser.paste():
            self.builder.get_object('paste').set_sensitive(False)

    def on_back_clicked(self, widget, data=None):
        self.filechooser.up_one_dir()

    def on_delete_clicked(self, widget, data=None):
        self.filechooser.delete_selected()

    # Toggle file filter
    def on_filter_toggled(self, widget, data=None):
        if self.builder.get_object('filter').get_active():
            self.filechooser.set_filter('gcode')
        else:
            self.filechooser.set_filter('all')

    def on_file_activated(self, obj, fpath):
        print("File activated: " + fpath)

    def on_file_selection_changed(self, obj, path):
        print("Selection changed: " + path)

    def on_file_name_editing_started(self, widget, entry):
        self.keyboard.show(entry, True)

    # Delete the window
    def on_delete_event(self, widget, event, data=None):
        self.window.destroy()
        Gtk.main_quit()


def main():
    Gtk.main()


if __name__ == "__main__":
    ui = FileChooser()
    main()
