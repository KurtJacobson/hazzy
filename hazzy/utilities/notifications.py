#!/usr/bin/env python


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
