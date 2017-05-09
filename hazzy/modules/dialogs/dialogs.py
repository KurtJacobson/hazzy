#!/usr/bin/env python


#   This class handles all the popup dialoges in Hazzy.


#   Copyright (c) 2017 Kurt Jacobson
#     <kurtjacobson@bellsouth.net>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.


import gtk
import os

pydir = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(pydir, "ui")


class Dialogs(gtk.Dialog):
    """ A object that creates various kinds of dialogs """

    def __init__(self, dialog_type=0):
        """ 0 = yes/no,
            1 = ok/cancel,
            2 = error """

        super(Dialogs, self).__init__()  # Initialize the gtk.Dialog super class

        # Glade setup
        if dialog_type == 0 or dialog_type == 1:
            gladefile = os.path.join(UIDIR, 'dialog.glade')
        else:
            gladefile = os.path.join(UIDIR, 'error_dialog.glade')

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)

        self.dialog_window = self.builder.get_object("window")

        self.message_label = self.builder.get_object("mesage_label")

        self.running = False
        self.result = False

        if dialog_type == 0:
            # We want a YES/NO dialog
            self.builder.get_object("button1").set_label("YES")
            self.builder.get_object("button2").set_label("NO")
        elif dialog_type == 1:
            # We want an OK/CANCEL dialog
            self.builder.get_object("button1").set_label("OK")
            self.builder.get_object("button2").set_label("CANCEL")

    def on_button1_clicked(self, widget, data=None):
        """ YES/OK Buttons"""

        self.result = True

        self.dialog_window.hide()
        gtk.main_quit()

    def on_button2_clicked(self, widget, data=None):
        """ NO/CANCEL Buttons"""

        self.dialog_window.hide()
        gtk.main_quit()

    def run(self, message):
        """ Show the Dialog only if not already running """

        if not self.running:
            self.running = True
            self.message_label.set_text(message)
            self.dialog_window.show()
            gtk.main()
            self.running = False

        return self.result
