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
import logging

GTK_BOOKMARKS = os.path.expanduser("~/.gtk-bookmarks")  # FixMe use XDG env


class BookMarks:

    def __init__(self):

        self.logger = logging.getLogger('HAZZY - FILECHOOSER')

        self.bookmarks_file = GTK_BOOKMARKS
        self.bookmarks = []

        # Initial read so we can prevent adding duplicates on start-up
        self.get()

    def get(self):

        try:
            with open(self.bookmarks_file) as f:
                lines = f.readlines()

            self.bookmarks = []  # clear the list
            for line in lines:
                if line[0] != '\n':
                    bk_dir = line.split()[0]
                    path = bk_dir[7:].replace("%20", " ")
                    name = line[len(bk_dir) +1:].rstrip()
                    self.bookmarks.append([path, name])
                else:
                    self.logger.info("No Bookmarks")

        except IOError as e:
            self.logger.error(e)  # File not found
            self.logger.info("Creating a new one")
            with open(self.bookmarks_file, 'w+') as f:
                f.write('')

        return self.bookmarks

    def add(self, path):

        # don't add bookmark to something other than a directory
        if not os.path.isdir(path):
            self.logger.error("Bookmark is not valid")
            return False  # indicate failure to add

        # don't add any duplicates
        for existing_path, existing_name in self.bookmarks:
            if path == existing_path:
                self.logger.info("Bookmark already exists")
                return False  # indicate failure to add

        name = os.path.basename(os.path.normpath(path))

        # must encode spaces in path for GTK-bookmarks
        path = path.replace(" ", "%20")
        line = "file://{0} {1}\n".format(path, name)

        with open(self.bookmarks_file, 'a') as f:
            f.write(line)

    def remove(self, path):

        path = path.replace(" ", "%20")

        # read the bookmarks
        with open(self.bookmarks_file, 'r') as f:
            lines = f.readlines()

        # open as write to clear file content
        with open(self.bookmarks_file, 'w') as f:

            # put back all the lines except the one we want to remove
            for line in lines:
                # path does not have prefix "file://" so take slice of line
                if path != line.split()[0][7:]:
                    f.write(line)

    def clear(self):
        with open(self.bookmarks_file, 'w') as f:
            pass


