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

import os
import shutil
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gio', '2.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GObject

from datetime import datetime

from utilities import logger
from widget_factory.TouchPads import keyboard

# Import our own file utility modules
from move2trash import move2trash
from userdirectories import UserDirectories
from bookmarks import BookMarks
from icons import Icons

# Set up paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
UIDIR = os.path.join(PYDIR, 'ui')

# Set up logging
log = logger.get(__name__)

class FileChooser(Gtk.Bin):
    __gtype_name__ = 'FileChooser'
    __gsignals__ = {
        'file-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'selection-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }

    def __init__(self, widget_window):
        Gtk.Bin.__init__(self)

        self.widget_window = widget_window

        # Glade setup
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(UIDIR, "filechooser.glade"))
        self.builder.connect_signals(self)

        self.builder.get_object = self.builder.get_object

        self.add(self.builder.get_object('filechooser'))

        # Retrieve frequently used objects
        self.nav_box = self.builder.get_object('nav_box')
        self.nav_btn_box = self.builder.get_object('nav_btn_box')

        file_adj = self.builder.get_object('fileview')
        self.file_vadj = file_adj.get_vadjustment()
        self.file_hadj = file_adj.get_hadjustment()

        # Retrieve data models
        self.file_liststore = self.builder.get_object("file_liststore")

        # Retrieve treeviews
        self.file_treeview = self.builder.get_object("file_treeview")
        self.bookmark_listbox = self.builder.get_object("bookmark_listbox")

        # Enable DnD ToDo implement DnD
        self.file_treeview.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                                    [('text/plain', 0, 0)], 
                                    Gdk.DragAction.MOVE | Gdk.DragAction.COPY)
        self.file_treeview.enable_model_drag_dest([('text/plain', 0, 0)],
                                                  Gdk.DragAction.COPY)

        # Connect callbacks to VolumeMonitor
        self.mounts = Gio.VolumeMonitor.get()
        self.mounts.connect('mount-added', self.on_mount_added)
        self.mounts.connect('mount-removed', self.on_mount_removed)

        # Initialize helpers
        self.bookmarks = BookMarks()
        self.icons = Icons(Gtk.IconTheme.get_default())

        # Initialize places
        self.userdirs = UserDirectories()
        desktop = self.userdirs.get_XDG_directory('XDG_DESKTOP_DIR')
        home = self.userdirs.get_home_directory()
        self.places = [home, desktop]

        # Initialize variables
        self._cur_dir = None
        self._old_dir = ''
        self._filters = {}
        self._filter = None
        self._files = []
        self._show_hidden = False
        self._hidden_exts = ['.desktop']
        self._copy = True
        self._selection = None
        self.nav_btn_list = []
        self.nav_btn_path_dict = {}
        self.eject_btn_path_dict = {}

        # Initialize
        self._init_nav_buttons()

        self.show_all()

    # Have to do this once realized so sizes will have been allocated
    def on_filechooser_realize(self, widget):
        self._update_bookmarks()
        self._fill_file_liststore(self._cur_dir)

    def _init_nav_buttons(self):
        # FixMe this needs a lot of work. Try to copy this implementation
        # https://searchcode.com/codesearch/view/22668315/
        box = self.nav_btn_box
        box.get_style_context().add_class(Gtk.STYLE_CLASS_LINKED)

        arrow_left = Gtk.Arrow.new(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE)
        self.arrow_btn_left = Gtk.Button()
        self.arrow_btn_left.add(arrow_left)
        box.add(self.arrow_btn_left)

        self.btn_goto_root = Gtk.Button.new_from_icon_name('gtk-harddisk', Gtk.IconSize.LARGE_TOOLBAR)
        self.btn_goto_root.connect('pressed', self.on_goto_root_clicked)
        box.add(self.btn_goto_root)

        btn_list = self.nav_btn_list
        btn_dict = self.nav_btn_path_dict
        for i in range(10):
            btn = Gtk.Button()
            btn.set_hexpand(False)
            btn.connect('clicked', self.on_nav_btn_clicked)
            btn.set_can_focus(False)
            btn.set_use_underline(False)
            btn_list.append(btn)
            box.add(btn)
            btn_dict[btn] = ''

#        arrow_right = Gtk.Arrow.new(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
#        self.arrow_btn_right = Gtk.Button()
#        self.arrow_btn_right.add(arrow_right)
#        box.add(self.arrow_btn_right)

        box.show_all()

    def _update_nav_buttons(self, path=None):
        for btn in self.nav_btn_list:
            btn.hide()
        if path is None:
            path = self._cur_dir
        if len(path) == 1:
            return
        places = path.split('/')[1:]
        path = '/'
        w_needed = 0
        w_allowed = self.nav_btn_box.get_allocated_width()
        for i, place in enumerate(places):
            btn = self.nav_btn_list[i]
            btn.set_label(place)
            path = os.path.join(path, place)
            self.nav_btn_path_dict[btn] = path
            btn.show()
            w_needed += btn.get_allocated_width()
        if w_needed > w_allowed:
            self.btn_goto_root.hide()
            self.arrow_btn_left.show()
        else:
            self.btn_goto_root.show()
            self.arrow_btn_left.hide()
        count = 0
        while w_needed > w_allowed:
            btn = self.nav_btn_list[count]
            w_needed -= btn.get_allocated_width()
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
        self.selected_row = None

        if path:
            self._cur_dir = path
            # Reset scrollbars since display has changed
            self.file_vadj.set_value(0)
            self.file_hadj.set_value(0)
        if self._cur_dir is None:
            self._cur_dir = self.userdirs.get_XDG_directory('XDG_DESKTOP_DIR')

        files = []
        folders = []
        if self._filter:
            exts = self._filters[self._filter]
        else:
            exts = '*' # Don't filter
        names = os.listdir(self._cur_dir)
        for name in names:
            if name[0] == '.' and not self._show_hidden:
                continue
            path = os.path.join(self._cur_dir, name)
            if os.path.islink(path):
                path = os.readlink(path)
            if os.path.isdir(path):
                folders.append(name)
            elif os.path.isfile(path):
                ext = os.path.splitext(name)[1]
                if '*' in exts or ext in exts and not ext in self._hidden_exts:
                    files.append(name)

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

        self.emit('selection-changed', self._cur_dir)

        # If dir is in bookmarks, select the bookmark
        for row in self.bookmark_listbox.get_children():
            bookmark_path = row.get_tooltip_text()
            if bookmark_path == self._cur_dir:
                self.bookmark_listbox.select_row(row)
                break
        else:
            self.bookmark_listbox.unselect_all()

        # No file selected yet, so desensitize edit buttons
        self.builder.get_object('edit_button').set_sensitive(False)
        self.builder.get_object('cut_button').set_sensitive(False)
        self.builder.get_object('copy_button').set_sensitive(False)
        self.builder.get_object('delete_button').set_sensitive(False)

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

    def count_lines(self, filename):
        lines = 0
        buf_size = 1024 * 1024
        with open(filename) as fh:
            read_f = fh.read
            buf = read_f(buf_size)
            while buf:
                lines += buf.count('\n')
                buf = read_f(buf_size)
        return lines + 1

    def on_select_toggled(self, widget, path):
        model = self.file_liststore
        model[path][0] = not model[path][0]

    def on_file_treeview_key_press_event(self, widget, event):
        kv = event.keyval
        # Events that don't need to know about modifiers
        if kv == Gdk.KEY_Escape:
            self.file_treeview.get_selection().unselect_all()
            self.builder.get_object('edit_button').set_sensitive(False)
            self.builder.get_object('cut_button').set_sensitive(False)
            self.builder.get_object('copy_button').set_sensitive(False)
            self.builder.get_object('delete_button').set_sensitive(False)
            return True
        elif kv == Gdk.KEY_Delete:
            self.delete_selected()
            return True
        elif kv == Gdk.KEY_F2:
            self.edit_selected()
            return True

        # Handle other events
        # Determine the actively pressed modifier
        modifier = event.get_state() & Gtk.accelerator_get_default_mod_mask()

        # Bool of Control or Shift modifier states
        control = modifier == Gdk.ModifierType.CONTROL_MASK
        shift = modifier == Gdk.ModifierType.SHIFT_MASK

        if control and kv == Gdk.KEY_c:
            return self.copy_selected()
        elif control and kv == Gdk.KEY_x:
            return self.cut_selected()
        elif control and kv == Gdk.KEY_v:
            return self.paste()


    def on_filechooser_treeview_cursor_changed(self, widget):
        row = widget.get_cursor()[0]
        # Prevent emitting selection changed on double click
        if row == self.selected_row or row is None:
            return

        self.selected_row = row

        fname = self.file_liststore[row][2]
        fpath = os.path.join(self._cur_dir, fname)
        self.emit('selection-changed', fpath)

        self.builder.get_object('edit_button').set_sensitive(True)
        self.builder.get_object('cut_button').set_sensitive(True)
        self.builder.get_object('copy_button').set_sensitive(True)
        self.builder.get_object('delete_button').set_sensitive(True)

    def on_filechooser_treeview_row_activated(self, widget, path, colobj):
        fname = self.file_liststore[path][2]
        fpath = os.path.join(self._cur_dir, fname)
        if os.path.isfile(fpath):
            self.emit('file-activated', fpath)
        elif os.path.isdir(fpath):
            self._fill_file_liststore(fpath)
        else:
            # If neither, probably does not exist, so reload
            self._fill_file_liststore()

    def on_file_name_editing_started(self, renderer, entry, row):
        keyboard.show(entry)

    def on_file_name_edited(self, widget, row, new_name):
        model = self.file_liststore
        model[row][0] = 0
        old_name = model[row][2]
        old_path = os.path.join(self._cur_dir, old_name)
        new_path = os.path.join(self._cur_dir, new_name)
        if old_name == new_name:
            return
        if not os.path.exists(new_path):
            os.rename(old_path, new_path)
            msg = 'Renamed "{}" to "{}"'.format(old_name, new_name)
            log.info(msg)
            self.widget_window.show_info(msg, 2)
            model[row][2] = new_name
        else:
            msg = "Destination file already exists, won't rename"
            log.warning(msg)
            self.widget_window.show_warning(msg)

    # =======================================
    #   Methods to be called externally
    # =======================================

    # Add filter by name
    def add_filter(self, name, exts):
        self._filters[name] = [ext.replace('*.', '.') for ext in exts]

    # Delete filter by name
    def delete_filter(self, name):
        if name in self._filters:
            del self._filters[name]
            if self._filter == name:
                self._filter = None
            return True
        return False

    # Set current filter by name
    def set_filter(self, name):
        if name is None:
            self._filter = None
        elif name in self._filters:
            self._filter = name
        self._fill_file_liststore()

    # Get current filter
    def get_filter(self):
        if self._filter in self._filters:
            return ['*' + ext for ext in self._filters[self._filter]]
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
#        fpath = fpath.rstrip('/')
        if os.path.exists(fpath):
            self._fill_file_liststore(fpath)
            log.info('Setting the current folder to "{}"'.format(fpath))
            return True
        log.error('Can not set current folder to "{}", folder does not exist' 
            .format(fpath))
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
        model, rows = self.file_treeview.get_selection().get_selected_rows()
        if not rows:
            return
        paths = []
        for row in rows:
            fpath = os.path.join(self._cur_dir, model[row.to_string()][2])
            paths.append(fpath)
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
            name = mount.get_name()
            paths.append([path, name, mount])
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
    def cut_selected(self, widegt=None, data=None):
        files = self.get_selected()
        if not files:
            log.error("No files selected to cut")
            return False
        self._files = files
        self._copy = False
        log.debug("Files to cut: {}".format(files))
        self.builder.get_object('paste_button').set_sensitive(True)
        return True

    # Copy selected files
    def copy_selected(self, widegt=None, data=None):
        files = self.get_selected()
        if files is None:
            log.error("No files selected to copy")
            return False
        self._files = files
        self._copy = True
        log.debug("Files to copy: {}".format(files))
        self.builder.get_object('paste_button').set_sensitive(True)
        return True

    # Paste previously cut/copied files to current directory
    def paste(self, widegt=None, data=None):
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
        self.builder.get_object('paste_button').set_sensitive(False)
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
    def new_folder(self, widegt=None, data=None):
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

    # Create a new folder in the current directory
    def new_file(self, widegt=None, data=None):
        model = self.file_liststore
        tree = self.file_treeview

        name = "New file"
        count = 1
        while os.path.exists(os.path.join(self._cur_dir, name)):
            name = 'New Folder {0}'.format(count)
            count += 1

        path = os.path.join(self._cur_dir, name)
        with open(path, 'w') as fh:
            pass
        self._fill_file_liststore()

        for row in range(len(model)):
            if model[row][2] == name:
                break
        focus_column = self.builder.get_object('col_file_name')
        model[row][0] = 1
        tree.set_cursor(row, focus_column, True)

    def edit_selected(self, widget=None, data=None):
        row = self.file_treeview.get_cursor()[0]
        if not row:
            return
        model = self.file_liststore
        tree = self.file_treeview
        focus_column = self.builder.get_object('col_file_name')
        model[row][0] = 1
        tree.set_cursor(row, focus_column, True)

    # Move selected files to trash (see file_util code at end)
    def delete_selected(self, widegt=None, data=None):
        paths = self.get_selected()
        if paths is None:
            return
        num = len(paths)
        for path in paths:
            result, msg = move2trash(path)
        self._fill_file_liststore()

        if result == 'INFO':
            self.widget_window.show_info(msg, 2)
        else:
            self.widget_window.show_error(msg)


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
        self.widget_window.show_info(msg, 2)
        self._update_bookmarks()

    def on_mount_removed(self, volume, mount):
        path = mount.get_root().get_path()
        name = os.path.split(path)[1]
        msg = 'External storage device "{}" removed'.format(name)
        log.info(msg)
        self.widget_window.show_info(msg, 2)
        if self._cur_dir.startswith(path):
            self.file_liststore.clear()
            self._update_nav_buttons('')
        self._update_bookmarks()

    def on_eject_clicked(self, widget):
        mount = self.eject_btn_path_dict[widget]
        path = mount.get_root().get_path()
        name = mount.get_name()
        mount.eject(0, None, self.on_eject_finished)

    def on_eject_finished(self, mount, result):
        msg ='Safe to remove external storage device "{}"'.format(mount.get_name())
        log.info(msg)
        self.widget_window.show_info(msg, 2)

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
        row = self.bookmark_listbox.get_selected_row()
        path = row.get_tooltip_text()
        if path is None:
            return
        self.bookmark_listbox.remove(row)
        self.bookmarks.remove(path)

    def _update_bookmarks(self):
        ext_media = sorted(self.get_mounts(), key=self.sort, reverse=False)
        bookmarks = sorted(self.bookmarks.get(), key=self.sort, reverse=False)

        for child in self.bookmark_listbox.get_children():
            self.bookmark_listbox.remove(child)

        # Add the places
        for path in self.places:
            icon = self.icons.get_for_directory(path)
            self.add_listbox_row(icon, path)

        # Add the mounts
        self.eject_btn_path_dict = {}
        icon = self.icons.get_for_device('USBdrive')
        for device in ext_media:
            path, name, mount = device
            if mount.can_eject():
                self.add_listbox_row(icon, path, name, mount)
            else:
                self.add_listbox_row(icon, path, name)

        # Add the seperator
        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        separator = Gtk.Separator()
        row.add(separator)
        self.bookmark_listbox.add(row)

        # Add the bookmarks
        for bookmark in bookmarks:
            path, name = bookmark
            if not os.path.exists(path):
                continue
            icon = self.icons.get_for_directory(path)
            self.add_listbox_row(icon, path, name)

        self.bookmark_listbox.show_all()


    def add_listbox_row(self, icon, path, name=None, mount=None):
        if not name or name == '':
            name = os.path.split(path)[1]
        row = Gtk.ListBoxRow()
        row.set_tooltip_text(path)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(hbox)

        # Add icon
        image = Gtk.Image.new_from_pixbuf(icon)
        hbox.pack_start(image, False, False, 0)

        # Add label
        label = Gtk.Label()
        label.set_text(name)
        label.set_xalign(0)
        hbox.pack_start(label, True, True, 4)

        # Add media eject button
        if mount is not None:
            icon = self.icons.get_for_device('media-eject')
            image = Gtk.Image.new_from_pixbuf(icon)
            btn = Gtk.Button()
            self.eject_btn_path_dict[btn] = mount
            btn.connect('clicked', self.on_eject_clicked)
            btn.set_name('eject')
            btn.set_image(image)
            hbox.pack_start(btn, False, False, 0)

        self.bookmark_listbox.add(row)

    # Generate sort key based on file basename
    def sort(self, location):
        path = location[0]
        name = location[1]
        if name is None:
            return os.path.basename(path).lower()
        return name

    def on_bookmark_activated(self, widget, data=None):
        path = data.get_tooltip_text()
        self._fill_file_liststore(path)

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
            overwrite = False #self.ok_cancel_dialog.run(text)
            if not overwrite:
                msg = "User selected not to overwrite {}".format(dst_name)
                log.info(msg)
                self.widget_window.show_info(msg, 2)
                return

        if os.path.isfile(src):
            shutil.copy2(src, dst)

        else:
            shutil.copytree(src, dst)

        msg = 'Copied "{0}" to "{1}"'.format(src_name, dst_dir)
        log.info(msg)
        self.widget_window.show_info(msg, 2)

        self._fill_file_liststore()
        return dst_name


    def _move_file(self, src, dst_dir):
        src_dir, src_name = os.path.split(src)

        if src_dir == dst_dir:
            msg = "MOVE ERROR: Source and destination are the same"
            log.error(msg)
            self.widget_window.show_error(msg)
            return

        dst = os.path.join(dst_dir, src_name)

        if os.path.exists(dst):
            msg = "WARNING: Destination already exists. Overwrite {}?".format(src_name)
            overwrite = False #self.ok_cancel_dialog.run(text)
            if not overwrite:
                msg = 'User selected not to overwrite "{}"'.format(src_name)
                log.info(msg)
                self.widget_window.show_info(msg, 2)
                return

        msg = 'Moving "{0}" to "{1}"'.format(src_name, dst_dir)
        log.info(msg)
        self.widget_window.show_info(msg, 2)
        shutil.move(src, dst)
