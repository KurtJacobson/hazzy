#!/usr/bin/env python
import os
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gst

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
if HAZZYDIR not in sys.path:
    sys.path.insert(1, HAZZYDIR)


UIDIR = os.path.join(PYDIR, 'ui')
STYLEDIR = os.path.join(HAZZYDIR, 'themes')

from utilities.constants import Paths
from utilities import logger


# Setup logging
log = logger.get("HAZZY.VIDEO")

Gst.init(None)
Gst.init_check(None)


class GstWidget(Gtk.Box):
    def __init__(self, *args, **kwargs):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.connect('unmap', self._on_unmap)
        self.connect('map', self._on_map)

        self.config_stack = False
        self.playing = False

        self.set_size_request(320, 280)
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

        self.video_device_entry = Gtk.Entry()
        self.video_device_entry.set_text("/dev/video0")

        self.config_box.pack_start(self.video_device_entry, False, True, 0)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)

        self.pipeline = None

        self.camera_filter = None

        self.video_source = None
        self.video_enc = None
        self.video_parse = None
        self.video_rtp_pay = None
        self.video_converter = None

        self.gtk_sink = None
        self.udp_sink = None

        self.tee = None

        self.queue_1 = None
        self.queue_2 = None

        self.gtksink_widget = None

    def run(self):

        self.pipeline = Gst.Pipeline()

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self._on_eos)
        self.bus.connect('message::tag', self._on_tag)
        self.bus.connect('message::error', self._on_error)

        self.video_source = Gst.ElementFactory.make('v4l2src', 'v4l2-source')
        self.video_source.set_property("device", "/dev/video0")
        self.pipeline.add(self.video_source)

        caps = Gst.Caps.from_string("video/x-raw, width=320,height=240")
        self.camera_filter = Gst.ElementFactory.make("capsfilter", "filter1")
        self.camera_filter.set_property("caps", caps)
        self.pipeline.add(self.camera_filter)

        self.video_enc = Gst.ElementFactory.make("x264enc", None)
        self.pipeline.add(self.video_enc)

        self.video_parse = Gst.ElementFactory.make("h264parse", None)
        self.pipeline.add(self.video_parse)

        self.video_mux = Gst.ElementFactory.make('mpegtsmux', None)
        self.pipeline.add(self.video_mux)

        self.video_rtp_pay = Gst.ElementFactory.make("rtpmp2tpay", None)
        self.pipeline.add(self.video_rtp_pay)

        self.video_converter = Gst.ElementFactory.make('videoconvert', None)
        self.pipeline.add(self.video_converter)

        self.gtk_sink = Gst.ElementFactory.make('gtksink', None)
        self.pipeline.add(self.gtk_sink)

        self.udp_sink = Gst.ElementFactory.make('udpsink', None)
        self.udp_sink.set_property('host', '127.0.0.1')
        self.udp_sink.set_property('port', 5000)
        self.pipeline.add(self.udp_sink)

        self.tee = Gst.ElementFactory.make('tee', None)
        self.pipeline.add(self.tee)

        self.queue_1 = Gst.ElementFactory.make('queue', "GtkSink")
        self.pipeline.add(self.queue_1)

        self.queue_2 = Gst.ElementFactory.make('queue', "RtpSink")
        self.pipeline.add(self.queue_2)

        self.video_source.link(self.camera_filter)
        self.camera_filter.link(self.video_converter)
        self.video_converter.link(self.tee)

        self.tee.link(self.queue_1)
        self.queue_1.link(self.gtk_sink)

        """
        self.tee.link(self.queue_2)
        self.queue_2.link(self.video_enc)
        self.video_enc.link(self.video_mux)
        self.video_mux.link(self.udp_sink)
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
        print('on_eos')

    def _on_tag(self, bus, msg):
        taglist = msg.parse_tag()
        print('on_tag:')
        for key in taglist.keys():
            print('\t{0} = {1}'.format(key, taglist[key]))

    def _on_error(self, bus, msg):
        error = msg.parse_error()
        print('on_error: {0}'.format(error[1]))

