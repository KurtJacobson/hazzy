#!/usr/bin/env python

import os
import sys
import json
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk
from gi.repository import Gst

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)


PYDIR = os.path.abspath(os.path.dirname(__file__))

SETTINGS_FILE = os.path.join(PYDIR, 'settings.json')

from gui import widgets
from utilities import preferences as prefs
from utilities import logger

# Setup logging
log = logger.get(__name__)


Gst.init(None)
Gst.init_check(None)


class GstWidget(Gtk.Box):
    def __init__(self, *args, **kwargs):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.connect('unmap', self._on_unmap)
        self.connect('map', self._on_map)

        self.settings = self.load_settings()

        self.config_stack = False

        self.set_size_request(self.settings["video_width"],
                              self.settings["video_height"])

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(500)

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        button_start = Gtk.ToggleButton("Start")
        button_start.connect("toggled", self._on_button_start_toggled, "1")

        self.widget_box.pack_end(button_start, False, True, 0)

#        self.add_config_field("Device", "video_device")
#        self.add_config_field("Width", "video_width")
#        self.add_config_field("Height", "video_height")

        self.size_group = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)

        devices = ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video3"]
        default = "/dev/video0"
        combo = widgets.PrefComboBox('VedioWidget', 'Device', devices, default)
        combo.connect('value-changed', self.on_device_changed)
        self.add_config_field(combo)

        entry = widgets.PrefEntry('VedioWidget', 'Host', '127.0.0.1')
        entry.connect('value-changed', self.on_host_chaned)
        self.add_config_field(entry)

        entry = widgets.PrefEntry('VedioWidget', 'Port', '5000')
        entry.connect('value-changed', self.on_port_changed)
        self.add_config_field(entry)

        switch = widgets.PrefSwitch('VedioWidget', 'Stream', True)
        switch.connect('value-changed', self.on_stream_state_changed)
        self.add_config_field(switch)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)

        self.connect('destroy', self.save_settings)

        # Initialize empty GST related vars

        self.pipeline = None

        self.bus = None

        self.camera_gtk_filter = None
        self.camera_stream_filter = None

        self.video_source = None
        self.video_enc = None
        self.video_parse = None
        self.video_mux = None
        self.video_pay = None
        self.video_converter = None

        self.gtk_sink = None
        self.udp_sink = None
        self.tcp_sink = None

        self.tee = None

        self.queue_1 = None
        self.queue_2 = None

        self.gtksink_widget = None

    def on_device_changed(self, widget, device):
        print 'Device changed: ', device

    def on_host_chaned(self, widget, host):
        print 'Host changed: ', host

    def on_port_changed(self, widget, port):
        print 'Port changed: ', port

    def on_stream_state_changed(self, widget, streaming):
        print 'Streaming changed: ', streaming

    def add_config_field(self, feild):
        box = widgets.PrefFeild(feild, self.size_group)
        self.config_box.pack_start(box, False, True, 5)

    def save_settings(self, widget=None):
        with open(SETTINGS_FILE, 'w') as fh:
            json.dump(self.settings, fh, indent=4, sort_keys=True)

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return dict()
        with open(SETTINGS_FILE, 'r') as fh:
            try:
                return json.load(fh)
            except ValueError:
                return dict()

    def run(self):

        self.pipeline = Gst.Pipeline()

        self.bus = self.pipeline.get_bus()

        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self._on_eos)
        self.bus.connect('message::tag', self._on_tag)
        self.bus.connect('message::error', self._on_error)

        self.video_source = Gst.ElementFactory.make('v4l2src', 'v4l2-source')
        self.video_source.set_property("device", prefs.get('VedioWidget', 'Device', "/dev/video0", str))
        self.pipeline.add(self.video_source)

        caps = Gst.Caps.from_string("video/x-raw,width=320,height=240")
        self.camera_gtk_filter = Gst.ElementFactory.make("capsfilter", "gtk-filter")
        self.camera_gtk_filter.set_property("caps", caps)
        self.pipeline.add(self.camera_gtk_filter)

        caps = Gst.Caps.from_string("video/x-raw,width=320,height=240")
        self.camera_stream_filter = Gst.ElementFactory.make("capsfilter", "stream-filter")
        self.camera_stream_filter.set_property("caps", caps)
        self.pipeline.add(self.camera_stream_filter)

        self.video_converter = Gst.ElementFactory.make('videoconvert', None)
        self.pipeline.add(self.video_converter)

        self.video_enc = Gst.ElementFactory.make("vp8enc", None)
        self.pipeline.add(self.video_enc)

        """
        self.video_parse = Gst.ElementFactory.make("h264parse", None)
        self.pipeline.add(self.video_parse)
        
        self.video_mux = Gst.ElementFactory.make('oggmux', None)
        self.pipeline.add(self.video_mux)
        """

        self.video_pay = Gst.ElementFactory.make("gdppay", None)
        self.pipeline.add(self.video_pay)

        self.video_converter = Gst.ElementFactory.make('videoconvert', None)
        self.pipeline.add(self.video_converter)

        self.gtk_sink = Gst.ElementFactory.make('gtksink', None)
        self.pipeline.add(self.gtk_sink)

        self.tcp_sink = Gst.ElementFactory.make('tcpserversink', None)
        self.tcp_sink.set_property('host', '127.0.0.1')
        self.tcp_sink.set_property('port', 5000)
        #self.pipeline.add(self.tcp_sink)

        self.tee = Gst.ElementFactory.make('tee', None)
        self.pipeline.add(self.tee)

        self.queue_1 = Gst.ElementFactory.make('queue', "GtkSink")
        self.pipeline.add(self.queue_1)

        self.queue_2 = Gst.ElementFactory.make('queue', "StreamSink")
        self.pipeline.add(self.queue_2)

        self.video_source.link(self.tee)

        self.tee.link(self.queue_1)
        self.queue_1.link(self.video_converter)
        self.video_converter.link(self.camera_gtk_filter)
        self.camera_gtk_filter.link(self.gtk_sink)

        """
        self.tee.link(self.queue_2)
        self.queue_2.link(self.video_converter)
        self.video_converter.link(self.camera_stream_filter)
        self.camera_stream_filter.link(self.video_enc)
        self.video_enc.link(self.video_pay)
        self.video_pay.link(self.tcp_sink)
        """

        self.gtksink_widget = self.gtk_sink.get_property("widget")
        self.gtksink_widget.show_all()

        self.widget_box.pack_start(self.gtksink_widget, True, True, 0)

    def stop(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        # Actually, we stop the thing for real
        self.pipeline.set_state(Gst.State.NULL)

    def pause(self):
        self.pipeline.set_state(Gst.State.NULL)

    def resume(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_settings_button_pressed(self, button):
        if self.config_stack:
            self.config_stack = False
            self.stack.set_visible_child_name("widget")
        else:
            self.config_stack = True
            self.stack.set_visible_child_name("config")

    def _on_button_start_toggled(self, button, name):
        if button.get_active():
            self.resume()
        else:
            self.pause()

    def _on_map(self, *args, **kwargs):
        """It seems this is called when the widget is becoming visible"""
        self.run()

    def _on_unmap(self, *args, **kwargs):
        """Hopefully called when this widget is hidden,
        e.g. when the tab of a notebook has changed"""
        self.stop()

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

