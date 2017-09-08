#!/usr/bin/env python

import logging
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gst

log = logging.getLogger(__name__)

Gst.init(None)
Gst.init_check(None)


class GstWidget(Gtk.Box):
    def __init__(self, *args, **kwargs):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.connect('unmap', self.on_unmap)
        # self.connect('map', self.on_map)

        self.set_size_request(320, 280)
        self.set_hexpand(True)
        self.set_vexpand(True)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        button_start = Gtk.ToggleButton("Start")

        button_start.connect("toggled", self.on_button_start_toggled, "1")

        button_box.pack_start(button_start, True, True, 0)

        self.pack_end(button_box, False, True, 0)
        self.gtksink_widget = None

    def on_button_start_toggled(self, button, name):
        if button.get_active():
            self.run()
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
                    log.error('GstError: %s, %s', err, debug)
                elif struct_name == 'GstMessageWarning':
                    err, debug = message.parse_warning()
                    log.warning('GstWarning: %s, %s', err, debug)

    def run(self):

        if self.gtksink_widget:
            self.gtksink_widget.destroy()
            self.stop()

        p = "v4l2src device=/dev/video0 \n"
        p += " ! tee name=t \n"
        p += "       t. ! videoconvert \n"
        p += ("                 ! gtksink "
              "name=imagesink "
              )

        pipeline = p
        log.info("Launching pipeline %s", pipeline)
        pipeline = Gst.parse_launch(pipeline)

        self.imagesink = pipeline.get_by_name('imagesink')
        self.gtksink_widget = self.imagesink.get_property("widget")

        self.pack_start(self.gtksink_widget, True, True, 0)
        self.gtksink_widget.show()

        self.pipeline = pipeline

        bus = pipeline.get_bus()
        bus.connect('message', self.on_message)
        bus.add_signal_watch()

        pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        # Actually, we stop the thing for real
        self.pipeline.set_state(Gst.State.NULL)


    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

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
