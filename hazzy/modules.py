import os
import sys

HAZZYDIR = os.path.dirname(os.path.realpath(__file__))
MODULEDIR = os.path.realpath(os.path.join(HAZZYDIR, '..', 'plugins'))
print("The module directory is: {0}".format(MODULEDIR))
sys.path.insert(2, MODULEDIR)

from filechooser.filechooser import Filechooser
