# hazzy

A UI for LinuxCNC designed for use with touchscreens

![Main screen with back-plot](/screenshots/Screenshot_1.png?raw=true "Main screen with back-plot")

##### File selection tab with G-code preview/edit window and pop-up keyboard
![File selection page](/screenshots/Screenshot_2.png?raw=true "File selection page")

##### Tool offsets tab with pop-up numberpad
![Tool edit page](/screenshots/Screenshot_3.png?raw=true "Optional Title")

### Introduction
Hazzy is an attempt at a UI for LinuxCNC that is uncompromised when used exclusively with a touchscreen (1024 x 728 ideally) and a basic control panel or MPG. It is designed to work with LinuxCNC 2.8 and should support any machine with trivial kinematics and up to 5 axes, including gantry configurations. I hope to make the interface customizable in the future by the use of embeddable panels and notebook pages.

### Features
* Pop-up keypads on all entries
* Type in DRO to set work offsets
* Expression evaluation in entry fields
    * Ex. entering 23/64 --> .3594
    * Ex. entering 1 + 1/64 --> 1.0156
    * Works in all floating point entries
* Unit conversions in entry fields
    * Ex. entering 1in --> 25.4 if the machine is metric or G21 is active
    * Ex. entering 6 + .35mm --> .25 if the machine is imperial or G20 is active 
    * Works in all unit specific entries
* Full touchscreen friendly file manager
    * Cut, Copy and Paste files and folders
    * Rename files and folders
    * Move files and folders to trash
    * Bookmark frequently used folders


### Installing

The UI is very much under development, so I don't recommend running a machine with it at this stage. However, if you want to give hazzy a spin I have included several sim configs in the sim.hazzy folder, you should also be able to run almost any of the sim configs included with LinuxCNC.  

If you have GIT installed the easiest way to try hazzy is to clone this repository and place a symbolic link to hazzy.py in your usr/bin directory. If you don't have git you can download and extract the zip and continue from step two. 

1. To clone this repository open a terminal at any convenient location (e.g. Desktop) and say

    ```$ git clone https://github.com/KurtJacobson/hazzy```

2. Enter the hazzy folder in the newly cloned hazzy directory by saying

    ```$ cd hazzy/hazzy```

3. Then add a link to hazzy.py to your usr/bin directory by saying

    ```$ sudo ln -sf $(pwd)/hazzy.py /usr/bin/hazzy```

4. The last step is to tell LinuxCNC to use hazzy as the UI. In your machine's ini file under the [DISPLAY] section set DISPLAY = hazzy

**Note:** If you prefer not to add a link to usr/bin you could skip step 3 and and enter the full path to hazzy.py in the INI file.  **Ex.** ```DISPLAY = /home/kurt/Desktop/hazzy/hazzy/hazzy.py```  This is fine but keep in mind that you will have to change the DISPLAY entries in all the example configurations before they will run.


If all went well that is it!  Start LinuxCNC however you normally would and click the Reset button. If the machine starts up in E-stop clicking Reset the first time puts the machine in E-stop Reset, click Reset again to turn the machine ON.  Home the machine by clicking on the ABS DROs.  If you click on the ABS DRO label all axes will be homed (assuming the ini file is configured correctly).


I will be updating this repository frequently. To get the latest version enter your hazzy directory and say

   ```$ git pull origin master```

If you have any problems, questions or suggestions, however minor, do not hesitate to open an issue, or better yet, a pull request!

### About Jogging
Hazzy does not support on-screen jogging. This is because I do not think it is a good idea to trust even the best industrial touchscreen with control of such a potentially disastrous operation. A single missed key release, caused by an oily chip or a little bit of spit on the screen, or the touchscreen driver crashing, or, whatever, could ruin days worth of work. For these reasons I strongly recommend that all jogging be handled by the real time components (FPGA cards etc.). All that being said , hazzy does have basic keyboard jogging, intended for use during initial machine setup and testing. It can be enabled by setting ```[JOGGING] USE_KEYBOARD = YES``` in the <machine_name>.prefs file located in the config directory.

Hazzy does work well with an MPG, which is what use. I have some info on setting up a basic MPG here: https://github.com/KurtJacobson/RF45-CNC/wiki/LinuxCNC-MPG

### Notes
I started working on this project some time in 2015 with the intention of trying to learn some basic programing (I am a mechanical/nuclear engineer by training, with little if any programing experience) while also learning about Linux and LinuxCNC.  My idea was to make a Haas like interface for LinuxCNC, hence the name hazzy, but it has morphed into something more like Mach3 or PathPilot.  It has been a great learning experience and I have had a lot of fun working on it the project.  I hope you enjoy!


Feedback of all types would be appreciated: kurtcjacobson at gmail
