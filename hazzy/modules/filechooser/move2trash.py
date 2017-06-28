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

# Note:
#   This trash implementation tries to follow the guidelines set for by
#   freedesktop.org here:
#   https://specifications.freedesktop.org/trash-spec/trashspec-latest.html

import os
import shutil
import logging
from datetime import datetime

log = logging.getLogger("HAZZY.FILCHOOSER.MOVE2TRASH")

XDG_DATA_HOME = os.path.expanduser(os.environ.get('XDG_DATA_HOME', '~/.local/share'))
HOMETRASH = os.path.join(XDG_DATA_HOME, 'Trash')

# FIXME if we try to trash a symbolic link the folder that is refers to
#       will be trashed.  Should fix this so only the link file is trashed
def move2trash(path):
    path = os.path.realpath(path)
    if not os.path.exists(path):
        msg = "TRASH ERROR: file does not exist: {0}".format(path)
        log.error(msg)
        return ['ERROR', msg]
    elif not os.access(path, os.W_OK):
        msg = "TRASH ERROR: permission denied: {0}".format(path)
        log.error(msg)
        return ['ERROR', msg]

    file_dev = os.lstat(path).st_dev
    trash_dev = os.lstat(os.path.expanduser('~')).st_dev
    if file_dev == trash_dev:
        file_vol_root = None
        trash_dir = HOMETRASH
    else:
        file_vol_root = _get_mount_point(path)
        trash_dev = os.lstat(file_vol_root).st_dev
        if trash_dev != file_dev:
            msg = "TRASH ERROR: Could not find mount point for: {0}".format(path)
            log.error(msg)
            return ['ERROR', msg]
        trash_dir = _find_ext_vol_trash(file_vol_root)
    return _move_to_trash(path, trash_dir, file_vol_root)

# Restore file from trash
def restore(path):
    raise NotImplementedError

def _find_ext_vol_trash(vol_root):
    trash_dir = os.path.join(vol_root, '.Trash')
    if os.path.exists(trash_dir):
        mode = os.lstat(trash_dir).st_mode
        # must be a directory, not a symlink, and have the sticky bit set.
        if os.path.isdir(trash_dir) or not os.path.islink(trash_dir) \
                or (mode & stat.S_ISVTX):
            log.debug("Volume topdir trash exists and is valid: {0}".format(trash_dir))
            return trash_dir
        else:
            log.debug("Volume topdir trash exists but is not valid: {0}".format(trash_dir))
    else:
        log.debug("A topdir trash does not exist on the volume")
    # If we got this far we need to try a UID trash dir
    uid = os.getuid()
    trash_dir = os.path.join(vol_root, '.Trash-{0}'.format(uid))
    if not os.path.exists(trash_dir):
        log.debug("Creating UID trash dir at volume root: {0}".format(trash_dir))
        os.makedirs(trash_dir, 0o700)
    else:
        log.debug("UID trash dir exists at volume root: {0}".format(trash_dir))
    return trash_dir

def _get_mount_point(path):
    path = os.path.realpath(path)
    # Move back thru the path until we find the mount point
    while not os.path.ismount(path):
        path = os.path.split(path)[0]
    return path

def _move_to_trash(src, dst, ext_vol=None):
    fname = os.path.basename(src)
    name, ext = os.path.splitext(fname)

    file_dst_dir = os.path.join(dst, 'files')
    info_dst_dir = os.path.join(dst, 'info')

    # Full paths to file and info destinations
    file_dst = os.path.join(file_dst_dir, fname)
    info_dst = os.path.join(info_dst_dir, fname + ".trashinfo")

    # Find unique trash name
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
        # Use relative path on ext volume
        path = os.path.relpath(src, ext_vol)

    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    info = "[Trash Info]\nPath={0}\nDeletionDate={1}\n".format(path, date)

    log.debug("Writing info file: {0}".format(info_dst))
    #log.debug(info)

    with open(info_dst, 'w') as infofile:
        infofile.write(info)

    # Actually move file to trash dir
    log.info('Moving file from "{0}" to "{1}"'.format(src, file_dst))
    os.rename(src, file_dst)
    msg = '"{0}" successfully moved to trash'.format(fname)
    return ['INFO', msg]

