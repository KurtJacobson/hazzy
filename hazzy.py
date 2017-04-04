#!/usr/bin/env python

#   An attempt at a basic UI for LinuxCNC that can be used
#   on a touch screen without any lost of functionality.
#   The code is almost a complete rewrite, but was influenced
#   mainly by Gmoccapy and Touchy, with some code adapted from 
#   the HAL vcp widgets.

#   Copyright (c) 2017 Kurt Jacobson
#        <kcjengr@gmail.com>
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
import hal_glib           # Needed to make our own hal pins
import gtk, glib          # Base for pygtk widgets and constants
import sys                # Handle system calls
import os                 # Needed to get the paths and directories
import pango              # Needed for font settings
import gladevcp.makepins  # To make HAL pins and set up updating for them
import atexit             # Needed to register child's to be closed on closing the GUI
import subprocess         # To launch onboard and other processes
import vte                # To get the embedded terminal
import tempfile           # Needed only if the user click new in edit mode to open a new empty file
import datetime           # Needed for the clock
import linuxcnc           # To get our own error system
import gobject            # Needed to add the timer for periodic
import logging            # Needed for logging errors
from gladevcp.gladebuilder import GladeBuilder
import gtksourceview2 as gtksourceview

# Setup paths to files
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
inifile = sys.argv[2]                             # Path to .ini file
CONFIGDIR = os.path.dirname(inifile)            # Path to config dir
HAZZYDIR = os.path.join(CONFIGDIR, 'hazzy')     # Path to hazzy dir
IMAGEDIR = os.path.join(HAZZYDIR, 'images')     # Path to hazzy images and glade file
LANGDIR = os.path.join(HAZZYDIR, 'gcode-lang')  # Set the highlighting in the gcode view
sys.path.insert(1 , HAZZYDIR)                   # Set system path so we can find our own modules

# Now we have the path to our own modules so we can import them
import tc                 # For highlighting terminal messages.
import widgets            # Norbert's module for geting objects quickly
import hazzy_prefs        # Handles the preferences
import getiniinfo         # Handles .ini file reading. Validation is done in this module
import touchpad           # On screen numpad and keypad for use with touchscreens
import keyboard           # On screen keyboard emulator for use with touchscreens
import entry_keyboard
import dialogs            # Used for confirmation and error dialogs

# Path to TCL for external programs eg. halshow
TCLPATH = os.environ['LINUXCNC_TCL_DIR']

# Have some fun with our Terminal Colors module.
# tc.I will print "HAZZY INFO" in gray, tc.W is for WARNINGS and tc.E is for ERRORS
print tc.I + "The config dir is: " + CONFIGDIR


# Create a logger
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Create file handler
fh = logging.FileHandler('hazzy.log')
fh.setLevel(logging.DEBUG)

# Create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
fformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
cformatter = logging.Formatter('HAZZY %(levelname)s - %(message)s')
fh.setFormatter(fformatter)
ch.setFormatter(cformatter)

# Add handlers to the logger
log.addHandler(fh)
log.addHandler(ch)


# Throw up a dialog with debug info when an error is encountered
def excepthook(exc_type, exc_value, exc_traceback):
    try:
        w = app.widgets.window
    except KeyboardInterrupt:
        sys.exit(0)
    except NameError:
        w = None
    message = traceback.format_exception(exc_type, exc_value, exc_traceback)
    log.error("".join(message))
    dialogs.dialogs("".join(message) , 2).run()
    
    
# Connect the exception hook
sys.excepthook = excepthook

    

class hazzy(object):

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
        self.prefs = hazzy_prefs.preferences(self.get_ini_info.get_preference_file_path())
        
        # Get the tool table liststore
        self.tool_listore = self.builder.get_object("tool_liststore")

       

# =========================================================
## BEGIN - HAL setup  
# =========================================================
            
        #Note: Pins/signals must be connected in the POSTGUI halfile

        self.hal.newpin('coolant', hal.HAL_BIT, hal.HAL_OUT)
        self.hal.newpin('error', hal.HAL_BIT, hal.HAL_OUT)
        panel = gladevcp.makepins.GladePanel(self.hal, gladefile, self.builder, None)
        
        self.hal.ready()


# =========================================================
## BEGIN - Get machine settings
# =========================================================
        
        self.dro_actual_pos = self.get_ini_info.get_position_feedback_actual()    
        self.no_force_homing = self.get_ini_info.get_no_force_homing()
        self.machine_metric = self.get_ini_info.get_machine_metric()
        self.nc_file_dir = self.get_ini_info.get_program_prefix()
        self.log_file = self.get_ini_info.get_log_file_path()
        self.tool_table = self.get_ini_info.get_tool_table()
        # CYCLE_TIME = time, in milliseconds, that display will sleep between polls
        cycle_time = self.get_ini_info.get_cycle_time()         # This defaults to 50ms if not specified in INI
        gobject.timeout_add(cycle_time, self._fast_periodic)  # Calls _fast_periodic at CYCLE_TIME
        
        # Set the conversions used for changing the DRO units
        # Only want to convert linear units, hence the need for a list of conversion factors
        if self.machine_metric: 
            # List of factors for converting from mm to inches
            self.conversion = [1.0/25.4]*3+[1]*3+[1.0/25.4]*3
        else:
            # List of factors for converting from inches to mm
            self.conversion = [25.4]*3+[1]*3+[25.4]*3

        
        # Clear the log file
        openfile = open(self.log_file, "w")
        openfile.write("*** HAZZY SESSION LOG FILE *** \n")
        openfile.close() 

        
# =========================================================
## BEGIN - Set initial toggle button states, and other values
# =========================================================
        
        # Define default button states 
        self.cycle_start_button_state = 'start'
        self.hold_resume_button_state = 'inactive'
        
        self.style_scheme = None
        self.lang_spec = None
        
        self.new_error = False          # Whether there is a new error, used to load error_flash.gif
        self.error_flash_timer = 0      # Keep track of _slow_periodic cycles since error_flash.gif loaded
        
        self.gremlin_mouse_mode = 2     # Keep track of current gremlin mouse btn mode
        
        self.display_metric = False
        self.start_line = 0             # Needed for start from line
        self.periodic_cycle_counter = 0 # Used to determine when to call _slow_periodic()

        self.dro_has_focus = False      # Used to stop DRO update if user is trying to type into it
        self.zoom_in_pressed = False    # Used to keep track of continuous zoom IN button on gremlin
        self.zoom_out_pressed = False   # Used to keep track of continuous zoom OUT button on gremlin
        
        self.gcodeerror = ""            # Needed to avoid printing multiple identical messages
        self.usb_dir = ""
        self.surface_speed = ""
        self.chip_load = ""
        self.feed_override = ""
        self.spindle_override = ""
        self.rapid_override = ""
        self.spindle_speed = ""
        self.current_tool = ""
        self.current_work_cord = ""     # Keep track of current work cord
        self.codes = []                 # Unformatted G codes + M codes to check if an update is required
        self.active_codes = []          # Formated G codes + M codes for display
        self.axis_list = []             # List of axes used in the machine [ X, Y, Z, B ]
        self.joint_list = []            # List of joints used in the machine 
        self.axis_joint_dict = {}       # 
        self.homed_joints = []          # List of homed joints

                
# =========================================================
## BEGIN - Preferences
# =========================================================
        # If a preference file does not exist it will be created in the config dir
        
        # [FILE PATHS]
        self.nc_file_path = self.prefs.getpref("FILE PATHS", "default_nc_dir", self.nc_file_dir, str)
        self.log_file = self.prefs.getpref("FILE PATHS", "LOG_FILE", self.log_file, str)
        
        # [FILE FILTERS]
        self.preview_ext = self.prefs.getpref("FILE FILTERS", "preview_ext", [".ngc", ".txt", ".tap", ".nc"], str)
        
        # [TOUCHSCREEN]        
        self.keypad = self.prefs.getpref("TOUCHSCREEN", "use_keypad", True)
        self.numpad = self.prefs.getpref("TOUCHSCREEN", "use_numpad", True)
        self.mdipad = self.prefs.getpref("TOUCHSCREEN", "use_mdipad", True)

        # [FONTS]
        self.mdi_font = pango.FontDescription(self.prefs.getpref("FONTS", "mdi_font", 'dejavusans condensed 14', str))
        self.dro_font = pango.FontDescription(self.prefs.getpref("FONTS", "dro_font", 'dejavusans condensed 16', str))
        self.abs_font = pango.FontDescription(self.prefs.getpref("FONTS", "abs_font", 'dejavusans condensed 12', str))
        self.vel_font = pango.FontDescription(self.prefs.getpref("FONTS", "vel_font", 'dejavusans condensed 14', str))
        self.label_font = pango.FontDescription(self.prefs.getpref("FONTS", "label_font", 'NimbusSansL 10', str))
        
        # [POS DROs]
        self.in_dro_plcs = self.prefs.getpref("POS DROs", "in_dec_plcs", 4, int)
        self.mm_dro_plcs = self.prefs.getpref("POS DROs", "mm_dec_plcs", 3, int)
        
        # [VEL DROs]
        self.in_vel_dec_plcs = self.prefs.getpref("VEL DROs", "in_vel_dec_plcs", 1, int)
        self.in_feed_dec_plcs = self.prefs.getpref("VEL DROs", "in_feed_dec_plcs", 1, int)
        self.in_g95_dec_plcs = self.prefs.getpref("VEL DROs", "in_g95_dec_plcs", 3, int)
        self.mm_vel_dec_plcs = self.prefs.getpref("VEL DROs", "mm_vel_dec_plcs", 2, int)
        self.mm_feed_dec_plcs = self.prefs.getpref("VEL DROs", "mm_feed_dec_plcs", 0, int)
        self.mm_g95_dec_plcs = self.prefs.getpref("VEL DROs", "mm_g95_dec_plcs", 0, int)
        
        # [GCODE VIEW]
        self.style_scheme_file = self.prefs.getpref("GCODE VIEW", "style_scheme_file", 'GCode.xml', str)
        self.style_scheme_name = self.prefs.getpref("GCODE VIEW", "style_scheme_name", 'gcode', str)
        self.lang_spec_file = self.prefs.getpref("GCODE VIEW", "lang_spec_file", 'hngc.lang', str)
        self.lang_spec_name = self.prefs.getpref("GCODE VIEW", "lang_spec_name", 'hngc', str)
        
        # [MACHINE DEFAULTS]
        self.df_feed = self.prefs.getpref("MACHINE DEFAULTS", "df_speed", 10, int)
        self.df_speed = self.prefs.getpref("MACHINE DEFAULTS", "df_feed", 300, int)
        
        
        
        
# =========================================================
## BEGIN - Appearance initialize
# =========================================================
        
        # Set the gcode sourceview style scheme if it is present, elif use Kate, else nothing   
        if os.path.isfile(os.path.join(BASE, 'share', 'gtksourceview-2.0', 'styles', self.style_scheme_file)):
            print(tc.I + self.style_scheme_name + " style scheme found!")
            self.style_scheme = self.style_scheme_name
        elif os.path.isfile(os.path.join(BASE, 'share', 'gtksourceview-2.0', 'styles', 'kate.xml')):
            print(tc.I + "Gcode style not found, using Kate instead")
            self.style_scheme = 'kate' # Use Kate instead
        else:
            print(tc.I + self.style_scheme_file + "style not found")
            print("Looked in: ", os.path.join(BASE, 'share', 'gtksourceview-2.0', 'styles'))
            print("Verify that the style scheme file and name are entered correctly")

        
        # Set the gcode sourceview language highlighting if it is present, else nothing
        if os.path.isfile(os.path.join(BASE, 'share', 'gtksourceview-2.0', 'language-specs', self.lang_spec_file)):
            print(tc.I + self.lang_spec_file + " found!")
            self.lang_spec = self.lang_spec_name
        else:
            print(tc.I + self.lang_spec_file  + " not found")
            print("Looked in: ", os.path.join(BASE, 'share', 'gtksourceview-2.0', 'language-specs'))
            
            
        if self.style_scheme != None:
            try:
                self.widgets.gcode_view.set_style_scheme(self.style_scheme)
            except:
                print(tc.E + "Could not set %s style scheme!" % self.style_scheme)
                print("Verify that the style scheme file and name are correct")
                
        if self.lang_spec != None:
            try:
                self.widgets.gcode_view.set_language(self.lang_spec)
            except:
                print(tc.E + "Could not set %s language spec!" % self.lang_spec)
                print("Verify that the lang spec file and name are correct")
                
         

        # Set the fonts for the labels in the spindle display area
        '''for i in range(1, 7):
            label = self.widgets["spindle_label_%s" % i]
            label.modify_font(pango.FontDescription('FreeSans 11'))
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('#262626'))'''
            
          
        # List of labels in the spindle display area    
        spindle_dro_list = [ 'spindle_speed_label', 'surface_speed_label', 'chip_load_label', 'active_feed_label',\
         'actual_feed_label', 'current_vel_label']
        
        '''for i in spindle_dro_list:
            label = self.widgets[i]
            label.modify_font(pango.FontDescription('dejavusans condensed 14'))
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))'''
            
        
        # Initialize MDI entry  
        self.widgets.mdi_entry.modify_font(self.mdi_font)
        self.widgets.mdi_entry.set_text("MDI:")
            
                  
        # List of DRO GtkEntry object names
        self.dro_list = ('dro_x', 'dro_y', 'dro_z', 'dro_4')

        # Convert to list of corresponding GtkEntry objects so we can refer to them by index
        self.dro_list = [ self.builder.get_object(dro) for dro in self.dro_list ]
        
        # Set DRO fonts/colors
        for axis in range(0, 4):
            self.dro_list[axis].modify_font(self.dro_font)
            self.dro_list[axis].modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
            #self.dro_list[axis].modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('#908e8e'))
        
        
        # List of DTG DRO GtkLable names
        self.dtg_list = ('dtg_x', 'dtg_y', 'dtg_z', 'dtg_4')
        
        # Convert to list of corresponding GtkLable objects
        self.dtg_list = [ self.builder.get_object(dtg) for dtg in self.dtg_list ]
            
        # Set DTG DRO fonts/colors. We don't refer to them elsewhere so no need to make object list
        
        for dtg_dro in self.dtg_list: 
            dtg_dro.modify_font(self.dro_font)
            dtg_dro.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
        
        
        # List of ABS DRO GtkLabel names  
        self.abs_list = ('abs_x', 'abs_y', 'abs_z', 'abs_4')
        
        # Convert to list of corresponding GtkLable objects so we can refer to them by index, SEE home_axis()
        self.abs_list = [ self.builder.get_object(abs_dro) for abs_dro in self.abs_list ]
        
        # Set ABS DRO fonts/colors 
        for axis in range(0, 4):
            self.abs_list[axis].modify_font(self.abs_font)
            if not self.no_force_homing:
                self.abs_list[axis].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('red'))
                
        self.widgets.abs_label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))

            
        self.widgets.spindle_text.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
        self.widgets.spindle_text.modify_font(pango.FontDescription('FreeSans condensed  14'))
        self.set_animation('reset_image', 'reset.gif') # Set the initial animated reset image
        
        
        
                
        # Initial poll so all is up to date
        self.stat.poll()
        self.error_channel.poll()
        
        # Initialize settings
        self._init_window()
        self._init_file_chooser()
        self._init_gremlin()
        self._init_gcode_preview()
        
        self._update_machine_state() 
        self._update_machine_mode()
        self._update_interp_state()
        self._get_axis_list()
       
        # Show the window    
        self.widgets.window.show()
        self._init_gremlin()
        
        #
        self.load_tool_table(self.tool_table)
        
        
    def print_to_log_file(self, message):
        # Print to log file
        log_entry = (datetime.datetime.now().strftime(" %Y-%m-%d %H:%M:%S") + "\n ERROR: " + message)
        log_file = open(self.log_file, "a")
        log_file.write("\n" + log_entry + "\n")
        log_file.close() 
        
        
    
# =========================================================
## BEGIN - Periodic status checking and updating
# =========================================================
    
    # Called at ini [DISPLAY] CYCLE_TIME to update readouts     
    def _fast_periodic(self): # Called at 50ms default
        self.stat.poll()
        self._update_dros()
        self._update_override_labels()
        self._update_spindle_speed_label()
        self._updade_dro_status()
        
        # Use this periodic to repeatedly zoom gremlin, better then
        # using a while loop with sleep() as that would block the thread
        if self.zoom_in_pressed:
            self.widgets.gremlin.zoom_in()
            
        if self.zoom_out_pressed:
            self.widgets.gremlin.zoom_out()
        
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
        message = self.error_channel.poll()
        if message:
            self._show_message(message)
        
        # Update work cord if it has changed
        if self.current_work_cord != self.stat.g5x_index:
            self._update_work_cord()

        # Update G/M codes if they have changed    
        if self.codes != self.stat.gcodes + self.stat.mcodes:
            self._update_active_codes()
            
        # Update LCNC state if it has changed
        if self.state != self.stat.task_state:
            self._update_machine_state()
        
        # Update LCNC mode if it has changed
        if self.mode != self.stat.task_mode:
            self._update_machine_mode()
        
        # Update interpreter state if it has changed    
        if self.interp != self.stat.interp_state:    
            self._update_interp_state()
            
        # Update homed joints
        if tuple(self.homed_joints) != self.stat.homed:
            self._update_homing_status()
            
        #print self.stat.homed
            
        # Update current tool data if it has changed
        if self.current_tool != self.stat.tool_in_spindle:
            self._update_current_tool_data()
          
        # self.stat.program_units returns 1 for inch, 2 for mm and 3 for cm  
        if self.stat.program_units != 1:
            self.display_metric = True
        else:
            self.display_metric = False
            
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
        if self.stat.block_delete != self.widgets.opskip.get_active() :
            self.widgets.opskip.set_active(self.stat.block_delete)
            
        
        # If new error flash message border red for 2s
        if self.new_error:
            self.error_flash_timer += 1
            if self.error_flash_timer >= 4:
                self.set_animation('error_image', None)
                self.new_error = False
                self.error_flash_timer = 0

 
# =========================================================
## BEGIN - Info/Error message display 
# =========================================================

    # Format Info & Error messages and display at bottom of screen, print to terminal
    def _show_message(self, message):
        
        kind, text = message # Unpack

        if "joint" in text:
            # Replace "joint N" with "L axis" to make messages easter to understand for newbies
            for axis in self.axis_list:
                joint = 'XYZABCUVWS'.index(axis)
                text = text.replace("joint %d" % joint, "%s axis" % axis)
            text = text.replace("joint -1", "all axes")
                
        if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
            kind = "ERROR"
            self.hal["error"] = True
        elif kind in (linuxcnc.NML_TEXT, linuxcnc.OPERATOR_TEXT):
            kind = "INFO"
        elif kind in (linuxcnc.NML_DISPLAY, linuxcnc.OPERATOR_DISPLAY):
            kind = "MSG"
        elif kind == "" or kind == None:
            kind = "ERROR"
            
        if text == "" or text == None:
            text = _("Unknown error!")
            
        # Print to terminal and display at bottom of screen
        if kind == "INFO":
            print tc.I + text
            message = '<span size=\"11000\" weight=\"bold\" foreground=\"blue\">INFO:</span> %s' % text
        elif kind == "MSG":
            print tc.I + text
            message = '<span size=\"11000\" weight=\"bold\" foreground=\"blue\">MSG:</span> %s' % text
        elif kind == "WARN":
            print tc.W + text
            message = '<span size=\"11000\" weight=\"bold\" foreground=\"orange\">WARNING:</span> %s' % text
        else:
            print tc.E + text
            message = '<span size=\"11000\" weight=\"bold\" foreground=\"red\">ERROR:</span> %s' % text
            self.set_animation('error_image', 'error_flash.gif')
            self.new_error = True
            
            self.print_to_log_file(text)
            
            '''# Print to log file
            log_entry = (datetime.datetime.now().strftime(" %Y-%m-%d %H:%M:%S") + "\n ERROR: " + text)
            openfile = open(self.log_file, "a")
            openfile.write("\n" + log_entry + "\n")
            openfile.close() '''
                        
        self.widgets.message_label.set_markup(message)
        
         
    def on_gremlin_gcode_error(self, widget, errortext):
        if self.gcodeerror == errortext:
            return
        else:
            self.gcodeerror = errortext
            text = errortext.splitlines()
            error_line = text[1].replace("Near line ", "").replace(" of","")
            message = text[0] + ' near line ' + error_line + ', see log for more info'
            self._show_message(["ERROR", message ])
            print errortext
            #dialogs.dialogs(errortext, 2).run()
            self.widgets.gcode_view.set_line_number(error_line)

     
# =========================================================
# BEGIN - Main control panel button handlers
# =========================================================
        
  
    # Toggle the cycle start/stop button state and set the corresponding image
    def on_cycle_start_pressed(self, widget, data = None):
        if self.cycle_start_button_state == 'start':
            # FIXME Check for no force homing in INI
            if self.is_homed() and self.stat.file != "" and self.widgets.notebook.get_current_page() == 0:
                self.set_mode(linuxcnc.MODE_AUTO)
                self.command.auto(linuxcnc.AUTO_RUN, self.start_line)
                self.set_cycle_start_button_state('stop')
                #self.widgets.notebook.set_current_page(0)
            elif not self.is_homed():
                self._show_message(["ERROR", "Can't run program when not homed"])
            elif self.stat.file == "":
                self._show_message(["ERROR", "No gcode file loaded"])
            elif self.widgets.notebook.get_current_page() != 0:
                self._show_message(["ERROR", "Must be on main page to run a program"])

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
             
            
    def on_feed_hold_pressed(self, widget, data = None):
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
    def on_reset_pressed(self, widget, data = None):
        if self.stat.task_state != linuxcnc.STATE_ESTOP_RESET:
            print "Reseting E-stop"
            self.set_state(linuxcnc.STATE_ESTOP_RESET)
            self.stat.poll()
        # Check if the machine actually reset
        self.stat.poll()
        if self.stat.task_state != linuxcnc.STATE_ESTOP_RESET and self.stat.task_state != linuxcnc.STATE_ON :
            print "Failed to bring machine out of E-stop"
            return
        # Turn on after reset
        if self.stat.task_state != linuxcnc.STATE_ON:
            print "Turning machine on"
            self.set_state(linuxcnc.STATE_ON)
            self.set_image('reset_image', 'reset.png')
        
        
    def on_home_all_clicked(self, widget, data = None):
        # Home -1 means all
        self.set_mode(linuxcnc.MODE_MANUAL)
        self.home_axis(-1)
        
        
    def on_home_selected_clicked(self, widget, data = None):
        # Make sure we are in manual mode  
        self.set_mode(linuxcnc.MODE_MANUAL)
        if widget == self.widgets.abs_x_eventbox:
            axis = 0
        elif widget == self.widgets.abs_y_eventbox:
            axis = 1
        elif widget == self.widgets.abs_z_eventbox:
            axis = 2
        elif widget == self.widgets.abs_4_eventbox:
            axis = 'xyzabcuvw'.index('a')
        # Home the selected axis    
        self.home_axis(axis)
        
        
    def on_exit_program_clicked(self, widget, data = None):
        self.close_window() # This function displays a popup


    # =========================================================      
    # Main panel CheckBoxe handlers
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
            
    # 
    def on_step_clicked(self, widget, data = None):
        print "STEP was clicked, I don't know by who though."
        
        
            
    
    
    def on_button1_clicked(self, widget, data = None):
        print "TOGGLE Pressed"
        tooledit.tooledit()     
        
    def on_redraw_clicked(self, widget, data = None):
        tooledit.tooledit()
    
        
    
# =========================================================      
# BEGIN - [Main] notebook page button handlers
# ========================================================= 
                
                    
    # HAL_Gremlin preview buttons
    def on_zoom_in_button_press_event(self, widget, data=None):
        self.zoom_in_pressed = True

    def on_zoom_in_button_release_event(self, widget, data=None):
        self.zoom_in_pressed = False
        
    def on_zoom_out_button_press_event(self, widget, data=None):
        self.zoom_out_pressed = True
        
    def on_zoom_out_button_release_event(self, widget, data=None):
        self.zoom_out_pressed = False
        
    def on_view_x_button_press_event(self, widget, data=None):
        self.widgets.gremlin.set_property('view', 'x') 

    def on_view_y_button_press_event(self, widget, data=None):
        self.widgets.gremlin.set_property('view', 'y')         
        
    def on_view_z_button_press_event(self, widget, data=None):
        self.widgets.gremlin.set_property('view', 'z')         
        
    def on_view_p_button_press_event(self, widget, data=None):
        self.widgets.gremlin.set_property('view', 'p')
        
    def on_mouse_mode_button_press_event(self, widget, data=None):
        if self.gremlin_mouse_mode == 0:
            self.widgets.gremlin.set_property("mouse_btn_mode", 2)
            self.set_image('mouse_mode_image', 'view_pan.png')
            self.gremlin_mouse_mode = 2
        else:
            self.widgets.gremlin.set_property("mouse_btn_mode", 0)
            self.set_image('mouse_mode_image', 'view_rotate.png')
            self.gremlin_mouse_mode = 0
            
    # Highlight code line for selected line in gremlin
    def on_gremlin_line_clicked(self, widget, line):
        self.widgets.gcode_view.set_line_number(line)
        
    # Double click gremlin to clear live plot
    def on_gremlin_button_press_event(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.widgets.gremlin.clear_live_plotter()
    
    # Toggle "show line numbers" in gcode view when double clicked
    def on_gcode_view_button_press_event(self, widget, event, data = None):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            if widget.get_show_line_numbers():
                widget.set_show_line_numbers(False)
            else:
                widget.set_show_line_numbers(True)
        
# =========================================================      
# BEGIN - [File] notebook page button handlers
# ========================================================= 

    def _init_file_chooser(self):
        self.nc_file_path = self.get_ini_info.get_program_prefix()
        self.widgets.filechooser.set_current_folder(self.nc_file_path)
        
        # Set filter for only .ngc files
        self.widgets.ngc_file_filter.add_pattern('*.ngc')
        self.widgets.filechooser.set_filter(self.widgets.ngc_file_filter)
        
        # Set filter for all .ext listed in INI file
        self.widgets.nc_file_filter.add_pattern('*.ngc')
        file_ext = self.get_ini_info.get_file_ext()
        for ext in file_ext:
            self.widgets.nc_file_filter.add_pattern(ext)
            
            
    # To filter or not to filter, that is the question
    def on_filter_ngc_chk_toggled(self, widget, data = None):
        if self.widgets.filter_ngc_chk.get_active():
            self.widgets.filechooser.set_filter(self.widgets.ngc_file_filter)
        else:
            self.widgets.filechooser.set_filter(self.widgets.nc_file_filter)
            
            
    # Change button label if a file or folder is selected
    def on_filechooser_selection_changed(self, widget, data = None):
        fname = str(self.widgets.filechooser.get_filename())
        if os.path.isfile(fname):
            self.widgets.load_gcode.set_label("Load Gcode")
            if not self.preview_buf.get_modified():         # If not modified we can load file
                self.load_gcode_preview(fname)    # Preview/edit in sourceview
        elif os.path.isdir(fname):
            self.widgets.load_gcode.set_label("Open Folder")
            if not self.preview_buf.get_modified():
                self.load_gcode_preview(None)     # Clear sourceview
                
                
    # If file has been edited ask if should save before reloading preview        
    # Need to do this on release or the popup gets the mouse up and we are stuck in drag
    def on_filechooser_button_release_event(self, widget, data = None):
        fname = str(self.widgets.filechooser.get_filename())
        if self.preview_buf.get_modified():
            message = ("Save changes to: \n %s?" % os.path.split(self.current_preview_file)[1])
            if dialogs.dialogs(message).run():
                self.save(self.current_preview_file)
            else:
                self.preview_buf.set_modified(False) 
        if os.path.isfile(fname):
            self.load_gcode_preview(fname)    # Preview/edit in sourceview
            self.current_preview_file = fname
        elif os.path.isdir(fname):
            self.load_gcode_preview(None)     # Clear sourceview

    
    # Jump to folder specified in .prefs, defaults to program prefix in INI file    
    def on_open_gcode_folder_clicked(self, widget, data = None):
        self.widgets.filechooser.set_current_folder(self.nc_file_path)
        
    
    # Jump to USB drive, if more than one list them all
    # FIXME need to auto mount USB drive so they show up in /media/
    def on_open_usb_folder_clicked(self, widget, data = None):
        usbdirs = os.listdir('/media/')
        # If only one dir assume it's the USB drive and set it to current
        if len(usbdirs) == 1:
            self.usb_dir = os.path.join(path, usbdirs[0])
            self.widgets.filechooser.set_current_folder(self.usb_dir)
            print "Only one USB device: ", self.usb_dir
        else:
            self.widgets.filechooser.set_current_folder('/media/')
            print "More then one USB device", usbdirs
            
            
    # Eject the USB drive FIXME this needs some work
    def on_eject_usb_clicked(self, widget, data=None):
        if self.usb_dir != "":
            usb_name = self.usb_dir
        else:
            usb_name = self.widgets.filechooser.get_current_folder()
        
        print "USB name: ", usb_name
        self.widgets.filechooser.set_current_folder(self.nc_file_path)
        if usb_name != '':
            # FIXME The quotes are need as there may be spaces in the drive name,
            #       is there a neater way to keep the path intact?
            os.system('eject ' + '"' + usb_name + '"')

        
    # TODO Need to make a popup for entering the new folder name
    def on_new_folder_btn_clicked(self, widget, data = None):
        currentdir = self.widgets.filechooser.get_current_folder()
        entry_keyboard.keyboard(self.get_win_pos(), currentdir)
        
        #os.makedirs(currentdir + '/test')
        
        
        
        
    # Load file on activate in file chooser, better for mouse users
    def on_filechooser_file_activated(self, widget, data = None): 
        self.load_gcode_file(str(self.widgets.filechooser.get_filename()))
    
    
    # Load file on "Load Gcode" button clicked, better for touchscreen users
    def on_load_gcode_clicked(self, widget, data = None):
        self.load_gcode_file(str(self.widgets.filechooser.get_filename()))
        

    def load_gcode_file(self, fname):
        if os.path.isfile(fname):
            self.set_mode(linuxcnc.MODE_AUTO)
            # If a file is already loaded clear the interpreter
            if self.stat.file != "":
                self.command.reset_interpreter()
                self.command.wait_complete()
            self.gcodeerror = "" # Clear any previous errors messages
            self.command.program_open(fname)
            self.widgets.notebook.set_current_page(0)
            self.widgets.gcode_file_label.set_text(fname)
            #self.widgets.gremlin.reloadfile(fname)
            print "NGC file loaded: ", fname
        elif os.path.isdir(fname):
            self.widgets.filechooser.set_current_folder(fname)
            
            
    def on_save_file_clicked(self, widget, data = None):
        self.save(self.current_preview_file)
        
        
    def on_gcode_preview_button_press_event(self, widget, data = None):
        if self.keypad:
            keyboard.keyboard(widget, self.get_win_pos())
            
            
# =========================================================      
# BEGIN - [Offsets] notebook page button handlers
# =========================================================
            

    # Parse and load tool table into the treeview
    def load_tool_table(self, fn = None):
        # If no valid tool table given
        if fn == None:
            fn = self.tool_table 
        if not os.path.exists(fn):
            print "Tool table does not exist"
            return
        self.tool_listore.clear() # Clear any existing data
        print "Loading tool table: ", fn              
        tf = open(fn, "r")
        tool_table = tf.readlines()
        tf.close()
        self.toolinfo = []
        for line in tool_table:
            # Separate tool data from comments
            comment =''
            index = line.find(";") # Find comment start index
            if index == -1: # Delimiter ';' is missing, so no comments
                line = line.rstrip("\n")
            else:
                comment = (line[index+1:]).rstrip("\n")
                line = line[0:index].rstrip()
            array = [ False, 1, 1, '0', '0', comment, 'white' ]
            # search beginning of each word for keyword letters
            # offset 0 is the checkbutton so ignore it
            # if i = ';' that is the comment and we have already added it
            # offset 1 and 2 are integers the rest floats
            for offset,i in enumerate(['S','T','P','D','Z',';']):
                if offset == 0 or i == ';': continue
                for word in line.split():
                    if word.startswith(i):
                        if offset in(1,2):
                            try:
                                array[offset]= int(word.lstrip(i))
                            except Exception as e:
                                print "Tooledit int error with:", word.lstrip(i)
                                print e
                        else:
                            try:
                                array[offset]= "%.4f" % float(word.lstrip(i))
                            except Exception as e:
                                print "Tooledit float error with:", word.lstrip(i)
                                print e
                        break
            # Add array to liststore
            self.add_tool(array)
            
            
    # Save to tool table
    def save_tool_table(self, fn = None):
        if fn == None:
            fn = self.tool_table
        if fn == None:
            return
        print "Saving tool table as: ", fn
        fn = open(fn, "w")
        for row in self.tool_listore:
            values = [ value for value in row ]
            line = ""
            for num,i in enumerate(values):
                if num in (0,6): continue
                elif num in (1,2): # tool# pocket#
                    line = line + "%s%d "%(['S','T','P','D','Z',';'][num], i)
                else:
                    line = line + "%s%s "%(['S','T','P','D','Z',';'][num], i.strip())
            # Write to file
            fn.write(line + "\n")
        # Theses lines make sure the OS doesn't cache the data so that
        # linuxcnc will actually load the updated tool table below
        fn.flush()
        os.fsync(fn.fileno())
        # Reload the tooltable to linuxcnc
        linuxcnc.command().load_tool_table()


    # Add a new tool
    def add_tool(self, data = None):
        self.tool_listore.append(data)
        
        
    # Get the selected tool info
    def get_selected_tool(self):
        model = self.tool_listore
        def match_value_cb(model, path, iter, pathlist):
            if model.get_value(iter, 0) == 1:
                pathlist.append(path)
            return False     # Keep the foreach going
        pathlist = []
        model.foreach(match_value_cb, pathlist)
        # Foreach works in a depth first fashion
        print pathlist
        if len(pathlist) != 1:
            return None
        else:
            return(model.get_value(model.get_iter(pathlist[0]), 1))
        
        
    # Delete selected tools
    def on_delete_selected_clicked(self, widget):
        liststore  = self.tool_listore
        def match_value_cb(model, path, iter, pathlist):
            if model.get_value(iter, 0) == 1 :
                pathlist.append(path)
            return False     # Feep the foreach going
        pathlist = []
        liststore.foreach(match_value_cb, pathlist)
        # Foreach works in a depth first fashion
        pathlist.reverse()
        for path in pathlist:
            liststore.remove(liststore.get_iter(path))
            
            
    def on_change_to_selected__tool_clicked(self, widget, data = None):
        tool_num = self.get_selected_tool()
        if tool_num != None:
            self.issue_mdi('M6 T%s' % tool_num )
        
    
    # Add tool button handler
    def on_add_tool_clicked(self, widget, data = None):
        num = len(self.tool_listore) + 1
        array = [ False, num, num, '0.0000', '0.0000', 'New Tool', 'white' ]
        self.add_tool(array)
        
        
    # Load tool table button handler
    def on_load_tool_table_clicked(self, widget, data = None):
        self.load_tool_table()
        
        
    # Save tool table button handler
    def on_save_tool_table_clicked(self, widget, data = None):
        self.save_tool_table()

        
    # Tool number entry
    def on_tool_num_edited(self, widget, path, new_text):
        try:
            new_int = int(new_text)
            self.tool_listore[path][1] = new_int
            self.tool_listore[path][2] = new_int
        except:
            self._show_message(["ERROR", '"%s" is not a valid tool number' % new_text])
            
        
    # Tool pocket entry
    def on_tool_pocket_edited(self, widget, path, new_text):
        try:
            new_int = int(new_text)
            self.tool_listore[path][2] = new_int
        except:
            self._show_message(["ERROR", '"%s" is not a valid tool pocket' % new_text])


    # Tool diameter entry
    def on_tool_dia_edited(self, widget, path, new_text):
        try:
            new_num = float(new_text)
            self.tool_listore[path][3] = "%.4f" % float(new_text)
        except:
            self._show_message(["ERROR", '"%s" is not a valid diameter' % new_text])


    # Tool length entry
    def on_z_offset_edited(self, widget, path, new_text):
        try:
            new_num = float(new_text)
            self.tool_listore[path][4] = "%.4f" % float(new_text)
        except:
            self._show_message(["ERROR", '"%s" is not a valid tool length' % new_text])


    # Remark entry
    def on_tool_remark_edited(self, widget, path, new_text):
       self.tool_listore[path][5] =  new_text


    # Popup numpad on number edit
    def on_editing_started(self, renderer, entry, dont_know):
        touchpad.touchpad(entry)
        
        
    # Popup keyboard on text edit
    def on_remark_editing_started(self, renderer, entry, dont_know):
        keyboard.keyboard(entry, self.get_win_pos())
        #touchpad.touchpad(entry, keypad)
        
    # Toggle selection checkbox value
    def on_select_toggled(self, widget, path):
        model = self.tool_listore
        model[path][0] = not model[path][0]
        #if model[path][0] == True:
        #    model[path][6] = 'gray'
        #else:
        #    model[path][6] = 'white'
        
        
    # For single click selection and edit
    def on_treeview_button_press_event(self, widget, event):
        if event.button == 1 : # left click
            try:
                path, model, x, y = widget.get_path_at_pos(int(event.x), int(event.y))
                widget.set_cursor(path, None, True)
            except:
                pass
      

            
# =========================================================      
# BEGIN - [Status] notebook page button handlers
# =========================================================

    # =========================================================
    # Launch HAL-tools, copied from gsreen
    def on_hal_show_clicked(self, widget, data = None):
        p = os.popen("tclsh %s/bin/halshow.tcl &" % TCLPATH)

    def on_calibration_clicked(self, widget, data = None):
        p = os.popen("tclsh %s/bin/emccalib.tcl -- -ini %s > /dev/null &" % (TCLPATH, sys.argv[2]), "w")

    def on_hal_meter_clicked(self, widget, data = None):
        p = os.popen("halmeter &")

    def on_status_clicked(self, widget, data = None):
        p = os.popen("linuxcnctop  > /dev/null &", "w")

    def on_hal_scope_clicked(self, widget, data = None):
        p = os.popen("halscope  > /dev/null &", "w")

    def on_classicladder_clicked(self, widget, data = None):
        if hal.component_exists("classicladder_rt"):
            p = os.popen("classicladder  &", "w")
        else:
            text = "Classicladder real-time component not detected"
            dialogs.dialogs(text, 2).run()


# =========================================================
## BEGIN - HAL Status
# =========================================================



# =========================================================
## BEGIN - Update functions
# =========================================================

    def _update_machine_state(self):
        if self.stat.task_state == linuxcnc.STATE_ESTOP:
            self.state = linuxcnc.STATE_ESTOP
            state_str = "ESTOP"
            print "Machine is in STATE_ESTOP"
        elif self.stat.task_state == linuxcnc.STATE_ESTOP_RESET:
            self.state = linuxcnc.STATE_ESTOP_RESET
            state_str = "RESET"
            print "Machine is in STATE_ESTOP_RESET"    
        elif self.stat.task_state == linuxcnc.STATE_ON:
            self.state = linuxcnc.STATE_ON
            state_str = "ON"
            print "Machine is in STATE_ON" 
        elif self.stat.task_state == linuxcnc.STATE_OFF:
            self.state = linuxcnc.STATE_OFF
            state_str = "OFF"
            print "Machine is in STATE_OFF"
        else:
            state_str = "Unknown state"
            print "Unknown state!!!"
        self.widgets.state_lable.set_text(state_str)
        
            
    def _update_machine_mode(self):
        if self.stat.task_mode == linuxcnc.MODE_MDI:
            self.mode = linuxcnc.MODE_MDI
            mode_str = "MDI"
            print "Machine is in MDI mode"
        elif self.stat.task_mode == linuxcnc.MODE_MANUAL:
            self.mode = linuxcnc.MODE_MANUAL
            mode_str = "MAN"
            print "Machine is in MANUAL mode"    
        elif self.stat.task_mode == linuxcnc.MODE_AUTO:
            self.mode = linuxcnc.MODE_AUTO
            mode_str = "AUTO"
            print "Machine is in AUTO mode" 
        else:
            state_str = "Unknown mode"
            print "Unknown mode!!!"
        self.widgets.mode_lable.set_text(mode_str)
        
        
    def _update_interp_state(self):
        if self.stat.interp_state == linuxcnc.INTERP_IDLE:
            self.interp = linuxcnc.INTERP_IDLE
            state_str = "IDLE"
            print "Interpreter is IDLE"
        elif self.stat.interp_state == linuxcnc.INTERP_READING:
            self.interp = linuxcnc.INTERP_READING
            state_str = "READ"
            print "Interpreter is READING"    
        elif self.stat.interp_state == linuxcnc.INTERP_PAUSED:
            self.interp = linuxcnc.INTERP_PAUSED
            state_str = "PAUS"
            print "Interpreter is PAUSED"
        elif self.stat.interp_state == linuxcnc.INTERP_WAITING:
            self.interp = linuxcnc.INTERP_WAITING
            state_str = "WAIT"
            print "Interpreter is WAITING"  
        else:
            state_str = "Unknown state"
            print "Unknown interp state!!!"
        self.widgets.interp_lable.set_text(state_str)     
            
                
    
    def _update_dros(self):
        
        if self.dro_actual_pos:
            # Get actual machine position
            pos = self.stat.actual_position
        else:
            # Get commanded machine position
            pos = self.stat.position
            
        # Get distance to go
        dtg = self.stat.dtg
        
        rel = []
        for joint in self.joint_list:
            rel.append(pos[joint] - self.stat.g5x_offset[joint] - self.stat.tool_offset[joint])
        
        if self.stat.rotation_xy != 0:
            t = math.radians(-self.stat.rotation_xy)
            xr = rel[0] * math.cos(t) - rel[1] * math.sin(t)
            yr = rel[0] * math.sin(t) + rel[1] * math.cos(t)
            rel[0] = xr
            rel[1] = yr
            
        for joint in self.joint_list:
            rel[joint] -= self.stat.g92_offset[joint]
            
        if self.display_metric != self.machine_metric: # We need to convert
            rel = self.convert_dro_units(rel)
            dtg = self.convert_dro_units(dtg)
            pos = self.convert_dro_units(pos)
        
        if self.display_metric:
            dec_plc = self.mm_dro_plcs
        else:
            dec_plc = self.in_dro_plcs
            
        # XXX - this is a hack, works for trivial configs, but not gantry etc.   
        # Put values in the DROs
        if not self.dro_has_focus: # Keep from overwriting user input
            for i in range(0, len(self.dro_list)):
                self.dro_list[i].set_text("%.*f" % (dec_plc, rel[self.joint_list[i]]))

        for i in range(0, len(self.dtg_list)):
            self.dtg_list[i].set_text("%.*f" % (dec_plc, dtg[self.joint_list[i]]))
        
        for i in range(0, len(self.abs_list)):
            self.abs_list[i].set_text("%.*f" % (dec_plc,pos[self.joint_list[i]]))
        
        
    def _update_work_cord(self):
        work_cords = [ "G53", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3" ]
        self.current_work_cord = self.stat.g5x_index
        self.widgets.work_cord_label.set_text(work_cords[self.current_work_cord])
        
        
    def _update_active_codes(self):
        active_codes = []
        for code in sorted(self.stat.gcodes[1:]):
            if code == -1: continue
            if code % 10 == 0:
                active_codes.append("G%d" % (code/10))
            else:
                active_codes.append("G%d.%d" % (code/10, code%10))
        for code in sorted(self.stat.mcodes[1:]):
            if code == -1: continue
            active_codes.append("M%d" % code)
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
        act_feed =  prog_feed * self.stat.feedrate  # Correct for feed override
        act_vel = self.stat.current_vel * 60.0      # Convert to units per min. Machine units???
        

        if self.stat.program_units == 1:            # If program is in inches
            vel_dec_plcs = self.in_vel_dec_plcs
            if "G95" in self.active_codes:          # If units per rev mode
                feed_dec_plcs = self.in_g95_dec_plcs
            else:
                feed_dec_plcs = self.in_feed_dec_plcs
            if self.machine_metric:
                 act_vel = act_vel / 25.4 # Is this conversion needed??
        else:                                       # The program is metric
            vel_dec_plcs = self.mm_vel_dec_plcs
            if "G95" in self.active_codes:          # If units per rev mode
                feed_dec_plcs = self.mm_g95_dec_plcs
            else:
                feed_dec_plcs = self.mm_feed_dec_plcs
            if not self.machine_metric:
                act_vel = act_vel * 25.4 # Is this conversion needed??
        
        # Set the labels
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
            self.widgets.spindle_speed_label.set_text('{:.0f}'.format(self.stat.spindle_speed))
            
            
    def _update_current_tool_data(self):
        self.current_tool = self.stat.tool_in_spindle
        self.current_tool_num = self.stat.tool_table[self.current_tool][1]
        self.current_tool_dia = self.stat.tool_table[self.current_tool][10]
        
        
    # FIXME This won't work properly till the "statetags" branch is merged
    def _update_cutting_parameters(self):
        if "G1" in self.active_codes and self.current_tool_dia != 0:
            self.surface_speed = self.spindle_speed * self.current_tool_dia * 0.2618
            self.chip_load = self.stat.current_vel * 60 / (self.spindle_speed + .01) * 2
            self.widgets.surface_speed_label.set_text('{:.1f}'.format(self.surface_speed))
            self.widgets.chip_load_label.set_text('{: .4f}'.format(self.chip_load))        
        else:        
            self.widgets.surface_speed_label.set_text("-")
            self.widgets.chip_load_label.set_text("-")


    def _get_axis_list(self):
        coordinates = self.get_ini_info.get_coordinates()
        coordinates = "".join(coordinates.split()).upper()
        self.axis_list = []
        for axis in coordinates:
            if axis in self.axis_list:
                continue
            if not axis in [ 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W' ]:
                continue
            self.axis_list.append(axis)

        if len(coordinates) != len(self.axis_list):
            print tc.E + 'Hazzy does not yet support gantry type machines!'
            
        # TODO Add support for gantry machines
        #    if self.stat.kinematics_type != linuxcnc.KINEMATICS_IDENTITY:
        #        print "Identity kinematics with more joints than axes"
        #        
        #    print "Coordinates:", coordinates
        #    
        #    for axis in [ 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W' ]:
        #        if coordinates.count(axis) > 1:
        #            # We have a gantry with something like XYYZ (or if we are RodW XXYZ!!)
        #            print tc.I + 'Machine is a gantry configuration' 
        #            
        #            if len(self.axis_list) == 3: # Gantry with no rotary axis
        #                print "Gantry with no rotary axis"
        #                self.joint_list = [0, 1, 2, 3]
        #              
        #                
        #            if len(self.axis_list) == 4: # Gantry with one rotary axis
        #                print "Gantry with one rotary axis"
        #                rotary_axis = [ 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W' ].index(self.axis_lisat[-1])
        #                self.joint_list = [0, 1, 2, 3] 
            
        else:
            for axis in coordinates:
                joint = [ 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W' ].index(axis)
                self.joint_list.append(joint)
        

    def _update_homing_status(self):
        homed_joints = [0]*9
        for joint in self.joint_list:
            if self.stat.homed[joint]:
                homed_joints[joint] = 1 # 1 indicates homed
                self.abs_list[joint].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('black'))
            elif self.stat.axis[joint]['homing'] != 0:
                homed_joints[joint] = 2 # 2 indicates homing in progress
                self.abs_list[joint].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('yellow'))
            else:
                homed_joints[joint] = 0 # 0 indicates unhomed
                self.abs_list[joint].modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color('red'))
        self.homed_joints = homed_joints


    #TODO Make so does not run if it does not need to 
    def _updade_dro_status(self):
        if self.is_moving() or not self.is_homed() or self.no_force_homing:
            # An eventbox is placed over the editable DROs, if it is visible it blocks them from events 
            self.widgets.dro_mask.set_visible(True)
            for axis in range(0, 4):
                self.dro_list[axis].modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('#908e8e'))
        else:
            self.widgets.dro_mask.set_visible(False)
            for axis in range(0, 4):
                self.dro_list[axis].modify_base(gtk.STATE_NORMAL, gtk.gdk.Color('white'))          



# =========================================================
## BEGIN - DRO entry handlers
# =========================================================

    def on_mdi_entry_changed(self, widget, data=None):
        # Convert MDI entry text to UPPERCASE
        self.widgets.mdi_entry.set_text(widget.get_text().upper())


    def on_dro_gets_focus(self, widget, event):
        self.dro_has_focus = True
        widget.select_region(0, -1)
        if self.numpad:
            touchpad.touchpad(widget)


    def on_dro_loses_focus(self, widget, data=None):
        self.dro_has_focus = False
        widget.select_region(-1, -1)
        self.window.set_focus(None)


    def on_dro_key_press_event(self, widget, event, data=None):
        if event.keyval == gtk.keysyms.Escape:
            self.dro_has_focus = False
            self.window.set_focus(None)
            #return True


    def on_dro_activate(self, widget):
        if widget == self.widgets.dro_x:
            axis = 'X'
        elif widget == self.widgets.dro_y:
            axis = 'Y'
        elif widget == self.widgets.dro_z:
            axis = 'Z'
        elif widget == self.widgets.dro_4:
            axis = 'A'

        self.set_work_offset(axis, widget.get_text())
        self.window.set_focus(None)
        
        
# =========================================================
## BEGIN - MDI entry handlers
# =========================================================
    
    def on_mdi_entry_gets_focus(self, widget, event):
        #if self.dro_is_locked:
        #    self.window.set_focus(None)
        #    return
        self.widgets.mdi_entry.set_text("")
        if self.mdipad: 
            #touchpad.touchpad(widget, True)
            keyboard.keyboard(widget, self.get_win_pos())
            
    def on_mdi_entry_loses_focus(self, widget, data=None):
        self.widgets.mdi_entry.set_text("MDI:")
        self.window.set_focus(None)
        
        
    def on_mdi_entry_key_press_event(self, widget, event): 
        if event.keyval == gtk.keysyms.Escape:
            self.window.set_focus(None)
            return True


    def on_mdi_entry_activate(self, widget):
        command = self.widgets.mdi_entry.get_text()
        if len(command) == 0:
            # Ignore an empty command
            return
        # Issue the command
        self.issue_mdi(command)
        # Set button to 'stop' so can kill MDI motion if need be
        self.set_cycle_start_button_state('stop')
        self.window.set_focus(None)
            
            
# =========================================================
## BEGIN - Helper functions
# =========================================================
                        
    def set_mode(self, mode):
        if self.stat.task_mode == mode:
            # If already in the desired mode do nothing
            return True
        self.command.mode(mode)
        self.command.wait_complete()
        return True
        
        
    def set_state(self, state):
        if self.stat.state == state:
            # If already in the desired state do nothing
            return True
        self.command.state(state)
        self.command.wait_complete()
        return True
        
        
    def issue_mdi(self, mdi_command):
        if self.set_mode(linuxcnc.MODE_MDI):
            print("Issuing MDI command: " + mdi_command)
            self.command.mdi(mdi_command)
            # Can't have a wait_complete() here or it locks up the UI
            
            
    def set_work_offset(self, axis, dro_text):
        try:
            dro_val = float(dro_text)
        except:
            self._show_message(["ERROR", "%s axis DRO entry '%s' is not a valid number" % (axis, dro_text)])
            return
        offset_command = 'G10 L20 P%d %s%.12f' % (self.current_work_cord, axis, dro_val)
        self.issue_mdi(offset_command)
        self.set_mode(linuxcnc.MODE_MANUAL)
        # FIXME This does not always work to display the new work offset
        self.widgets.gremlin.reloadfile(self.stat.file)

    
    def home_axis(self, joint):
        if self.stat.axis[joint]['homed'] == 0 and not self.stat.estop and self.stat.axis[joint]['homing'] == 0:
            self.set_mode(linuxcnc.MODE_MANUAL)
            self._show_message(["INFO", "Homing joint %s " % joint])
            self.command.home(joint)
            self.homed_joints[joint] = 2 # Indicate homing in process, needed to cause update of joint states
        elif self.stat.homed[joint]:
            message = ("joint %s is already homed. \n Unhome?" % joint)
            if dialogs.dialogs(message).run():
                self.set_mode(linuxcnc.MODE_MANUAL)
                self._show_message(["INFO", "Unhoming joint %s " % joint])
                self.command.unhome(joint)
        elif self.stat.axis[joint]['homing'] != 0:
            self._show_message(["ERROR", "Homing sequence already in progress"])
        else:
            self._show_message(["ERROR", "Can't home joint %s, check E-stop and machine power" % joint])
            
    
    # Check if all joints are homed  
    def is_homed(self):
        for joint in self.joint_list:
            if not self.stat.homed[joint]:
                return False
        return True            
        
            
    # Convert DRO units back and forth from in to mm    
    def convert_dro_units(self, values):
        out = []
        for joint in self.joint_list:  
            out.append(values[joint] * self.conversion[joint])
        return out
        

    # Check if the machine is moving due to MDI, program execution, etc.        
    def is_moving(self):
        # http://wallacecompany.com/tmp/probing.py
        # self.stat.state (returns integer) for current command execution status. One of RCS_DONE, RCS_EXEC, RCS_ERROR.
        if self.stat.state == linuxcnc.RCS_EXEC:
            return True
        else:
            return self.stat.task_mode == linuxcnc.MODE_AUTO and self.stat.interp_state != linuxcnc.INTERP_IDLE


    # Set image from file
    def set_image(self, image_name, image_file):
        self.builder.get_object(image_name).set_from_file(os.path.join(IMAGEDIR, image_file))
        
          
    # Set animation from file         
    def set_animation(self, image_name, image_file):
        if image_file == None:
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
        self.close_window()
        return True # If does not return True will close window without popup! 


    # Display a dialog to confirm exit
    def close_window(self):
        message = "Are you sure you want \n to close LinuxCNC?"
        if dialogs.dialogs(message).run():
            print tc.I + "Turning machine off and E-stoping..."
            self.set_state(linuxcnc.STATE_OFF)
            self.set_state(linuxcnc.STATE_ESTOP)
            print tc.I + "Hazzy UI will now quit"
            gtk.main_quit()
            
        
# =========================================================
## BEGIN - init functions
# =========================================================
    
    # Decorate the window if screen is big enough
    def _init_window(self):
        screen_w = gtk.gdk.Screen().get_width()
        screen_h = gtk.gdk.Screen().get_height()
        if screen_w > 1024 and screen_h > 768:
            print(tc.I + "Screen size: " + str(screen_w)+ " x " + \
            str(screen_h) + "  Decorating the window!")
            self.window.set_decorated(True)
        else:
            print(tc.I + "Screen size: " + str(screen_w)+ " x "\
             + str(screen_h) + "  Screen too small to decorate window")
            
        
    # init the preview
    def _init_gremlin(self):
        self.widgets.gremlin.set_property('view', 'z')
        self.widgets.gremlin.set_property("mouse_btn_mode", 2)
        self.widgets.gremlin.grid_size = 1.0
        self.widgets.gremlin.set_property("metric_units", int(self.stat.linear_units))
        self.widgets.gremlin.set_property("use_commanded", not self.dro_actual_pos)
        
        
    def _init_gcode_preview(self):
        self.preview_buf = gtksourceview.Buffer()
        self.preview_buf.set_max_undo_levels(20)
        self.widgets.gcode_preview.set_buffer(self.preview_buf)
        
        # Set style scheme and language 
        self.lm = gtksourceview.LanguageManager()
        self.sm = gtksourceview.StyleSchemeManager()
        if self.lang_spec_name != None:
            self.preview_buf.set_language(self.lm.get_language(self.lang_spec))
        if self.style_scheme_name != None:
            self.preview_buf.set_style_scheme(self.sm.get_scheme(self.style_scheme))
    
        
    def load_gcode_preview(self, fn=None):
        self.preview_buf.begin_not_undoable_action()
        if not fn or not os.path.splitext(fn)[1] in self.preview_ext:
            self.preview_buf.set_text('\t\t\t\t\t*** No file to Preview ***')
            self.preview_buf.set_modified(False)
            return 
        self.preview_buf.set_text(open(fn).read())
        self.preview_buf.end_not_undoable_action()
        self.preview_buf.set_modified(False)


            
    # If no "save as" file name specified save to the current file in preview    
    def save(self, fn = None):
        if fn == None:
            fn = self.current_preview_file
        text = self.preview_buf.get_text(self.preview_buf.get_start_iter(), self.preview_buf.get_end_iter())
        openfile = open(fn, "w")
        openfile.write(text)
        openfile.close()
        self.preview_buf.set_modified(False)
        print "Saved file as: ", fn 
        
        
    def get_win_pos(self):
        pos = self.window.get_position()
        return pos
        

def main():
    gtk.main()

if __name__ == "__main__":
    ui = hazzy()
    main()
