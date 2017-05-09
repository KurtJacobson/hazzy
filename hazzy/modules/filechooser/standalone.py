#!/usr/bin/env python

# For stand-alone testing of the filechooser

import gtk
import os
import sys
import filechooser


MODULEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(1, MODULEDIR)

try:
    from touchpads.keyboard import Keyboard
    KEYBOARD = True
except:
    KEYBOARD = False
    print("Keyboard not available for testing")


class Filechooser(object):

    def __init__(self):

        # Glade setup
        self.builder = gtk.Builder()
        self.builder.add_from_file("ui/standalone.glade")
        self.window = self.builder.get_object("window1")
        self.builder.connect_signals(self)

        # Filechooser setup
        self.filechooser = filechooser.Filechooser()
        box = self.builder.get_object("hbox1")
        filechooser_widget = self.filechooser.get_filechooser_widget()
        box.add(filechooser_widget)

        # Initialize keyboard if we found it
        if KEYBOARD:
            self.keyboard = Keyboard()

        # Connect signals emited by filechooser
        self.filechooser.connect('file-activated', self.on_file_activated)
        self.filechooser.connect('selection-changed', self.on_file_selection_changed)
        self.filechooser.connect('filename-editing-started', self.on_file_name_editing_started)
        self.filechooser.connect('error', self.on_error)
        self.builder.get_object('paste').set_sensitive(False)

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
        if KEYBOARD:
            self.keyboard.show(entry, "", True)

    # Delete the window
    def on_window1_delete_event(self, widget, event, data=None):
        self.window.destroy()
        gtk.main_quit()


def main():
    gtk.main()


if __name__ == "__main__":
    ui = Filechooser()
    main()
