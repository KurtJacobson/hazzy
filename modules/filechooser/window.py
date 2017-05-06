#!/usr/bin/env python

import gtk
import os
import filechooser

# For stand-alone testing of the filechooser

class Filechooser(object):

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("window.glade")
        self.window = self.builder.get_object("window1")
        self.fixed = self.builder.get_object("alignment1")
        self.builder.connect_signals(self)
        self.filechooser = filechooser.Filechooser()
        self.filechooser.connect('file-activated', self.on_file_activated)
        self.filechooser.connect('selection-changed', self.on_file_selection_changed)
        self.filechooser.connect('filename-editing-started', self.on_filename_edited)
        self.filechooser.connect('error', self.on_error)
        self.builder.get_object('paste').set_sensitive(False)
        
        box = self.filechooser.get_filechooser_widget()
        
        self.fixed.add(box)
        self.filechooser.add_filter('gcode', ['.ngc', '.TAP', '.txt'])
        self.filechooser.add_filter('all', ['*'])
        self.filechooser.set_filter('gcode')
        self.filechooser.set_show_hidden(False)
        
        #print self.filechooser.get_filter()
        #print self.filechooser.get_filters()
        
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

    def on_file_activated(self, obj, fpath):
        print("File activated: " + fpath)

    def on_file_selection_changed(self, obj, path):
        print("Selection changed: " + path)

    # Delete the window
    def on_window1_delete_event(self, widget, event, data=None):
        self.window.destroy()
        gtk.main_quit()

    def on_filename_edited(self, obj, entry):
        # TODO add popup keyboard here
        pass


def main():
    gtk.main()


if __name__ == "__main__":
    ui = Filechooser()
    main()
