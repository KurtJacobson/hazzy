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


class BookMarks:

    def __init__(self, path):

        self.bookmarks_file = path
        self.bookmarks = []


    def read(self):

        try:
            with open(self.bookmarks_file) as f:
                file_content = f.readlines()

                for line in file_content:
                    if line[0] != '\n':
                        bk_dir = line.split()[0]
                        path = bk_dir[7:].replace("%20", " ")
                        self.bookmarks.append(path)
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

        # don't add duplicates
        if path in self.bookmarks:
            print('Bookmark already exists')
            return False  # indicate failure to add

        # add to our list
        name = os.path.basename(os.path.normpath(path))
        self.bookmarks.append([path , name])

        # must encode spaces in path for GTK-bookmarks
        path = path.replace(" ", "%20")
        line = "file://{0} {1}\n".format(path, name)

        with open(self.bookmarks_file, 'a') as f:
            f.write(line)

    def remove(self, path):

        # can't remove if not here!
        if not path in self.bookmarks:
            return False

        # self.bookmarks.remove(path)

        name = os.path.basename(os.path.normpath(path))
        path = path.replace(" ", "%20")

        output = []

        with open(self.bookmarks_file, 'r+w') as f:
            bookmarks_read = f.readlines()

            for bookmark in bookmarks_read:
                if path != bookmark.split()[0]:
                    output.append(bookmark)

            f.writelines(output)


