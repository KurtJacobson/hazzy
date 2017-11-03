#!/usr/bin/env python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from utilities import command

class ProgramControls(Gtk.Box):
    def __init__(self, widget_window):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.get_style_context().add_class('red')

        self.run_button = Gtk.Button.new_with_label('Run')
        self.run_button.get_style_context().add_class('blue')
        self.run_button.connect('clicked', self.on_run_button_clicked)
        self.pack_start(self.run_button, True, True, 4)

#        self.run_button = Gtk.Button.new_with_label('Run')
#        self.run_button.get_style_context().add_class('.blue')
#        self.connect('clicked', self.on_run_button_cliked)
#        self.pack_start(self.run_button, True, True, 4)

        self.stop_button = Gtk.Button.new_with_label('Stop')
        self.stop_button.get_style_context().add_class('red')
        self.stop_button.connect('clicked', self.on_stop_button_clicked)
        self.pack_start(self.stop_button, True, True, 4)

    def on_run_button_clicked(self, widegt):
        command.program_run()
        print 'RUN'

    def on_stop_button_clicked(self, widegt):
        print 'STOP'
