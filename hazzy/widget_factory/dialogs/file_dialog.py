#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#       <kurtcjacobson@gmail.com>
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
#   File chooser dialog to be called by app menu etc.

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk


class FileDialog(Gtk.FileChooserDialog):
    def __init__(self, *args, **kwargs):
        super(FileDialog, self).__init__(*args, **kwargs)

        self.set_titlebar(Gtk.HeaderBar(show_close_button=True))
        self.set_title("Open File")
        self.add_button("_Open", Gtk.ResponseType.OK)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.set_default_response(Gtk.ResponseType.OK)

        #TODO Add file filters based on extensions given in INI

        filefiler = Gtk.FileFilter()
        filefiler.add_pattern('*.ngc')
        filefiler.set_name('G-code')
        self.add_filter(filefiler)

        filefiler = Gtk.FileFilter()
        filefiler.add_pattern('*')
        filefiler.set_name('All Files')
        self.add_filter(filefiler)

        self.show_all()

if __name__ == '__main__':
    app = FileDialog()
    response = app.run()

    if response == Gtk.ResponseType.OK:
        file_name = app.get_filename()
        print("File selected: %s" % file_name)

    app.destroy()
