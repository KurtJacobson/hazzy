#!/usr/bin/python3

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import GObject, Gst, Gtk

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo


GObject.threads_init()
Gst.init(None)


class Video:
    def __init__(self):

        self.drawing_area = Gtk.DrawingArea()

        # Create GStreamer pipeline
        self.pipeline = Gst.Pipeline()

        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)

        # This is needed to make the video output in our DrawingArea:
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)

        # Create GStreamer elements
        self.src = Gst.ElementFactory.make('autovideosrc', None)
        self.sink = Gst.ElementFactory.make('autovideosink', None)

        # Add elements to the pipeline
        self.pipeline.add(self.src)
        self.pipeline.add(self.sink)

        self.src.link(self.sink)

    def run(self):
        # You need to get the XID after window.show_all().  You shouldn't get it
        # in the on_sync_message() handler because threading issues will cause
        # segfaults there.

        self.xid = self.drawing_area.get_property('window').get_xid()
        self.pipeline.set_state(Gst.State.PLAYING)

    def quit(self, window):
        self.pipeline.set_state(Gst.State.NULL)

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            msg.src.set_property('force-aspect-ratio', True)
            msg.src.set_window_handle(self.xid)

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())

    def get_drawing_area(self):
        return self.drawing_area


class VideoWidget(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)

        self.webcam = Video()
        drawing_area = self.webcam.get_drawing_area()

        self.pack_start(drawing_area, True, True, 0)



def main():
    window = Gtk.Window()

    video_widget = VideoWidget()
    window.add(video_widget)
    window.show_all()

    video_widget.webcam.run()

    Gtk.main()

if __name__ == "__main__":
    main()
