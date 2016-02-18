#!/usr/bin/env python

import os
import sys
from shutil import copyfile

import version

version.getVersion()
src = os.path.abspath('./RELEASE-VERSION')
dst = os.path.abspath('./dstat_interface/CURRENT-VERSION')
copyfile(src, dst)
