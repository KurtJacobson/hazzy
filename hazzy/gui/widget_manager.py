#!/usr/bin/env python

import os
import ast
import importlib

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from utilities import logger

log = logger.get('HAZZY.WIDGET_MANAGER')

# Setup paths
PYDIR = os.path.abspath(os.path.dirname(__file__))
HAZZYDIR = os.path.abspath(os.path.join(PYDIR, '../..'))
WIDGET_DIR = os.path.join(HAZZYDIR, 'hazzy/modules')

class WidgetManager:

    def __init__(self):

        self.widget_data = {}
        self.widget_positions = {}
        self.get_widgets()


    def get_widget(self, pakage):

        info = self.widget_data[pakage]
        name = info.get('name')
        module = info.get('module')
        clas = info.get('class')
        size = info.get('size', [0, 0])

        module = importlib.import_module('.' + module, 'modules.' + pakage)
        widget = getattr(module, clas)

        return widget(), name, size

    def check_exist(self, package):
        info = self.widget_data.get(package)
        return bool(info)


    def get_widgets(self):
        categories = os.listdir(WIDGET_DIR)
        for category in categories:
            print category
            if not os.path.isdir(os.path.join(WIDGET_DIR, category)):
                print "not dir"
                continue
            packages = os.listdir(os.path.join(WIDGET_DIR, category))

            for package in packages:
                print package
                path = os.path.join(WIDGET_DIR, package, 'widget.info')
                info_dict = {}
                if os.path.exists(path):
                    with open(path, 'r') as fh:
                        lines = fh.readlines()
                    for line in lines:
                        if line.startswith('#'):
                            continue
                        key, value = line.split(':')
                        value = ast.literal_eval(value.strip())
                        info_dict[key] = value
                    self.widget_data[package] = info_dict
                
        return self.widget_data
