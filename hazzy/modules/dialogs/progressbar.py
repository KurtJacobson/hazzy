#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
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
import gobject


pydir = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(pydir, "ui")
IMGDIR = os.path.join(pydir, "images")


class ProgressBar:

    def __init__(self):

        # Glade setup
        gladefile = os.path.join(UIDIR, 'progressbar.glade')

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)

        self.window = self.builder.get_object("window")
        self.window.connect('destroy', self.destroy)
        self.window.set_keep_above(True)

        self.progressbar = self.builder.get_object("progressbar")

    def show(self):
        self.window.show()

    def hide(self):
        self.window.hide()

    def update(self, percentage):
        fraction = float(percentage) / 100
        self.progressbar.set_fraction(fraction)

    def destroy(self):
        gtk.main_quit()

# ==========================================================
# For standalone testing
# ==========================================================

def update(progressbar):
    value = progressbar.progressbar.get_fraction() + .01
    if value > 1:
        value = 0
    progressbar.progressbar.set_fraction(value)
    return True


def main():
    gtk.main()

if __name__ == "__main__":
    progressbar = ProgressBar()
    progressbar.show()
    gobject.timeout_add(50, update, progressbar)
    main()
