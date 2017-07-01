import gremlin

#self.gremlin = HazzyGremlin(self,680,410)

class HazzyGremlin(gremlin.Gremlin):
    def __init__(self, ui, width, height):
        print "INIfile", ui.inifile
        gremlin.Gremlin.__init__(self, ui.inifile)
        self.status = ui.stat
        self.ui_view = 'p'
        self.ui = ui
        self.g21 = self.status.gcodes[5] == 210
        self.grid_size = (10.0/25.4) if self.g21 else 0.5
        self.connect("button_press_event", self.on_gremlin_double_click)
        self.set_size_request(width, height)

    def realize(self,widget):
        super(Tormach_Mill_Gremlin, self).realize(widget)

    def set_grid_size(self, size):
        self.grid_size = size
        self._redraw()

    # necessary to support recent changes to gremlin in 2.6.  We might want to make this configurable
    # down the road, but for now it's set to a grid of .1 inches.  The grid doesn't display for me
    # but at least the ui will load without error again.
    ###def get_grid_size(self):
    ###    return .5

    def get_view(self):
        # gremlin as used as a gladevcp widegt has a propery for the view, which for a lathe
        # should be 'y'.  When it's not right the program extents won't be drawn.
        view_dict = {'x':0, 'y':1, 'z':2, 'p':3}
        return view_dict.get(self.ui_view)

    def get_show_metric(self):
        if self.status.gcodes[5] == 200:
            return False
        else:
            return True

    def posstrs(self):
        l, h, p, d = gremlin.Gremlin.posstrs(self)
        return l, h, [''], ['']

    def report_gcode_error(self, result, seq, filename):
        import gcode
        error_str = gcode.strerror(result)
        error_str = "\n\nG-Code error in " + os.path.basename(filename) + "\n" + "Near line: " + str(seq) + "\n" + error_str + "\n"
        self.ui.error_handler.write(error_str)
        self.ui.interp_alarm = True

    def report_gcode_warnings(self, warnings, filename, suppress_after = 3):
        """ Show the warnings from a loaded G code file.
        Accepts a list of warnings produced by the load_preview function, the
        current filename, and an optional threshold to suppress warnings after.
        """

        num_warnings = len(warnings)
        if num_warnings == 0:
            return

        # Find the maximum number of warnings to print
        max_ind = min(max(suppress_after,0), num_warnings)
        # Find out how many we're suppressing if any
        num_suppressed = max(num_warnings-max_ind,0)
        
        # warn, but still switch to main page if loading the file
        self.ui.notebook.set_current_page(MAIN_PAGE)
        
        #Iterate in reverse to print a coherent list to the status window, which shows most recent first
        if num_suppressed:
            self.ui.error_handler.write("Suppressed %d more warnings" % num_suppressed, ALARM_LEVEL_LOW)
        else:
            if num_warnings > 1: self.ui.error_handler.write("*** End of warning list ***", ALARM_LEVEL_LOW)
        for w in warnings[max_ind::-1]:
            # Add a space to show that the warning is part of the list
            self.ui.error_handler.write("  "+w, ALARM_LEVEL_LOW)

        warning_header = "G-Code warnings in %s " % os.path.basename(filename) + ":"
        self.ui.error_handler.write(warning_header, ALARM_LEVEL_LOW)

        self.ui.interp_alarm = True
              
    def on_gremlin_double_click(self, widget, event, data=None):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.clear_live_plotter()
            return
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            # it's a right click if event.button == 3
            menu = gtk.Menu()
            set_front_view = gtk.MenuItem("Front View")
            set_top_view = gtk.MenuItem("Top View")
            set_side_view = gtk.MenuItem("Side View")
            set_iso_view = gtk.MenuItem("Iso View")
            enable_fourth_display = gtk.MenuItem("Enable A Axis Display")
            disable_fourth_display = gtk.MenuItem("Disable A Axis Display")
            set_front_view.connect("activate", self.set_front_view)
            set_top_view.connect("activate", self.set_top_view)
            set_side_view.connect("activate", self.set_side_view)
            set_iso_view.connect("activate", self.set_iso_view)
            enable_fourth_display.connect("activate", self.enable_fourth_axis_toolpath_display)
            disable_fourth_display.connect("activate", self.disable_fourth_axis_toolpath_display)
            menu.append(set_iso_view)
            menu.append(set_top_view)
            menu.append(set_front_view)
            menu.append(set_side_view)

            imperial = not self.ui.g21
            sml_text = "Grid 0.1 inch" if imperial else "Grid 5 mm"            
            med_text = "Grid 0.5 inch" if imperial else "Grid 10 mm"
            lrg_text = "Grid 1.0 inch" if imperial else "Grid 25 mm"

            set_grid_size_small = gtk.MenuItem(sml_text)
            set_grid_size_med = gtk.MenuItem(med_text)
            set_grid_size_large = gtk.MenuItem(lrg_text)
            set_grid_size_none = gtk.MenuItem("No Grid")

            set_grid_size_small.connect("activate", self.set_grid_size_small)
            set_grid_size_med.connect("activate", self.set_grid_size_med)
            set_grid_size_large.connect("activate", self.set_grid_size_large)
            set_grid_size_none.connect("activate", self.set_grid_size_none)

            menu.append(set_grid_size_small)
            menu.append(set_grid_size_med)
            menu.append(set_grid_size_large)
            menu.append(set_grid_size_none)
            
            menu.append(enable_fourth_display)
            menu.append(disable_fourth_display)            

            menu.popup(None, None, None, event.button, event.time)
            set_front_view.show()
            set_side_view.show()
            set_top_view.show()
            set_iso_view.show()
            
            if self.ui_view != 'p':
                set_grid_size_small.show()
                set_grid_size_med.show()
                set_grid_size_large.show()
                
            try:
                if self.ui.redis.hget('machine_prefs', 'enable_fourth_axis_toolpath') == 'True':
                    disable_fourth_display.show()
                else:
                    enable_fourth_display.show()
            except:
                enable_fourth_display.show()

    def set_current_ui_view(self):
        if self.ui_view == 'y':
            self.set_front_view()
        elif self.ui_view == 'x':
            self.set_side_view()
        elif self.ui_view == 'z':
            self.set_top_view()
        elif self.ui_view == 'p':
            self.set_iso_view()
            
    def set_front_view(self, widget=None):
        self.set_view_y()
        self.ui_view = 'y'
        self._redraw()
        return

    def set_side_view(self, widget=None):
        self.set_view_x()
        self.ui_view = 'x'
        self._redraw()
        return

    def set_top_view(self, widget=None):
        self.set_view_z()
        self.ui_view = 'z'
        self._redraw()
        return

    def set_iso_view(self, widget=None):
        self.set_view_p()
        self.ui_view = 'p'
        self._redraw()
        return

    def set_grid_size_small(self, widget):
        size = (5/25.4) if self.ui.g21 else .1
        self.set_grid_size(size)

    def set_grid_size_med(self, widget):
        size = (10/25.4) if self.ui.g21 else .5
        self.set_grid_size(size)

    def set_grid_size_large(self, widget):
        size = (25/25.4) if self.ui.g21 else 1.0
        self.set_grid_size(size)

    def set_grid_size_none(self, widget):
        self.set_grid_size(0.0)
        
    def enable_fourth_axis_toolpath_display(self, widget):
        self.ui.redis.hset('machine_prefs', 'enable_fourth_axis_toolpath', 'True')
        self.set_geometry('AXYZ')
        
    def disable_fourth_axis_toolpath_display(self, widget):
        self.ui.redis.hset('machine_prefs', 'enable_fourth_axis_toolpath', 'False')
        self.set_geometry('XYZ')

