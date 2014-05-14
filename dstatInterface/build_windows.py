#!/usr/bin/env python
__requires__ = 'PyInstaller==2.1'


import os, sys
os.chdir(os.path.dirname(sys.argv[0]))

import PyInstaller.main as pyi #For some reason, it gets the path here, so working dir must be set first
pyi.run(['interface_test.spec'])
