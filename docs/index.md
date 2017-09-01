# Welcome to hazzy Docs!

Hazzy is an attempt at a highly configurable and touchscreen friendly UI for 
[LinuxCNC](http://linuxcnc.org/). It is written in python and GTK+ 3, and takes
advantage of the latest GTK+ widgets and their excellent touchscreen support.

It is designed to work with LinuxCNC 2.8 and currently supports any machine with
trivial kinematics and up to 9 axes, including gantry configurations.

## Features
* Pop-up keypads on all entries
* Type in DRO to set work offsets
* Expression evaluation in entry fields
    * Ex. entering 23/64 --> .3594
    * Ex. entering 1 + 1/64 --> 1.0156
    * Works in all floating point entries
* Unit conversions in entry fields
    * Ex. entering 1in --> 25.4 if the machine is metric or G21 is active
    * Ex. entering 6 + .35mm --> .25 if the machine is Imperial or G20 is active
    * Works in all unit specific entries
* Full touchscreen friendly file manager
    * Cut, Copy and Paste files and folders
    * Rename files and folders
    * Move files and folders to trash
    * Bookmark frequently used folders


## Notes
I started working on this project in the summer of 2015 with the intention of
learning some basic programing, while also learning about Linux and LinuxCNC.
My plan was to make a Haas-like interface for LinuxCNC; hence, the name hazzy.
It has since morphed into something _very_ different. It has been a great
learning experience. I have had a lot of fun working on the project, and
I hope it might be of some value to others.
