#!/usr/bin/env python

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from utilities.version import VERSION, VERSION_URL

LICENSE = Gtk.License.GPL_3_0
AUTHORS = ['Kurt Jacobson', 'TurBoss']
COPYRIGHT = "Copyright \xc2\xa9 2017 Kurt Jacobson"

LCNC_VERSION = "v" + (os.environ.get('LINUXCNCVERSION'))
GTK_VERSION = "v{}.{}.{}".format(Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION)

class About(Gtk.AboutDialog):

    def __init__(self, app_window):
        Gtk.AboutDialog.__init__(self, use_header_bar=False)

        self.set_transient_for(app_window)
        self.set_modal(True)

        self.header_bar = Gtk.HeaderBar(title='About')
        self.set_titlebar(self.header_bar)

        self.set_program_name("hazzy")

        self.set_version(VERSION)

        self.set_comments('LinuxCNC: {} \n GTK: {}'.format(LCNC_VERSION, GTK_VERSION))

        self.set_website(VERSION_URL)
        self.set_website_label(VERSION_URL)

        self.set_copyright(COPYRIGHT)
        self.set_license_type(LICENSE)

        self.set_authors(AUTHORS)
        self.set_title("Hazzy")

        self.connect("response", self.on_response)
        self.show()

    def on_response(self, dialog, response_id):
        dialog.destroy()
