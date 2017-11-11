#!/usr/bin/env python

#   Copyright (c) 2017 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of Hazzy.
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

# Description:
#   TBA

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gio', '2.0')

from gi.repository import Gtk
from gi.repository import Gio

import mimetypes

import userdirectories

ICONSIZE = 24

class Icons():

    def __init__(self, theme):

        self.theme = theme
        self.userdirs = userdirectories.UserDirectories()

        # get default directory  icon
        if self.theme.has_icon('folder'):
            self.default_icon = self.theme.load_icon('folder', ICONSIZE, 0)
        else:
            self.default_icon = self.theme.load_icon(Gtk.STOCK_DIRECTORY, ICONSIZE, 0)

        self._user_directories = {}
        self._prepare_icons()


    def _prepare_icons(self):

        directories = []
        icon_names = {
                        userdirectories.DESKTOP: 'desktop',
                        userdirectories.DOWNLOADS: 'folder-downloads',
                        userdirectories.TEMPLATES: 'folder-templates',
                        userdirectories.PUBLIC: 'folder-publicshare',
                        userdirectories.DOCUMENTS: 'folder-documents',
                        userdirectories.MUSIC: 'folder-music',
                        userdirectories.PICTURES: 'folder-pictures',
                        userdirectories.VIDEOS: 'folder-videos'
                      }

        # get paths
        for directory in icon_names.keys():
            full_path = self.userdirs.get_XDG_directory(directory)
            icon_name = icon_names[directory]

            # check if icon exists
            if self.theme.has_icon(icon_name):
                icon = self.theme.load_icon(icon_name, ICONSIZE, 0)
            else:
                icon = self.default_icon

            self._user_directories[full_path] = icon

        # add user home directory
        home = self.userdirs.get_home_directory()
        if self.theme.has_icon('user-home'):  # 'folder-home'
            icon = self.theme.load_icon('user-home', ICONSIZE, 0)
        else:
            icon = self.default_icon
        self._user_directories[home] = icon


    def get_for_directory(self, path):
        return self._user_directories.get(path, self.default_icon)


    def get_for_file(self, fname):
        mime = Gio.content_type_guess(fname)
        if mime:
            icon_name = Gio.content_type_get_icon(str(mime))
            icon = self.theme.choose_icon(icon_name.get_names(), ICONSIZE, 0)
            if icon:
                return Gtk.IconInfo.load_icon(icon)
            else:
                name = Gtk.STOCK_FILE
        else:
            name = Gtk.STOCK_FILE
        return self.theme.load_icon(name, ICONSIZE, 0)


    # TODO expand for other devices
    def get_for_device(self, name):
        if name == "USBdrive":
            if self.theme.has_icon('drive-removable-media'):
                return self.theme.load_icon('drive-removable-media', ICONSIZE, 0)
        if name == "media-eject":
            if self.theme.has_icon('media-eject'):
                return self.theme.load_icon('media-eject', ICONSIZE, 0)
