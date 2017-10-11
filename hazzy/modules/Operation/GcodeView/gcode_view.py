#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
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

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GtkSource

# Set up paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
LANGDIR = os.path.join(PYDIR, 'gcode_highlight', "language-specs")
STYLEDIR = os.path.join(PYDIR, 'gcode_highlight', "styles")


class GcodeView(GtkSource.View):

    def __init__(self):
        GtkSource.View.__init__(self)

        # create buffer
        self.buf = self.get_buffer()

        # setup style and lang managers
        self.lm = GtkSource.LanguageManager()
        self.sm = GtkSource.StyleSchemeManager()

        self.lm.set_search_path([LANGDIR])
        self.sm.set_search_path([STYLEDIR])

        self.buf.set_style_scheme(self.sm.get_scheme('gcode'))
        self.buf.set_language(self.lm.get_language('gcode'))

        self.buf.set_max_undo_levels(20)

        self.set_show_line_numbers(True)
        self.set_show_line_marks(False)
        self.set_highlight_current_line(False)

        self.connect('key-press-event', self.on_key_press)

        # Set line highlight styles
        self.add_mark_category('error', '#ff7373')
        self.add_mark_category('motion', '#c5c5c5')
        self.add_mark_category('selected', '#96fef6')

        self.mark = None
        self.current_file = None
        self.error_line = None

        self.show()

    def add_mark_category(self, category, bg_color):
        att = GtkSource.MarkAttributes()
        color = Gdk.RGBA()
        color.parse(bg_color)
        att.set_background(color)
        self.set_mark_attributes(category, att, 1)

    def load_file(self, fn=None):
        self.current_file = fn
        self.buf.begin_not_undoable_action()
        if not fn:
            self.buf.set_text('')
        else:
            with open(fn, 'r') as f:
                self.buf.set_text(f.read())
        self.buf.end_not_undoable_action()
        self.buf.set_modified(False)

        if self.error_line:
            self.highlight_line(self.error_line, 'error')
            self.error_line = None
        else:
            self.highlight_line(None)


    def highlight_line(self, lnum=None, style=None):
        style = style or 'none' # Must be a string
        if not lnum or lnum == -1:
            if self.mark:
                self.buf.delete_mark(self.mark)
                self.mark = None
            return
        iter = self.buf.get_iter_at_line(lnum-1)
        if not self.mark:
            self.mark = self.buf.create_source_mark(style, style, iter)
        elif self.mark != self.buf.get_mark(style):
            self.buf.delete_mark(self.mark)
            self.mark = self.buf.create_source_mark(style, style, iter)
        else:
            self.buf.move_mark(self.mark, iter)
        self.scroll_to_mark(self.mark, 0, True, 0, 0.5)

    # Since Gremlin3D reports any errors before GStat emits the 'file-loaded'
    # signal, we have to save the error line here and then do the actual 
    # highlighting after we have loaded the sourceview in 'self.load_file'
    def highlight_error_line(self, lnum):
        self.error_line = lnum

    def get_modified(self):
        return self.buf.get_modified()

    def set_modified(self, modified):
        self.buf.set_modified(modified)

    def set_line_number(self, lnum):
        self.highlight_line(int(lnum))

    def get_program_length(self):
        return self.buf.get_line_count()

    # If no "save as" file name specified save to the current file in preview
    def save(self, fn=None):
        if fn is None:
            fn = self.current_file
        text = self.buf.get_text(self.buf.get_start_iter(), self.buf.get_end_iter(), include_hidden_chars=True)

        with open(fn, "w") as openfile:
            openfile.write(text)

        self.buf.set_modified(False)
        log.info('Saved file as "{0}"'.format(fn))

    # ctrl+s to save the file
    def on_key_press(self, widget, event):
        kv = event.keyval
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            if kv == Gdk.KEY_s:
                self.save()


def demo():
    view = GcodeView()
    buf = view.get_buffer()
    buf.set_text('''(TEST OF G-CODE HIGHLIGHTING)\n\nG1 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0\n\nM3''')
    view.highlight_line(3, None)

    scrolled = Gtk.ScrolledWindow()
    scrolled.add(view)

    win = Gtk.Window()
    win.set_default_size(400, 300)
    win.add(scrolled)

    win.connect('destroy', Gtk.main_quit)

    file = Gio.File.new_for_path('/home/kurt/Desktop/theme.py')
    print file. get_path()

    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    demo()
