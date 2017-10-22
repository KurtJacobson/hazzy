import os
from linuxcnc import ini

class DroType(enumerate):
    ABS = 0
    REL = 1
    DTG = 2

class Paths(enumerate):

    # Hazzy Paths
    HAZZYDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    MAINDIR = os.path.dirname(HAZZYDIR)

    UIDIR = os.path.join(HAZZYDIR, 'ui')
    MODULEDIR = os.path.join(HAZZYDIR, 'modules')
    STYLEDIR = os.path.join(HAZZYDIR, 'themes')


    # LinuxCNC Paths
    INI_FILE = os.environ['INI_FILE_NAME']
    CONFIGDIR = os.environ['CONFIG_DIR']
    NC_FILE_DIR = os.environ['LINUXCNC_NCFILES_DIR']
    TCLPATH = os.environ['LINUXCNC_TCL_DIR']

    ini = ini(INI_FILE)

    MACHINE_NAME = ini.find("EMC", "MACHINE") or "hazzy"

    LOG_FILE = ini.find("DISPLAY", "LOG_FILE_PATH") \
        or os.path.join(CONFIGDIR, MACHINE_NAME.replace(' ', '_') + '.log')

    PREF_FILE = ini.find("DISPLAY", "PREFERENCE_FILE_PATH") \
        or os.path.join(CONFIGDIR, MACHINE_NAME.replace(' ', '_') + '.pref')

    XML_FILE = ini.find("DISPLAY", "XML_FILE") \
        or os.path.join(CONFIGDIR, MACHINE_NAME.replace(' ', '_') + '.xml')

    OPEN_FILE = ini.find("DISPLAY", "OPEN_FILE") \
        or os.path.join(HAZZYDIR, "sim.hazzy/example_gcode/hazzy.ngc")
