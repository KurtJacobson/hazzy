#!/usr/bin/env python

#   An attempt at a basic UI for LinuxCNC that can be used
#   on a touch screen without any lost of functionality.
#   The code is almost a complete rewrite, but was influenced
#   mainly by Gmoccapy and Touchy, with some code adapted from
#   the HAL vcp widgets.

#   Copyright (c) 2017 Kurt Jacobson
#       <kurtcjacobson@gmail.com>
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


class BookMarks:

    def __init__(self, path):

        self.bookmarks_file = path
        self.bookmarks = []

    def read(self):

        try:
            with open(self.bookmarks_file) as f:
                file_content = f.readlines()

                for bk in file_content:
                    if bk[0] != '\n':
                        bk_temp = bk.split()
                        bk_dir = bk_temp[0]
                        name = bk[len(bk_dir) + 1:].rstrip()
                        self.bookmarks.append([name.replace(" ", "_"), bk_dir[7:].replace("%20", " ")])
                    else:
                        print("No Bookmarks")

            print(self.bookmarks)

        except IOError as e:
            print(e)  # File not found
            print("Creating a new one")
            with open(self.bookmarks_file, 'w+') as f:
                f.write('')

    def get(self):

        return self.bookmarks

    def add(self, path):

        name = os.path.basename(os.path.normpath(path))

        line = "file//{0} {1}\n".format(path, name)

        with open(self.bookmarks_file, 'a') as f:
            f.write(line)

    def remove(self, path):

        name = os.path.basename(os.path.normpath(path))
        output = []

        with open(self.bookmarks_file, 'r+w') as f:
            bookmarks_read = f.readlines()

            for bookmark in bookmarks_read:
                if name != bookmark.split()[-1]:
                    output.append(bookmark)

            f.writelines(output)


