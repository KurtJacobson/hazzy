## Installing

The UI is very much under development, so I would not recommend running a machine
with it at this stage. However, if you want to give hazzy a spin, I have included
several sim configs in the sim.hazzy folder. You should also be able to run
almost any of the sim configs included with LinuxCNC.

If you have git installed, the easiest way to try hazzy is to clone the
[hazzy repository](https://github.com/KurtJacobson/hazzy), and place a symbolic link 
to hazzy.py in your usr/bin directory. If you don't have git, you can download 
and extract the zip, then continue from Step 2. To clone this repository:

1. Open a terminal at the destination location and say

    `$ git clone https://github.com/KurtJacobson/hazzy`

2. Enter the hazzy folder in the newly cloned hazzy directory

    `$ cd hazzy/hazzy`

3. Link the hazzy startup script to your usr/bin directory

    `$ sudo ln -sf $(pwd)/hazzy /usr/bin/hazzy`

4. Tell LinuxCNC to use hazzy as the UI. In your machine's INI file set

    `[DISPLAY] DISPLAY = hazzy`

!!! note
    If you don't want to add a link to ```usr/bin```, you can skip Step 3
    and simply enter the full path to the startup script in the INI file.

    **Ex.** ```DISPLAY = /home/kurt/Desktop/hazzy/hazzy/hazzy.py```

    This is fine, but keep in mind that you will have to change the DISPLAY
    entries in all the example configurations before they will run.


## Running the Example Configs

Hazzy ships with several example configs. These can be launched by specifying
them when starting LCNC from the comand line

`$ linuxcnc /path/to/hazzy/sim.hazzy/hazzy_XYZ.ini`

Or they can be made available from the LCNC config picker by recursively
copying the entire `sim.hazzy` directory to `~/linuxcnc/configs`

`$ cp $(pwd)/sim.hazzy $HOME/linuxcnc/configs -r`


## Updating

This repo is updated frequently. To get the latest version, enter the
directory were you cloned hazzy and say

   `$ git pull origin master`

If you have any problems, questions or suggestions, however minor, do not
hesitate to [open an issue](https://github.com/KurtJacobson/hazzy/issues/new),
or better yet, a pull request!
