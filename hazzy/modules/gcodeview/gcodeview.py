#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#       <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.


import pygtk
import gtk
import os
import sys
import gtksourceview2 as gtksourceview

PYDIR = os.path.dirname(os.path.realpath(__file__))

LANGDIR = os.path.join(PYDIR, 'gcode_highlight', "language-specs")
STYLEDIR = os.path.join(PYDIR, 'gcode_highlight', "styles")


class GcodeView(object):

    def __init__( self ):

        # Glade setup
        gladefile = os.path.join(PYDIR, "ui", "gcodeview.glade")

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        self.window1 = self.builder.get_object("window1")
        self.gtksourceview = self.builder.get_object("gtksourceview1")

        self.lm = gtksourceview.LanguageManager()
        self.sm = gtksourceview.StyleSchemeManager()

        self.lm.set_search_path([LANGDIR])
        self.sm.set_search_path([STYLEDIR])

        self.buf = gtksourceview.Buffer()
        self.buf.set_max_undo_levels(20)
        self.buf.set_data('languages-manager', self.lm)
        self.buf.set_style_scheme(self.sm.get_scheme('gcode'))
        self.buf.set_language(self.lm.get_language('.ngc'))

        self.gtksourceview.set_buffer(self.buf)
        self.gtksourceview.set_show_line_numbers(True)
        self.gtksourceview.set_show_line_marks(True)
        self.gtksourceview.set_highlight_current_line(True)
        self.gtksourceview.set_mark_category_icon_from_icon_name('motion', 'gtk-forward')
        self.gtksourceview.set_mark_category_background('motion', gtk.gdk.Color('#ff0'))
        self.gtksourceview.found_text_tag = self.buf.create_tag(background="yellow")

        self.buf.set_text('(DOES THE HIGHLIGHTING WORK HERE??)\n\nG0 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0 \n\nM3\n')

        self.window1.show_all()

    def on_window1_delete_event(self, widget, event):
        gtk.main_quit()


def main():
    gtk.main()

if __name__ == "__main__":
    test = GcodeView()
    main()
