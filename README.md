# hazzy

A new UI for LinuxCNC designed for use with touch screens

![Main screen with back-plot](/screenshots/Screenshot_1.png?raw=true "Optional Title")


##### File selection tab with G-code preview/edit window and pop-up keyboard
![File selection page](/screenshots/Screenshot_2.png?raw=true "Optional Title")

##### Tool offsets tab with pop-up number-pad
![Tool edit page](/screenshots/Screenshot_3.png?raw=true "Optional Title")


### Installing

This UI is very much under development and is not fully functional yet. However, it does support homing and you should be able to test it out on a 4 axis sim config if you want. I don't recommend running a machine with it at this stage, although I do.
The easiest way to try hazzy is to clone this repository and than place symbolic links in the correct places.

To clone this repository open a terminal at a convenient location (e.g. Desktop) and say:
```
git clone https://github.com/KurtJacobson/hazzy
```
Next place a  symbolic link to the hazzy folder in you machines config directory. In debian you can do this by dragging the folder into your config directory and holding **Shift+Ctrl** before dropping the folder.

The last step is to put a link to hazzy.py in your usr/bin directory. To do this graphically open a root file browser. On Debian say
```
sudo thunar
```
If you are using Ubuntu you might need to say
```
 sudo nautilus
```

Navigate to **usr/bin** and create a link to hazzy.py in the same manner as you did for the folder above. *You will need to remove the .py extension from the link or hazzy will not run.*

The last step is to tell Linuxcnc to use hazzy as the UI. In your machines ini file change [DISPLAY] DISPLAY = hazzy

That should be all you need to do to try hazzy. If this does not work for you let me know!
