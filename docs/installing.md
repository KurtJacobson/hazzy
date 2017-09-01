# Installing

The UI is very much under development, so I would not recommend running a machine
with it at this stage. However, if you want to give hazzy a spin, I have included
several sim configs in the sim.hazzy folder. You should also be able to run
almost any of the sim configs included with LinuxCNC.

If you have git installed, the easiest way to try hazzy is to clone the
[hazzy repository](https://github.com/KurtJacobson/hazzy), and place a symbolic link 
to hazzy.py in your usr/bin directory. If you don't have git, you can download 
and extract the zip, then continue from Step 2. To clone this repository:

1. Open a terminal at the destination location and say

    ```$ git clone https://github.com/KurtJacobson/hazzy```

2. Enter the hazzy folder in the newly cloned hazzy directory

    ```$ cd hazzy/hazzy```

3. Add a link to hazzy.py to your usr/bin directory

    ```$ sudo ln -sf $(pwd)/hazzy.py /usr/bin/hazzy```

4. Tell LinuxCNC to use hazzy as the UI. In your machine's INI file set

    ```[DISPLAY] DISPLAY = hazzy```

!!! note
    If you prefer not to add a link to ```usr/bin```, you could skip Step 3
    and enter the full path to hazzy.py in the INI file.

    **Ex.** ```DISPLAY = /home/kurt/Desktop/hazzy/hazzy/hazzy.py```

    This is fine, but keep in mind that you will have to change the DISPLAY
    entries in all the example configurations before they will run.


If all went well, you should be able to start LinuxCNC as usual.

Click the Reset button. If the machine starts up in E-stop, clicking Reset the
first time will put the machine in E-stop Reset. Click Reset again to turn the
machine ON. Home the machine by clicking on the ABS DROs. If you click on the
ABS DRO label, all axes will be homed (assuming the INI file is configured correctly).


I will be updating this repository frequently. To get the latest version, enter
your hazzy directory and say

   ```$ git pull origin master```

If you have any problems, questions or suggestions, however minor, do not
hesitate to [open an issue](https://github.com/KurtJacobson/hazzy/issues/new),
or better yet, a pull request!
