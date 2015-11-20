# -*- mode: python -*-
a = Analysis(['interface_test.py'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
glade_tree = Tree('./interface', prefix = 'interface', excludes=['*.py','*.pyc'])
drivers_tree = Tree('./drivers', prefix = 'drivers')
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='interface_test.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               drivers_tree,
               glade_tree,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='interface_test')
