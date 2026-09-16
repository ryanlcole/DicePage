# 051620.python.empty_volume_cache.line1.comment A sample implementation of IEmptyVolumeCache - see
# 051621.python.empty_volume_cache.line2.comment https://learn.microsoft.com/en-ca/windows/win32/lwef/disk-cleanup for an overview.
# 051622.python.empty_volume_cache.line3.comment
# 051623.python.empty_volume_cache.line4.comment * Execute this script to register the handler
# 051624.python.empty_volume_cache.line5.comment * Start the "disk cleanup" tool - look for "pywin32 compiled files"
import os
import stat
import sys

import pythoncom
import win32gui
import winerror
from win32com.server.exception import COMException
from win32com.shell import shell, shellcon

# 051625.python.empty_volume_cache.line16.comment Our shell extension.
IEmptyVolumeCache_Methods = (
    "Initialize GetSpaceUsed Purge ShowProperties Deactivate".split()
)
IEmptyVolumeCache2_Methods = "InitializeEx".split()

ico = os.path.join(sys.prefix, "py.ico")
if not os.path.isfile(ico):
    ico = os.path.join(sys.prefix, "PC", "py.ico")
if not os.path.isfile(ico):
    ico = None
    print("Can't find python.ico - no icon will be installed")


class EmptyVolumeCache:
    _reg_progid_ = "Python.ShellExtension.EmptyVolumeCache"
    _reg_desc_ = "Python Sample Shell Extension (disk cleanup)"
    _reg_clsid_ = "{EADD0777-2968-4c72-A999-2BF5F756259C}"
    _reg_icon_ = ico
    _com_interfaces_ = [shell.IID_IEmptyVolumeCache, shell.IID_IEmptyVolumeCache2]
    _public_methods_ = IEmptyVolumeCache_Methods + IEmptyVolumeCache2_Methods

    def Initialize(self, hkey, volume, flags):
        # 051626.python.empty_volume_cache.line39.comment This should never be called, except on win98.
        print("Unless we are on 98, Initialize call is unexpected!")
        raise COMException(hresult=winerror.E_NOTIMPL)

    def InitializeEx(self, hkey, volume, key_name, flags):
        # 051627.python.empty_volume_cache.line44.comment Must return a tuple of:
        # 051628.python.empty_volume_cache.line45.comment (display_name, description, button_name, flags)
        print("InitializeEx called with", hkey, volume, key_name, flags)
        self.volume = volume
        if flags & shellcon.EVCF_SETTINGSMODE:
            print("We are being run on a schedule")
            # 051629.python.empty_volume_cache.line50.comment In this case, "because there is no opportunity for user
            # 051630.python.empty_volume_cache.line51.comment feedback, only those files that are extremely safe to clean up
            # 051631.python.empty_volume_cache.line52.comment should be touched. You should ignore the initialization
            # 051632.python.empty_volume_cache.line53.comment method's pcwszVolume parameter and clean unneeded files
            # 051633.python.empty_volume_cache.line54.comment regardless of what drive they are on."
            self.volume = None  # flag as 'any disk will do'
        elif flags & shellcon.EVCF_OUTOFDISKSPACE:
            # 051635.python.empty_volume_cache.line57.comment In this case, "the handler should be aggressive about deleting
            # 051636.python.empty_volume_cache.line58.comment files, even if it results in a performance loss. However, the
            # 051637.python.empty_volume_cache.line59.comment handler obviously should not delete files that would cause an
            # 051638.python.empty_volume_cache.line60.comment application to fail or the user to lose data."
            print("We are being run as we are out of disk-space")
        else:
            # 051639.python.empty_volume_cache.line63.comment This case is not documented - we are guessing :)
            print("We are being run because the user asked")

        # 051640.python.empty_volume_cache.line66.comment For the sake of demo etc, we tell the shell to only show us when
        # 051641.python.empty_volume_cache.line67.comment there are > 0 bytes available.  Our GetSpaceUsed will check the
        # 051642.python.empty_volume_cache.line68.comment volume, so will return 0 when we are on a different disk
        flags = shellcon.EVCF_DONTSHOWIFZERO | shellcon.EVCF_ENABLEBYDEFAULT

        return (
            "pywin32 compiled files",
            "Removes all .pyc and .pyo files in the pywin32 directories",
            "click me!",
            flags,
        )

    def _GetDirectories(self):
        root_dir = os.path.abspath(os.path.dirname(os.path.dirname(win32gui.__file__)))
        if self.volume is not None and not root_dir.lower().startswith(
            self.volume.lower()
        ):
            return []
        return [
            os.path.join(root_dir, p)
            for p in ("win32", "win32com", "win32comext", "isapi")
        ]

    def _WalkCallback(self, arg, directory, files):
        # 051643.python.empty_volume_cache.line90.comment callback function for os.path.walk - no need to be member, but it's
        # 051644.python.empty_volume_cache.line91.comment close to the callers :)
        callback, total_list = arg
        for file in files:
            fqn = os.path.join(directory, file).lower()
            if file.endswith(".pyc") or file.endswith(".pyo"):
                # 051645.python.empty_volume_cache.line96.comment See below - total_list is None means delete files,
                # 051646.python.empty_volume_cache.line97.comment otherwise it is a list where the result is stored. It's a
                # 051647.python.empty_volume_cache.line98.comment list simply due to the way os.walk works - only [0] is
                # 051648.python.empty_volume_cache.line99.comment referenced
                if total_list is None:
                    print("Deleting file", fqn)
                    # 051649.python.empty_volume_cache.line102.comment Should do callback.PurgeProcess - left as an exercise :)
                    os.remove(fqn)
                else:
                    total_list[0] += os.stat(fqn)[stat.ST_SIZE]
                    # 051650.python.empty_volume_cache.line106.comment and callback to the tool
                    if callback:
                        # 051651.python.empty_volume_cache.line108.comment for the sake of seeing the progress bar do its thing,
                        # 051652.python.empty_volume_cache.line109.comment we take longer than we need to...
                        # 051653.python.empty_volume_cache.line110.comment ACK - for some bizarre reason this screws up the XP
                        # 051654.python.empty_volume_cache.line111.comment cleanup manager - clues welcome!! :)
                        # 051655.python.empty_volume_cache.line112.comment # print("Looking in", directory, ", but waiting a while...")
                        # 051656.python.empty_volume_cache.line113.comment # time.sleep(3)
                        # 051657.python.empty_volume_cache.line114.comment now do it
                        used = total_list[0]
                        callback.ScanProgress(used, 0, "Looking at " + fqn)

    def GetSpaceUsed(self, callback):
        total = [0]  # See _WalkCallback above
        try:
            for d in self._GetDirectories():
                os.path.walk(d, self._WalkCallback, (callback, total))
                print("After looking in", d, "we have", total[0], "bytes")
        except pythoncom.error as exc:
            # 051659.python.empty_volume_cache.line125.comment This will be raised by the callback when the user selects 'cancel'.
            if exc.hresult != winerror.E_ABORT:
                raise  # that's the documented error code!
            print("User cancelled the operation")
        return total[0]

    def Purge(self, amt_to_free, callback):
        print("Purging", amt_to_free, "bytes...")
        # 051661.python.empty_volume_cache.line133.comment we ignore amt_to_free - it is generally what we returned for
        # 051662.python.empty_volume_cache.line134.comment GetSpaceUsed
        try:
            for d in self._GetDirectories():
                os.path.walk(d, self._WalkCallback, (callback, None))
        except pythoncom.error as exc:
            # 051663.python.empty_volume_cache.line139.comment This will be raised by the callback when the user selects 'cancel'.
            if exc.hresult != winerror.E_ABORT:
                raise  # that's the documented error code!
            print("User cancelled the operation")

    def ShowProperties(self, hwnd):
        raise COMException(hresult=winerror.E_NOTIMPL)

    def Deactivate(self):
        print("Deactivate called")
        return 0


def DllRegisterServer():
    # 051665.python.empty_volume_cache.line153.comment Also need to register specially in:
    # 051666.python.empty_volume_cache.line154.comment HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches
    # 051667.python.empty_volume_cache.line155.comment See link at top of file.
    import winreg

    kn = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\{}".format(
        EmptyVolumeCache._reg_desc_,
    )
    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, kn)
    winreg.SetValueEx(key, None, 0, winreg.REG_SZ, EmptyVolumeCache._reg_clsid_)


def DllUnregisterServer():
    import winreg

    kn = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\{}".format(
        EmptyVolumeCache._reg_desc_,
    )
    try:
        key = winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, kn)
    except OSError as details:
        import errno

        if details.errno != errno.ENOENT:
            raise
    print(EmptyVolumeCache._reg_desc_, "unregistration complete.")


if __name__ == "__main__":
    from win32com.server import register

    register.UseCommandLine(
        EmptyVolumeCache,
        finalize_register=DllRegisterServer,
        finalize_unregister=DllUnregisterServer,
    )
