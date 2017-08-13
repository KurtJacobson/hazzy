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

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GtkSource

# Set up paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if not HAZZYDIR in sys.path:
    sys.path.insert(1, HAZZYDIR)

LANGDIR = os.path.join(PYDIR, 'gcode_highlight', "language-specs")
STYLEDIR = os.path.join(PYDIR, 'gcode_highlight', "styles")

# Import our own modules
from utilities.preferences import Preferences
from modules.touchpads.keyboard import Keyboard

# Setup logger
from utilities import logger
log = logger.get("HAZZY.GCODEVIEW")


class GcodeViewWidget(Gtk.Frame):
    def __init__(self):
        Gtk.Frame.__init__(self)

        self.gcodeview = GcodeView(preview=True)
        self.scrolled = Gtk.ScrolledWindow()

        self.scrolled.add(self.gcodeview.view)

        self.add(self.scrolled)

        self.gcodeview.buf.set_text('''(TEST OF G-CODE HIGHLIGHTING)\n\nG1 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0\n\nM3''')
        self.gcodeview.highlight_line(3, 'motion')

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.show_all()

class GcodeView(GObject.GObject,):
    __gtype_name__ = 'GcodeView'
    __gsignals__ = {
        'file-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'selection-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'button-press-event': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'error': (GObject.SignalFlags.RUN_FIRST, None, (str, str))
    }

    def __init__(self, preview=False):

        GObject.GObject.__init__(self)
        self.is_preview = preview

        # Module init
#        self.prefs = Preferences
#        self.keyboard = Keyboard

        # create buffer
        self.view = GtkSource.View()
        self.buf = self.view.get_buffer()

        # setup style and lang managers
        self.lm = GtkSource.LanguageManager()
        self.sm = GtkSource.StyleSchemeManager()

        self.lm.set_search_path([LANGDIR])
        self.sm.set_search_path([STYLEDIR])

        self.buf.set_style_scheme(self.sm.get_scheme('gcode'))
        self.buf.set_language(self.lm.get_language('gcode'))

        self.buf.set_max_undo_levels(20)

        self.view.set_show_line_numbers(True)
        self.view.set_show_line_marks(False)
        self.view.set_highlight_current_line(False)

        # Only allow edit if gcode preview
        self.view.set_editable(self.is_preview)

        self.holder_text = "\t\t\t****No file to preview****"

        # Only highlight motion line if not preview
        if not self.is_preview:
            self.view.set_can_focus(False)
            self.holder_text = ""

        self.view.connect('button-press-event', self.on_button_press)
        self.view.connect('key-press-event', self.on_key_press)

        # Set line highlight styles
        self.add_mark_category('error', '#ff7373')
        self.add_mark_category('motion', '#c5c5c5')
        self.add_mark_category('selected', '#96fef6')


        self.mark = None
        self.current_file = None
        self.error_line =None

        self.view.show()


    def add_mark_category(self, category, bg_color):
        att = GtkSource.MarkAttributes()
        color = Gdk.RGBA()
        color.parse(bg_color)
        att.set_background(color)
        self.view.set_mark_attributes(category, att, 1)


    def load_file(self, fn=None):
        self.current_file = fn
        self.buf.begin_not_undoable_action()
        if not fn:
            self.buf.set_text(self.holder_text)
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


    def highlight_line(self, lnum, style='none'):
        print lnum, style
        if not lnum or lnum == -1:
            if self.mark:
                self.buf.delete_mark(self.mark)
                self.mark = None
            print '1'
            return
        iter = self.buf.get_iter_at_line(lnum-1)
        print iter
        if not self.mark:
            print '2'
            self.mark = self.buf.create_source_mark(style, style, iter)
        elif self.mark != self.buf.get_mark(style):
            self.buf.delete_mark(self.mark)
            self.mark = self.buf.create_source_mark(style, style, iter)
            print '3'
        else:
            self.buf.move_mark(self.mark, iter)
        self.view.scroll_to_mark(self.mark, 0, True, 0, 0.5)

    # Since Gremlin reports any errors before GStat emits the 'file-loaded'
    # signal, we have to save the error line here and then do the actual 
    # highlighting after we have loaded the sourceview in 'self.load_file'
    def highlight_error_line(self, lnum):
        self.error_line = lnum

    def get_modified(self):
        return self.buf.get_modified()

    def set_modified(self, data):
        self.buf.set_modified(data)

    def set_line_number(self, lnum):
        self.highlight_line(int(lnum))

    def get_program_length(self):
        return self.buf.get_line_count()


    # Toggle line numbers on double click
    def on_button_press(self, widget, event):
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            if widget.get_show_line_numbers():
                widget.set_show_line_numbers(False)
            else:
                widget.set_show_line_numbers(True)
        elif event.button == 3:
            return True

        if self.is_preview:
            if self.current_file is None:
                pass #self.load_file(self.prefs.getpref("FILE PATHS", "NEW_PROGRAM_TEMPLATE", "", str))
            if False: #self.prefs.getpref("POP-UP KEYPAD", "USE_ON_EDIT", "YES"):
                pass #self.keyboard.show(widget, True)


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


# ==========================================================
# For standalone testing
# ==========================================================

def main():

    gcodeview = GcodeView(preview=True)
    window = Gtk.Window()
    scrolled = Gtk.ScrolledWindow()

    window.connect('destroy', Gtk.main_quit)

    scrolled.add(gcodeview.view)

    window.add(scrolled)
    window.set_default_size(350, 400)

    gcodeview.buf.set_text('''(TEST OF G-CODE HIGHLIGHTING)\n\nG1 X1.2454 Y2.3446 Z-10.2342 I0 J0 K0\n\nM3''')
    gcodeview.highlight_line(3, 'motion')

    window.show_all()

    Gtk.main()

if __name__ == "__main__":
    main()
