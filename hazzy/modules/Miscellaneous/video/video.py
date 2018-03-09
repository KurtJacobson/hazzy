#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
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
#   Video widget for use with spotting camera or machine web-cam.

# ToDo:
#   Finish streaming over HTTP
#   Add crosshairs

import os
import sys
from threading import Thread
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gtk
from gi.repository import Gst
from gi.repository import GstVideo
from gi.repository import GObject
from gi.repository import GLib

from widget_factory import pref_widgets
from utilities import preferences as prefs
from utilities import logger

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

# Setup logging
log = logger.get(__name__)

Gst.init(None)
GObject.threads_init()


class GstWidget(Gtk.Box):
    title = 'Video'
    author = 'TurBoss'
    version = '0.1.0'
    date = '09/07/2017'
    description = 'Video'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.gst_video = VideoModule()

        # self.gst_widget = self.gst_video.get_gtksink()

        self.connect('unmap', self._on_unmap)
        self.connect('map', self._on_map)

        self.config_stack = False

        self.set_size_request(320, 240)

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        button_start = Gtk.ToggleButton(label="Start")
        button_start.connect("toggled", self.on_button_start_toggled, "1")

        button_stream = Gtk.ToggleButton(label="Stream")
        button_stream.connect("toggled", self.on_button_stream_toggled, "1")

        self.button_box.pack_start(button_start, False, True, 0)
        self.button_box.pack_start(button_stream, False, True, 0)

        # self.widget_box.pack_start(self.gst_widget, False, True, 0)
        self.widget_box.pack_start(self.button_box, False, True, 0)

        self.size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        self.video_device = None
        devices = ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video3"]
        default = "/dev/video0"
        combo = pref_widgets.PrefComboBox('VedioWidget', 'Device', devices, default)
        combo.connect('value-changed', self.on_device_changed)
        self.add_config_field(combo)

        entry = pref_widgets.PrefEntry('VedioWidget', 'Host', '127.0.0.1')
        entry.connect('value-changed', self.on_host_chaned)
        # self.add_config_field(entry)

        entry = pref_widgets.PrefEntry('VedioWidget', 'Port', '5000')
        entry.connect('value-changed', self.on_port_changed)
        # self.add_config_field(entry)

        switch = pref_widgets.PrefSwitch('VedioWidget', 'Stream', True)
        switch.connect('value-changed', self.on_stream_state_changed)
        # self.add_config_field(switch)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)

    def on_device_changed(self, widget, device):
        self.video_device = device
        print 'Device changed: ', device

    def on_host_chaned(self, widget, host):
        print 'Host changed: ', host

    def on_port_changed(self, widget, port):
        print 'Port changed: ', port

    def on_stream_state_changed(self, widget, streaming):
        print 'Streaming changed: ', streaming
        self.streaming(streaming)

    def add_config_field(self, feild):
        box = pref_widgets.PrefFeild(feild, self.size_group)
        self.config_box.pack_start(box, False, True, 5)

    def on_settings_button_pressed(self, button):
        if self.config_stack:
            self.config_stack = False
            self.stack.set_visible_child_name("widget")
        else:
            self.config_stack = True
            self.stack.set_visible_child_name("config")

    def on_button_start_toggled(self, button, name):
        if button.get_active():
            self.gst_video.run()
        else:
            self.gst_video.stop()

    def on_button_stream_toggled(self, button, name):
        if button.get_active():
            self.gst_video.run()
        else:
            self.gst_video.stop()

    def _on_map(self, *args, **kwargs):
        """It seems this is called when the widget is becoming visible"""
        self.gst_video.run()

    def _on_unmap(self, *args, **kwargs):
        """Hopefully called when this widget is hidden,
        e.g. when the tab of a notebook has changed"""
        self.gst_video.stop()

    def streaming(self, enabled):
        if enabled:
            self.stream_thread.start()
        else:
            self.stream_thread.stop()


class Settings:
    stream_location = 'https://127.0.0.1:1337/video.mpd'
    speed_preset = 3
    amplification = 4


class VideoModule:
    def __init__(self):

        self.mainloop = GLib.MainLoop()

        self.pipeline = Gst.Pipeline()

        self.clock = self.pipeline.get_pipeline_clock()

        self.bus = self.pipeline.get_bus()

        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self._on_eos)
        self.bus.connect('message::tag', self._on_tag)
        self.bus.connect('message::error', self._on_error)

        rates = [
            ['low', 'video/x-raw, width=320, height=240', 500, 3],
            ['med', 'video/x-raw, width=640, height=480', 1500, 3],
            ['high', 'video/x-raw, width=1024, height=768', 5000, 4]
        ]

        # Video input
        self.malm([
            ['videotestsrc', None, {}],
            ['capsfilter', None, {'caps': 'video/x-raw, width=320, height=240'}],
            ['videoconvert', None, {}],
            ['deinterlace', None, {}],
            ['videorate', None, {}],
            ['capsfilter', None, {'caps': 'video/x-raw, framerate=30000/1001'}],
            ['tee', 'vinput', {}]
        ])

        # Create each encoder, muxer, and rtmpsink.
        for rate in rates:
            self.malm([
                ['queue', 'v{}'.format(rate[0]), {'max-size-bytes': 104857600}],
                ['videoscale', None, {}],
                ['capsfilter', None, {'caps': rate[1]}],
                ['x264enc', None, {
                    'speed-preset': Settings.speed_preset,
                    'tune': 'zerolatency',
                    'bitrate': rate[2],
                    'threads': rate[3],
                    'option-string': 'scenecut=0'
                }],
                ['capsfilter', None, {'caps': 'video/x-h264, profile=baseline'}],
                ['h264parse', None, {}],
                ['flvmux', 'm{}'.format(rate[0]), {'streamable': True}],
                ['rtmpsink', None, {'location': Settings.stream_location + rate[0]}]
            ])

            self.vinput.link(getattr(self, 'v{}'.format(rate[0])))

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        GLib.timeout_add(2 * 1000, self.do_keyframe, None)
        self.mainloop.run()

    def stop(self):
        print('Exiting...')
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, 'stream')
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()

    def do_keyframe(self, user_data):
        # Forces a keyframe on all video encoders
        event = GstVideo.video_event_new_downstream_force_key_unit(self.clock.get_time(), 0, 0, True, 0)
        self.pipeline.send_event(event)

        return True

    def _on_eos(self, bus, msg):
        log.info('on_eos')

    def _on_tag(self, bus, msg):
        taglist = msg.parse_tag()
        log.info('on_tag:')
        for key in taglist.keys():
            log.info('\t{0} = {1}'.format(key, taglist[key]))

    def _on_error(self, bus, msg):
        error = msg.parse_error()
        log.error('on_error: {0}'.format(error[1]))

    def _pipe_video(self):

        # self.video_source = Gst.ElementFactory.make('videotestsrc', 'test-source')
        self.video_source = Gst.ElementFactory.make('v4l2src', 'v4l2-source')
        self.video_source.set_property("device", prefs.get('VedioWidget', 'Device', self.video_device, str))
        self.pipeline.add(self.video_source)

        self.video_converter = Gst.ElementFactory.make('videoconvert', None)
        self.pipeline.add(self.video_converter)

        self.video_scale = Gst.ElementFactory.make('videoscale', None)
        self.pipeline.add(self.video_scale)

        caps = Gst.Caps.from_string("video/x-raw,width=320,height=240")
        self.camera_filter = Gst.ElementFactory.make("capsfilter", "gtk-filter")
        self.camera_filter.set_property("caps", caps)
        self.pipeline.add(self.camera_filter)

        self.video_enc = Gst.ElementFactory.make("theoraenc", None)
        self.pipeline.add(self.video_enc)

        self.video_mux = Gst.ElementFactory.make('oggmux', None)
        self.pipeline.add(self.video_mux)

        self.gtk_sink = Gst.ElementFactory.make('gtksink', None)
        self.pipeline.add(self.gtk_sink)

        self.tcp_sink = Gst.ElementFactory.make('tcpserversink', None)
        self.tcp_sink.set_property('host', '127.0.0.1')
        self.tcp_sink.set_property('port', 1337)
        self.pipeline.add(self.tcp_sink)

        self.tee = Gst.ElementFactory.make('tee', None)
        self.pipeline.add(self.tee)

        self.queue_1 = Gst.ElementFactory.make('queue', "GtkSink")
        self.pipeline.add(self.queue_1)

        self.queue_2 = Gst.ElementFactory.make('queue', "StreamSink")
        self.pipeline.add(self.queue_2)

        self.video_source.link(self.video_converter)
        self.video_converter.link(self.video_scale)
        self.video_scale.link(self.camera_filter)
        self.camera_filter.link(self.tee)

        self.tee.link(self.queue_1)
        self.queue_1.link(self.gtk_sink)

        self.tee.link(self.queue_2)
        self.queue_2.link(self.tcp_sink)

    def get_gtksink(self):
        return self.gtk_sink.get_property("widget")

    def malm(self, to_add):
        # Make-add-link multi
        prev = None
        for n in to_add:
            element = Gst.ElementFactory.make(n[0], n[1])

            if not element:
                raise Exception('cannot create element {}'.format(n[0]))

            if n[1]: setattr(self, n[1], element)

            for p, v in n[2].items():
                if p == 'caps':
                    caps = Gst.Caps.from_string(v)
                    element.set_property('caps', caps)
                else:
                    element.set_property(p, v)

            self.pipeline.add(element)
            if prev: prev.link(element)

            prev = element
