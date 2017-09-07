import os


class Paths(enumerate):

    # Path to TCL for external programs eg. halshow
    # TCLPATH = os.environ['LINUXCNC_TCL_DIR']  # unsused for now

    # Get actual paths so we can run from any location
    HAZZYDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    MAINDIR = os.path.dirname(HAZZYDIR)

    CONFIGDIR = os.environ['CONFIG_DIR']

    UIDIR = os.path.join(HAZZYDIR, 'ui')
    MODULEDIR = os.path.join(HAZZYDIR, 'modules')
    STYLEDIR = os.path.join(HAZZYDIR, 'themes')

    # File Paths
    XML_FILE = os.path.join(CONFIGDIR, 'interface.xml')
    NC_FILE_DIR = os.environ['LINUXCNC_NCFILES_DIR']


