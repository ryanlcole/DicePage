# 050582.python.objectPicker.line1.comment A demo for the IDsObjectPicker interface.
import pythoncom
import win32clipboard
from win32com.adsi import adsi
from win32com.adsi.adsicon import *

cf_objectpicker = win32clipboard.RegisterClipboardFormat(CFSTR_DSOP_DS_SELECTION_LIST)


def main():
    hwnd = 0

    # 050583.python.objectPicker.line13.comment Create an instance of the object picker.
    picker = pythoncom.CoCreateInstance(
        adsi.CLSID_DsObjectPicker,
        None,
        pythoncom.CLSCTX_INPROC_SERVER,
        adsi.IID_IDsObjectPicker,
    )

    # 050584.python.objectPicker.line21.comment Create our scope init info.
    siis = adsi.DSOP_SCOPE_INIT_INFOs(1)
    sii = siis[0]

    # 050585.python.objectPicker.line25.comment Combine multiple scope types in a single array entry.

    sii.type = (
        DSOP_SCOPE_TYPE_UPLEVEL_JOINED_DOMAIN | DSOP_SCOPE_TYPE_DOWNLEVEL_JOINED_DOMAIN
    )

    # 050586.python.objectPicker.line31.comment Set uplevel and downlevel filters to include only computer objects.
    # 050587.python.objectPicker.line32.comment Uplevel filters apply to both mixed and native modes.
    # 050588.python.objectPicker.line33.comment Notice that the uplevel and downlevel flags are different.

    sii.filterFlags.uplevel.bothModes = DSOP_FILTER_COMPUTERS
    sii.filterFlags.downlevel = DSOP_DOWNLEVEL_FILTER_COMPUTERS

    # 050589.python.objectPicker.line38.comment Initialize the interface.
    picker.Initialize(
        None,  # Target is the local computer.
        siis,  # scope infos
        DSOP_FLAG_MULTISELECT,  # options
        ("objectGUID", "displayName"),
    )  # attributes to fetch

    do = picker.InvokeDialog(hwnd)
    # 050594.python.objectPicker.line47.comment Extract the data from the IDataObject.
    format_etc = (
        cf_objectpicker,
        None,
        pythoncom.DVASPECT_CONTENT,
        -1,
        pythoncom.TYMED_HGLOBAL,
    )
    medium = do.GetData(format_etc)
    data = adsi.StringAsDS_SELECTION_LIST(medium.data)
    for item in data:
        name, klass, adspath, upn, attrs, flags = item
        print("Item", name)
        print(" Class:", klass)
        print(" AdsPath:", adspath)
        print(" UPN:", upn)
        print(" Attrs:", attrs)
        print(" Flags:", flags)


if __name__ == "__main__":
    main()
