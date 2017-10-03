# Status Monitor

Hazzy uses GObject signaling to inform its widgets of any changes to the status
of linuxcnc. status.py runs in a 50ms loop and 'listens' for any changes in the
`linuxcnc.stat` attributes. When a change is detected, status.py emits a GObject
signal with the same name as the attribute that changed, and passes along
the updated value. A python script can connect a callback to these signals, which
can then perform any necessary updates when a signal is received.

This is referred to as event-driven programing, and has several advantages:

* Instead of having each widget actively polling LinuxCNC for status updates, at
  (say) 100ms intervals (regardless of whether a change has actually occurred),
  only one script (status.py) needs to poll for changes. This reduces the load on 
  the LinuxCNC status channel.

* Widgets can simply connect a callback, wait for a signal to be received,
  and then update only what is necessary. This greatly reduces the load on the
  system by avoiding useless screen refreshes, etc.


!!! note
    status.py monitors only the `linuxcnc.stat` attributes which have been
    connected to a callback. This is to avoid needless monitoring of attributes,
    and emission of signals which are not used.


## Connecting Callbacks

status.on_changed(_**attribute**_, _**callback**_)

where _**attribute**_ is any [linuxcnc.stat](http://linuxcnc.org/docs/devel/html/config/python-interface.html#_linuxcnc_stat_attributes) attribute and _**callback**_ is the method to be called when the value of that attribute changes.

## Examples

Here is a basic example that prints the tool number when the
`linuxcnc.stat.tool_in_spindle` attribute changes.

```python
#!/usr/bin/env python

from hazzy.utilities import status

def update_tool(status, tool_num):
    print tool_num

# Connect "tool_in_spindle" changed signal to "update_tool" callback
status.on_changed('tool_in_spindle', update_tool)
```

status.py also monitors the `linuxcnc.stat.joint` dictionaries for changes. So 
it is simple to do things like keep track of the homing status, report the current
following error, etc.

Here is an example of printing the following error for each joint used in the machine

```python
def print_ferror(status, joint_num, ferror):
    print 'joint {} f-error: {:.5f}'.format(joint_num, ferror)

# Connect "joint.ferror_current" changed signal to "print_ferror" callback
status.on_changed('joint.ferror_current', print_ferror)
```

!!! note
    This is roughly equivalent to the pseudo code

    ```python
    while True:
        stat.poll()

        for jnum in range(num_joints):
            if ferror has changed:
                print stat.joint[jnum]['ferror_current']

        sleep(.05)
    ```

    So the signal will only be emitted if the value has changed since the previous 
    emission. If no joints are moving no signal will be emitted. If one joint
    is moving, only the ferror for that joint will be emitted, etc.


## Additional Signals

In addition to the [linuxcnc.stat](http://linuxcnc.org/docs/devel/html/config/python-interface.html#_linuxcnc_stat_attributes)
attributes, status.py also has five convenience signals.


### axis-positions

The _axis-position_ signal is emitted every cycle and returns a tuple of 
three tuples of floats representing:

1. Current absolute axis positions in machine units, taking into account the 
  setting of `[DISPLAY] POSITION_FEEDBACK` in the INI

2. Current g5x relative position in machine units, taking into account any
  active g92 offsets, rotation in the XY plane, and/or tool offsets

3. Remaining distance of the current move, as reported by the trajectory planner

!!! note
    Only the position values for used axes are calculated, the positions of all
    unused axes will be reported as 0. Status.py uses the the value of
    linuxcnc.axis_mask do determine which axes are in use. This should reflect
    the axes as defined by `[TRAJ] COORDINATES` in the INI.


### joint-positions

The _joint-positions_ signal is emitted every cycle and returns a tuple of
floats representing:

* Current absolute joint positions in machine units, taking into account the
  setting of `[DISPLAY] POSITION_FEEDBACK` in the INI


### formated-gcodes

The _formated-gcodes_ signal returns a list containing the currently active
g-codes formed as strings.

Example:

```python
def update_gcodes(widget, gcodes):
    print "G-codes: ", " ".join(gcodes)

status.on_changed('formated_gcodes', update_gcodes)
```

Result: ```G-codes:  G8 G17 G20 G40 G49 G54 G64 G80 G90 G91.1 G94 G97 G99```


### formated-mcodes

The _formated-mcodes_ signal returns a list containing the currently active
m-codes formed as strings.

Example:

```python
def update_mcodes(widget, mcodes):
    print "M-codes: ", " ".join(mcodes)

status.on_changed('formated_mcodes', update_mcodes)
```

Result: ```M-codes:  M0 M5 M9 M48 M53```


### file-loaded

The _file-loaded_ signal is emitted when a file is loaded and returns the full
path to the file. This makes an attempt to avoid spurious emissions resulting
from remap procedures.
