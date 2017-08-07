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

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gio
import sys
import os
import shutil
import logging

from datetime import datetime
from move2trash import move2trash
from bookmarks import BookMarks
from icons import Icons
from modules.dialogs.dialogs import Dialogs, DialogTypes

log = logging.getLogger("HAZZY.FILECHOOSER")

pydir = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(pydir, 'ui')


class Filechooser(GObject.GObject):
    __gtype_name__ = 'Filechooser'
    __gsignals__ = {
        'file-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'selection-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'filename-editing-started': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'button-release-event': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'error': (GObject.SignalFlags.RUN_FIRST, None, (str, str))
    }

    def __init__(self):

        GObject.GObject.__init__(self)

        # Glade setup
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, "filechooser.glade"))
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
        self.file_treeview.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, \
                                                    [('text/plain', 0, 0)], Gdk.DragAction.MOVE | Gdk.DragAction.COPY)
        self.file_treeview.enable_model_drag_dest([('text/plain', 0, 0)], \
                                                  Gdk.DragAction.COPY)

        # Connect callbacks to VolumeMonitor
        self.mounts = Gio.VolumeMonitor()
        self.mounts.connect('mount-added', self.on_mount_added)
        self.mounts.connect('mount-removed', self.on_mount_removed)

        # Initialize objects
        self.ok_cancel_dialog = Dialogs(DialogTypes.OK_CANCEL)
        self.bookmarks = BookMarks()
        self.icons = Icons(Gtk.IconTheme.get_default())

        # Initialize places
        home = os.environ['HOME']
        desktop = os.path.expanduser("~/Desktop")
        self.places = [home, desktop]

        # Initialize variables
        self._cur_dir = desktop
        self._old_dir = " "
        self._filters = {}
        self._filter = ''
        self._files = []
        self._show_hidden = False
        self._hidden_exts = ['.desktop']
        self._copy = True
        self._selection = None
        self.nav_btn_list = []
        self.nav_btn_path_dict = {}

        # Initialize
        self._init_nav_buttons()


    # Have to do this once realized so sizes will have been allocated
    def on_vbox1_realize(self, widget):
        self._update_bookmarks()
        self._fill_file_liststore(self._cur_dir)

    def _init_nav_buttons(self):
        box = self.nav_box
        btn_list = self.nav_btn_list
        btn_dict = self.nav_btn_path_dict
        for i in range(10):
            btn = Gtk.Button()
            btn.connect('clicked', self.on_nav_btn_clicked)
            btn.set_can_focus(False)
            btn.set_use_underline(False)
            btn_list.append(btn)
            box.pack_start(btn, False, False, 0)
            btn_dict[btn] = ''

    def _update_nav_buttons(self, path=None):
        if path is None:
            path = self._cur_dir
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
        if path != self._cur_dir:
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
            self._cur_dir = path #os.path.realpath(path)

            # Reset scrollbars since display has changed
            self.file_vadj.set_value(0)
            self.file_hadj.set_value(0)

        files = []
        folders = []
        if self._filter in self._filters:
            exts = self._filters[self._filter]
        else:
            exts = ''
        dirs = os.listdir(self._cur_dir)
        for obj in dirs:
            if obj[0] == '.' and not self._show_hidden:
                continue
            path = os.path.join(self._cur_dir, obj)
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
        for fname in folders:
            fpath = os.path.join(self._cur_dir, fname)
            icon = self.icons.get_for_directory(fpath)
            model.append([0, icon, fname, None, None])

        files.sort(key=str.lower, reverse=False)
        for fname in files:
            fpath = os.path.join(self._cur_dir, fname)
            icon = self.icons.get_for_file(fname)
            size, date = self._get_file_data(fpath)
            model.append([0, icon, fname, size, date])

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
        fpath = os.path.join(self._cur_dir, fname)
        self.emit('selection-changed', fpath)

    def on_filechooser_treeview_row_activated(self, widget, path, colobj):
        fname = self.file_liststore[path][2]
        fpath = os.path.join(self._cur_dir, fname)
        if os.path.isfile(fpath):
            self.emit('file-activated', fpath)
        elif os.path.isdir(fpath):
            self._fill_file_liststore(fpath)

    def on_file_name_editing_started(self, renderer, entry, row):
        self.emit('filename-editing-started', entry)

    def on_file_name_edited(self, widget, row, new_name):
        model = self.file_liststore
        old_name = model[row][2]
        old_path = os.path.join(self._cur_dir, old_name)
        new_path = os.path.join(self._cur_dir, new_name)
        if old_name == new_name:
            return
        if not os.path.exists(new_path):
            msg = "Renamed {} to {}".format(old_name, new_name)
            log.info(msg)
            self.info(msg)
            os.rename(old_path, new_path)
            model[row][2] = new_name
        else:
            msg = "Destination file already exists, won't rename"
            log.warning(msg)
            self.warn(msg)
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
        return self._cur_dir

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
            fpath = os.path.join(self._cur_dir, fname)
            return fpath
        return None

    # Set cursor at path
    def set_cursor_at_path(self, fpath):
        model = self.file_liststore
        tree = self.file_treeview
        if not os.path.exists(fpath):
            return False
        fpath, fname = os.path.split(fpath)
        if fpath != self._cur_dir:
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
                fpath = os.path.join(self._cur_dir, model[row][2])
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
        if fpath != self._cur_dir:
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

    # Get list of user bookmarks
    def get_bookmarks(self):
        return self.bookmarks.get()

    # Add bookmark
    def add_bookmark(self, path):
        if not path in self.places:
            self.bookmarks.add(path)
            self._update_bookmarks()

    # Remove bookmark
    def remove_bookmark(self, path):
        if not path in self.places:
            self.bookmarks.remove(path)
            self._update_bookmarks()

    # Clear all bookmarks
    def clear_bookmarks(self):
        self.bookmarks.clear()
        self._update_bookmarks()

    # Display parent of current directory
    def up_one_dir(self):
        path = os.path.dirname(self._cur_dir)
        self._fill_file_liststore(path)

    # Cut selected files
    def cut_selected(self):
        files = self.get_selected()
        if files is None:
            log.error("No files selected to cut")
            return False
        self._files = files
        self._copy = False
        log.debug("Files to cut: {}".format(files))
        return True

    # Copy selected files
    def copy_selected(self):
        files = self.get_selected()
        if files is None:
            log.error("No files selected to copy")
            return False
        self._files = files
        self._copy = True
        log.debug("Files to copy: {}".format(files))
        return True

    # Paste previously cut/copied files to current directory
    def paste(self):
        src_list = self._files
        if src_list is None:
            return False
        dst_dir = self._cur_dir
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
        fpath, fname = os.path.split(path)
        new_name = self._copy_file(path, fdir)
        for row in range(len(model)):
            if model[row][2] == new_name:
                break
        focus_column = self.builder.get_object('col_file_name')
        model[row][0] = 1
        tree.set_cursor(row, focus_column, True)

    # Create a new folder in the current directory
    def new_folder(self):
        model = self.file_liststore
        tree = self.file_treeview

        name = "New Folder"
        count = 1
        while os.path.exists(os.path.join(self._cur_dir, name)):
            name = 'New Folder {0}'.format(count)
            count += 1

        path = os.path.join(self._cur_dir, name)
        os.makedirs(path)
        self._fill_file_liststore()

        for row in range(len(model)):
            if model[row][2] == name:
                break
        focus_column = self.builder.get_object('col_file_name')
        model[row][0] = 1
        tree.set_cursor(row, focus_column, True)


    # Move selected files to trash (see file_util code at end)
    def delete_selected(self):
        paths = self.get_selected()
        if paths is None:
            return
        num = len(paths)
        for path in paths:
            info = move2trash(path)
        self._fill_file_liststore()

        # Show ERROR/INFO message at bottom of screen
        self.emit('error', info[0], info[1])

    # =======================================
    #   Drag and Drop TODO
    # =======================================

    def on_file_treeview_drag_begin(self, data, som):
        log.debug("drag {0} {1}".format(data, som))

    def on_file_treeview_drag_data_received(self):
        log.debug("got drag")

    def drag_data_received_cb(self, treeview, context, x, y, selection, info, timestamp):
        drop_info = treeview.get_dest_row_at_pos(x, y)
        log.debug("got drag")
        if drop_info:
            model = treeview.get_model()
            path, position = drop_info
            data = selection.data
            # do something with the data and the model
            log.debug("{0} {1} {2}".format(model, path, data))
        return

    # =======================================
    #   Bookmark treeview
    # =======================================

    def on_mount_added(self, volume, mount):
        path = mount.get_root().get_path()
        name = os.path.split(path)[1]
        msg = 'External storage device "{}" mounted'.format(name)
        log.info(msg)
        self.info(msg)
        self._update_bookmarks()

    def on_mount_removed(self, volume, mount):
        path = mount.get_root().get_path()
        name = os.path.split(path)[1]
        msg = 'External storage device "{}" removed'.format(name)
        log.info(msg)
        self.info(msg)
        if self._cur_dir.startswith(path):
            self.file_liststore.clear()
            self._update_nav_buttons('')
        self._update_bookmarks()

    def on_bookmark_treeview_cursor_changed(self, widget):
        model = self.bookmark_liststore
        path, column = widget.get_cursor()
        fpath = model[path][2]
        if column == self.eject_column and model[path][3] == True:
            os.system('eject "{0}"'.format(fpath))
            if fpath == self._cur_dir:
                self.file_liststore.clear()
            return
        self._fill_file_liststore(fpath)

    def on_add_bookmark_button_release_event(self, widget, data=None):
        path = self.file_treeview.get_cursor()[0]
        if path is None:
            fpath = self._cur_dir
        else:
            fname = self.file_liststore[path][2]
            fpath = os.path.join(self._cur_dir, fname)
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
        bookmarks = sorted(self.bookmarks.get(), key=self.sort, reverse=False)
        model = self.bookmark_liststore
        model.clear()

        # Add the places
        for path in places:
            name = os.path.split(path)[1]
            icon = self.icons.get_for_directory(path)
            model.append([icon, name, path, False])

        # Add the mounts
        for path in mounts:
            name = os.path.split(path)[1]
            icon = self.icons.get_for_device('USBdrive')
            model.append([icon, name, path, True])

        # Add the seperator
        model.append([None, None, None, False])

        # Add the bookmarks
        for bookmark in bookmarks:
            path, name = bookmark
            if not os.path.exists(path):
                continue
            if name == '':
                name = os.path.split(path)[1]
            icon = self.icons.get_for_directory(path)
            model.append([icon, name, path, False])

    # Generate sort key based on file basename
    def sort(self, path):
        return os.path.basename(path[0]).lower()

    # If name is None row should be a separator
    def bookmark_separator(self, model, iter):
        return self.bookmark_liststore.get_value(iter, 1) is None

    # =======================================
    #   File utilities
    # =======================================

    def _copy_file(self, src, dst_dir):
        src_dir, src_name = os.path.split(src)
        dst_name = src_name

        # find a unique copy name
        if src_dir == dst_dir:
            name, ext = os.path.splitext(dst_name)
            if '_copy' in name:
                name = name.rpartition('_copy')[0]

            count = 1
            while os.path.exists(os.path.join(dst_dir, dst_name)):
                dst_name = '{0}_copy{1}{2}'.format(name, count, ext)
                count += 1

        dst = os.path.join(dst_dir, dst_name)

        if os.path.exists(dst):
            text = "Destination already exists! \n Overwrite {}?".format(dst_name)
            overwrite = self.ok_cancel_dialog.run(text)
            if not overwrite:
                msg = "User selected not to overwrite {}".format(dst_name)
                log.info(msg)
                self.info(msg)
                return

        msg = 'Copying "{0}" to "{1}"'.format(src_name, dst_dir)
        log.info(msg)
        self.info(msg)

        if os.path.isfile(src):
            shutil.copy2(src, dst)

        else:
            shutil.copytree(src, dst)

        self._fill_file_liststore()
        return dst_name


    def _move_file(self, src, dst_dir):
        src_dir, src_name = os.path.split(src)

        if src_dir == dst_dir:
            msg = "MOVE ERROR: Source and destination are the same"
            log.error(msg)
            self.error(msg)
            return

        dst = os.path.join(dst_dir, src_name)

        if os.path.exists(dst):
            text = "Destination already exists! \n Overwrite {}?".format(src_name)
            overwrite = self.ok_cancel_dialog.run(text)
            if not overwrite:
                msg = 'User selected not to overwrite "{}"'.format(src_name)
                log.info(msg)
                self.info(msg)
                return

        msg = 'Moving "{0}" to "{1}"'.format(src_name, dst_dir)
        log.info(msg)
        self.info(msg)
        shutil.move(src, dst)

    # Shortcut methods to emit errors and print to terminal
    def error(self, text):
        self.emit('error', 'ERROR', text)

    def warn(self, text):
        self.emit('error', 'WARN', text)

    def info(self, text):
        self.emit('error', 'INFO', text)
