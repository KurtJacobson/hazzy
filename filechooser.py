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

import gobject
import gtk
import sys
import gio
import os
import shutil
import mimetypes
import json
from datetime import datetime

DATADIR = os.path.abspath(os.path.dirname(__file__))
GLADEDIR = os.path.join(DATADIR, 'images')
XDG_DATA_HOME = os.path.expanduser(os.environ.get('XDG_DATA_HOME', '~/.local/share'))
HOMETRASH = os.path.join(XDG_DATA_HOME, 'Trash')


class Filechooser(gobject.GObject):
    __gtype_name__ = 'Filechooser'
    __gsignals__ = {
        'file-activated': (gobject.SIGNAL_RUN_FIRST, None, (str,)),
        'selection-changed': (gobject.SIGNAL_RUN_FIRST, None, (str,)),
        'filename-editing-started': (gobject.SIGNAL_RUN_FIRST, None, (object,)),
        'button-release-event': (gobject.SIGNAL_RUN_FIRST, None, ()),
        'error': (gobject.SIGNAL_RUN_FIRST, None, (str, str))
    }

    def __init__(self):

        gobject.GObject.__init__(self)

        # Glade setup
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(GLADEDIR, "filechooser.glade"))
        self.builder.connect_signals(self)

        # Retrieve frequently used objects
        self.nav_box = self.builder.get_object('hbox1')
        self.eject_column = self.builder.get_object('eject_col')
        file_adj = self.builder.get_object('scrolledwindow1')
        self.file_vadj = file_adj.get_vadjustment()
        self.file_hadj = file_adj.get_hadjustment()

        # Retrieve data models
        self.file_liststore = self.builder.get_object("file_liststore")
        self.bookmark_liststore = self.builder.get_object("bookmark_liststore")

        # Retrieve treeviews
        self.file_treeview = self.builder.get_object("file_treeview")
        self.bookmark_treeview = self.builder.get_object("bookmark_treeview")

        self.bookmark_treeview.set_row_separator_func(self.bookmark_separator)

        # Enable DnD TODO DnD is not implemented yet
        self.file_treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, \
                                                    [('text/plain', 0, 0)], gtk.gdk.ACTION_MOVE | gtk.gdk.ACTION_COPY)
        self.file_treeview.enable_model_drag_dest([('text/plain', 0, 0)], \
                                                  gtk.gdk.ACTION_COPY)

        # Connect callbacks to VolumeMonitor
        self.mounts = gio.VolumeMonitor()
        self.mounts.connect('mount-added', self.on_mount_added)
        self.mounts.connect('mount-removed', self.on_mount_removed)

        # Initialize variables
        self.data_file = '/home/kurt/Desktop/test.json'
        self.cur_dir = os.path.expanduser("~/Desktop")
        self.icon_theme = gtk.icon_theme_get_default()
        self.old_dir = " "
        self._filters = {}
        self._filter = ''
        self._files = []
        self._show_hidden = False
        self._hidden_exts = ['.desktop']
        self._copy = True
        self._selection = None
        self.nav_btn_list = []
        self.nav_btn_path_dict = {}

        # Default bookmarks
        home = os.environ['HOME']
        self.places = [self.cur_dir, home]
        self.folders = [os.path.join(home, 'linuxcnc/nc_files')]

        # Initialize
        self._init_bookmarks()
        self._init_nav_buttons()

    # Have to do this once realized so sizes will have been allocated
    def on_vbox1_realize(self, widget):
        self._update_bookmarks()
        self._fill_file_liststore(self.cur_dir)

    def _init_bookmarks(self):
        try:
            with open(self.data_file) as data:
                self.places, self.folders = json.load(data)
        except Exception as e:
            print(e)

    def _init_nav_buttons(self):
        box = self.nav_box
        btn_list = self.nav_btn_list
        btn_dict = self.nav_btn_path_dict
        for i in range(10):
            btn = gtk.Button()
            btn.connect('clicked', self.on_nav_btn_clicked)
            btn.set_can_focus(False)
            btn_list.append(btn)
            box.pack_start(btn, False, False, 0)
            btn_dict[btn] = ''

    def _update_nav_buttons(self, path=None):
        if path is None:
            path = self.cur_dir
        places = path.split('/')[1:]
        path = '/'
        for btn in self.nav_btn_list:
            btn.hide()
        w_needed = 0
        for i, place in enumerate(places):
            btn = self.nav_btn_list[i]
            btn.set_label(place)
            path = os.path.join(path, place)
            self.nav_btn_path_dict[btn] = path
            btn.show()
            w_needed += btn.size_request()[0]
        w_allowed = self.nav_box.get_allocation()[2]
        if w_needed > w_allowed:
            self.builder.get_object('goto_root').hide()
            self.builder.get_object('arrow_left').show()
        else:
            self.builder.get_object('goto_root').show()
            self.builder.get_object('arrow_left').hide()
        count = 0
        while w_needed > w_allowed:
            btn = self.nav_btn_list[count]
            w_needed -= btn.size_request()[0]
            btn.hide()
            count += 1

    def on_nav_btn_clicked(self, widget, data=None):
        path = self.nav_btn_path_dict[widget]
        if path != self.cur_dir:
            self._fill_file_liststore(path)

    def on_goto_root_clicked(self, widget, data=None):
        self._fill_file_liststore('/')

    # HACK for now
    def on_arrow_left_clicked(self, widget, data=None):
        self.up_one_dir()

    def on_arrow_right_clicked(self, widget, data=None):
        pass

    def _fill_file_liststore(self, path=None):
        model = self.file_liststore
        model.clear()
        self.current_selection = None

        if path:
            self.cur_dir = os.path.realpath(path)

        files = []
        folders = []
        if self._filter in self._filters:
            exts = self._filters[self._filter]
        else:
            exts = ''
        dirs = os.listdir(self.cur_dir)
        for obj in dirs:
            if obj[0] == '.' and not self._show_hidden:
                continue
            path = os.path.join(self.cur_dir, obj)
            if os.path.islink(path):
                path = os.readlink(path)
            if os.path.isdir(path):
                folders.append(obj)
            elif os.path.isfile(path):
                ext = os.path.splitext(obj)[1]
                if '*' in exts and not ext in self._hidden_exts:
                    files.append(obj)
                elif '*{0}'.format(ext) in exts:
                    files.append(obj)

        folders.sort(key=str.lower, reverse=False)
        for folder in folders:
            icon = self._get_place_icon(folder)
            model.append([0, icon, folder, None, None])

        files.sort(key=str.lower, reverse=False)
        for fname in files:
            fpath = os.path.join(self.cur_dir, fname)
            icon = self._get_file_icon(fname)
            size, date = self._get_file_data(fpath)
            model.append([0, icon, fname, size, date])

        # Reset scrollbars
        self.file_vadj.set_value(0)
        self.file_hadj.set_value(0)

        self._update_nav_buttons()

    def _get_file_data(self, fpath):
        size = os.path.getsize(fpath)
        if size >= 1E9:
            size_str = "{:.1f} GB".format(size / 1E9)
        elif size >= 1E6:
            size_str = "{:.1f} MB".format(size / 1E6)
        elif size >= 1E3:
            size_str = "{:.1f} KB".format(size / 1E3)
        else:
            size_str = "{} bytes".format(size)
        tstamp = os.path.getmtime(fpath)
        date_str = datetime.fromtimestamp(tstamp).strftime("%m/%d/%y %X")
        return size_str, date_str

    def _get_file_icon(self, fname):
        theme = self.icon_theme
        mime = gio.content_type_guess(fname)
        if mime:
            icon_name = gio.content_type_get_icon(mime)
            icon = theme.choose_icon(icon_name.get_names(), 16, 0)
            if icon:
                return gtk.IconInfo.load_icon(icon)
            else:
                name = gtk.STOCK_FILE
        else:
            name = gtk.STOCK_FILE
        return theme.load_icon(name, 16, 0)

    def _get_place_icon(self, place):
        theme = self.icon_theme
        if place == os.environ['USER']:
            icon_name = 'user-home'
        elif place == 'Desktop':
            icon_name = 'user-desktop'
        elif place == 'Documents':
            icon_name = 'folder-documents'
        elif place == 'Downloads':
            icon_name = 'folder-download'
        elif place == 'Templates':
            icon_name = 'folder-templates'
        elif place == 'USBdrive':
            icon_name = 'drive-removable-media'
        else:
            icon_name = 'folder'
        if not theme.has_icon(icon_name):
            icon_name = gtk.STOCK_DIRECTORY
        return theme.load_icon(icon_name, 16, 0)

    def on_select_toggled(self, widget, path):
        model = self.file_liststore
        model[path][0] = not model[path][0]

    def on_filechooser_treeview_cursor_changed(self, widget):
        path = widget.get_cursor()[0]
        # Prevent emiting selection changed on double click
        if path == self.current_selection:
            return
        self.current_selection = path
        fname = self.file_liststore[path][2]
        fpath = os.path.join(self.cur_dir, fname)
        self.emit('selection-changed', fpath)

    def on_filechooser_treeview_row_activated(self, widget, path, colobj):
        fname = self.file_liststore[path][2]
        fpath = os.path.join(self.cur_dir, fname)
        if os.path.isfile(fpath):
            self.emit('file-activated', fpath)
        elif os.path.isdir(fpath):
            self._fill_file_liststore(fpath)

    def on_file_name_editing_started(self, renderer, entry, row):
        self.emit('filename-editing-started', entry)

    def on_file_name_edited(self, widget, row, new_name):
        model = self.file_liststore
        old_name = model[row][2]
        old_path = os.path.join(self.cur_dir, old_name)
        new_path = os.path.join(self.cur_dir, new_name)
        if old_name == new_name:
            return
        if not os.path.exists(new_path):
            self.info("Renaming: {} to {}".format(old_path, new_path))
            os.rename(old_path, new_path)
            model[row][2] = new_name
        else:
            self.warn("Destination file already exists, won't rename")
            # TODO add overwrite confirmation dialog

    def on_file_treeview_button_release_event(self, widget, data=None):
        self.emit('button-release-event')

    # =======================================
    #   Methods to be called externally
    # =======================================

    # Get filechooser object to embed in main window
    def get_filechooser_widget(self):
        return self.builder.get_object('vbox1')

    # Add filter by name and list of extensions to display
    def add_filter(self, name, ext):
        self._filters[name] = ext

    # Delete filter by name
    def remove_filter(self, name):
        if name in self._filters:
            del self._filters[name]
            return True
        return False

    # Set current filter by name
    def set_filter(self, name):
        if name in self._filters:
            self._filter = name
            self._fill_file_liststore()
            return True
        return False

    # Get current filter
    def get_filter(self):
        if self._filter in self._filters:
            return [self._filter, self._filters[self._filter]]
        return None

    # Get names of all specified filters
    def get_filters(self):
        filters = []
        for filter in self._filters:
            filters.append(filter)
        return filters

    # Get whether hidden files are shown
    def get_show_hidden(self):
        return self._show_hidden

    # Set whether hidden files are shown
    def set_show_hidden(self, setting):
        self._show_hidden = setting

    # Get the path of the current display directory
    def get_current_folder(self):
        return self.cur_dir

    # Set current display directory to path
    def set_current_folder(self, fpath):
        if os.path.exists(fpath):
            self._fill_file_liststore(fpath)
            return True
        return False

    # Get absolute path at cursor
    def get_path_at_cursor(self):
        path = self.file_treeview.get_cursor()[0]
        if path is not None:
            fname = self.file_liststore[path][2]
            fpath = os.path.join(self.cur_dir, fname)
            return fpath
        return None

    # Set cursor at path
    def set_cursor_at_path(self, fpath):
        model = self.file_liststore
        tree = self.file_treeview
        if not os.path.exists(fpath):
            return False
        fpath, fname = os.path.split(fpath)
        if fpath != self.cur_dir:
            self._fill_file_liststore(fpath)
        for row in range(len(model)):
            if model[row][2] == fname:
                tree.set_cursor(row)
                return True
        return False

    # Get paths for selected
    def get_selected(self):
        model = self.file_liststore
        paths = []
        for row in range(len(model)):
            if model[row][0] == 1:
                fpath = os.path.join(self.cur_dir, model[row][2])
                paths.append(fpath)
        if len(paths) == 0:
            return None
        return paths

    # Check checkbox at file path
    def set_selected(self, fpath):
        model = self.file_liststore
        tree = self.file_treeview
        if not os.path.exists(fpath):
            return False
        fpath, fname = os.path.split(fpath)
        if fpath != self.cur_dir:
            self._fill_file_liststore(fpath)
        for row in range(len(model)):
            if model[row][2] == fname:
                model[row][0] = 1
                return True
        return False

    # Check all checkboxes in current display directory
    def select_all(self, fpath=None):
        model = self.file_liststore
        if fpath is not None:
            if os.path.isdir(fpath):
                self._fill_file_liststore(fpath)
            else:
                return False
        for row in range(len(model)):
            model[row][0] = 1
        return True

    # Uncheck all checkboxes in current display directory
    def unselect_all(self):
        model = self.file_liststore
        for row in range(len(model)):
            model[row][0] = 0

    # Get paths to current mounts
    def get_mounts(self):
        mounts = self.mounts.get_mounts()
        paths = []
        for mount in mounts:
            path = mount.get_root().get_path()
            paths.append(path)
        return paths

    # Get list of place bookmarks
    def get_places(self):
        return self.places

    # Get list of user bookmarks
    def get_bookmarks(self):
        return self.folders

    # Add a single bookmark linking to path
    def add_bookmark(self, path):
        return self.add_bookmarks([path])

    # Add multiple bookmarks, one for each path in list
    def add_bookmarks(self, paths):
        skiped = []
        for path in paths:
            if not os.path.exists(path) or not os.path.isdir(path) \
                    or path in self.folders or path in self.places:
                skiped.append(path)
                continue
            self.folders.append(path)
        self._update_bookmarks()
        if len(skiped) == 0:
            return True
        return skiped

    # Remove single bookmark linking to path
    def remove_bookmark(self, path):
        return self.remove_bookmarks([path])

    # Remove multiple bookmarks for each path in list
    def remove_bookmarks(self, paths):
        skiped = []
        for path in paths:
            if path in self.folders:
                self.folders.remove(path)
            else:
                skiped.append(path)
        self._update_bookmarks()
        if len(skiped) == 0:
            return True
        return skiped

    # Remove all bookmarks
    def remove_all_bookmarks(self):
        self.folders = []
        self._update_bookmarks()

    # Display parent of current directory
    def up_one_dir(self):
        path = os.path.dirname(self.cur_dir)
        self._fill_file_liststore(path)

    # Cut selected files
    def cut_selected(self):
        files = self.get_selected()
        if files is None:
            return False
        self._files = files
        self._copy = False
        return True

    # Copy selected files
    def copy_selected(self):
        files = self.get_selected()
        if files is None:
            return False
        self._files = files
        self._copy = True
        return True

    # Paste previously cut/copied files to current directory
    def paste(self):
        src_list = self._files
        if src_list is None:
            return False
        dst_dir = self.cur_dir
        if self._copy:
            for src in self._files:
                self._copy_file(src, dst_dir)
        elif not self._copy:
            for src in self._files:
                self._move_file(src, dst_dir)
            self._files = None
        self._fill_file_liststore()
        return True

    # Save file as, if path is specified it will be saved in that directory
    def save_as(self, path=None):
        model = self.file_liststore
        tree = self.file_treeview
        if path is None:
            path = self.get_selected()[0]
        if not os.path.exists(path) or path is None:
            return False
        fdir, fname = os.path.split(path)
        new_name = self._copy_file(path, fdir)
        for row in range(len(model)):
            if model[row][2] == new_name:
                break
        focus_column = self.builder.get_object('col_file_name')
        model[row][0] = 1
        tree.set_cursor(row, focus_column, True)

    # Move selected files to trash (see file_util code at end)
    def delete_selected(self):
        paths = self.get_selected()
        for path in paths:
            self._trash_file(path)
        self._fill_file_liststore()

    # =======================================
    #   Drag and Drop TODO
    # =======================================

    def on_file_treeview_drag_begin(self, data, som):
        print("drag {0} {1}".format(data, som))

    def on_file_treeview_drag_data_received(self):
        print("got drag")

    def drag_data_received_cb(self, treeview, context, x, y, selection, info, timestamp):
        drop_info = treeview.get_dest_row_at_pos(x, y)
        print("got drag")
        if drop_info:
            model = treeview.get_model()
            path, position = drop_info
            data = selection.data
            # do something with the data and the model
            print("{0} {1} {2}".format(model, path, data))
        return

    # =======================================
    #   Bookmark treeview
    # =======================================

    def on_mount_added(self, volume, mount):
        path = mount.get_root().get_path()
        name = os.path.split(path)[1]
        text = "External storage device mounted - " + name
        self.info(text)
        self._update_bookmarks()

    def on_mount_removed(self, volume, mount):
        path = mount.get_root().get_path()
        name = os.path.split(path)[1]
        text = "External storage device removed - " + name
        self.info(text)
        if self.cur_dir.startswith(path):
            self.file_liststore.clear()
            self._update_nav_buttons('')
        self._update_bookmarks()

    def on_bookmark_treeview_cursor_changed(self, widget):
        model = self.bookmark_liststore
        path, column = widget.get_cursor()
        fpath = model[path][2]
        if column == self.eject_column and model[path][3] == True:
            os.system('eject "{0}"'.format(fpath))
            if fpath == self.cur_dir:
                self.file_liststore.clear()
            return
        self._fill_file_liststore(fpath)

    def on_add_bookmark_button_release_event(self, widget, data=None):
        path = self.file_treeview.get_cursor()[0]
        if path is None:
            fpath = self.cur_dir
        else:
            fname = self.file_liststore[path][2]
            fpath = os.path.join(self.cur_dir, fname)
        if not os.path.isdir(fpath):
            return
        self.add_bookmark(fpath)

    def on_remove_bookmark_button_release_event(self, widget, data=None):
        path = self.bookmark_treeview.get_cursor()[0]
        if path is None:
            return
        fpath = self.bookmark_liststore[path][2]
        self.remove_bookmark(fpath)

    def _update_bookmarks(self):
        places = sorted(self.places, key=len, reverse=False)
        mounts = sorted(self.get_mounts(), key=self.sort, reverse=False)
        folders = sorted(self.folders, key=self.sort, reverse=False)
        model = self.bookmark_liststore
        model.clear()
        for path in places:
            name = os.path.split(path)[1]
            icon = self._get_place_icon(name)
            model.append([icon, name, path, False])
        for path in mounts:
            name = os.path.split(path)[1]
            icon = self._get_place_icon('USBdrive')
            model.append([icon, name, path, True])
        model.append([None, None, None, False])
        for path in folders:
            if not os.path.exists(path):
                continue
            name = os.path.split(path)[1]
            icon = self._get_place_icon(name)
            model.append([icon, name, path, False])

        data = [places, folders]
        try:
            with open(self.data_file, 'w') as file:
                json.dump(data, file, sort_keys=True, indent=4)
        except Exception as e:
            print(e)

    # Generate sort key based on file basename
    def sort(self, path):
        return os.path.basename(path).lower()

    # If name is None row should be a separator
    def bookmark_separator(self, model, iter):
        return self.bookmark_liststore.get_value(iter, 1) is None

    # =======================================
    #   File utility functions
    # =======================================

    def _copy_file(self, src, dst_dir):
        src_dir, dst_name = os.path.split(src)
        if src_dir == dst_dir:
            # self.error("COPY ERROR: Source and destination are the same")
            # return
            name, ext = os.path.splitext(dst_name)
            dst_name = '{0}_copy{1}'.format(name, ext)
        dst = os.path.join(dst_dir, dst_name)
        if os.path.exists(dst):
            self.error("COPY ERROR: Destination file {0} already exists".format(dst))
            return
        self.info("Copying: {0} to {1}".format(src, dst))
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            shutil.copytree(src, dst)
        self._fill_file_liststore()
        return dst_name

    def _move_file(self, src, dst_dir):
        src_dir, src_name = os.path.split(src)
        if src_dir == dst_dir:
            self.error("MOVE ERROR: Source and destination are the same")
            return
        dst = os.path.join(dst_dir, src_name)
        if os.path.exists(dst):
            self.error("MOVE ERRPR: Destination file {} already exists".format(dst))
        self.info("Moving: {0} to {1}".format(src, dst))
        shutil.move(src, dst)


    # Note:
    # This trash implementation tries to follow the guidelines set for by
    # freedesktop.org, see the specifications here:
    # https://specifications.freedesktop.org/trash-spec/trashspec-latest.html

    # FIXME if you try to trash a symbolic link the folder that is refers to
    #       will be trashed.  Should fix this so only the link file is trashed
    def _trash_file(self, path):
        path = os.path.realpath(path)
        if not os.path.exists(path):
            print("Can't move file to trash, file does not exist\nFile path: {0}".format(path))
            return
        elif not os.access(path, os.W_OK):
            print("Can't move file to trash, permission denied\nFile path: {0}".format(path))
            return

        file_dev = os.lstat(path).st_dev
        trash_dev = os.lstat(os.path.expanduser('~')).st_dev
        if file_dev == trash_dev:
            file_vol_root = None
            trash_dir = HOMETRASH
        else:
            file_vol_root = self._get_mount_point(path)
            trash_dev = os.lstat(file_vol_root).st_dev
            if trash_dev != file_dev:
                print("Could not find mount point for: {0}".format(path))
                print("The file will not be moved to trash")
                return
            trash_dir = self._find_ext_vol_trash(file_vol_root)
        self._move_to_trash(path, trash_dir, file_vol_root)

    def _find_ext_vol_trash(self, vol_root):
        trash_dir = os.path.join(vol_root, '.Trash')
        if os.path.exists(trash_dir):
            mode = os.lstat(trash_dir).st_mode
            # must be a directory, not a symlink, and have the sticky bit set.
            if os.path.isdir(trash_dir) or not os.path.islink(trash_dir) \
                    or (mode & stat.S_ISVTX):
                print("Volume topdir trash exists and is valid: {0}".format(trash_dir))
                return trash_dir
            else:
                print("Volume topdir trash exists but is not valid: {0}".format(trash_dir))
        else:
            print("A topdir trash does not exist on the volume")
        # If we got this far we need to try a UID trash dir
        uid = os.getuid()
        trash_dir = os.path.join(vol_root, '.Trash-{0}'.format(uid))
        if not os.path.exists(trash_dir):
            print("Creating UID trash dir at volume root: {0}".format(trash_dir))
            os.makedirs(trash_dir, 0o700)
        else:
            print("UID trash dir exists at volume root: {0}".format(trash_dir))
        return trash_dir

    def _get_mount_point(self, path):
        path = os.path.realpath(path)
        while not os.path.ismount(path):
            path = os.path.split(path)[0]
        return path

    def _move_to_trash(self, src, dst, ext_vol=None):
        fname = os.path.basename(src)
        name, ext = os.path.splitext(fname)

        file_dst_dir = os.path.join(dst, 'files')
        info_dst_dir = os.path.join(dst, 'info')

        file_dst = os.path.join(file_dst_dir, fname)
        info_dst = os.path.join(info_dst_dir, fname + ".trashinfo")

        count = 0
        while os.path.exists(file_dst) or os.path.exists(info_dst):
            count += 1
            dst_name = '{0} {1} {2}'.format(name, count, ext)
            file_dst = os.path.join(file_dst_dir, dst_name)
            info_dst = os.path.join(info_dst_dir, "{0}.trashinfo".format(dst_name))

        # Create trash info file
        if ext_vol is None:
            path = src
        else:
            # Use relative path on volume
            path = os.path.relpath(src, ext_vol)

        date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        info = "[Trash Info]\nPath={0}\nDeletionDate={1}\n".format(path, date)

        print("Writing info file: {0}".format(info_dst))
        print(info)

        with open(info_dst, 'w') as infofile:
            infofile.write(info)

        # Finally, lets move the file
        print("Moving the file from {0} to {1}".format(src, file_dst))
        os.rename(src, file_dst)

    # Shortcut methods to emit errors and print to terminal
    def error(self, text):
        self.emit('error', 'ERROR', text)
        print(text)

    def warn(self, text):
        self.emit('error', 'WARN', text)
        print(text)

    def info(self, text):
        self.emit('error', 'INFO', text)
        print(text)


def main():
    gtk.main()


if __name__ == "__main__":
    ui = Filechooser()
    main()
