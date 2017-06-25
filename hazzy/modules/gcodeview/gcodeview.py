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
import gobject
from hal_glib import GStat

# Set up paths
PYDIR = os.path.dirname(os.path.realpath(__file__))
LANGDIR = os.path.join(PYDIR, 'gcode_highlight', "language-specs")
STYLEDIR = os.path.join(PYDIR, 'gcode_highlight', "styles")


class GcodeView(gobject.GObject,):
    __gtype_name__ = 'GcodeView'
    __gsignals__ = {
        'file-activated': (gobject.SIGNAL_RUN_FIRST, None, (str,)),
        'selection-changed': (gobject.SIGNAL_RUN_FIRST, None, (str,)),
        'button-press-event': (gobject.SIGNAL_RUN_FIRST, None, (object,)),
        'error': (gobject.SIGNAL_RUN_FIRST, None, (str, str))
    }

    def __init__(self, preview=False):

        gobject.GObject.__init__(self)

        self.is_preview = preview

        # create buffer
        self.buf = gtksourceview.Buffer()
        self.gtksourceview = gtksourceview.View(self.buf)

        # setup style and lang managers
        self.lm = gtksourceview.LanguageManager()
        self.sm = gtksourceview.StyleSchemeManager()

        self.lm.set_search_path([LANGDIR])
        self.sm.set_search_path([STYLEDIR])

        self.buf.set_style_scheme(self.sm.get_scheme('gcode'))
        self.buf.set_language(self.lm.get_language('gcode'))

        self.buf.set_max_undo_levels(20)

        self.gtksourceview.set_show_line_numbers(True)
        self.gtksourceview.set_show_line_marks(False)
        self.gtksourceview.set_highlight_current_line(False)

        # Only allow edit if gcode preview
        self.gtksourceview.set_editable(self.is_preview)

        # Only highlight motion line if not preview
        if not self.is_preview:
            self.gstat = GStat()
            self.gstat.connect('line-changed', self.highlight_motion_line)
            self.gstat.connect('file-loaded', self.load_file)
            self.gtksourceview.set_can_focus(False)

        self.gtksourceview.connect('button-press-event', self.on_button_press)
        self.gtksourceview.connect('key-press-event', self.on_key_press)

        self.gtksourceview.set_mark_category_background('motion', gtk.gdk.Color('#c5c5c5'))
        self.gtksourceview.set_mark_category_background('error', gtk.gdk.Color('#ff7373'))

        self.mark = None
        self.current_file = None
        self.error_line =None

        self.gtksourceview.show()


    def load_file(self, widget, fn=None):
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


    def highlight_line(self, lnum, style='motion'):
        if not lnum:
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
        self.gtksourceview.scroll_to_mark(self.mark, 0, True, 0, 0.5)


    def highlight_motion_line(self, gobject, lnum):
        self.highlight_line(lnum, 'motion')

    def highlight_error_line(self, lnum):
        self.error_line = lnum

    def get_modified(self):
        return self.buf.get_modified()

    def set_modified(self, data):
        self.buf.set_modified(data)

    def set_line_number(self, lnum):
        self.highlight_line(None, int(lnum))

    def get_program_length(self):
        return self.buf.get_line_count()


    # Toggle line numbers on double click
    def on_button_press(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            if widget.get_show_line_numbers():
                widget.set_show_line_numbers(False)
            else:
                widget.set_show_line_numbers(True)
        elif event.button == 3:
            return True

        if self.is_preview:
            if self.current_file is None:
                pass #self.load_(self.new_program_template)
#            if self.keypad_on_edit:
#                self.keyboard.show(widget, None, True)


    # If no "save as" file name specified save to the current file in preview
    def save(self, fn=None):
        if fn is None:
            fn = self.current_file
        text = self.buf.get_text(self.buf.get_start_iter(), self.buf.get_end_iter())

        with open(fn, "w") as openfile:
            openfile.write(text)

        self.buf.set_modified(False)
        print("Saved file as: {0}".format(fn))


    # ctrl+s to save the file
    def on_key_press(self, widget, event):
        kv = event.keyval
        if event.state & gtk.gdk.CONTROL_MASK:
            if kv == gtk.keysyms.s:
                self.save()
        elif kv == gtk.keysyms.Escape:
            # FIXME this is OK??
            self.gtksourceview.parent.parent.set_focus(None)
            pass


# ==========================================================
# For standalone testing
# ==========================================================

def main():
    gtk.main()

def destroy(widget):
    gtk.main_quit()

if __name__ == "__main__":
    gcodeview = GcodeView(preview=True)
    window = gtk.Window()
    scrolled = gtk.ScrolledWindow()
    window.connect('destroy', destroy)
    scrolled.add(gcodeview.gtksourceview)
    window.add(scrolled)
    window.set_default_size(350, 400)
    gcodeview.buf.set_text(
'''(TEST OF G-CODE HIGHLIGHTING)

G1 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0

M3''')
    window.show_all()
    gcodeview.highlight_line(2, 'error')
    main()
