# hazzy

A new UI for LinuxCNC designed for use with touch screens

![Main screen with back-plot](/screenshots/Screenshot_1.png?raw=true "Optional Title")


##### File selection tab with G-code preview/edit window and pop-up keyboard
![File selection page](/screenshots/Screenshot_2.png?raw=true "Optional Title")

##### Tool offsets tab with pop-up number-pad
![Tool edit page](/screenshots/Screenshot_3.png?raw=true "Optional Title")


### Installing

The UI is very much under development, and is not fully functional yet, so I don't recommend running a machine with it at this stage.  However, if you want to give hazzy a spin it should run fine on any basic 4-axis sim config. 

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


I will be updating this repo frequently. To get the latest commits say
```
git pull origin master
```
in your hazzy directory
