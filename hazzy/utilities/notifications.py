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
#   Desktop notification convenience functions.

# ToDo:
#   Since some notifications time out, and others don't the notification can
#   get out of order which can become confusing. Maybe make our own notification
#   system so we have more control.

# Note: 
#   Timeout = 0 is never time out
#   Timeout = -1 is default time out

import gi
gi.require_version('Notify', '0.7')

from gi.repository import Notify

Notify.init("hazzy")

def show_info(body, summary='INFO', timeout=2000):
    show(summary, body, 'dialog-information', timeout)

def show_warning(body, summary='WARNING!', timeout=3000):
    show(summary, body, 'dialog-warning', timeout)

def show_error(body, summary='ERROR!', timeout=5000):
    show(summary, body, 'dialog-error', timeout)

def show_question(body, summary='QUESTION?', timeout=5000):
    show(summary, body, 'dialog-question', timeout)

def show_success(body, summary='SUCCESS!', timeout=2000):
    show(summary, body, 'emblem-default', timeout)

def show(summary, body, icon_name='dialog-error', timeout=5000):
    notification = Notify.Notification(summary=summary,
                                        body=body,
                                        icon_name=icon_name)

    notification.set_timeout(timeout)
    notification.show()

def demo():
    show_info('This is just a information message.')
    show_warning('This is a warning message.')
    show_error('This is an error message.')
    show_question('Do you like this?')
    show_success('The demo completed successfully!')
if __name__ == '__main__':
    demo()
