"""
modulegraph.find_modules - High-level module dependency finding interface
=========================================================================

History
........

Originally (loosely) based on code in py2exe's build_exe.py by Thomas Heller.
"""
import os
import pkgutil

from .modulegraph import Alias

def get_implies():
    def _xml_etree_modules():
        import xml.etree
        return [
            f"xml.etree.{module_name}"
            for _, module_name, is_package in pkgutil.iter_modules(xml.etree.__path__)
            if not is_package
        ]

    result = {
        # 008698.python.find_modules.line25.comment imports done from C code in built-in and/or extension modules
        # 008699.python.find_modules.line26.comment (untrackable by modulegraph).
        "_curses": ["curses"],
        "posix": ["resource"],
        "gc": ["time"],
        "time": ["_strptime"],
        "datetime": ["time"],
        "parser": ["copyreg"],
        "codecs": ["encodings"],
        "_sre": ["copy", "re"],
        "zipimport": ["zlib"],

        # 008700.python.find_modules.line37.comment _frozen_importlib is part of the interpreter itself
        "_frozen_importlib": None,

        # 008701.python.find_modules.line40.comment os.path is an alias for a platform specific module,
        # 008702.python.find_modules.line41.comment ensure that the graph shows this.
        "os.path": Alias(os.path.__name__),

        # 008703.python.find_modules.line44.comment Python >= 3.2:
        "_datetime": ["time", "_strptime"],
        "_json": ["json.decoder"],
        "_pickle": ["codecs", "copyreg", "_compat_pickle"],
        "_posixsubprocess": ["gc"],
        "_ssl": ["socket"],

        # 008704.python.find_modules.line51.comment Python >= 3.3:
        "_elementtree": ["pyexpat"] + _xml_etree_modules(),

        # 008705.python.find_modules.line54.comment This is not C extension, but it uses __import__
        "anydbm": ["dbhash", "gdbm", "dbm", "dumbdbm", "whichdb"],

        # 008706.python.find_modules.line57.comment Known package aliases
        "wxPython.wx": Alias('wx'),
    }

    return result
