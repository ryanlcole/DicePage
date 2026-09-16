# 050403.python.testmakepy.line1.comment Test makepy - try and run it over every OCX in the windows system directory.

import sys
import traceback

import pythoncom
import win32com.test.util
import winerror
from win32com.client import gencache, makepy, selecttlb


def TestBuildAll(verbose=1):
    num = 0
    tlbInfos = selecttlb.EnumTlbs()
    for info in tlbInfos:
        if verbose:
            print(f"{info.desc} ({info.dll})")
        try:
            makepy.GenerateFromTypeLibSpec(info)
            # 050404.python.testmakepy.line20.comment sys.stderr.write("Attr typeflags for coclass referenced object %s=%d (%d), typekind=%d\n" % (name, refAttr.wTypeFlags, refAttr.wTypeFlags & pythoncom.TYPEFLAG_FDUAL,refAttr.typekind))
            num += 1
        except pythoncom.com_error as details:
            # 050405.python.testmakepy.line23.comment Ignore these 2 errors, as the are very common and can obscure
            # 050406.python.testmakepy.line24.comment useful warnings.
            if details.hresult not in [
                winerror.TYPE_E_CANTLOADLIBRARY,
                winerror.TYPE_E_LIBNOTREGISTERED,
            ]:
                print("** COM error on", info.desc)
                print(details)
        except KeyboardInterrupt:
            print("Interrupted!")
            raise
        except:
            print("Failed:", info.desc)
            traceback.print_exc()
        if makepy.bForDemandDefault:
            # 050407.python.testmakepy.line38.comment This only builds enums etc by default - build each
            # 050408.python.testmakepy.line39.comment interface manually
            tinfo = (info.clsid, info.lcid, info.major, info.minor)
            mod = gencache.EnsureModule(info.clsid, info.lcid, info.major, info.minor)
            for name in mod.NamesToIIDMap:
                makepy.GenerateChildFromTypeLibSpec(name, tinfo)
    return num


def TestAll(verbose=0):
    num = TestBuildAll(verbose)
    print("Generated and imported", num, "modules")
    win32com.test.util.CheckClean()


if __name__ == "__main__":
    TestAll("-q" not in sys.argv)
