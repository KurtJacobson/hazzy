#!/usr/bin/env python
#  -*- coding: utf-8 -*-
#
#   An attempt at a basic UI for LinuxCNC that can be used
#   on a touch screen without any lost of functionality.
#   The code is almost a complete rewrite, but was influenced
#   mainly by Gmoccapy and Touchy, with some code adapted from
#   the HAL vcp widgets.
#
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
import logging.handlers
import sys

from color_formatter import *

loggingLevelMapping = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'error': logging.ERROR,
    'warn': logging.WARN,
    'warning': logging.WARNING,
    'critical': logging.CRITICAL,
    'fatal': logging.FATAL,
}


class ILogger(object):
    """Logging interface class that"""

    def __init__(self, prefix=None):
        self.default_prefix = prefix
        self._initialised = False

    def _prepare(self, msg, prefix):
        if prefix:
            msg = '[{0}] {1}'.format(prefix, msg)
        if self.default_prefix:
            msg = '<{0}> {1}'.format(self.default_prefix, msg)
        if not self._initialised:
            print('{0} Logger not initialised\n'.format(str(msg)))
            return 'WARGH! logging is NOT initialised'
        return msg

    def error(self, msg, prefix=None):
        if hasattr(self, '_logger'):
            self._logger.error(self._prepare(msg, prefix))
        else:
            print("{0}:{1}".format(str(prefix), str(msg)))

    def debug(self, msg, prefix=None):
        if hasattr(self, '_logger'):
            self._logger.debug(self._prepare(msg, prefix))
        else:
            print("{0}:{1}".format(str(prefix), str(msg)))

    def info(self, msg, prefix=None):
        if hasattr(self, '_logger'):
            self._logger.info(self._prepare(msg, prefix))
        else:
            print("{0}:{1}".format(str(prefix), str(msg)))

    def exception(self, e):
        # TODO needs prefix handling
        if hasattr(self, '_logger'):
            self._logger.exception(e)
        else:
            print("Exception: {0}".format(str(e)))

    def loaded(self, t):
        self.info(t, "LOADED")

    def reloaded(self, t):
        self.info(t, "RELOADED")

    def notice(self, t):
        self.info(t, "NOTICE")

    def good(self, t):
        self.info(t, "GOOD")

    def bad(self, t):
        self.error(t, "BAD")

    def warn(self, t):
        self.error(t, "WARNING")


class CLog(ILogger):
    """Main Logging instance, forwards al logging calls to the stdlib's logging
    via a RotatingFileHandler and proper stream formatters"""

    def __init__(self):
        """Since this is called at module import time we cannot do all
        we'd want here, see init for the rest"""
        super(CLog, self).__init__(prefix=None)
        self._initialised = False
        self._FORMAT = '$BOLD%(levelname)s$RESET - %(asctime)s - %(message)s'
        self.filehandler = 0
        self.streamhandler = 0
        self.streamhandler = 0
        self.streamformatter = 0
        self.fileformatter = 0
        self._logger = 0

    def init(self, logfile_name, level='info', stdout_log=True):
        """All the setup that is possible only after this module was imported."""
        logfile_name = logfile_name
        self.filehandler = logging.handlers.RotatingFileHandler(logfile_name,
                                                                maxBytes=1048576, backupCount=5)  # 1MB files
        if stdout_log:
            self.streamhandler = logging.StreamHandler(sys.stderr)
        else:
            self.streamhandler = logging.NullHandler()
        self.streamformatter = ColoredFormatter(formatter_message(self._FORMAT, True))
        self.fileformatter = ColoredFormatter(formatter_message(self._FORMAT, False))
        self.streamhandler.setFormatter(self.streamformatter)
        self.filehandler.setFormatter(self.fileformatter)
        self._logger = logging.getLogger('main')
        self._logger.addHandler(self.streamhandler)
        self._logger.addHandler(self.filehandler)
        try:
            self._logger.setLevel(loggingLevelMapping[level])
        except KeyError:
            self._logger.setLevel(logging.ERROR)
            self._logger.error('unknown log level {0} requested, defaulting to logging.ERROR'.format(level))

        self._initialised = True
        self._logger.info('Hazzy started')

    def getPluginLogger(self, name):
        return PluginLogger(self, name)


class PluginLogger(ILogger):
    """ILogger with prefix based on given plugin name.
    Shares the backend with its parent clog."""

    def __init__(self, clog, plugin):
        super(PluginLogger, self).__init__(prefix='PL {0}'.format(plugin))
        self._logger = clog._logger
        self._initialised = True
