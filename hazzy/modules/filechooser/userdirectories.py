#!/usr/bin/env python

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

import os

# XDG user directories
DESKTOP = 'XDG_DESKTOP_DIR'
DOWNLOADS = 'XDG_DOWNLOAD_DIR'
TEMPLATES = 'XDG_TEMPLATES_DIR'
PUBLIC = 'XDG_PUBLICSHARE_DIR'
DOCUMENTS = 'XDG_DOCUMENTS_DIR'
MUSIC = 'XDG_MUSIC_DIR'
PICTURES = 'XDG_PICTURES_DIR'
VIDEOS = 'XDG_VIDEOS_DIR'


class UserDirectories:

    def __init__(self):

        self.default = {
            DESKTOP: '~/Desktop',
            DOWNLOADS: '~/Downloads',
            TEMPLATES: '~/Templates',
            PUBLIC: '~/Public',
            DOCUMENTS: '~/Documents',
            MUSIC: '~/Music',
            PICTURES: '~/Pictures',
            VIDEOS: '~/Videos'
        }

        self.XDG_directories = {}

        # Fill the dictionary
        self.get_XDG_directories()

    # Get full path to user home
    def get_home_directory(self):
        default = os.path.expanduser('~')
        return os.path.expanduser(os.environ.get('HOME', default))

    # Get full path to cache files for current user
    def get_cache_directory(self):
        return os.path.expanduser(os.environ.get('XDG_CACHE_HOME', '~/.cache'))

    # Get full path to configuration files for current user
    def get_config_directory(self):
        return os.path.expanduser(os.environ.get('XDG_CONFIG_HOME', '~/.config'))

    # Get full path to data files for current user
    def get_data_directory(self):
        return os.path.expanduser(os.environ.get('XDG_DATA_HOME', '~/.local/share'))

    # Get path from XDG name
    def get_XDG_directory(self, XDG_name):
        default = os.path.expanduser(self.default[XDG_name])
        return self.XDG_directories.get(XDG_name, default)

    # Get full paths to current users XDG directories
    def get_XDG_directories(self):
        user_home = self.get_home_directory()
        config_file = os.path.join(self.get_config_directory(), 'user-dirs.dirs')

        if os.path.isfile(config_file):
            # read configuration file
            with open(config_file, 'r') as data_file:
                lines = data_file.read().splitlines(False)

            for line in lines:

                # ignore comments
                if line.startswith('#'):
                    continue

                # extract XDG dir name and the path
                XDG_dir, path = line.split('=')
                path = path.replace('$HOME', user_home).strip('"')

                # add to dictionary
                self.XDG_directories[XDG_dir] = path

        return self.XDG_directories
