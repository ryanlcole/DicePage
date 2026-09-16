# 036582.python.pythoncom.line1.comment Magic utility that "redirects" to pythoncomXX.dll
import pywintypes

pywintypes.__import_pywin32_system_module__("pythoncom", globals())
