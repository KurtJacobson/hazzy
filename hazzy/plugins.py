import os
import sys

HAZZYDIR = os.path.dirname(os.path.realpath(__file__))
PLUGINDIR = os.path.realpath(os.path.join(HAZZYDIR, '..', 'plugins'))
print("The plugin directory is: {0}".format(PLUGINDIR))
sys.path.insert(2, PLUGINDIR)

from filechooser.filechooser import Filechooser
