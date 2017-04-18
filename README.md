# hazzy

A UI for LinuxCNC designed for use with touch screens

![Main screen with back-plot](/screenshots/Screenshot_1.png?raw=true "Main screen with back-plot")

##### File selection tab with G-code preview/edit window and pop-up keyboard
![File selection page](/screenshots/Screenshot_2.png?raw=true "File selection page")

##### Tool offsets tab with pop-up numberpad
![Tool edit page](/screenshots/Screenshot_3.png?raw=true "Optional Title")

### Introduction
Hazzy is an attempt at a new UI for LinuxCNC specifically intended for use on my RF45 clone milling machine. It will work with LinuxCNC 2.8 and should support any machine with trivial kinematics and up to 5 axes, including gantry configurations. The code is greatly influenced by Norbert's Gmoccapy, however, for better or worse, hazzy makes very sparing use of the HAL VCP widgets.

### Features
* Pop-up keypads on all entries
* Type in DRO to set work offsets
* Expression entry support
    * Ex. entering 23/64 --> .3594
    * Ex. entering 1 + 1/64 --> 1.0156
    * Works in offset DROs and tooltable
* Unit entry support
    * Ex. entering 1in --> 25.4 if the machine is metric or G21 is active
    * Ex. entering 6.35mm --> .25 if the machine is inch or G20 is active 
    * Works in offset DROs and tooltable

### Installing

The UI is very much under development, so I don't recommend running a machine with it at this stage. However, if you want to give hazzy a spin I have included several sim configs in the sim.hazzy folder, you should also be able to run almost any of the sim configs includes with LinuxCNC.  

The easiest way to try hazzy is to clone this repository and place a symbolic link to hazzy.py in your usr/bin directory.

To clone this repository open a terminal at any convenient location (e.g. Desktop) and say
```
git clone https://github.com/KurtJacobson/hazzy
```

Enter the newly cloned hazzy directory by saying
```
cd hazzy
```

Then add a link to hazzy.py to your usr/bin directory by saying  

```
sudo ln -sf $(pwd)/hazzy.py /usr/bin/hazzy
```

The last step is to tell Linuxcnc to use hazzy as the UI. In your machine's ini file under the [DISPLAY] section set DISPLAY = hazzy


If all went well that is it!  Start LinuxCNC however you normally would and click the Reset button. If the machine starts up in E-stop clicking Reset the first time puts the machine in E-stop Reset, click Reset again to turn the machine ON.  Home the machine by clicking on the ABS DROs.  If you click on the ABS DRO label all axes will be homed (assuming the ini file is configured correctly).


I will be updating this repo frequently. To get the latest version enter your hazzy directory and say
```
git pull origin master
```

Feedback of all types would be gratfully accepted at: kurtcjacobson at gmail
