#!/usr/bin/env python

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gst

Gst.init(None)
Gst.init_check(None)


class GstWidget(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)

        self.set_size_request(200, 150)
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Only setup the widget after the window is shown.
        self.connect('realize', self._on_realize)

        # Parse a gstreamer pipeline and create it.
        self._bin = Gst.parse_bin_from_description('videotestsrc', True)

    def _on_realize(self, widget):
        pipeline = Gst.Pipeline()
        factory = pipeline.get_factory()
        gtksink = factory.make('gtksink')
        pipeline.add(self._bin)
        pipeline.add(gtksink)
        # Link the pipeline to the sink that will display the video.
        self._bin.link(gtksink)
        self.pack_start(gtksink.props.widget, True, True, 0)
        gtksink.props.widget.show()
        # Start the video
        pipeline.set_state(Gst.State.PLAYING)


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
