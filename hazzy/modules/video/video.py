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
        self.connect('unmap', self.on_unmap)
        self.connect('map', self.on_map)

        self.config_stack = False

        self.set_size_request(320, 280)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(500)

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        button_start = Gtk.ToggleButton("Start")
        button_start.connect("toggled", self.on_button_start_toggled, "1")

        self.widget_box.pack_end(button_start, False, True, 0)

        self.video_device_entry = Gtk.Entry()
        self.video_device_entry.set_text("/dev/video0")

        self.config_box.pack_start(self.video_device_entry, False, True, 0)

        self.stack.add_titled(self.widget_box, "widget", "Widget View")
        self.stack.add_titled(self.config_box, "config", "Widget Config")

        self.pack_start(self.stack, True, True, 0)

        self.player  = None
        self.gtksink_widget = None

    def on_settings_button_pressed(self, button):
        if self.config_stack:
            self.config_stack = False
            self.stack.set_visible_child_name("widget")
        else:
            self.config_stack = True
            self.stack.set_visible_child_name("config")

    def on_button_start_toggled(self, button, name):
        if button.get_active():
            self.resume()
        else:
            self.pause()

    def on_message(self, bus, message):
        # log.debug("Message: %s", message)
        if message:
            struct = message.get_structure()
            if struct:
                struct_name = struct.get_name()
                # log.debug('Message name: %s', struct_name)

                if struct_name == 'GstMessageError':
                    err, debug = message.parse_error()
                    log.error('GstError: {}, {}'.format(err, debug))
                elif struct_name == 'GstMessageWarning':
                    err, debug = message.parse_warning()
                    log.warning('GstWarning: {}, {}'.format(err, debug))

    def run(self):

        pipeline = 'v4l2src device=/dev/video0 !' \
                   ' tee name=t !' \
                   ' queue ! video/x-raw ! videoconvert ! gtksink name=imagesink t. !' \
                   ' queue ! video/x-raw ! jpegenc ! rtpjpegpay !' \
                   ' tcpserversink host=0.0.0.0 port=5000'

        self.player = Gst.parse_launch(pipeline)

        self.imagesink = self.player.get_by_name('imagesink')
        self.gtksink_widget = self.imagesink.get_property("widget")

        self.widget_box.pack_start(self.gtksink_widget, True, True, 0)
        self.gtksink_widget.show()

        bus = self.player.get_bus()
        bus.connect('message', self.on_message)
        bus.add_signal_watch()

    def stop(self):
        self.player.set_state(Gst.State.PAUSED)
        # Actually, we stop the thing for real
        self.player.set_state(Gst.State.NULL)

    def pause(self):
        self.player.set_state(Gst.State.NULL)

    def resume(self):
        self.player.set_state(Gst.State.PLAYING)

    def on_map(self, *args, **kwargs):
        '''It seems this is called when the widget is becoming visible'''
        self.run()

    def on_unmap(self, *args, **kwargs):
        '''Hopefully called when this widget is hidden,
        e.g. when the tab of a notebook has changed'''
        self.stop()


def main():
    window = Gtk.Window()
    window.connect('destroy', Gtk.main_quit)

    # Create a gstreamer pipeline with no sink.
    # A sink will be created inside the GstWidget.
    widget = GstWidget()

    window.add(widget)
    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
