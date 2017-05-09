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

class Dialogs(object):

    def __init__(self, message, dialog_type=0):

        # Glade setup
        if dialog_type == 0 or dialog_type == 1:
            gladefile = os.path.join(UIDIR, 'dialog.glade')
        else:
            gladefile = os.path.join(UIDIR, 'error_dialog.glade')

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")
        self.message = message
        self.result = False

        self.builder.get_object("mesage_label").set_text(message)

        if dialog_type == 0:
            # We want a YES/NO dialog
            self.builder.get_object("button1").set_label("YES")
            self.builder.get_object("button2").set_label("NO")
        elif dialog_type == 1:
            # We want an OK/CANCEL dialog
            self.builder.get_object("button1").set_label("OK")
            self.builder.get_object("button2").set_label("CANCEL")

    def on_button1_clicked(self, widget, data = None):
        self.result = True
        gtk.main_quit()

    def on_button2_clicked(self, widget, data = None):
        self.result = False
        gtk.main_quit()

    def show(self):
        self.window.show()
        #self.builder.get_object("button1").grab_focus()
        gtk.main()
        self.window.destroy()
        return self.result
