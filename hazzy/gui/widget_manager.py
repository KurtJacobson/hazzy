#!/usr/bin/env python

import os
import ast
import importlib

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk


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


    def get_widgets(self):
        pakages = os.listdir(WIDGET_DIR)
        for pakage in pakages:
            path = os.path.join(WIDGET_DIR, pakage, 'widget.info')
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
                self.widget_data[pakage] = info_dict
        return self.widget_data
