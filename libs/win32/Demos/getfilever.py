import os

import win32api

ver_strings = (
    "Comments",
    "InternalName",
    "ProductName",
    "CompanyName",
    "LegalCopyright",
    "ProductVersion",
    "FileDescription",
    "LegalTrademarks",
    "PrivateBuild",
    "FileVersion",
    "OriginalFilename",
    "SpecialBuild",
)
fname = os.environ["comspec"]
d = win32api.GetFileVersionInfo(fname, "\\")
# 046061.python.getfilever.line21.comment # backslash as parm returns dictionary of numeric info corresponding to VS_FIXEDFILEINFO struc
for n, v in d.items():
    print(n, v)

pairs = win32api.GetFileVersionInfo(fname, "\\VarFileInfo\\Translation")
# 046062.python.getfilever.line26.comment # \VarFileInfo\Translation returns list of available (language, codepage) pairs that can be used to retreive string info
# 046063.python.getfilever.line27.comment # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle two are language/codepage pair returned from above
for lang, codepage in pairs:
    print("lang:", lang, "codepage:", codepage)
    for ver_string in ver_strings:
        str_info = f"\\StringFileInfo\\{lang:04X}{codepage:04X}\\{ver_string}"
        # 046064.python.getfilever.line32.comment print(str_inf)
        print(ver_string, repr(win32api.GetFileVersionInfo(fname, str_info)))
