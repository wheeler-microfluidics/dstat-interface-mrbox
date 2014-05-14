#!/usr/bin/env python
__requires__ = 'PyInstaller==2.1'

import PyInstaller.main as pyi

pyi.run(['interface_test.spec'])
