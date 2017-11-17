[![Travis CI][Travis-badge]](https://travis-ci.org/KurtJacobson/hazzy)
[![LinuxCNC 2.8][linuxcnc-badge]](https://github.com/LinuxCNC/linuxcnc)
[![Chat on IRC ][irc-badge]](https://kiwiirc.com/client/irc.kiwiirc.com/hazzy)

[Travis-badge]: https://img.shields.io/travis/KurtJacobson/hazzy/GTK3.svg?label=docs
[linuxcnc-badge]: https://img.shields.io/badge/LinuxCNC-%202.8-blue.svg
[irc-badge]: https://img.shields.io/badge/Chat%20on%20IRC-%23hazzy-green.svg


## DISCLAIMER

THE AUTHORS OF THIS SOFTWARE ACCEPT ABSOLUTELY NO LIABILITY FOR
ANY HARM OR LOSS RESULTING FROM ITS USE.  IT IS _EXTREMELY_ UNWISE
TO RELY ON SOFTWARE ALONE FOR SAFETY.  Any machinery capable of
harming persons must have provisions for completely removing power
from all motors, etc, before persons enter any danger area.  All
machinery must be designed to comply with local and national safety
codes, and the authors of this software can not, and do not, take
any responsibility for such compliance.

This software is released under the GPLv2.


# hazzy: A UI for LinuxCNC

hazzy is a modern GTK+ interface for LinuxCNC written in Python  


## Installation and Usage

See the [documentation](https://kurtjacobson.github.io/hazzy/).

## Resources

* [Development](https://github.com/KurtJacobson/hazzy/)
* [Documentation](https://kurtjacobson.github.io/hazzy/)
* [Freenode IRC](http://webchat.freenode.net/?channels=%23hazzy) (#hazzy)
* [Issue Tracker](https://github.com/KurtJacobson/hazzy/issues)


## Dependancies

* LinuxCNC master (2.8~pre)
* Gtk+ v3.22.11 or later
* Python 2.7

Hazzy is developed and tested using the LinuxCNC Debian 9 (stretch)
[Live ISO](http://www.linuxcnc.org/testing-stretch-rtpreempt/). It should run
on any system that has Gtk+ v3.22.11 or later installed, unfortunately I have
not been able to install that version of Gtk+ on Debian 8 (wheezy), though it
should be possible.


## Contributors

* Kurt Jacobson: initiated the project
* TurBoss: fixed the bugs
