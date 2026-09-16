# 046958.python.pywintypes.line1.comment Magic utility that "redirects" to pywintypesXX.dll
import importlib.machinery
import importlib.util
import os
import sys


def __import_pywin32_system_module__(modname, globs):
    # 046959.python.pywintypes.line9.comment This has been through a number of iterations.  The problem: how to
    # 046960.python.pywintypes.line10.comment locate pywintypesXX.dll when it may be in a number of places, and how
    # 046961.python.pywintypes.line11.comment to avoid ever loading it twice.  This problem is compounded by the
    # 046962.python.pywintypes.line12.comment fact that the "right" way to do this requires win32api, but this
    # 046963.python.pywintypes.line13.comment itself requires pywintypesXX.
    # 046964.python.pywintypes.line14.comment And the killer problem is that someone may have done 'import win32api'
    # 046965.python.pywintypes.line15.comment before this code is called.  In that case Windows will have already
    # 046966.python.pywintypes.line16.comment loaded pywintypesXX as part of loading win32api - but by the time
    # 046967.python.pywintypes.line17.comment we get here, we may locate a different one.  This appears to work, but
    # 046968.python.pywintypes.line18.comment then starts raising bizarre TypeErrors complaining that something
    # 046969.python.pywintypes.line19.comment is not a pywintypes type when it clearly is!

    # 046970.python.pywintypes.line21.comment So in what we hope is the last major iteration of this, we now
    # 046971.python.pywintypes.line22.comment rely on a _win32sysloader module, implemented in C but not relying
    # 046972.python.pywintypes.line23.comment on pywintypesXX.dll.  It then can check if the DLL we are looking for
    # 046973.python.pywintypes.line24.comment lib is already loaded.
    # 046974.python.pywintypes.line25.comment See if this is a debug build.
    suffix = "_d" if "_d.pyd" in importlib.machinery.EXTENSION_SUFFIXES else ""
    filename = "%s%d%d%s.dll" % (
        modname,
        sys.version_info.major,
        sys.version_info.minor,
        suffix,
    )
    if hasattr(sys, "frozen"):
        # 046975.python.pywintypes.line34.comment If we are running from a frozen program (py2exe, McMillan, freeze, PyInstaller)
        # 046976.python.pywintypes.line35.comment then we try and load the DLL from our sys.path
        # 046977.python.pywintypes.line36.comment XXX - This path may also benefit from _win32sysloader?  However,
        # 046978.python.pywintypes.line37.comment MarkH has never seen the DLL load problem with py2exe programs...
        for look in sys.path:
            # 046979.python.pywintypes.line39.comment If the sys.path entry is a (presumably) .zip file, use the
            # 046980.python.pywintypes.line40.comment directory
            if os.path.isfile(look):
                look = os.path.dirname(look)
            found = os.path.join(look, filename)
            if os.path.isfile(found):
                break
        else:
            raise ImportError(f"Module '{modname}' isn't in frozen sys.path {sys.path}")
    else:
        # 046981.python.pywintypes.line49.comment First see if it already in our process - if so, we must use that.
        import _win32sysloader

        found = _win32sysloader.GetModuleFilename(filename)
        if found is None:
            # 046982.python.pywintypes.line54.comment We ask Windows to load it next.  This is in an attempt to
            # 046983.python.pywintypes.line55.comment get the exact same module loaded should pywintypes be imported
            # 046984.python.pywintypes.line56.comment first (which is how we are here) or if, eg, win32api was imported
            # 046985.python.pywintypes.line57.comment first thereby implicitly loading the DLL.

            # 046986.python.pywintypes.line59.comment Sadly though, it doesn't quite work - if pywintypesXX.dll
            # 046987.python.pywintypes.line60.comment is in system32 *and* the executable's directory, on XP SP2, an
            # 046988.python.pywintypes.line61.comment import of win32api will cause Windows to load pywintypes
            # 046989.python.pywintypes.line62.comment from system32, where LoadLibrary for that name will
            # 046990.python.pywintypes.line63.comment load the one in the exe's dir.
            # 046991.python.pywintypes.line64.comment That shouldn't really matter though, so long as we only ever
            # 046992.python.pywintypes.line65.comment get one loaded.
            found = _win32sysloader.LoadModule(filename)
        if found is None:
            # 046993.python.pywintypes.line68.comment Windows can't find it - which although isn't relevent here,
            # 046994.python.pywintypes.line69.comment means that we *must* be the first win32 import, as an attempt
            # 046995.python.pywintypes.line70.comment to import win32api etc would fail when Windows attempts to
            # 046996.python.pywintypes.line71.comment locate the DLL.
            # 046997.python.pywintypes.line72.comment This is most likely to happen for "non-admin" installs, where
            # 046998.python.pywintypes.line73.comment we can't put the files anywhere else on the global path.

            # 046999.python.pywintypes.line75.comment If there is a version in our Python directory, use that
            if os.path.isfile(os.path.join(sys.prefix, filename)):
                found = os.path.join(sys.prefix, filename)
        if found is None:
            # 047000.python.pywintypes.line79.comment Not in the Python directory?  Maybe we were installed via
            # 047001.python.pywintypes.line80.comment easy_install...
            if os.path.isfile(os.path.join(os.path.dirname(__file__), filename)):
                found = os.path.join(os.path.dirname(__file__), filename)

        # 047002.python.pywintypes.line84.comment There are 2 site-packages directories - one "global" and one "user".
        # 047003.python.pywintypes.line85.comment We could be in either, or both (but with different versions!). Factors include
        # 047004.python.pywintypes.line86.comment virtualenvs, post-install script being run or not, `pip install` flags, etc.

        # 047005.python.pywintypes.line88.comment In a worst-case, it means, say 'python -c "import win32api"'
        # 047006.python.pywintypes.line89.comment will not work but 'python -c "import pywintypes, win32api"' will,
        # 047007.python.pywintypes.line90.comment but it's better than nothing.

        # 047008.python.pywintypes.line92.comment We use the same logic as pywin32_bootstrap to find potential location for the dll
        # 047009.python.pywintypes.line93.comment Simply import pywin32_system32 and look in the paths in pywin32_system32.__path__

        if found is None:
            import pywin32_system32

            for path in pywin32_system32.__path__:
                maybe = os.path.join(path, filename)
                if os.path.isfile(maybe):
                    found = maybe
                    break

        if found is None:
            # 047010.python.pywintypes.line105.comment give up in disgust.
            raise ImportError(f"No system module '{modname}' ({filename})")
    # 047011.python.pywintypes.line107.comment After importing the module, sys.modules is updated to the DLL we just
    # 047012.python.pywintypes.line108.comment loaded - which isn't what we want. So we update sys.modules to refer to
    # 047013.python.pywintypes.line109.comment this module, and update our globals from it.
    old_mod = sys.modules[modname]
    # 047014.python.pywintypes.line111.comment Load the DLL.
    loader = importlib.machinery.ExtensionFileLoader(modname, found)
    spec = importlib.machinery.ModuleSpec(name=modname, loader=loader, origin=found)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # 047015.python.pywintypes.line117.comment Check the sys.modules[] behaviour we describe above is true...
    assert sys.modules[modname] is mod
    # 047016.python.pywintypes.line119.comment as above - re-reset to the *old* module object then update globs.
    sys.modules[modname] = old_mod
    globs.update(mod.__dict__)


__import_pywin32_system_module__("pywintypes", globals())
