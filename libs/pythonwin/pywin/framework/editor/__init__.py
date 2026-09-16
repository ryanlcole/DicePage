# 037304.python.init.line1.comment __init__ for the Pythonwin editor package.
# 037305.python.init.line2.comment
# 037306.python.init.line3.comment We used to support optional editors - eg, color or non-color.
# 037307.python.init.line4.comment
# 037308.python.init.line5.comment This really isn't necessary with Scintilla, and scintilla
# 037309.python.init.line6.comment is getting so deeply embedded that it was too much work.

import win32ui

defaultCharacterFormat = (-402653169, 0, 200, 0, 0, 0, 49, "Courier New")

# 037310.python.init.line12.comment #def GetDefaultEditorModuleName():
# 037311.python.init.line13.comment #	import pywin
# 037312.python.init.line14.comment #	# If someone has set pywin.editormodulename, then this is what we use
# 037313.python.init.line15.comment #	try:
# 037314.python.init.line16.comment #		prefModule = pywin.editormodulename
# 037315.python.init.line17.comment #	except AttributeError:
# 037316.python.init.line18.comment #		prefModule = win32ui.GetProfileVal("Editor","Module", "")
# 037317.python.init.line19.comment #	return prefModule
# 037318.python.init.line20.comment #
# 037319.python.init.line21.comment #def WriteDefaultEditorModule(module):
# 037320.python.init.line22.comment #	try:
# 037321.python.init.line23.comment #		module = module.__name__
# 037322.python.init.line24.comment #	except:
# 037323.python.init.line25.comment #		pass
# 037324.python.init.line26.comment #	win32ui.WriteProfileVal("Editor", "Module", module)


def LoadDefaultEditor():
    pass


# 037325.python.init.line33.comment #	prefModule = GetDefaultEditorModuleName()
# 037326.python.init.line34.comment #	restorePrefModule = None
# 037327.python.init.line35.comment #	mod = None
# 037328.python.init.line36.comment #	if prefModule:
# 037329.python.init.line37.comment #		try:
# 037330.python.init.line38.comment #			mod = __import__(prefModule)
# 037331.python.init.line39.comment #		except 'xx':
# 037332.python.init.line40.comment #			msg = "Importing your preferred editor ('%s') failed.\n\nError %s: %s\n\nAn attempt will be made to load the default editor.\n\nWould you like this editor disabled in the future?" % (prefModule, sys.exc_info()[0], sys.exc_info()[1])
# 037333.python.init.line41.comment #			rc = win32ui.MessageBox(msg, "Error importing editor", win32con.MB_YESNO)
# 037334.python.init.line42.comment #			if rc == win32con.IDNO:
# 037335.python.init.line43.comment #				restorePrefModule = prefModule
# 037336.python.init.line44.comment #			WriteDefaultEditorModule("")
# 037337.python.init.line45.comment #			del rc
# 037338.python.init.line46.comment #
# 037339.python.init.line47.comment #	try:
# 037340.python.init.line48.comment #		# Try and load the default one - don't catch errors here.
# 037341.python.init.line49.comment #		if mod is None:
# 037342.python.init.line50.comment #			prefModule = "pywin.framework.editor.color.coloreditor"
# 037343.python.init.line51.comment #			mod = __import__(prefModule)
# 037344.python.init.line52.comment #
# 037345.python.init.line53.comment #		# Get at the real module.
# 037346.python.init.line54.comment #		mod = sys.modules[prefModule]
# 037347.python.init.line55.comment #
# 037348.python.init.line56.comment #		# Do a "from mod import *"
# 037349.python.init.line57.comment #		globals().update(mod.__dict__)
# 037350.python.init.line58.comment #
# 037351.python.init.line59.comment #	finally:
# 037352.python.init.line60.comment #		# Restore the users default editor if it failed and they requested not to disable it.
# 037353.python.init.line61.comment #		if restorePrefModule:
# 037354.python.init.line62.comment #			WriteDefaultEditorModule(restorePrefModule)


def GetEditorOption(option, defaultValue, min=None, max=None):
    rc = win32ui.GetProfileVal("Editor", option, defaultValue)
    if min is not None and rc < min:
        rc = defaultValue
    if max is not None and rc > max:
        rc = defaultValue
    return rc


def SetEditorOption(option, newValue):
    win32ui.WriteProfileVal("Editor", option, newValue)


def DeleteEditorOption(option):
    try:
        win32ui.WriteProfileVal("Editor", option, None)
    except win32ui.error:
        pass


# 037355.python.init.line85.comment Load and save font tuples
def GetEditorFontOption(option, default=None):
    if default is None:
        default = defaultCharacterFormat
    fmt = GetEditorOption(option, "")
    if fmt == "":
        return default
    try:
        return eval(fmt)
    except:
        print("WARNING: Invalid font setting in registry - setting ignored")
        return default


def SetEditorFontOption(option, newValue):
    SetEditorOption(option, str(newValue))


from pywin.framework.editor.color.coloreditor import (  # nopycln: import
    editorTemplate as editorTemplate,  # Adds doc template & Re-export
)
