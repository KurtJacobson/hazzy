import os


class Paths(enumerate):

    # Path to TCL for external programs eg. halshow
    # TCLPATH = os.environ['LINUXCNC_TCL_DIR']  # unsused for now

    # Get actual paths so we can run from any location
    HAZZYDIR = os.path.dirname(os.path.realpath(__file__))
    MAINDIR = os.path.dirname(HAZZYDIR)

    UIDIR = os.path.join(HAZZYDIR, 'hazzy', 'ui')
    MODULEDIR = os.path.join(HAZZYDIR, 'hazzy', 'modules')
    STYLEDIR = os.path.join(HAZZYDIR, 'hazzy', 'themes')