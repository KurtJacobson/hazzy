#!/usr/bin/env python

#   An attempt at a new UI for LinuxCNC that can be used
#   on a touch screen without any lost of functionality.
#   The code is written in python and glade and is almost a
#   complete rewrite, but was influenced mainly by Gmoccapy
#   and Touchy, with some code adapted from the HAL VCP widgets.

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


import traceback          # Needed to launch traceback errors
import hal                # Base hal class to react to hal signals
import gtk                # Base for pygtk widgets
import sys                # Handle system calls
import os                 # Needed to get the paths and directories
import pango              # Needed for font settings
import gladevcp.makepins  # To make HAL pins and set up updating for them
import linuxcnc           # To get our own error system
import gobject            # Needed to add the timer for periodic
import math

# Setup paths to files
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
INIFILE = sys.argv[2]                               # Path to .ini file
CONFIGDIR = os.path.dirname(INIFILE)                # Path to config dir

# Path to TCL for external programs eg. halshow
TCLPATH = os.environ['LINUXCNC_TCL_DIR']

# We use __file__ to get the file dir so we can run from any location
HAZZYDIR = os.path.dirname(os.path.realpath(__file__))
IMAGEDIR = os.path.join(HAZZYDIR, 'images')
MODULEDIR = os.path.join(HAZZYDIR, 'modules')
MAINDIR = os.path.dirname(HAZZYDIR)

# Set system path so we can find our own modules
if not HAZZYDIR in sys.path:
    sys.path.insert(1, HAZZYDIR)


# Set up logging
import logger
log = logger.get('HAZZY')

log.info("The hazzy directory is: ".format(HAZZYDIR))
log.info("The config dir is: ".format(CONFIGDIR))

# Now we have the path to our own modules so we can import them
import widgets                  # Norbert's module for geting objects
import preferences              # Handles the preferences
import getiniinfo               # Handles .ini file reading and value validation
import simpleeval               # Used to evaluate expressions in numeric entries


# Import modules
from modules.touchpads.keyboard import Keyboard
from modules.touchpads.touchpad import Touchpad
from modules.filechooser.filechooser import Filechooser
from modules.dialogs.dialogs import Dialogs, DialogTypes
from modules.gcodeview.gcodeview import GcodeView
from modules.hazzygremlin.hazzygremlin import HazzyGremlin



# Init error dialog
error_dialog = Dialogs(DialogTypes.ERROR)

# Throw up a dialog with debug info when an error is encountered
def excepthook(exc_type, exc_value, exc_traceback):

    try:
        w = app.widgets.window
    except KeyboardInterrupt:
        sys.exit(0)
    except NameError:
        w = None

    message = traceback.format_exception(exc_type, exc_value, exc_traceback)
    log.critical("".join(message))
    error_dialog.run("".join(message))

# Connect the except hook to the handler
sys.excepthook = excepthook


class Hazzy:

    def __init__(self):

        # Glade setup
        gladefile = os.path.join(IMAGEDIR, 'hazzy.glade')
        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        self.widgets = widgets.Widgets(self.builder)

        # Retrieve main window
        self.window = self.widgets.window

        # Components needed to communicate with hal and linuxcnc
        self.hal = hal.component('hazzy')
        self.command = linuxcnc.command()
        self.stat = linuxcnc.stat()
        self.error_channel = linuxcnc.error_channel()

        # Norbert's module to get information from the ini file
        self.get_ini_info = getiniinfo.GetIniInfo()

        # Module to get/set preferences
        pref_file = self.get_ini_info.get_preference_file_path()
        self.prefs = preferences.Preferences
        self.prefs.set_file_path(pref_file)

        # Module used to evaluate expressions in entries
        self.s = simpleeval.SimpleEval()

        # Hazzy Modules init
        self.gcode_view = GcodeView(preview=False)
        self.gcode_preview = GcodeView(preview=True)
        self.float_touchpad = Touchpad("float")
        self.int_touchpad = Touchpad("int")
        self.keyboard = Keyboard
        self.keyboard.set_parent(self.window)
        self.filechooser = Filechooser()
        self.yes_no_dialog = Dialogs(DialogTypes.YES_NO)
        self.error_dialog = Dialogs(DialogTypes.ERROR)

        # Get the tool table liststore
        self.tool_liststore = self.builder.get_object("tool_liststore")


# =========================================================
# BEGIN - HAL setup  
# =========================================================

        # Note: Pins/signals must be connected in the POSTGUI halfile

        self.hal.newpin('coolant', hal.HAL_BIT, hal.HAL_OUT)
        self.hal.newpin('error', hal.HAL_BIT, hal.HAL_OUT)
        panel = gladevcp.makepins.GladePanel(self.hal, gladefile, self.builder, None)

        self.hal.ready()


# =========================================================
# BEGIN - Get machine settings
# =========================================================

        self.dro_actual_pos = self.get_ini_info.get_position_feedback_actual()    
        self.no_force_homing = self.get_ini_info.get_no_force_homing()
        self.nc_file_path = self.get_ini_info.get_program_prefix()
        self.tool_table = self.get_ini_info.get_tool_table()
        # CYCLE_TIME = time, in ms, that display will sleep between polls
        # cycle_time = self.get_ini_info.get_cycle_time() # Defaults to 50ms
        gobject.timeout_add(75, self._fast_periodic)

        # Set the conversions used for changing the DRO units
        # Only convert linear axes (XYZUVW), use factor of unity for ABC
        if self.get_ini_info.get_machine_metric(): 
            # List of factors for converting from mm to inches
            self.conversion = [1.0/25.4]*3+[1]*3+[1.0/25.4]*3
            self.machine_units = 'mm'
        else:
            # List of factors for converting from inches to mm
            self.conversion = [25.4]*3+[1]*3+[25.4]*3
            self.machine_units = 'in'


# =========================================================
# BEGIN - Set initial toggle button states, and other values
# =========================================================

        # Constants
        self.axis_letters = ['X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W']
        self.inifile = linuxcnc.ini(INIFILE)

        # Define default button states
        self.cycle_start_button_state = 'start'
        self.hold_resume_button_state = 'inactive'
        self.is_pressed = {}

        self.task_state = None
        self.task_mode = None
        self.interp_state = None
        self.motion_mode = None

        self.new_error = False          # Used to know when to load error_flash.gif
        self.error_flash_timer = 0      # Slow_periodic cycles since error

        self.gremlin_mouse_mode = 2     # Current gremlin mouse btn mode

        self.display_units = 'in'
        self.start_line = 0             # Needed for start from line
        self.periodic_cycle_counter = 0 # Determine when to call slow_periodic()

        self.dro_has_focus = False      # To stop DRO update if user is trying to type into it
        self.mdi_has_focus = False      #

        self.current_preview_file = None
        self.surface_speed = ""
        self.chip_load = ""
        self.feed_override = ""
        self.spindle_override = ""
        self.rapid_override = ""
        self.spindle_speed = ""
        self.current_tool = ""
        self.motion_line = 0
        self.current_tool_data = [""]*5 + ["No Tool Loaded"]
        self.current_work_cord = ""     # Keep track of current work cord
        self.codes = []                 # Unformatted G codes + M codes to check if an update is required
        self.active_codes = []          # Formated G codes + M codes for display
        self.num_axes = 0               # Total number of Cartesian axes
        self.num_joints = 0             # Total number of joints
        self.axis_letter_list = []      # Axes used in the machine [X, Y, Z, B]
        self.axis_number_list = []      # Corresponding axis numbers [0, 1, 2, 4]
        self.joint_axis_dict = {}       # Joint axis correspondence
        self.homed_joints = []          # List of homed joints


# =========================================================
# BEGIN - Preferences
# =========================================================
        # If a preference file does not exist it will be created in the config dir

        # [FILE PATHS]
        self.nc_file_path = self.prefs.getpref("FILE PATHS", "DEFAULT_NC_DIR", self.nc_file_path, str)
        path = os.path.join(MAINDIR, "sim.hazzy/example_gcode/new file.ngc")
        self.new_program_template = self.prefs.getpref("FILE PATHS", "NEW_PROGRAM_TEMPLATE", path, str)

        # [FILE FILTERS]
        self.preview_ext = self.prefs.getpref("FILE FILTERS", "PREVIEW_EXT", [".ngc", ".txt", ".tap", ".nc"], str)

        # [JOGGING]
        self.allow_keyboard_jog = self.prefs.getpref("JOGGING", "USE_KEYBOARD", "YES")
        self.jog_velocity = self.prefs.getpref("JOGGING", "VELOCITY", 1, int)

        # [POP-UP KEYPAD]        
        self.keypad_on_mdi = self.prefs.getpref("POP-UP KEYPAD", "USE_ON_MDI", "YES")
        self.keypad_on_dro = self.prefs.getpref("POP-UP KEYPAD", "USE_ON_DRO", "YES")
        self.keypad_on_offsets = self.prefs.getpref("POP-UP KEYPAD", "USE_ON_OFFSETS", "YES")
        self.keypad_on_edit = self.prefs.getpref("POP-UP KEYPAD", "USE_ON_EDIT", "YES")

        # [FONTS]
        self.mdi_font = pango.FontDescription(self.prefs.getpref("FONTS", "MDI_FONT", 'dejavusans condensed 14', str))
        self.dro_font = pango.FontDescription(self.prefs.getpref("FONTS", "DRO_FONT", 'dejavusans condensed 16', str))
        self.abs_font = pango.FontDescription(self.prefs.getpref("FONTS", "ABS_FONT", 'dejavusans condensed 12', str))
        self.vel_font = pango.FontDescription(self.prefs.getpref("FONTS", "VEL_FONT", 'dejavusans condensed 14', str))
        self.label_font = pango.FontDescription(self.prefs.getpref("FONTS", "LABEL_FONT", 'NimbusSansL 10', str))

        # [POS DROs]
        self.in_dro_plcs = self.prefs.getpref("POS DROs", "IN_DEC_PLCS", 4, int)
        self.mm_dro_plcs = self.prefs.getpref("POS DROs", "MM_DEC_PLCS", 3, int)

        # [VEL DROs]
        self.in_vel_dec_plcs = self.prefs.getpref("VEL DROs", "IN_VEL_DEC_PLCS", 1, int)
        self.in_feed_dec_plcs = self.prefs.getpref("VEL DROs", "IN_FEED_DEC_PLCS", 1, int)
        self.in_g95_dec_plcs = self.prefs.getpref("VEL DROs", "IN_G95_DEC_PLCS", 3, int)
        self.mm_vel_dec_plcs = self.prefs.getpref("VEL DROs", "MM_VEL_DEC_PLCS", 2, int)
        self.mm_feed_dec_plcs = self.prefs.getpref("VEL DROs", "MM_FEED_DEC_PLCS", 0, int)
        self.mm_g95_dec_plcs = self.prefs.getpref("VEL DROs", "MM_G95_DEC_PLCS", 0, int)

        # [GCODE VIEW]
        self.style_scheme_file = self.prefs.getpref("GCODE VIEW", "STYLE_SCHEME_FILE", 'GCode.xml', str)
        self.style_scheme_name = self.prefs.getpref("GCODE VIEW", "STYLE_SCHEME_NAME", 'gcode', str)
        self.lang_spec_file = self.prefs.getpref("GCODE VIEW", "LANG_SPEC_FILE", 'GCode.lang', str)
        self.lang_spec_name = self.prefs.getpref("GCODE VIEW", "LANG_SPEC_NAME", 'gcode', str)

        # [MACHINE DEFAULTS]
        self.df_feed = self.prefs.getpref("MACHINE DEFAULTS", "DF_SPEED", 10, int)
        self.df_speed = self.prefs.getpref("MACHINE DEFAULTS", "DF_FEED", 300, int)


# =========================================================
# BEGIN - Do initial updates
# =========================================================        

        # Initial poll so all is up to date
        self.stat.poll()
        self.error_channel.poll()

        # Initialize settings
        self._init_window()
        self._update_machine_state() 
        self._update_machine_mode()
        self._update_interp_state()
        self._update_motion_mode()
        self._get_axis_list()

# =========================================================
# BEGIN - Appearance initialization
# =========================================================

        # Set the fonts for the labels in the spindle display area
        '''
        for i in range(1, 7):
            label = self.widgets["spindle_label_%s" % i]
            label.modify_font(pango.FontDescription('FreeSans 11'))
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('#262626'))
        '''

        # List of labels in the spindle display area
        spindle_dro_list = ['surface_speed_label',
                            'chip_load_label',
                            'active_feed_label',
                            'actual_feed_label',
                            'current_vel_label']

        '''
        for i in spindle_dro_list:
            label = self.widgets[i]
            label.modify_font(pango.FontDescription('dejavusans condensed 14'))
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
        '''

        # Initialize MDI entry
        self.widgets.mdi_entry.modify_font(self.mdi_font)
        self.widgets.mdi_entry.set_text("MDI:")
        self.widgets.tool_number_entry.modify_font(self.dro_font)
        self.widgets.spindle_speed_entry.modify_font(self.dro_font)

        # Axis DROs TODO Move to a DRO init section?
        # Hide extra DROs
        count = 4
        while count >= self.num_axes:
            self.widgets['dro_{0}'.format(count)].hide()
            self.widgets['dtg_{0}'.format(count)].hide()
            self.widgets['abs_{0}'.format(count)].hide()
            self.widgets['dro_label_{0}'.format(count)].hide()
            count -= 1

        # Dict of DRO GtkEntry objects and there corresponding axes
        self.rel_dro_dict = {}
        for i in range(self.num_axes):
            axis = self.axis_number_list[i]
            self.rel_dro_dict[axis] = self.widgets['dro_{0}'.format(i)]

        # Set DRO fonts/colors
        for axis, dro in self.rel_dro_dict.iteritems():
            dro.modify_font(self.dro_font)
            dro.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('black'))

        self.dtg_dro_dict = {}
        for i in range(self.num_axes):
            axis = self.axis_number_list[i]
            self.dtg_dro_dict[axis] = self.widgets['dtg_{0}'.format(i)]

        # Set DTG DRO fonts/colors.
        for axis, dro in self.dtg_dro_dict.iteritems():
            dro.modify_font(self.dro_font)
            dro.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))

        self.abs_dro_dict = {}
        for i in range(self.num_axes):
            axis = self.axis_number_list[i]
            self.abs_dro_dict[axis] = self.widgets['abs_{0}'.format(i)]

        # Set ABS DRO fonts/colors 
        for axis, dro in self.abs_dro_dict.iteritems():
            dro.modify_font(self.abs_font)
            if not self.no_force_homing:
                dro.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('red'))

        self.abs_dro_eventboxes_dict = {}
        for i in range(self.num_axes):
            axis = self.axis_number_list[i]
            self.abs_dro_eventboxes_dict[axis] = self.widgets['abs_eventbox_{0}'.format(i)]

        # Set DRO axis labels
        for i in range(self.num_axes):
            label = self.widgets['dro_label_{0}'.format(i)]
            label.modify_font(self.mdi_font)
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('#333333'))
            label.set_text(self.axis_letter_list[i])

        for i in ['rel_dro_label', 'dtg_dro_label', 'abs_dro_label', 'spindle_rpm_label']:
            label = self.widgets[i]
            label.modify_font(pango.FontDescription('dejavusans condensed 12'))
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('#333333'))

        # Joint DROs
        # Hide extra DROs
        count = 4
        while count >= self.num_joints:
            self.widgets['joint_label_{0}'.format(count)].hide()
            self.widgets['joint_pos_{0}'.format(count)].hide()
            self.widgets['joint_status_{0}'.format(count)].hide()
            self.widgets['joint_home_btn_{0}'.format(count)].hide()
            count -= 1

        for joint in range(self.num_joints):
            axis = self.jnum_aletter_dict[joint]
            label = self.widgets['joint_label_{0}'.format(joint)]
            label.set_text("{0} ({1})".format(joint, axis))

        self.joint_pos_dro_list = []
        for joint in range(self.num_joints):
            dro = self.widgets['joint_pos_{0}'.format(joint)]
            self.joint_pos_dro_list.append(dro)

        self.joint_status_label_list = []
        for joint in range(self.num_joints):
            label = self.widgets['joint_status_{0}'.format(joint)]
            self.joint_status_label_list.append(label)

        self.home_joint_btn_list = []
        for joint in range(self.num_joints):
            btn = self.widgets['joint_home_btn_{0}'.format(joint)]
            self.home_joint_btn_list.append(btn)

        # self.widgets.spindle_text.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
        # self.widgets.spindle_text.modify_font(pango.FontDescription('FreeSans condensed  14'))
        self.set_animation('reset_image', 'reset.gif')  # Set the initial animated reset image

        # Last things to init
        self._init_file_chooser()
        self._init_gremlin()
        self._init_gcode_view()
        self._init_gcode_preview()
        self.load_tool_table(self.tool_table)

        # Finally, show the window 
        self.window.show()

        # Open file specified in INI [DISPLY] OPEN_FILE
        self.load_gcode_file(self.get_ini_info.get_open_file())

# =========================================================
# BEGIN - Periodic status checking and updating
# =========================================================

    # Called at ini [DISPLAY] CYCLE_TIME to update readouts
    def _fast_periodic(self): # Called at 50ms default

        # Check for messages
        message = self.error_channel.poll()
        if message:
            self._show_message(message)

        self.stat.poll()

        if self.stat.motion_mode == linuxcnc.TRAJ_MODE_FREE or not self.is_homed():
            self._update_joint_dros()
            if self.widgets.dro_notebook.get_current_page() != 0:
                self.widgets.dro_notebook.set_current_page(0)
                self.window.set_focus(None)
        else:
            self._update_axis_dros()
            if self.widgets.dro_notebook.get_current_page() != 1:
                self.widgets.dro_notebook.set_current_page(1)
                self.window.set_focus(None)

        self._update_override_labels()
        self._update_spindle_speed_label()
        self._updade_dro_status()

        # Call _slow_periodic() every 5 cycles of _fast_periodic()
        self.periodic_cycle_counter += 1
        if self.periodic_cycle_counter >= 5:
            self._slow_periodic()
            self.periodic_cycle_counter = 0

        # Keep the timer running
        # If there is an error in here the timer will stop
        return True

    # Called every 5 fast_periodic cycles to update slower moving readouts and button states
    def _slow_periodic(self):

        # Check for messages
        # message = self.error_channel.poll()
        # if message:
        #   self._show_message(message)

        # Update motion line
        if self.stat.motion_line != self.motion_line:
            self.motion_line = self.stat.motion_line
            self.gcode_view.highlight_line(self.motion_line, 'motion')

        # Update work cord if it has changed
        if self.current_work_cord != self.stat.g5x_index:
            self.refresh_gremlin()
            self._update_work_cord()

        # Update G/M codes if they have changed    
        if self.codes != self.stat.gcodes + self.stat.mcodes:
            self._update_active_codes()

        # Update LCNC state if it has changed
        if self.task_state != self.stat.task_state:
            self._update_machine_state()

        # Update LCNC mode if it has changed
        if self.task_mode != self.stat.task_mode:
            self._update_machine_mode()

        # Update interpreter state if it has changed
        if self.interp_state != self.stat.interp_state:
            self._update_interp_state()

        if self.motion_mode != self.stat.motion_mode:
            self._update_motion_mode()

        # Update homed joints
        if tuple(self.homed_joints) != self.stat.homed:
            self._update_homing_status()

        # Update current tool data if it has changed
        if self.current_tool != self.stat.tool_in_spindle:
            self._update_current_tool_data()

        # self.stat.program_units returns 1 for inch, 2 for mm and 3 for cm  
        if self.stat.program_units != 1:
            if self.display_units != 'mm':
                self.display_units = 'mm'
                self.gremlin.set_display_units('mm')
        else:
            if self.display_units != 'in':
                self.display_units = 'in'
                self.gremlin.set_display_units('in')

        # Update velocity DROs
        self._update_vel()

        # Update cutting parameter labels
        self._update_cutting_parameters()

        # Update button states
        self._update_cycle_start_stop_button_state()
        self._update_hold_resume_button_state()

        # Update opstop status
        if self.stat.optional_stop != self.widgets.opstop.get_active():
            self.widgets.opstop.set_active(self.stat.optional_stop)

        # Update opskip status
        if self.stat.block_delete != self.widgets.opskip.get_active():
            self.widgets.opskip.set_active(self.stat.block_delete)

        # If new error, flash message border red for 2s
        if self.new_error:
            self.error_flash_timer += 1
            if self.error_flash_timer >= 4:
                self.set_animation('error_image', None)
                self.new_error = False
                self.error_flash_timer = 0

        if not self.is_moving():
            self.set_mode(linuxcnc.MODE_MANUAL)


# =========================================================
# BEGIN - Info/Error message display 
# =========================================================

    # Format Info & Error messages and display at bottom of screen, terminal
    def _show_message(self, message):
        kind, text = message # Unpack

        if "joint" in text:
            # Replace "joint N" with "L axis"
            for axis in self.axis_letter_list:
                joint = 'XYZABCUVWS'.index(axis)
                text = text.replace("joint {0}".format(joint), "{0} axis".format(axis))
            text = text.replace("joint -1", "all axes")

        if text == "" or text is None:
            text = "Unknown error!"

        # Print to terminal and display at bottom of screen
        if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR, 'ERROR'):
            if kind != "ERROR":
                log.error(text)
            kind = "ERROR"
            color = 'red'
            self.hal['error'] = True
            # flash the border in the message area
            self.set_animation('error_image', 'error_flash.gif')
            self.new_error = True
        elif kind in (linuxcnc.NML_TEXT, linuxcnc.OPERATOR_TEXT, 'INFO'):
            if kind != "INFO":
                log.info(text)
            kind = "INFO"
            color = 'blue'
        elif kind in (linuxcnc.NML_DISPLAY, linuxcnc.OPERATOR_DISPLAY, 'MSG'):
            if kind != "MSG":
                log.info(text)
            kind = "MSG"
            color = 'blue'
        elif kind == 'WARN':
            kind = "WARNING"
            color = 'orange'
        else:
            kind == "ERROR"
            color = 'red'
            log.error(text)

        msg = '<span size=\"11000\" weight=\"bold\" foreground=\"{0}\">{1}:' \
        '</span> {2}'.format(color, kind, text)
        self.widgets.message_label.set_markup(msg)


# =========================================================
# BEGIN - Main control panel button handlers
# =========================================================

    # Toggle the cycle start/stop button state and set the corresponding image
    def on_cycle_start_pressed(self, widget, data=None):
        if self.cycle_start_button_state == 'start':
            # FIXME Check for no force homing in INI
            if self.is_homed() and self.stat.file != "" and self.widgets.notebook.get_current_page() == 0:
                self.set_mode(linuxcnc.MODE_AUTO)
                self.command.auto(linuxcnc.AUTO_RUN, self.start_line)
                self.set_cycle_start_button_state('stop')
                # self.widgets.notebook.set_current_page(0)
            elif not self.is_homed():
                log.error("Can't run program when not homed")
                self._show_message(["ERROR", "Can't run program when not homed"])
            elif self.stat.file == "":
                log.error("Can't run program, no gcode file loaded")
                self._show_message(["ERROR", "Can't run program, no gcode file loaded"])
            elif self.widgets.notebook.get_current_page() != 0:
                log.error("Must be on main page to run program")
                self._show_message(["ERROR", "Must be on main page to run program"])

        elif self.cycle_start_button_state == 'stop':
            self.command.abort()
            self.start_line = 0

    def _update_cycle_start_stop_button_state(self):
        if self.is_moving():
            self.set_cycle_start_button_state('stop')
        else:
            self.set_cycle_start_button_state('start')

    def set_cycle_start_button_state(self, state):
        if state == 'start' and state != self.cycle_start_button_state:
            self.set_image('cycle_start_image', 'start.png')
            self.cycle_start_button_state = 'start'
        elif state == 'stop' and state != self.cycle_start_button_state:
            self.set_image('cycle_start_image', 'stop.png')
            self.cycle_start_button_state = 'stop'

    def on_feed_hold_pressed(self, widget, data=None):
        if self.hold_resume_button_state == 'hold':
            self.command.auto(linuxcnc.AUTO_PAUSE)
        elif self.hold_resume_button_state == 'resume':
            self.command.auto(linuxcnc.AUTO_RESUME)

    def _update_hold_resume_button_state(self):
        if self.is_moving() and not self.stat.paused:
            self.set_hold_resume_button_state('hold')
        elif self.stat.paused:
            self.set_hold_resume_button_state('resume')
        else:
            self.set_hold_resume_button_state('disabled')

    def set_hold_resume_button_state(self, state):
        if state == 'hold' and state != self.hold_resume_button_state:
            self.set_image('feed_hold_image', 'pause.png')
            self.hold_resume_button_state = 'hold'
        elif state == 'resume' and state != self.hold_resume_button_state:
            self.set_image('feed_hold_image', 'resume.png')
            self.hold_resume_button_state = 'resume'
        elif state == 'disabled' and state != self.hold_resume_button_state:
            self.set_image('feed_hold_image', 'pause.png')
            self.hold_resume_button_state = 'disabled'

    # Toggle the reset button state and set the corresponding image
    def on_reset_pressed(self, widget, data=None):

        if self.stat.task_state != linuxcnc.STATE_ON:
            if self.stat.task_state != linuxcnc.STATE_ESTOP_RESET:
                log.debug("Reseting E-stop")
                self.set_state(linuxcnc.STATE_ESTOP_RESET)

                # Check if the machine actually reset
                self.stat.poll()
                if self.stat.task_state != linuxcnc.STATE_ESTOP_RESET and self.stat.task_state != linuxcnc.STATE_ON :
                    log.debug("Failed to bring machine out of E-stop")
                    return

            # Turn on after reset
            if self.stat.task_state != linuxcnc.STATE_ON:
                log.debug("Turning machine on")
                self.set_state(linuxcnc.STATE_ON)
                self.set_image('reset_image', 'reset.png')

        else:
            if self.is_moving():
                self.command.abort()
            if self.is_homed():
                self.issue_mdi('M30')
                self.gcode_view.set_line_number(1)
                self.gremlin.clear_live_plotter()
                self.gremlin.set_view('z')
            self.set_mode(linuxcnc.MODE_MANUAL)


    def on_abs_label_clicked(self, widget, data=None):
        # Home all
        self.home_joint(-1)

    def on_abs_dro_clicked(self, widget, data=None):
        # Make sure we are in manual mode  
        self.set_mode(linuxcnc.MODE_MANUAL)
        # Look up the axis from the GTK object 
        for anum, eventbox in self.abs_dro_eventboxes_dict.iteritems():
            if eventbox == widget:
                aletter = self.axis_letters[anum]
                break
        if aletter in self.aletter_jnum_dict:
            jnum = self.aletter_jnum_dict[aletter]
        else:
            aletter += "0" 
            jnum = self.aletter_jnum_dict[aletter]
        log.debug("Attempting to home Axis {0} --> Joint {1}".format(aletter, jnum))
        self.home_joint(jnum)

    # New handlers for btns in Joint DRO page, might get rid of above handlers  
    def on_home_all_clicked(self, widget, data=None):
        self.home_joint(-1)
    
    def on_home_joint_clicked(self, widget, data=None):
        jnum = self.home_joint_btn_list.index(widget)
        self.home_joint(jnum)

    def on_exit_program_clicked(self, widget, data=None):
        message = "Are you sure you want \n to close LinuxCNC?"
        exit_hazzy = self.yes_no_dialog.run(message)
        if exit_hazzy:
            self.close_window()

    # =========================================================
    # Main panel CheckBox handlers
    # Have to use pressed for these as clicked is emited on
    # set_active() in the update function in slow_periodic

    def on_opstop_pressed(self, widget, data= None):
        if self.stat.optional_stop == 0:
            self.command.set_optional_stop(1)
            log.debug("Setting opstop ON")
        else:
            self.command.set_optional_stop(0)
            log.debug("Setting opstop OFF")

    def on_opskip_pressed(self, widget, data= None):
        if self.stat.block_delete == 0:
            self.command.set_block_delete(1)
            log.debug("Setting opskip ON")
        else:
            self.command.set_block_delete(0)
            log.debug("Setting opskip OFF")

    def on_step_clicked(self, widget, data=None):
        pass

    # =========================================================
    # DRO entry handlers

    def on_dro_gets_focus(self, widget, event):
        if not self.dro_has_focus:
            widget.select_region(0, -1)
            self.dro_has_focus = True
        if self.keypad_on_dro:
            self.float_touchpad.show(widget, self.display_units)

    def on_dro_loses_focus(self, widget, data=None):
        self.dro_has_focus = False
        widget.select_region(-1, -1)
        self.window.set_focus(None)

    def on_dro_key_press_event(self, widget, event, data=None):
        if event.keyval == gtk.keysyms.Escape:
            self.dro_has_focus = False
            self.window.set_focus(None)

    def on_dro_activate(self, widget):
        # Look up the axis from the GTK object 
        for axis_number, dro in self.rel_dro_dict.iteritems():
            if dro == widget:
                aletter = self.axis_letters[axis_number]
                break

        factor = 1
        entry = widget.get_text().lower()
        if "in" in entry or '"' in entry:
            entry = entry.replace("in", "").replace('"', "")
            if self.stat.program_units != 1:
                factor = 25.4
        elif "mm" in entry:
            entry = entry.replace("mm", "")
            if self.stat.program_units != 2:
                factor = 1/25.4
        try:
            val = self.s.eval(entry) * factor
            self.set_work_offset(aletter, val)
        except (SyntaxError, simpleeval.NameNotDefined):
            msg = "{0} axis DRO entry '{1}' is not valid".format(aletter, entry)
            log.error(msg)
            self._show_message(["ERROR", msg])
        except Exception as e:
            log.exception(e)
            msg = "{0} axis DRO entry error, see log for details".format(aletter)
            self._show_message(["ERROR", msg])

        self.window.set_focus(None)

    def on_int_dro_gets_focus(self, widget, event):
        widget.select_region(0, -1)
        if self.keypad_on_dro:
            self.int_touchpad.show(widget)

    def on_tool_number_entry_activate(self, widget):
        tnum = widget.get_text()
        try:
            tnum = int(tnum)
            self.issue_mdi("M6 T%s G43" % tnum)
        except:
            msg = '"{0}" is not a valid tool number'.format(tnum)
            log.error(msg)
            self._show_message(["ERROR", msg])

        widget.set_text(str(self.current_tool))
        self.window.set_focus(None)

    def on_spindle_speed_entry_activate(self, widget):
        speed = widget.get_text()
        try:
            speed = float(speed) 
            self.issue_mdi("S%s" % speed)
        except:
            msg = '"{}" is not a valid spindle speed'.format(speed)
            log.error(msg)
            self._show_message(["ERROR", msg])
        self.window.set_focus(None)

    # =========================================================
    # MDI entry handlers

    def on_mdi_entry_gets_focus(self, widget, event):
        # if self.dro_is_locked:
        #   self.window.set_focus(None)
        #   return
        if not self.mdi_has_focus:  # Keep from clearing entry on cursor placed
            self.widgets.mdi_entry.set_text("")
            self.mdi_has_focus = True
        if self.keypad_on_mdi:
            self.keyboard.show(widget)

    def on_mdi_entry_changed(self, widget, data=None):
        # Convert MDI entry text to UPPERCASE
        self.widgets.mdi_entry.set_text(widget.get_text().upper())

    def on_mdi_entry_loses_focus(self, widget, data=None):
        self.widgets.mdi_entry.set_text("MDI:")
        self.window.set_focus(None)
        self.mdi_has_focus = False

    def on_mdi_entry_key_press_event(self, widget, event): 
        if event.keyval == gtk.keysyms.Escape:
            self.window.set_focus(None)

    def on_mdi_entry_activate(self, widget):
        cmd = self.widgets.mdi_entry.get_text()
        if len(cmd) == 0:
            self.window.set_focus(None)
        else:
            self.issue_mdi(cmd)
            # Set button to 'stop' so can kill MDI motion if need be
            self.set_cycle_start_button_state('stop')
            self.window.set_focus(None)

    def on_button1_clicked(self, widget, data=None):
        self.gremlin.expose()

    def on_redraw_clicked(self, widget, data=None):
        self.gremlin.expose()
        #self.gremlin.load()


# =========================================================
# BEGIN - [Main] notebook page button handlers
# =========================================================

    def _init_gcode_view(self):
        self.widgets['gcode_view'].add(self.gcode_view.gtksourceview)

    def _init_gremlin(self):
        w, h = self.widgets.grembox.get_size_request()
        self.gremlin = HazzyGremlin(self.inifile, w, h)
        self.widgets.grembox.add(self.gremlin.gremlin_view)
        self.widgets.grembox.show_all()

        self.gremlin.set_view('z')
        self.gremlin.mouse_btn_mode = 2
        #self.gremlin.set_display_units(self.machine_units)
        self.gremlin.connect('gcode-error', self.on_gremlin_gcode_error)
        self.gremlin.connect('line-clicked', self.on_gremlin_line_clicked)
        self.gremlin.connect('loading_progress', self.on_gremlin_loading_progress_changed)
        self.gremlin.use_commanded = not self.dro_actual_pos

    def on_gremlin_gcode_error(self, widget, fname, lnum, text):
        msg = "{2} near line {1} of '{0}'".format(fname, lnum, text)
        self._show_message(["ERROR", msg])
        self.gcode_view.highlight_error_line(lnum)

    # Highlight code line for selected line in gremlin
    def on_gremlin_line_clicked(self, widget, line):
        self.gcode_view.highlight_line(line, 'selected')

    def on_gremlin_loading_progress_changed(self, widget, percent):
        #print "Generating preview: {}%".format(percent)
        pass

    def refresh_gremlin(self):
        # Switch modes to cause an interp sync
        self.set_mode(linuxcnc.MODE_MANUAL)
        self.set_mode(linuxcnc.MODE_MDI)
        self.gremlin.clear_live_plotter()
        self.gremlin.load()

# =========================================================
# BEGIN - [File] notebook page button handlers
# =========================================================

    def _init_file_chooser(self):

        # Add filechooser
        filechooser_widget = self.filechooser.get_filechooser_widget()
        self.widgets['filechooser_box'].add(filechooser_widget)

        self.filechooser.connect('file-activated', self.on_file_activated)
        self.filechooser.connect('selection-changed', self.on_file_selection_changed)
        self.filechooser.connect('filename-editing-started', 
                                    self.on_file_name_editing_started)
        self.filechooser.connect('button-release-event', 
                                    self.on_filechooser_button_release_event)
        self.filechooser.connect('error', self.on_filechooser_error)

        path = os.path.expanduser(self.nc_file_path)
        if not os.path.isdir(path):
            msg = "Path given in [DISPLAY] PROGRAM_PREFIX in INI is not valid"
            log.warning(msg)
            self._show_message(['WARN', msg])
            path = os.path.expanduser('~/linuxcnc/nc_files')  # Good guess!!

        self.filechooser.add_bookmark(path)
        self.filechooser.set_current_folder(path)

        # Add file filters
        self.filechooser.add_filter('all', ['*'])
        exts = self.get_ini_info.get_file_ext()
        self.filechooser.add_filter('gcode', exts)
        self.filechooser.set_filter('gcode')

    # Connect main message system to filechooser error signal
    def on_filechooser_error(self, widget, kind, text):
        self._show_message([kind, text])

    # To filter or not to filter, that is the question
    def on_filter_ngc_chk_toggled(self, widget, data=None):
        if self.widgets.filter_ngc_chk.get_active():
            self.filechooser.set_filter('gcode')
        else:
            self.filechooser.set_filter('all')

    # Change button label if a file or folder is selected
    def on_file_selection_changed(self, widget, fpath):
        if os.path.isfile(fpath):
            self.widgets.load_gcode.set_label("Load Gcode")
            if not self.gcode_preview.buf.get_modified():  # If not modified we can load file
                self.load_gcode_preview(fpath)    # Preview/edit in sourceview
        elif os.path.isdir(fpath):
            self.widgets.load_gcode.set_label("Open Folder")
            if not self.gcode_preview.buf.get_modified():
                self.load_gcode_preview(None)     # Clear the preview

    # If file has been edited ask if should save before reloading preview
    # Need to do this on release or the popup gets the mouse up and we are stuck in drag
    def on_filechooser_button_release_event(self, widget, data=None):
        fname = self.filechooser.get_path_at_cursor()
        if self.current_preview_file == fname:
            return
        if self.gcode_preview.get_modified():
            if self.current_preview_file is None:
                pass  # TODO Add save-as pop-up here
            else:
                name = os.path.split(self.current_preview_file)[1]
                message = ("Save changes to: \n" + name)
                save_changes = self.yes_no_dialog.run(message)
                if save_changes:
                    self.gcode_preview.save(self.current_preview_file)
                else:
                    self.gcode_preview.set_modified(False)
        if fname is not None:
            if os.path.isfile(fname):
                self.load_gcode_preview(fname)    # Preview/edit in sourceview
            elif os.path.isdir(fname):
                self.load_gcode_preview()         # Clear sourceview

    # Load file on activate in file chooser, better for mouse users
    def on_file_activated(self, widget, fpath):
        self.load_gcode_file(fpath)

    # Load file on "Load Gcode" button clicked, better for touchscreen users
    def on_load_gcode_clicked(self, widget, data=None):
        fpath = self.filechooser.get_path_at_cursor()
        if fpath is not None:
            if os.path.isfile(fpath):
                self.load_gcode_file(fpath)
            elif os.path.isdir(fpath):
                self.filechooser.set_current_folder(fpath)

    def load_gcode_file(self, fname):
        self.widgets.notebook.set_current_page(0)
        if self.stat.file != "":
            self.set_mode(linuxcnc.MODE_MDI)
            self.set_mode(linuxcnc.MODE_AUTO)
        self.gcode_view.load_file(fname)
        self.command.program_open(fname)
        self.widgets.gcode_file_label.set_text(fname)
        self.gremlin.load()
        log.debug("NGC file loaded: {0}".format(fname))

    def on_file_name_editing_started(self, widget, entry):
        if self.keypad_on_edit:
            self.keyboard.show(entry, True)

    def on_cut_clicked(self, widget, data=None):
        if self.filechooser.cut_selected():
            self.builder.get_object('paste').set_sensitive(True)

    def on_copy_clicked(self, widget, data=None):
        if self.filechooser.copy_selected():
            self.builder.get_object('paste').set_sensitive(True)

    def on_paste_clicked(self, widget, data=None):
        if self.filechooser.paste():
            self.builder.get_object('paste').set_sensitive(False)

    def on_delete_clicked(self, widget, data=None):
        self.filechooser.delete_selected()

    def on_save_as_clicked(self, widget, data=None):
        self.filechooser.save_as()

    def on_new_folder_clicked(self, widget, data=None):
        self.filechooser.new_folder()

    def on_save_file_clicked(self, widget, data=None):
        self.gcode_preview.save(self.current_preview_file)

    # G-code preview
    def _init_gcode_preview(self):
        self.widgets['gcode_preview'].add(self.gcode_preview.gtksourceview)

    def load_gcode_preview(self, fn=None):
        self.current_preview_file = fn
        self.gcode_preview.load_file(fn)


# =========================================================
# BEGIN - [Tool] notebook page handlers
# =========================================================

    # Parse and load tool table into the treeview
    # More or less copied from Chris Morley's GladeVcp tooledit widget
    def load_tool_table(self, fn = None):
        # If no valid tool table given
        if fn is None:
            fn = self.tool_table
        if not os.path.exists(fn):
            log.warning("Tool table does not exist")
            return
        self.tool_liststore.clear()  # Clear any existing data
        log.debug("Loading tool table: {0}".format(fn))
        with open(fn, "r") as tf:
            tool_table = tf.readlines()

        self.toolinfo = []  # TODO move to __init__
        for line in tool_table:
            # Separate tool data from comments
            comment = ''
            index = line.find(";")  # Find comment start index
            if index == -1:  # Delimiter ';' is missing, so no comments
                line = line.rstrip("\n")
            else:
                comment = (line[index+1:]).rstrip("\n")
                line = line[0:index].rstrip()
            array = [False, 1, 1, '0', '0', comment, 'white']
            # search beginning of each word for keyword letters
            # offset 0 is the checkbox so ignore it
            # if i = ';' that is the comment and we have already added it
            # offset 1 and 2 are integers the rest floats
            for offset, i in enumerate(['S', 'T', 'P', 'D', 'Z', ';']):
                if offset == 0 or i == ';':
                    continue
                for word in line.split():
                    if word.startswith(i):
                        if offset in(1, 2):
                            try:
                                array[offset] = int(word.lstrip(i))
                            except ValueError:
                                msg = 'Error reading tool table, can\'t convert "{0}" to integer in {1}' \
                                    .format(word.lstrip(i), line)
                                log.error(msg)
                                self._show_message(["ERROR", msg])
                        else:
                            try:
                                array[offset] = "%.4f" % float(word.lstrip(i))
                            except ValueError:
                                msg = 'Error reading tool table, can\'t convert "{0}" to float in {1}' \
                                    .format(word.lstrip(i), line)
                                log.error(msg)
                                self._show_message(["ERROR", msg])
                        break

            # Add array to liststore
            self.add_tool(array)

    # Save tool table
    # More or less copied from Chris Morley's GladeVcp tooledit widget
    def save_tool_table(self, fn=None):
        if fn is None:
            fn = self.tool_table
        if fn is None:
            return
        log.debug("Saving tool table as: {0}".format(fn))
        fn = open(fn, "w")
        for row in self.tool_liststore:
            values = [value for value in row]
            line = ""
            for num,i in enumerate(values):
                if num in (0, 6):
                    continue
                elif num in (1, 2):  # tool# pocket#
                    line = line + "%s%d " % (['S', 'T', 'P', 'D', 'Z', ';'][num], i)
                else:
                    line = line + "%s%s " % (['S', 'T', 'P', 'D', 'Z', ';'][num], i.strip())
            # Write line to file
            fn.write(line + "\n")
        # Theses lines make sure the OS doesn't cache the data so that
        # linuxcnc will actually load the updated tool table
        fn.flush()
        os.fsync(fn.fileno())
        linuxcnc.command().load_tool_table()

    def add_tool(self, data=None):
        self.tool_liststore.append(data)

    def get_selected_tools(self):
        model = self.tool_liststore
        tools = []
        for row in range(len(model)):
            if model[row][0] == 1:
                tools.append(int(model[row][1]))
        return tools

    def on_delete_selected_clicked(self, widget):
        model = self.tool_liststore
        rows = []
        for row in range(len(model)):
            if model[row][0] == 1:
                rows.append(row)
        rows.reverse()  # So we don't invalidate iters
        for row in rows:
            model.remove(model.get_iter(row))

    def on_change_to_selected_tool_clicked(self, widget, data=None):
        selected = self.get_selected_tools()
        if len(selected) == 1:
            tool_num = selected[0]
            self.issue_mdi('M6 T{0} G43'.format(tool_num))
        else:
            num = len(selected)
            msg = "{0} tools selected, you must select exactly one".format(num)
            log.error(msg)
            self._show_message(["ERROR", msg])

    def on_add_tool_clicked(self, widget, data=None):
        num = len(self.tool_liststore) + 1
        array = [0, num, num, '0.0000', '0.0000', 'New Tool', 'white']
        self.add_tool(array)

    def on_load_tool_table_clicked(self, widget, data=None):
        self.load_tool_table()

    def on_save_tool_table_clicked(self, widget, data=None):
        self.save_tool_table()

    def on_tool_num_edited(self, widget, path, new_text):
        try:
            new_int = int(new_text)
            self.tool_liststore[path][1] = new_int
            self.tool_liststore[path][2] = new_int
        except ValueError:
            msg = '"{0}" is not a valid tool number'.format(new_text)
            log.error(msg)
            self._show_message(["ERROR", msg])

    def on_tool_pocket_edited(self, widget, path, new_text):
        try:
            new_int = int(new_text)
            self.tool_liststore[path][2] = new_int
        except ValueError:
            msg = '"{0}" is not a valid tool pocket'.format(new_text)
            log.error(msg)
            self._show_message(["ERROR", msg])

    def on_tool_dia_edited(self, widget, path, new_text):
        try:
            num = self.eval(new_text)
            self.tool_liststore[path][3] = "{:.4f}".format(float(num))
        except:
            msg = '"{0}" does not evaluate to a valid tool diameter'.format(new_text)
            log.error(msg)
            self._show_message(["ERROR", msg])

    def on_z_offset_edited(self, widget, path, new_text):
        try:
            num = self.eval(new_text)
            self.tool_liststore[path][4] = "{:.4f}".format(float(num))
        except:
            msg = '"{0}" does not evaluate to a valid tool length'.format(new_text)
            log.error(msg)
            self._show_message(["ERROR", msg])

    def on_tool_remark_edited(self, widget, path, new_text):
        self.tool_liststore[path][5] =  new_text

    # Popup int numpad on int edit
    def on_int_editing_started(self, renderer, entry, row):
        if self.keypad_on_offsets:
            self.int_touchpad.show(entry)

    # Popup float numpad on float edit
    def on_float_editing_started(self, renderer, entry, row):
        if self.keypad_on_offsets:
            self.float_touchpad.show(entry, self.machine_units)

    # Popup keyboard on text edit
    def on_remark_editing_started(self, renderer, entry, row):
        if self.keypad_on_offsets:
            self.keyboard.show(entry)

    # Toggle selection checkbox value
    def on_select_toggled(self, widget, row):
        model = self.tool_liststore
        model[row][0] = not model[row][0]

    # For single click selection and edit
    def on_treeview_button_press_event(self, widget, event):
        if event.button == 1:  # left click
            try:
                path, model, x, y = widget.get_path_at_pos(int(event.x), int(event.y))
                widget.set_cursor(path, None, True)
            except:
                pass

    # Used for indicating tool in spindle
    def highlight_tool(self, tool_num):
        model = self.tool_liststore
        for row in range(len(model)):
            model[row][0] = 0
            model[row][6] = "white"
            if model[row][1] == tool_num:
                self.current_tool_data = model[row]
                model[row][6] = "gray"

    # This is not used now, but might be useful at some point
    def set_selected_tool(self, toolnum):
        model = self.tool_liststore
        found = False
        for row in range(len(model)):
            if model[row][1] == toolnum:
                found = True
                break
        if found:
            model[row][0] = 1 # Check the box
            self.widgets.tooltable_treeview.set_cursor(row)
        else:
            log.warning("Did not find tool {0} in the tool table".format(toolnum))

# =========================================================      
# BEGIN - [Status] notebook page button handlers
# =========================================================

    # =========================================================
    # Launch HAL-tools, copied from gsreen
    def on_hal_show_clicked(self, widget, data=None):
        p = os.popen("tclsh {0}/bin/halshow.tcl &".format(TCLPATH))

    def on_calibration_clicked(self, widget, data=None):
        p = os.popen("tclsh {0}/bin/emccalib.tcl -- -ini {1} > /dev/null &".format(TCLPATH, sys.argv[2]), "w")

    def on_hal_meter_clicked(self, widget, data=None):
        p = os.popen("halmeter &")

    def on_status_clicked(self, widget, data=None):
        p = os.popen("linuxcnctop  > /dev/null &", "w")

    def on_hal_scope_clicked(self, widget, data=None):
        p = os.popen("halscope  > /dev/null &", "w")

    def on_classicladder_clicked(self, widget, data=None):
        if hal.component_exists("classicladder_rt"):
            p = os.popen("classicladder  &", "w")
        else:
            text = "Classicladder real-time component not detected"
            self.error_dialog.run(text)

# =========================================================
# BEGIN - HAL Status
# =========================================================

# =========================================================
# BEGIN - Update functions
# =========================================================

    def _update_machine_state(self):
        if self.stat.task_state == linuxcnc.STATE_ESTOP:
            self.task_state = linuxcnc.STATE_ESTOP
            state_str = "ESTOP"
        elif self.stat.task_state == linuxcnc.STATE_ESTOP_RESET:
            self.task_state = linuxcnc.STATE_ESTOP_RESET
            state_str = "RESET"   
        elif self.stat.task_state == linuxcnc.STATE_ON:
            self.task_state = linuxcnc.STATE_ON
            state_str = "ON" 
        elif self.stat.task_state == linuxcnc.STATE_OFF:
            self.task_state = linuxcnc.STATE_OFF
            state_str = "OFF"
        else:
            state_str = "Unknown"
        log.debug("Machine is in state: {0}".format(state_str))
        self.widgets.emc_state_label.set_text("State: {0}".format(state_str))

    def _update_machine_mode(self):
        if self.stat.task_mode == linuxcnc.MODE_MDI:
            self.task_mode = linuxcnc.MODE_MDI
            mode_str = "MDI"
        elif self.stat.task_mode == linuxcnc.MODE_MANUAL:
            self.task_mode = linuxcnc.MODE_MANUAL
            mode_str = "MAN"
        elif self.stat.task_mode == linuxcnc.MODE_AUTO:
            self.task_mode = linuxcnc.MODE_AUTO
            mode_str = "AUTO"
        else:
            mode_str = "Unknown"
        log.debug("Machine is in mode: {0}".format(mode_str))
        self.widgets.emc_mode_label.set_text("Mode: {0}".format(mode_str))

    def _update_interp_state(self):
        if self.stat.interp_state == linuxcnc.INTERP_IDLE:
            self.interp_state = linuxcnc.INTERP_IDLE
            state_str = "IDLE"
        elif self.stat.interp_state == linuxcnc.INTERP_READING:
            self.interp_state = linuxcnc.INTERP_READING
            state_str = "READ"
        elif self.stat.interp_state == linuxcnc.INTERP_PAUSED:
            self.interp_state = linuxcnc.INTERP_PAUSED
            state_str = "PAUSE"
        elif self.stat.interp_state == linuxcnc.INTERP_WAITING:
            self.interp_state = linuxcnc.INTERP_WAITING
            state_str = "WAIT"
        else:
            state_str = "Unknown"
        log.debug("Interpreter is in state: {0}".format(state_str))
        self.widgets.emc_interp_label.set_text("Interp: {0}".format(state_str))

    def _update_motion_mode(self):
        if self.stat.motion_mode == linuxcnc.TRAJ_MODE_COORD:
            self.motion_mode = linuxcnc.TRAJ_MODE_COORD
            motion_str = "COORD"
        elif self.stat.motion_mode == linuxcnc.TRAJ_MODE_FREE:
            self.motion_mode = linuxcnc.TRAJ_MODE_FREE
            motion_str = "FREE"
        elif self.stat.motion_mode == linuxcnc.TRAJ_MODE_TELEOP:
            self.motion_mode = linuxcnc.TRAJ_MODE_TELEOP
            motion_str = "TELEOP"
        else:
            motion_str = "Unknown"
        log.debug("Motion mode is: {0}".format(motion_str))
        self.widgets.emc_motion_label.set_text("Motion: {0}".format(motion_str))

    def _update_axis_dros(self):
        if self.dro_actual_pos:
            pos = self.stat.actual_position
        else:
            pos = self.stat.position
            
        dtg = self.stat.dtg
        g5x_offset = self.stat.g5x_offset
        g92_offset = self.stat.g92_offset
        tool_offset = self.stat.tool_offset

        rel = [0]*9
        for axis in self.axis_number_list:
            rel[axis] = pos[axis] - g5x_offset[axis] - tool_offset[axis]

        if self.stat.rotation_xy != 0:
            t = math.radians(-self.stat.rotation_xy)
            xr = rel[0] * math.cos(t) - rel[1] * math.sin(t)
            yr = rel[0] * math.sin(t) + rel[1] * math.cos(t)
            rel[0] = xr
            rel[1] = yr

        for axis in self.axis_number_list:
            rel[axis] -= g92_offset[axis]

        if self.display_units != self.machine_units: # We need to convert
            rel = self.convert_dro_units(rel)
            dtg = self.convert_dro_units(dtg)
            pos = self.convert_dro_units(pos)

        if self.display_units == 'mm':
            dec_plc = self.mm_dro_plcs
        else:
            dec_plc = self.in_dro_plcs

        if not self.dro_has_focus: # Keep from overwriting user input
            for axis, dro in self.rel_dro_dict.iteritems():
                dro.set_text("%.*f" % (dec_plc, rel[axis]))

        for axis, dro in self.dtg_dro_dict.iteritems():
                dro.set_text("%.*f" % (dec_plc, dtg[axis]))

        for axis, dro in self.abs_dro_dict.iteritems():
                dro.set_text("%.*f" % (dec_plc, pos[axis]))

    def _update_joint_dros(self):
        if self.dro_actual_pos:
            pos = self.stat.joint_actual_position
        else:
            pos = self.stat.joint_position
        for joint in range(self.num_joints):
            dro = self.joint_pos_dro_list[joint]
            dro.set_text("%.4f" % pos[joint])

    # Convert DRO units back and forth from in to mm
    def convert_dro_units(self, values):
        out = [0]*9
        for axis, value in enumerate(values):
            out[axis] = values[axis] * self.conversion[axis]
        return out

    def _update_work_cord(self):
        work_cords = ["G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]
        self.current_work_cord = self.stat.g5x_index
        self.widgets.rel_dro_label.set_text(work_cords[self.current_work_cord])

    def _update_active_codes(self):
        active_codes = []
        for code in sorted(self.stat.gcodes[1:]):
            if code == -1:
                continue
            if code % 10 == 0:
                active_codes.append("G{0}".format(code / 10))
            else:
                active_codes.append("G{0}.{1}".format(code / 10, code % 10))
        for code in sorted(self.stat.mcodes[1:]):
            if code == -1: continue
            active_codes.append("M{0}".format(code))
        self.active_codes = active_codes
        self.codes = self.stat.gcodes + self.stat.mcodes
        self.widgets.active_gcodes_label.set_label(" ".join(self.active_codes))

    # Update the feedrate/current velocity labels
    def _update_vel(self):
        # self.stat.program_units returns 1 for inch, 2 for mm and 3 for cm
        # self.stat.settings[1] returns the feedrate
        # self.stat.feedrate returns the current feedrate override
        # self.stat.current_vel returns the current velocity in Cartesian space in units/s

        prog_feed = self.stat.settings[1]           # Programed feed
        act_feed = prog_feed * self.stat.feedrate  # Correct for feed override
        act_vel = self.stat.current_vel * 60.0      # Convert to units per min. Machine units???

        if self.stat.program_units == 1:            # Program is in inches
            vel_dec_plcs = self.in_vel_dec_plcs
            if "G95" in self.active_codes:          # Units per rev mode
                feed_dec_plcs = self.in_g95_dec_plcs
            else:
                feed_dec_plcs = self.in_feed_dec_plcs
            if self.machine_units == 'mm':
                 act_vel = act_vel / 25.4  # Is this conversion needed??
        else:                                       # Program is metric
            vel_dec_plcs = self.mm_vel_dec_plcs
            if "G95" in self.active_codes:          # Units per rev mode
                feed_dec_plcs = self.mm_g95_dec_plcs
            else:
                feed_dec_plcs = self.mm_feed_dec_plcs
            if self.machine_units == 'in':
                act_vel = act_vel * 25.4  # Is this conversion needed??

        self.widgets.current_vel_label.set_text("%.*f" %(vel_dec_plcs, act_vel))
        self.widgets.active_feed_label.set_label("%.*f" %(feed_dec_plcs, prog_feed))
        self.widgets.actual_feed_label.set_text("%.*f" %(feed_dec_plcs, act_feed))

    def _update_override_labels (self):
        if self.feed_override != self.stat.feedrate:
            self.feed_override = self.stat.feedrate
            self.widgets.feed_override_label.set_text('{: .0f}%'.format(self.feed_override * 100))
        if self.spindle_override != self.stat.spindlerate:
            self.spindle_override = self.stat.spindlerate
            self.widgets.spindle_override_label.set_text('{: .0f}%'.format(self.spindle_override * 100))
        if self.rapid_override != self.stat.rapidrate:
            self.rapid_override = self.stat.rapidrate
            self.widgets.rapid_override_label.set_text('{: .0f}%'.format(self.rapid_override * 100))

    def _update_spindle_speed_label(self):
        if self.spindle_speed != self.stat.spindle_speed:
            self.spindle_speed = self.stat.spindle_speed
            self.widgets.spindle_speed_entry.set_text('{:.0f}'.format(self.stat.spindle_speed))

    def _update_current_tool_data(self):
        self.current_tool = self.stat.tool_in_spindle
        if self.current_tool == 0:
            self.highlight_tool(self.current_tool)
            self.widgets.tool_number_entry.set_text("0")
            self.widgets.tool_comment_label.set_text("No tool in spindle")
            self.widgets.tool_diameter.set_text("-")
            self.widgets.tool_length.set_text("-")
        else:
            self.highlight_tool(self.current_tool)
            self.widgets.tool_number_entry.set_text(str(self.current_tool))
            self.widgets.tool_comment_label.set_text(self.current_tool_data[5])
            self.widgets.tool_diameter.set_text(self.current_tool_data[3])
            self.widgets.tool_length.set_text(self.current_tool_data[4])

    # FIXME This won't work properly till the "state-tags" branch is merged
    def _update_cutting_parameters(self):
        if "G1" in self.active_codes and self.current_tool_data[3] != 0 and self.current_tool_data[3] != '' and self.stat.current_vel != 0:
            tool_dia = float(self.current_tool_data[3])
            self.surface_speed = self.spindle_speed * tool_dia * 0.2618
            self.chip_load = self.stat.current_vel * 60 / (self.spindle_speed + .01) * 2
            self.widgets.surface_speed.set_text('{:.1f}'.format(self.surface_speed))
            self.widgets.chip_load.set_text('{:.4f}'.format(self.chip_load))
        else:
            self.widgets.surface_speed.set_text("-")
            self.widgets.chip_load.set_text("-")

    def _get_axis_list(self):
        coordinates = self.get_ini_info.get_coordinates()
        self.num_joints = self.get_ini_info.get_joints()

        # Axis letter list (Ex. ['X', 'Y', 'Z', 'B'])
        for joint, axis_letter in enumerate(coordinates):
            if axis_letter in self.axis_letter_list:
                continue
            self.axis_letter_list.append(axis_letter)

        self.num_axes = len(self.axis_letter_list)

        # Axis number list (Ex. [0, 1, 2, 4])
        for axis in self.axis_letter_list:
            axis_number = self.axis_letters.index(axis)
            self.axis_number_list.append(axis_number)

        # Joint:Axis dict (Ex. {0:0, 1:1, 2:2, 3:4})
        for jnum, aletter in enumerate(coordinates):
            anum = self.axis_letters.index(aletter)
            self.joint_axis_dict[jnum] = anum

        double_aletter = ""
        for aletter in self.axis_letters:
            if coordinates.count(aletter) > 1:
                double_aletter += aletter
        if double_aletter != "":
            log.info("Machine appearers to be a gantry config having a double {0} axis"
                  .format(double_aletter))

        self.aletter_jnum_dict = {}
        self.jnum_aletter_dict = {}
        if self.num_joints == len(coordinates):
            log.info("The machine has {0} axes and {1} joints".format(self.num_axes, self.num_joints))
            log.info("The Axis/Joint mapping is:")
            count = 0
            for jnum, aletter in enumerate(coordinates):
                if aletter in double_aletter:
                    aletter = aletter + str(count)
                    count += 1
                self.aletter_jnum_dict[aletter] = jnum
                self.jnum_aletter_dict[jnum] = aletter
                log.info("Axis {0} --> Joint {1}".format(aletter, jnum))
        else:
            log.info("The number of joints ({0}) is not equal to the number of coordinates ({1})"
                  .format(self.num_joints, len(coordinates)))
            log.info("It is highly recommended that you update your config.")
            log.info("Reverting to old style. This could result in incorrect behavior...")
            log.info("\nGuessing the Axes/Joints mapping is:")
            for jnum, aletter in enumerate(self.axis_letters):
                if aletter in coordinates:
                    self.aletter_jnum_dict[aletter] = jnum
                    log.info("Axis {0} --> Joint {1}".format(aletter, jnum))

    def _update_homing_status(self):
        homed_joints = [0]*9
        for joint in range(self.num_joints):
            if self.stat.joint[joint]['homed'] != 0:
                homed_joints[joint] = 1 # 1 indicates homed
                self.joint_pos_dro_list[joint].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
                self.joint_status_label_list[joint].set_text("homed")
                self.home_joint_btn_list[joint].set_label("Unhome")
                axis = self.joint_axis_dict[joint]
                self.abs_dro_dict[axis].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
            elif self.stat.joint[joint]['homing'] != 0:
                homed_joints[joint] = 2 # 2 indicates homing in progress
                self.joint_pos_dro_list[joint].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('yellow'))
                self.joint_status_label_list[joint].set_text("homing")
                axis = self.joint_axis_dict[joint]
                self.abs_dro_dict[axis].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('yellow'))
            else:
                homed_joints[joint] = 0 # 0 indicates unhomed
                self.joint_pos_dro_list[joint].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('red'))
                self.joint_status_label_list[joint].set_text("unhomed")
                self.home_joint_btn_list[joint].set_label("Home")
                axis = self.joint_axis_dict[joint]
                self.abs_dro_dict[axis].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('red'))
        self.homed_joints = homed_joints

    #TODO Make so does not run if it does not need to
    def _updade_dro_status(self):
        if self.is_moving() or not self.is_homed():  # or not self.no_force_homing:
            # An eventbox is placed over the editable DROs, if it is visible it blocks them from events 
            self.widgets.dro_mask.set_visible(True)
            for anum, dro in self.rel_dro_dict.iteritems():
                dro.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('#908e8e'))
        else:
            self.widgets.dro_mask.set_visible(False)
            for joint, dro in self.rel_dro_dict.iteritems():
                dro.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('white'))


# =========================================================
# BEGIN - Jogging
# =========================================================

    def on_key_press_event(self, widget, event):

        keyname = gtk.gdk.keyval_name(event.keyval)

        allow_jog = self.prefs.getpref("JOGGING", "USE_KEYBOARD", "YES")
        if allow_jog == False:
            return

        if self.is_pressed.get(keyname, False) == True:
            return True

        if self.stat.task_mode != linuxcnc.MODE_MANUAL \
            or not self.widgets.notebook.get_current_page() == 0 \
            or not self.is_homed():
            return

        if keyname == 'Up':
            self.jog("+y")
            self.is_pressed[keyname] = True
            return True
        elif keyname == 'Down':
            self.jog("-y")
            self.is_pressed[keyname] = True
            return True
        elif keyname == 'Left':
            self.jog("-x")
            self.is_pressed[keyname] = True
            return True
        elif keyname == 'Right':
            self.jog("+x")
            self.is_pressed[keyname] = True
            return True
        elif keyname == 'Page_Up':
            self.jog("+z")
            self.is_pressed[keyname] = True
            return True
        elif keyname == 'Page_Down':
            self.jog("-z")
            self.is_pressed[keyname] = True
            return True


    def on_key_release_event(self, widget, event):

        keyname = gtk.gdk.keyval_name(event.keyval)

        if self.stat.task_mode != linuxcnc.MODE_MANUAL:
            return

        if not keyname in self.is_pressed:
            return

        if keyname == 'Up':
            self.jog_stop("y")
            self.is_pressed[keyname] = False
            return True
        elif keyname == 'Down':
            self.jog_stop("y")
            self.is_pressed[keyname] = False
            return True
        elif keyname == 'Left':
            self.jog_stop("x")
            self.is_pressed[keyname] = False
            return True
        elif keyname == 'Right':
            self.jog_stop("x")
            self.is_pressed[keyname] = False
            return True
        elif keyname == 'Page_Up':
            self.jog_stop("z")
            self.is_pressed[keyname] = False
            return True
        elif keyname == 'Page_Down':
            self.jog_stop("z")
            self.is_pressed[keyname] = False
            return True


    def jog(self, axis):
        JOGMODE = 0
        dir = axis[0]
        vel = self.prefs.getpref("JOGGING", "VELOCITY", 1, int)
        axis_num = "xyzabcuvw".index(axis[1])
        log.debug("green$STARTED jogging {} axis".format(axis))
        self.command.jog(linuxcnc.JOG_CONTINUOUS, JOGMODE, axis_num, float('{}{}'.format(dir, vel)))


    def jog_stop(self, axis):
        JOGMODE = 0
        axis_num = "xyzabcuvw".index(axis)
        log.debug("red$STOPED jogging {} axis".format(axis))
        self.command.jog(linuxcnc.JOG_STOP, JOGMODE, axis_num)


# =========================================================
# BEGIN - Helper functions
# =========================================================

    def set_mode(self, mode):
        self.stat.poll()
        if self.stat.task_mode == mode:
            return True
        self.command.mode(mode)
        self.command.wait_complete()
        return True

    def set_state(self, state):
        self.stat.poll()
        if self.stat.state == state:
            return True
        self.command.state(state)
        self.command.wait_complete()
        return True

    def set_motion_mode(self, mode):
        self.stat.poll()
        if self.stat.motion_mode == mode:
            return True
        self.command.teleop_enable(0)
        self.command.traj_mode(mode)
        self.command.wait_complete()
        return True

    def issue_mdi(self, mdi_command):
        if self.set_mode(linuxcnc.MODE_MDI):
            log.info("Issuing MDI command: {}".format(mdi_command))
            self.command.mdi(mdi_command)
            # Can't have a wait_complete() here or it locks up the UI

    def set_work_offset(self, axis, value):
        offset_command = 'G10 L20 P%d %s%.12f' % (self.current_work_cord, axis, value)
        self.issue_mdi(offset_command)
        self.set_mode(linuxcnc.MODE_MANUAL)
        self.refresh_gremlin()

    def home_joint(self, joint):
        self.set_mode(linuxcnc.MODE_MANUAL)
        if self.stat.joint[joint]['homed'] == 0 and not self.stat.estop and self.stat.joint[joint]['homing'] == 0:
            msg = "Homing joint {0}".format(joint)
            log.info(msg)
            self._show_message(["INFO", msg])
            self.command.home(joint)
            # Indicate homing in process, needed to cause update of joint status
            self.homed_joints[joint] = 2
        elif self.stat.homed[joint]:
            message = ("joint {0} is already homed. \n Unhome?".format(joint))
            unhome_joint = self.yes_no_dialog.run(message)
            if unhome_joint:
                msg = "Unhoming joint {0}".format(joint)
                log.info(msg)
                self._show_message(["INFO", msg])
                self.set_motion_mode(linuxcnc.TRAJ_MODE_FREE)
                self.command.unhome(joint)
        elif self.stat.joint[joint]['homing'] != 0:
            msg = "Homing sequence already in progress"
            log.error(msg)
            self._show_message(["ERROR", msg])
        else:
            msg = "Can't home joint {0}, check E-stop and machine power".format(joint)
            log.error(msg)
            self._show_message(["ERROR", msg])

    # Check if all joints are homed
    def is_homed(self):
        for joint in range(self.num_joints):
            if not self.stat.joint[joint]['homed']:
                return False
        return True

    # Check if the machine is moving due to MDI, program execution, etc.
    def is_moving(self):
        # self.stat.state returns current command execution status.
        # one of RCS_DONE, RCS_EXEC, RCS_ERROR.
        if self.stat.state == linuxcnc.RCS_EXEC:
            return True
        else:
            return self.stat.task_mode == linuxcnc.MODE_AUTO and self.stat.interp_state != linuxcnc.INTERP_IDLE

    # Evaluate expressions in numeric entries
    def eval(self, data):
        factor = 1
        data = data.lower()
        if "in" in data or '"' in data:
            data = data.replace("in", "").replace('"', "")
            if self.machine_units == 'mm':
                factor = 25.4
        elif "mm" in data:
            data = data.replace("mm", "")
            if self.machine_units == 'in':
                factor = 1/25.4
        return self.s.eval(data) * factor

    # Set image from file
    def set_image(self, image_name, image_file):
        image = self.builder.get_object(image_name)
        image.set_from_file(os.path.join(IMAGEDIR, image_file))

    # Set animation from file
    def set_animation(self, image_name, image_file):
        if image_file is None:
            image = self.builder.get_object(image_name)
            image.set_from_file(None)
            return
        else:
            image = self.builder.get_object(image_name)
            image.set_from_file(os.path.join(IMAGEDIR, image_file))

    # Used to throw out unintentional mouse wheelin thru notebook tabs
    def on_notebook_scroll_event(self, widget, event):
        return True

    # Handle window exit button press
    def on_window_delete_event(self, widget, data=None):
        message = "Are you sure you want \n to close LinuxCNC?"
        exit_hazzy = self.yes_no_dialog.run(message)
        if exit_hazzy:
            self.close_window()

        return True  # If does not return True will close window without popup!

    # Exit steps
    def close_window(self):

        log.info("Turning machine off and E-stoping")
        self.set_state(linuxcnc.STATE_OFF)
        self.set_state(linuxcnc.STATE_ESTOP)
        log.info("Hazzy will now quit...")
        gtk.main_quit()

# =========================================================
# BEGIN - init functions
# =========================================================

    # Decorate the window if screen is big enough
    def _init_window(self):
        self.window.connect( "key_press_event", self.on_key_press_event)
        self.window.connect( "key_release_event", self.on_key_release_event)
        screen_w = gtk.gdk.Screen().get_width()
        screen_h = gtk.gdk.Screen().get_height()
        if screen_w > 1024 and screen_h > 768:
            log.debug("Screen size: {0}x{1} Decorating the window"
                  .format(str(screen_w), str(screen_h)))
            self.window.set_decorated(True)
        else:
            log.debug("Screen size: {0}x{1} Screen too small to decorate window"
                  .format(str(screen_w), str(screen_h)))


def main():
    gtk.main()

if __name__ == "__main__":
    ui = Hazzy()
    main()
