#!/usr/bin/env python
#    Copyright (C) 2009-2012
#    Jeff Epler <jepler@unpythonic.net>,
#    Pavel Shramov <psha@kamba.psha.org.ru>,
#    Chris Morley <chrisinnanaimo@hotmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    2014 Steffen Noack
#    add property 'mouse_btn_mode'
#    0 = default: left rotate, middle move,   right zoom
#    1 =          left zoom,   middle move,   right rotate
#    2 =          left move,   middle rotate, right zoom
#    3 =          left zoom,   middle rotate, right move
#    4 =          left move,   middle zoom,   right rotate
#    5 =          left rotate, middle zoom,   right move
#
#    2015 Moses McKnight introduced mode 6
#    6 = left move, middle zoom, right zoom (no rotate - for 2D plasma machines or lathes)
#
#    2016 Norbert Schechner
#    corrected mode handling for lathes, as in most modes it was not possible to move, as
#    it has only been allowed in p view.

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from deps import glnav3
from deps.rs274 import glcanon
from deps.rs274 import interpret

import linuxcnc
import gcode

import re
import tempfile
import shutil
import os
import sys

import thread


class DummyProgress:
    def nextphase(self, unused): pass

    def progress(self): pass


class StatCanon(glcanon.GLCanon, interpret.StatMixin):
    def __init__(self, colors, geometry, lathe_view_option, stat, random):
        glcanon.GLCanon.__init__(self, colors, geometry)
        interpret.StatMixin.__init__(self, stat, random)
        self.progress = DummyProgress()
        self.lathe_view_option = lathe_view_option

    def is_lathe(self): return self.lathe_view_option

    def change_tool(self, pocket):
        glcanon.GLCanon.change_tool(self, pocket)
        interpret.StatMixin.change_tool(self, pocket)


class Gremlin3D(Gtk.GLArea, glnav3.GlNavBase,
                glcanon.GlCanonDraw):
    rotation_vectors = [(1., 0., 0.), (0., 0., 1.)]

    def __init__(self, inifile):

        Gtk.GLArea.__init__(self)
        glnav3.GlNavBase.__init__(self)

        def get_color(s):
            a = self.colors[s + "_alpha"]
            s = self.colors[s]
            return [int(x * 255) for x in s + (a,)]

        self.inifile = inifile
        self.logger = linuxcnc.positionlogger(linuxcnc.stat(),
                                              get_color('backplotjog'),
                                              get_color('backplottraverse'),
                                              get_color('backplotfeed'),
                                              get_color('backplotarc'),
                                              get_color('backplottoolchange'),
                                              get_color('backplotprobing'),
                                              self.get_geometry()
                                              )
        thread.start_new_thread(self.logger.start, (.01,))

        glcanon.GlCanonDraw.__init__(self, linuxcnc.stat(), self.logger)

        self.current_view = 'z'

        self.select_primed = None

        self.connect_after('realize', self.realize)
        self.connect('configure_event', self.reshape)
        self.connect('map-event', self.map)
        self.connect('draw', self.on_draw)
        self.connect('motion-notify-event', self.motion)
        self.connect('button-press-event', self.pressed)
        self.connect('button-release-event', self.select_fire)
        self.connect('scroll-event', self.scroll)

        self.add_events(Gdk.EventMask.EXPOSURE_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.SCROLL_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                        Gdk.EventMask.ENTER_NOTIFY_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.fingerprint = ()

        self.lat = 0
        self.minlat = -90
        self.maxlat = 90

        self.highlight_line = None
        self.program_alpha = False
        self.use_joints_mode = False
        self.use_commanded = True
        self.show_limits = True
        self.show_extents_option = True
        self.show_live_plot = True
        self.show_velocity = True
        self.metric_units = True
        self.show_program = True
        self.show_rapids = True
        self.use_relative = True
        self.show_tool = True
        self.show_dtg = True
        self.grid_size = 0.0
        temp = inifile.find("DISPLAY", "LATHE")
        self.lathe_option = bool(temp == "1" or temp == "True" or temp == "true")
        self.foam_option = bool(inifile.find("DISPLAY", "FOAM"))
        self.show_offsets = False
        self.use_default_controls = True
        self.mouse_btn_mode = 0

        self.a_axis_wrapped = inifile.find("AXIS_A", "WRAPPED_ROTARY")
        self.b_axis_wrapped = inifile.find("AXIS_B", "WRAPPED_ROTARY")
        self.c_axis_wrapped = inifile.find("AXIS_C", "WRAPPED_ROTARY")

        live_axis_count = 0
        for i, j in enumerate("XYZABCUVW"):
            if self.stat.axis_mask & (1 << i) == 0:
                continue
            live_axis_count += 1
        self.num_joints = int(inifile.find("KINS", "JOINTS") or live_axis_count)

    def activate(self):
        glcontext = Gtk.GLArea.get_context(self)
        gldrawable = Gtk.GLArea.widget_get_gl_drawable(self)

        return gldrawable and glcontext and gldrawable.gl_begin(glcontext)

    def swapbuffers(self):
        gldrawable = Gtk.GLArea.widget_get_gl_drawable(self)
        gldrawable.swap_buffers()

    def deactivate(self):
        gldrawable = Gtk.GLArea.widget_get_gl_drawable(self)
        gldrawable.gl_end()

    def winfo_width(self):
        return self.width

    def winfo_height(self):
        return self.height

    def reshape(self, widget, event):
        self.width = event.width
        self.height = event.height

    def on_draw(self, widget=None, event=None):
        if not self.initialised: return
        if self.perspective:
            self.redraw_perspective()
        else:
            self.redraw_ortho()

        return True

    def _redraw(self):
        self.on_draw()

    def clear_live_plotter(self):
        self.logger.clear()

    def map(self, *args):
        GObject.timeout_add(50, self.poll)

    def poll(self):
        s = self.stat
        try:
            s.poll()
        except:
            return
        fingerprint = (self.logger.npts, self.soft_limits(),
                       s.actual_position, s.joint_actual_position,
                       s.homed, s.g5x_offset, s.g92_offset, s.limit, s.tool_in_spindle,
                       s.motion_mode, s.current_vel)

        if fingerprint != self.fingerprint:
            self.fingerprint = fingerprint
            self.queue_draw()

        # return self.visible
        return True

    @glcanon.with_context
    def realize(self):
        self.set_current_view()
        s = self.stat
        try:
            s.poll()
        except:
            return
        self._current_file = None

        self.font_base, width, linespace = \
            glnav3.use_pango_font('courier bold 16', 0, 128)
        self.font_linespace = linespace
        self.font_charwidth = width
        glcanon.GlCanonDraw.realize(self)

        if s.file:
            self.load()

    def set_current_view(self):
        if self.current_view not in ['p', 'x', 'y', 'y2', 'z', 'z2']:
            return
        return getattr(self, 'set_view_%s' % self.current_view)()

    def load(self, filename=None):
        s = self.stat
        s.poll()
        if not filename and s.file:
            filename = s.file
        elif not filename and not s.file:
            return

        td = tempfile.mkdtemp()
        self._current_file = filename
        try:
            random = int(self.inifile.find("EMCIO", "RANDOM_TOOLCHANGER") or 0)
            canon = StatCanon(self.colors, self.get_geometry(), self.lathe_option, s, random)
            parameter = self.inifile.find("RS274NGC", "PARAMETER_FILE")
            temp_parameter = os.path.join(td, os.path.basename(parameter or "linuxcnc.var"))
            if parameter:
                shutil.copy(parameter, temp_parameter)
            canon.parameter_file = temp_parameter

            unitcode = "G%d" % (20 + (s.linear_units == 1))
            initcode = self.inifile.find("RS274NGC", "RS274NGC_STARTUP_CODE") or ""
            result, seq = self.load_preview(filename, canon, unitcode, initcode)
            if result > gcode.MIN_ERROR:
                self.report_gcode_error(result, seq, filename)

        finally:
            shutil.rmtree(td)

        self.set_current_view()

    def get_program_alpha(self):
        return self.program_alpha

    def get_num_joints(self):
        return self.num_joints

    def get_geometry(self):
        temp = self.inifile.find("DISPLAY", "GEOMETRY")
        if temp:
            geometry = re.split(" *(-?[XYZABCUVW])", temp.upper())
            self.geometry = "".join(reversed(geometry))
        else:
            self.geometry = 'XYZ'
        return self.geometry

    def get_joints_mode(self):
        return self.use_joints_mode

    def get_show_commanded(self):
        return self.use_commanded

    def get_show_extents(self):
        return self.show_extents_option

    def get_show_limits(self):
        return self.show_limits

    def get_show_live_plot(self):
        return self.show_live_plot

    def get_show_machine_speed(self):
        return self.show_velocity

    def get_show_metric(self):
        return self.metric_units

    def get_show_program(self):
        return self.show_program

    def get_show_rapids(self):
        return self.show_rapids

    def get_show_relative(self):
        return self.use_relative

    def get_show_tool(self):
        return self.show_tool

    def get_show_distance_to_go(self):
        return self.show_dtg

    def get_grid_size(self):
        return self.grid_size

    def get_view(self):
        view_dict = {'x': 0, 'y': 1, 'y2': 1, 'z': 2, 'z2': 2, 'p': 3}
        return view_dict.get(self.current_view, 3)

    def is_lathe(self):
        return self.lathe_option

    def is_foam(self):
        return self.foam_option

    def get_current_tool(self):
        for i in self.stat.tool_table:
            if i[0] == self.stat.tool_in_spindle:
                return i

    def get_highlight_line(self):
        return self.highlight_line

    def get_a_axis_wrapped(self):
        return self.a_axis_wrapped

    def get_b_axis_wrapped(self):
        return self.b_axis_wrapped

    def get_c_axis_wrapped(self):
        return self.c_axis_wrapped

    def get_font_info(self):
        return self.font_charwidth, self.font_linespace, self.font_base

    def get_show_offsets(self):
        return self.show_offsets

    def select_prime(self, x, y):
        self.select_primed = x, y

    @glcanon.with_context
    def select_fire(self, widget, event):
        if not self.select_primed: return
        x, y = self.select_primed
        self.select_primed = None
        self.select(x, y)

    def select_cancel(self, widget=None, event=None):
        self.select_primed = None

    def pressed(self, widget, event):
        if not self.use_default_controls:
            return
        button1 = event.button == 1
        button2 = event.button == 2
        button3 = event.button == 3
        if button1:
            self.select_prime(event.x, event.y)  # select G-Code element

        if button3 and (event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS):
            self.clear_live_plotter()
        elif button1 or button2 or button3:
            self.startZoom(event.y)
            self.recordMouse(event.x, event.y)

    def motion(self, widget, event):
        if not self.use_default_controls:
            return
        button1 = event.get_state() & Gdk.ModifierType.BUTTON1_MASK
        button2 = event.get_state() & Gdk.ModifierType.BUTTON2_MASK
        button3 = event.get_state() & Gdk.ModifierType.BUTTON3_MASK
        shift = event.get_state() & Gdk.ModifierType.SHIFT_MASK
        # for lathe or plasmas rotation is not used, so we check for it
        # recomended to use mode 6 for that type of machines
        cancel = bool(self.lathe_option)

        # 0 = default: left rotate, middle move, right zoom
        if self.mouse_btn_mode == 0:
            if button1:
                if shift:
                    self.translateOrRotate(event.x, event.y)
                elif not cancel:
                    self.set_prime(event.x, event.y)
                    self.rotateOrTranslate(event.x, event.y)
            elif button2:
                self.translateOrRotate(event.x, event.y)
            elif button3:
                self.continueZoom(event.y)
        # 1 = left zoom, middle move, right rotate
        elif self.mouse_btn_mode == 1:
            if button1:
                if shift:
                    self.translateOrRotate(event.x, event.y)
                else:
                    self.continueZoom(event.y)
            elif button2:
                self.translateOrRotate(event.x, event.y)
            elif button3 and not cancel:
                self.set_prime(event.x, event.y)
                self.rotateOrTranslate(event.x, event.y)
        # 2 = left move, middle rotate, right zoom
        elif self.mouse_btn_mode == 2:
            if button1:
                if shift:
                    if not cancel:
                        self.set_prime(event.x, event.y)
                        self.rotateOrTranslate(event.x, event.y)
                else:
                    self.translateOrRotate(event.x, event.y)
            elif button2 and not cancel:
                self.set_prime(event.x, event.y)
                self.rotateOrTranslate(event.x, event.y)
            elif button3:
                self.continueZoom(event.y)
        # 3 = left zoom, middle rotate, right move
        elif self.mouse_btn_mode == 3:
            if button1:
                if shift:
                    if not cancel:
                        self.set_prime(event.x, event.y)
                        self.rotateOrTranslate(event.x, event.y)
                else:
                    self.continueZoom(event.y)
            elif button2 and not cancel:
                self.set_prime(event.x, event.y)
                self.rotateOrTranslate(event.x, event.y)
            elif button3:
                self.translateOrRotate(event.x, event.y)
        # 4 = left move,   middle zoom,   right rotate
        elif self.mouse_btn_mode == 4:
            if button1:
                if shift:
                    if not cancel:
                        self.set_prime(event.x, event.y)
                        self.rotateOrTranslate(event.x, event.y)
                else:
                    self.translateOrRotate(event.x, event.y)
            elif button2:
                self.continueZoom(event.y)
            elif button3 and not cancel:
                self.set_prime(event.x, event.y)
                self.rotateOrTranslate(event.x, event.y)
        # 5 = left rotate, middle zoom, right move
        elif self.mouse_btn_mode == 5:
            if button1:
                if shift:
                    self.continueZoom(event.y)
                elif not cancel:
                    self.set_prime(event.x, event.y)
                    self.rotateOrTranslate(event.x, event.y)
            elif button2:
                self.continueZoom(event.y)
            elif button3:
                self.translateOrRotate(event.x, event.y)
        # 6 = left move, middle zoom, right zoom (no rotate - for 2D plasma machines or lathes)
        elif self.mouse_btn_mode == 6:
            if button1:
                if shift:
                    self.continueZoom(event.y)
                else:
                    self.translateOrRotate(event.x, event.y)
            elif button2:
                self.continueZoom(event.y)
            elif button3:
                self.continueZoom(event.y)

    def scroll(self, widget, event):
        if not self.use_default_controls: return
        if event.direction == Gdk.ScrollDirection.UP:
            self.zoomin()
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.zoomout()

    def report_gcode_error(self, result, seq, filename):

        error_str = gcode.strerror(result)
        sys.stderr.write("G-Code error in " + os.path.basename(filename) + "\n" + "Near line "
                         + str(seq) + " of\n" + filename + "\n" + error_str + "\n")

    # These are for external controlling of the view

    def zoom_in(self):
        self.zoomin()

    def zoom_out(self):
        self.zoomout()

    def start_continuous_zoom(self, y):
        self.startZoom(y)

    def continuous_zoom(self, y):
        self.continueZoom(y)

    def set_mouse_start(self, x, y):
        self.recordMouse(x, y)

    def set_prime(self, x, y):
        if self.select_primed:
            primedx, primedy = self.select_primed
            distance = max(abs(x - primedx), abs(y - primedy))
            if distance > 8: self.select_cancel()

    def pan(self, x, y):
        self.translateOrRotate(x, y)

    def rotate_view(self, x, y):
        self.rotateOrTranslate(x, y)
