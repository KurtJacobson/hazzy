#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#     <kurtjacobson@bellsouth.net>
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


import os
import gtk
import pango
import gobject
import threading

import gcode
import gremlin
import logging

pydir = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(pydir, "ui")

log = logging.getLogger("HAZZY.GREMLIN")
#log.setLevel(logging.INFO)
log.setLevel(logging.DEBUG)

class HazzyGremlin(gremlin.Gremlin):
    __gtype_name__ = "HazzyGremlin"
    __gsignals__ = {
        'line-clicked': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'gcode-error': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, 
            (gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING,)),
        'loading-progress': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
    }


    def __init__(self, inifile, width, height):
        gobject.GObject.__init__(self)
        gremlin.Gremlin.__init__(self, inifile)

        self.width = width
        self.height = height

        self.percent = 0
        self.mouse_mode = None
        self.zoom_in_pressed = False
        self.zoom_out_pressed = False

        self.set_display_units('in')

        # Gremlin width = width - 40 to allow room for the controls
        self.set_size_request(self.width - 40, self.height)

        # Add gremlin back-plot
        self.gremlin_view = gtk.HBox()
        fixed = gtk.Fixed()
        fixed.put(self, 0, 0)
        self.gremlin_view.add(fixed)
        self.connect('button_press_event', self.on_gremlin_clicked)

        # Add touchscreen controls
        gladefile = os.path.join(UIDIR, 'controls.glade')
        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        controls = self.builder.get_object('controls')
        controls.set_size_request(40, self.height)
        self.gremlin_view.add(controls)

        # Add progress label
        self.label = gtk.Label()
        self.label.modify_font(pango.FontDescription('FreeSans 11'))
        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('White'))
        labelbox = gtk.EventBox()
        labelbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color('Black'))
        labelbox.set_size_request(-1, 20)
        labelbox.add(self.label)
        fixed.put(labelbox, 0 , self.height - 20)


#    def fileloading(self, current_line):
#        self.progressbar.show()
#        percent = current_line * 100 / self.line_count
#        if self.percent != percent:
#            self.percent = percent
#            msg = "Generating preview {}%".format(self.percent)
#            self.progressbar.set_text(msg)
#            self.progressbar.set_fraction(self.percent / 100)
#            log.debug(msg)
#            self.emit('loading_progress', percent)


    def realize(self,widget):
        super(HazzyGremlin, self).realize(widget)
        self.label.hide()


    def posstrs(self):
        l, h, p, d = gremlin.Gremlin.posstrs(self)
        return l, h, [''], ['']


    def set_display_units(self, units):
        if units == 'mm':
            self.metric_units = True
            self.grid_size = 20/25.4
            self._redraw()
            print "display mm"
        else:
            self.metric_units = False
            self.grid_size = 1
            self._redraw()
            print "dispaly in"

    def set_grid_size(self, size):
        self.grid_size = size
        self._redraw()


    def report_gcode_error(self, result, seq, fpath):
        fname = os.path.basename(fpath)
        lnum = seq - 1
        msg = gcode.strerror(result)
        log.error('G-Code error in "{0}" near line {1}, {2}'.format(fname, lnum, msg))
        self.emit('gcode-error', fname, lnum, msg)


    # Override gremlin's / glcannon's function so we can emit a GObject signal
    def update_highlight_variable(self, line):
        self.highlight_line = line
        if line is None:
            line = 0
        self.emit('line-clicked', line - 1)


# =========================================================
# Touchscreen control handlers
# =========================================================

# Zoom
    def zoom(self):
        if self.zoom_in_pressed:
            self.zoom_in()
            return True
        elif self.zoom_out_pressed:
            self.zoom_out()
            return True
        return False

    def on_zoom_in_pressed(self, widget, data=None):
        self.zoom_in_pressed = True
        gobject.timeout_add(50, self.zoom)

    def on_zoom_in_released(self, widget, data=None):
        self.zoom_in_pressed = False

    def on_zoom_out_pressed(self, widget, data=None):
        self.zoom_out_pressed = True
        gobject.timeout_add(50, self.zoom)

    def on_zoom_out_released(self, widget, data=None):
        self.zoom_out_pressed = False


# View
    def on_view_x_pressed(self, widget, data=None):
        self.set_view('x')

    def on_view_y_pressed(self, widget, data=None):
        self.set_view('y')

    def on_view_z_pressed(self, widget, data=None):
        self.set_view('z')

    def on_view_p_pressed(self, widget, data=None):
        self.set_view('p')

    def set_view(self, view):
        view = view.lower()
        if view not in ['p', 'x', 'y', 'y2', 'z', 'z2']:
            return
        self.current_view = view
        self.set_current_view()


# Mouse mode
    def on_toggle_mouse_mode_pressed(self, widget, data=None):
        if self.mouse_mode == 0:
            self.mouse_btn_mode = 2
            self.set_image('mouse_mode_image', 'view_pan.png')
            self.mouse_mode = 2
        else:
            self.mouse_btn_mode = 0
            self.set_image('mouse_mode_image', 'view_rotate.png')
            self.mouse_mode = 0

    def set_image(self, image_name, image_file):
        image = self.builder.get_object(image_name)
        image.set_from_file(os.path.join(UIDIR, image_file))


# Clear on double click
    def on_gremlin_clicked(self, widget, event, data=None):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.clear_live_plotter()

