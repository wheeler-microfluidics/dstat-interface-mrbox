# -*- mode: python -*-
a = Analysis(['./main.py'],
             pathex=['/Users/mdryden/src/dstat-interface2/dstatInterface'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='DStat',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='DStat')
app = BUNDLE(coll,
             name='DStat.app',
             icon=None)
