##### _DStat is described in detail in [Dryden MDM, Wheeler AR (2015) DStat: A Versatile, Open-Source Potentiostat for Electroanalysis and Integration. PLoS ONE 10(10): e0140349. doi: 10.1371/journal.pone.0140349](http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0140349) If you use this information in published work, please cite accordingly._
---

This is the documentation for the DStat interface software.
The DStat interface is written primarily in Python and runs on Linux, Mac, and Windows.
It is the main method for running experiments on the DStat, controlling experimental parameters and collecting and plotting data.
It currently has no abilities for analyzing recorded data or opening previously saved data files, but data is saved in a simple text format or numpy-compatible binary format and plots can be saved as images.

## Table of Contents:

1. [Installation](#Installation)
	1.  [Manual Install](#manual-install)
    1.  [pip Install](#pip-install)
2. [Getting Started](#Getting-Started)

# Introduction
The DStat interface is written primarily in Python and runs on Linux, Mac, and Windows.
It is the main method for running experiments on the DStat, controlling experimental parameters and collecting and plotting data.
It currently has no abilities for analyzing recorded data or opening previously saved data files, but data is saved in a simple text format or numpy-compatible binary format and plots can be saved as images.

*New in version 1.3:* dstat-interface-mrbox can now save all data files to a ZODB database for later analysis.
The old autosave functionality has still been retained.

# Installation
Unfortunately, due to the python packages used, dstat-interface-mrbox is difficult to make into a single self-contained package, so for the time being, the simplest way to run it is to install a python distribution. dstat-interface-mrbox itself, therefore, requires no installation and can be run from any directory by executing `/dstat-interface-mrbox/main.py` with python.

## Manual Install

Python and related packages needed: (versions listed are tested, older versions may still work)

* Python (2.7.9)
* matplotlib (1.4.3—compiled with gtk backend)
* numpy (1.9.2)
* py2cairo (1.10.0)
* pyserial (2.7)
* pygtk (2.24.0)
* pygobject (2.28.6)
* XQuartz (2.7.7)
* zeromq (4.0.5) and pyzmq (14.6.0)
* pyyaml (3.11)
* zodb
* zeo
* psutil

Optional:

* seaborn (0.7.0)—Makes prettier plots if available

### Mac OS X
The easiest way to get most of the necessary requirements to run dstat-interface-mrbox is using [Homebrew](http://brew.sh):

	brew tap homebrew/python
	brew update
	brew install python pygtk pygobject py2cairo zeromq
	brew install matplotlib --with-pygtk

Be patient on the last step—matplotlib needs to be compiled and may take 2 or 3 minutes.

Make sure you're using brew-installed python, not OS X's default python. `which python` should point to `/usr/local/bin/python` not `/usr/bin/python`. Type `brew doctor` for more information if you are having issues.

The interface runs in X11 using the GTK+ toolkit, so [XQuartz](http://xquartz.macosforge.org/landing/) needs to be installed.

The final requirements, can be installed using python's pip system:

    pip install pyserial pyzmq pyyaml seaborn

### Linux
Linux prerequisite installation is similar to that of Mac OS X, only using your distribution's native package manager rather than Homebrew, and X11 will likely be installed already. Some distributions may not have packages available for installing matplotlib or numpy, in which case, they should be installed using pip.

The final requirements, can be installed using python's pip system:

    pip install pyserial pyzmq pyyaml seaborn

### Windows
**These instructions are tricky on Windows, see the [pip install](#pip-install) below for an easier alternative.**

While it is possible to install a bare python distribution and install the required prerequisites separately, [Python(x,y)](https://code.google.com/p/pythonxy/wiki/Downloads) has a python 2.7 distribution that already contains most of the necessary packages. However, pyserial is not installed in the recommended install so it should be manually selected or the full install done instead (tested with 2.7.9.0).

The newest versions of Python(x,y) are also missing PyGTK, so it should be installed from [here](http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi) once Python(x,y) is installed. Matplotlib should then be reinstalled to get gtk support from [here](https://downloads.sourceforge.net/project/matplotlib/matplotlib/matplotlib-1.4.3/windows/matplotlib-1.4.3.win32-py2.7.exe).

## pip Install
Tagged git versions are uploaded to [PiPy](https://pypi.python.org/pypi/dstat-interface-mrbox) regularly, and thus dstat-interface-mrbox can be installed using the command `pip install dstat-interface-mrbox`, which will attempt to automatically install matplotlib, numpy, pyserial, and pyzmq. (N.B. matplotlib does not install well with pip on Mac and should be manually installed with Homebrew as described above)
This is still a bit experimental as pygtk and pygobject must be installed separately.

To launch a pip-installed dstat-interface-mrbox, simply type:

    python -m dstat_interface_mrbox.main
    
into a terminal.

### Windows
The following terminal commands will result in a full installation of dstat-interface-mrbox and its requirements, assuming [32-bit Miniconda][1] is installed:

    conda create -n dstat python pywin32
    activate dstat
    pip install --find-links http://192.99.4.95/wheels --trusted-host 192.99.4.95 scipy==0.17.0 pygtk2-win pycairo-gtk2-win dstat-interface-mrbox

This makes use of pre-built binary wheels for many of the Windows packages, stored on our server.
We are installing in a separate environment to keep a clean system.
`activate dstat` will enter the environment (must be done whenever a new terminal is opened),
and `deactivate` will return to the root environment.

Therefore, to run dstat-interface-mrbox from our environment, we must first activate it (if not already done) before launching it:

    activate dstat
    python -m dstat_interface_mrbox.main

[1]: https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86.exe

# Getting started
## Interface overview

![Main interface](images/1.png)

1. Menu bar
	![Menu bar](images/5.png)
	* File
		* Save Current data… — Saves the data of the currently visible plot as a space-separated text file or numpy .npy file
		* Save Plot… – Save the currently visible plot as a .pdf
		* Quit — Quits dstat-interface-mrbox
	* Dropbot
		* Connect — Listens for µDrop connection over ZMQ
		* Disconnect — Disconnect from µDrop
	* Help
		* About — Displays license information
2. ADC Settings Panel
	* PGA Setting — Sets the ADC's internal voltage gain. Should almost always be left at 2x except for potentiometry as increasing voltage gain reduces S/N. Settings other than 2x do not adjust data to match (e.g. one must halve measured current/voltage values if PGA is set to 4x).
	* Sample Rate - Sets the ADC's sample frequency. Lower rates give less noise, but reduced temporal resolution. Digital filter has a zero at multiples of the sample rate, so the Sample Rate setting can be used to filter out AC line noise by setting the rate to a factor of the line frequency, e.g. for 60 Hz rejection, choose 60, 30, 15, 10, 5, or 2.5 Hz.
	* Input Buffer — Sets the ADC's internal input buffer. Should generally be enabled.
3. Potentiostat Settings Panel
	* Gain — Controls the current-to-voltage converter gain. Higher values produce better S/N but reduce full scale current limit. Has no effect on potentiometry experiments.
4. Experiment Panel - Pulldown menu changes between experiment types and parameters are entered below.
5. Experiment Control
	* Execute — Start the currently selected experiment with the given parameters.
	* Stop — Stop the currently running experiment. If Autosave is enabled, the partial experiment will be saved.
6. Communications Panel
	* Serial Port — Select the port where DStat is located. On Windows, this is generally something like `COM3`. On Mac OS X, it should appear as `/dev/cu.usbmodem12...E1`. On Linux, it may vary, but will start with `/dev`. If you're not sure, the simplest way is to check the list before and after plugging the DStat in. (Clicking the Refresh button after)
	* Refresh — Refreshes the Serial Port list
	* Connect — Attempts to handshake with DStat. If unsuccessful, it will time out after approximately 30 seconds.
	* OCP — Displays the current open circuit potential measured at the reference electrode input. Active when DStat is connected and an experiment is not running.
	* Status bar — Displays status and error messages.
7. Data display tabs — Switches between the plot and raw data tabs
	* Plot — Displays the graphical representation of the incoming data.
	* Raw Data — The raw experiment data. Doesn't appear until the experiment is complete. The first column corresponds to the x-axis of the plot (time or voltage), and the second column corresponds to the y-axis (current or voltage). For mult-scan experiments, additional pairs of columns represent successive scans.
	![raw data](images/4.png)
	* Extra Data — For SWV and DPV, the separate forward and reverse currents are recorded here.
8. Autosave controls
	* Autosave — Enables automatic data saving on experiment completion. A text data file and a .pdf image of the plot will be saved.
	* File save location
	* File name selector — A number will be appended automatically if a file with the same name already exists.
9. Plot display
10. Plot navigation controls — For changing the view of the data plot.

## Connecting to DStat

1. Plug the DStat into a USB port, ensuring that drivers are loaded correctly on Windows systems.
2. Click Refresh in the Communications Panel to refresh the Serial Port list and choose the correct entry for the DStat (described above).
3. Click Connect.
4. If the connection was successful, a number should appear in the OCP field and the version number will appear in the status bar.
![connect](images/2.png)

If the connection failed, unplug the DStat and try again.

## Running an experiment

1. Choose the experiment you want to run in the Experiment Panel.
2. Fill the parameter fields.
3. Set an appropriate potentiostat gain.
4. Click Execute.

![experiment](images/3.png)