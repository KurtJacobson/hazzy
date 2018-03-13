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

from gi.repository import Gtk
from gi.repository import Gst

from widget_factory import pref_widgets
from utilities import preferences as prefs
from utilities import logger

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))

# Setup logging
log = logger.get(__name__)

Gst.init(None)


class GstWidget(Gtk.Box):
    title = 'Video'
    author = 'TurBoss'
    version = '0.1.0'
    date = '09/07/2017'
    description = 'Video'

    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.video_module = VideoModule()

        self.gst_widget = self.video_module.get_gtksink()

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

        self.widget_box.pack_start(self.gst_widget, False, True, 0)
        self.widget_box.pack_start(self.button_box, False, True, 0)

        self.size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        devices = ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video3"]
        default = "/dev/video0"

        self.video_device = default

        combo = pref_widgets.PrefComboBox('VideoWidget', 'Device', devices, default)
        combo.connect('value-changed', self.on_device_changed)
        self.add_config_field(combo)

        entry = pref_widgets.PrefEntry('VideoWidget', 'Host', '0.0.0.0')
        entry.connect('value-changed', self.on_host_chaned)
        # self.add_config_field(entry)

        entry = pref_widgets.PrefEntry('VideoWidget', 'Port', '1337')
        entry.connect('value-changed', self.on_port_changed)
        # self.add_config_field(entry)

        switch = pref_widgets.PrefSwitch('VideoWidget', 'Stream', True)
        switch.connect('value-changed', self.on_stream_state_changed)
        # self.add_config_field(switch)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)

    def on_device_changed(self, widget, device):
        self.video_device = device
        log.debug('Device changed: {}'.format(device))

    def on_host_chaned(self, widget, host):
        log.debug('Host changed: {}'.format(host))

    def on_port_changed(self, widget, port):
        log.debug('Port changed: {}'.format(port))

    def on_stream_state_changed(self, widget, streaming):
        log.debug('Stream changed: {}'.format(streaming))
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
            self.video_module.start()
        else:
            self.video_module.stop()

    def on_button_stream_toggled(self, button, name):
        if button.get_active():
            self.video_module.start()
        else:
            self.video_module.stop()

    def _on_map(self, *args, **kwargs):
        """It seems this is called when the widget is becoming visible"""
        self.video_module.start()

    def _on_unmap(self, *args, **kwargs):
        """Hopefully called when this widget is hidden,
        e.g. when the tab of a notebook has changed"""
        self.video_module.stop()

    def streaming(self, enabled):
        if enabled:
            self.stream_thread.start()
        else:
            self.stream_thread.stop()


class Pipeline(object):

    def __init__(self):
        self.pipe = Gst.Pipeline.new()
        self.bus = None

        self._make_pipeline()

    def set_message_handler(self, func):
        if self.bus is None:
            self._set_bus()

        self.bus.connect('message', func)

    def set_sync_message_handler(self, func):
        if self.bus is None:
            self._set_bus()

        self.bus.connect('sync-message::element', func)

    def start(self):
        self.pipe.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipe.set_state(Gst.State.PAUSED)
        self.pipe.set_state(Gst.State.NULL)

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

    def _set_bus(self):
        self.bus = self.pipe.get_bus()
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus.connect('message::eos', self._on_eos)
        self.bus.connect('message::tag', self._on_tag)
        self.bus.connect('message::error', self._on_error)

    def _make_pipeline(self):
        raise NotImplementedError()


class VideoModule(Pipeline):

    def __init__(self):
        self.video_device = '/dev/video0'
        self.listen_address = '0.0.0.0'
        self.listen_port = 1337

        super(VideoModule, self).__init__()

    def _make_pipeline(self):
        factory = self.pipe.get_factory()

        # self.video_source = factory.make('videotestsrc', 'test-source')
        self.video_source = Gst.ElementFactory.make('v4l2src', 'v4l2-source')
        self.video_source.set_property("device", self.video_device)

        self.video_conv1 = factory.make('videoconvert', "gtk-conv")
        self.video_conv2 = factory.make('videoconvert', "tcp-conv")

        self.video_scale = factory.make('videoscale', None)

        caps = Gst.Caps.from_string("video/x-raw,width=320,height=240")
        self.camera_filter = factory.make("capsfilter", "cam-gtk-filter")
        self.camera_filter.set_property("caps", caps)

        self.video_enc = factory.make("theoraenc", None)

        self.video_mux = factory.make('oggmux', None)

        self.gtk_sink = factory.make('gtksink', None)

        self.tcp_sink = factory.make('tcpserversink', None)
        self.tcp_sink.set_property('host', self.listen_address)
        self.tcp_sink.set_property('port', self.listen_port)

        self.tee = factory.make('tee', None)

        self.queue_1 = factory.make('queue', "gtk-sink")

        self.queue_2 = factory.make('queue', "tcp-sink")

        for ele in (self.video_source,
                    self.camera_filter,
                    self.tee,
                    self.queue_1,
                    self.video_conv1,
                    self.gtk_sink,
                    self.queue_2,
                    self.video_conv2,
                    self.video_enc,
                    self.video_mux,
                    self.tcp_sink):
            self.pipe.add(ele)

        self.video_source.link(self.camera_filter)
        self.camera_filter.link(self.tee)

        self.tee.link(self.queue_1)
        self.queue_1.link(self.video_conv1)
        self.video_conv1.link(self.gtk_sink)

        self.tee.link(self.queue_2)
        self.queue_2.link(self.video_conv2)
        self.video_conv2.link(self.video_enc)
        self.video_enc.link(self.video_mux)
        self.video_mux.link(self.tcp_sink)

    def get_gtksink(self):
        return self.gtk_sink.get_property("widget")
