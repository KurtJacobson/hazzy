#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#     <kurtjacobson@bellsouth.net>
#
#   This file is part of Hazzy.
#   This is a copy of a class from gmoccapy and originaly came from gscreen:
#   Original Author: Chris Morley
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.



# Class for holding the glade widgets rather then searching for them each time
class Widgets:

    def __init__(self, builder):
        self._builder = builder

    def __getattr__(self, attr):
        widget = self._builder.get_object(attr)
        if widget is None:
            raise AttributeError, "No widget %widget" % attr
        return widget

    def __getitem__(self, attr):
        widget = self._builder.get_object(attr)
        if widget is None:
            raise IndexError, "No widget %widget" % attr
        return widget

