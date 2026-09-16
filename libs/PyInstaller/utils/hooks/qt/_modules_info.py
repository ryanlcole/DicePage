# 010585.python.modules_info.line1.comment ----------------------------------------------------------------------------
# 010586.python.modules_info.line2.comment Copyright (c) 2022-2023, PyInstaller Development Team.
# 010587.python.modules_info.line3.comment
# 010588.python.modules_info.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 010589.python.modules_info.line5.comment or later) with exception for distributing the bootloader.
# 010590.python.modules_info.line6.comment
# 010591.python.modules_info.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 010592.python.modules_info.line8.comment
# 010593.python.modules_info.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 010594.python.modules_info.line10.comment -----------------------------------------------------------------------------

# 010595.python.modules_info.line12.comment Qt modules information - the core of our Qt collection approach
# 010596.python.modules_info.line13.comment ----------------------------------------------------------------
# 010597.python.modules_info.line14.comment
# 010598.python.modules_info.line15.comment The python bindings for Qt (``PySide2``, ``PyQt5``, ``PySide6``, ``PyQt6``) consist of several python binary extension
# 010599.python.modules_info.line16.comment modules that provide bindings for corresponding Qt modules. For example, the ``PySide2.QtNetwork`` python extension
# 010600.python.modules_info.line17.comment module provides bindings for the ``QtNetwork`` Qt module from the ``qt/qtbase`` Qt repository.
# 010601.python.modules_info.line18.comment
# 010602.python.modules_info.line19.comment A Qt module can be considered as consisting of:
# 010603.python.modules_info.line20.comment * a shared library (for example, on Linux, the shared library names for the ``QtNetwork`` Qt module in Qt5 and Qt6
# 010604.python.modules_info.line21.comment are ``libQt5Network.so`` and ``libQt6Network.so``, respectively).
# 010605.python.modules_info.line22.comment * plugins: a certain type (or class) of plugins is usually associated with a single Qt module (for example,
# 010606.python.modules_info.line23.comment ``imageformats`` plugins are associated with the ``QtGui`` Qt module from the ``qt/qtbase`` Qt repository), but
# 010607.python.modules_info.line24.comment additional plugins of that type may come from other Qt repositories. For example, ``imageformats/qsvg`` plugin
# 010608.python.modules_info.line25.comment is provided by ``qtsvg/src/plugins/imageformats/svg`` from the ``qt/qtsvg`` repository, and ``imageformats/qpdf``
# 010609.python.modules_info.line26.comment is provided by ``qtwebengine/src/pdf/plugins/imageformats/pdf`` from the ``qt/qtwebengine`` repository.
# 010610.python.modules_info.line27.comment * translation files: names of translation files consist of a base name, which typically corresponds to the Qt
# 010611.python.modules_info.line28.comment repository name, and language code. A single translation file usually covers all Qt modules contained within
# 010612.python.modules_info.line29.comment the same repository. For example, translation files with base name ``qtbase``  contain translations for ``QtCore``,
# 010613.python.modules_info.line30.comment ``QtGui``, ``QtWidgets``, ``QtNetwork``, and other Qt modules from the ``qt/qtbase`` Qt repository.
# 010614.python.modules_info.line31.comment
# 010615.python.modules_info.line32.comment The PyInstaller's built-in analysis of link-time dependencies ensures that when collecting a Qt python extension
# 010616.python.modules_info.line33.comment module, we automatically pick up the linked Qt shared libraries. However, collection of linked Qt shared libraries
# 010617.python.modules_info.line34.comment does not result in collection of plugins, nor translation files. In addition, the dependency of a Qt python extension
# 010618.python.modules_info.line35.comment module on other Qt python extension modules (i.e., at the bindings level) cannot be automatically determined due to
# 010619.python.modules_info.line36.comment PyInstaller's inability to scan imports in binary extensions.
# 010620.python.modules_info.line37.comment
# 010621.python.modules_info.line38.comment PyInstaller < 5.7 solved this problem using a dictionary that associated a Qt shared library name with python
# 010622.python.modules_info.line39.comment extension name, plugins, and translation files. For each hooked Qt python extension module, the hook calls a helper
# 010623.python.modules_info.line40.comment that analyzes the extension file for link-time dependencies, and matches those against the dictionary. Therefore,
# 010624.python.modules_info.line41.comment based on linked shared libraries, we could recursively infer the list of files to collect in addition to the shared
# 010625.python.modules_info.line42.comment libraries themselves:
# 010626.python.modules_info.line43.comment - plugins and translation files belonging to Qt modules whose shared libraries we collect
# 010627.python.modules_info.line44.comment - Qt python extension modules corresponding to the Qt modules that we collect
# 010628.python.modules_info.line45.comment
# 010629.python.modules_info.line46.comment The above approach ensures that even if analyzed python script contains only ``from PySide2 import QtWidgets``,
# 010630.python.modules_info.line47.comment we would also collect ``PySide2.QtGui`` and ``PySide2.QtCore``, as well as all corresponding Qt module files
# 010631.python.modules_info.line48.comment (the shared libraries, plugins, translation files). For this to work, a hook must be provided for the
# 010632.python.modules_info.line49.comment ``PySide2.QtWidgets`` that performs the recursive analysis of the extension module file; so to ensure that each
# 010633.python.modules_info.line50.comment Qt python extension module by itself ensures collection of all its dependencies, we need to hook all Qt python
# 010634.python.modules_info.line51.comment extension modules provided by specific python Qt bindings package.
# 010635.python.modules_info.line52.comment
# 010636.python.modules_info.line53.comment The above approach with single dictionary, however, has several limitations:
# 010637.python.modules_info.line54.comment - it cannot provide association for Qt python module that binds a Qt module without a shared library (i.e., a
# 010638.python.modules_info.line55.comment headers-only module, or a statically-built module). In such cases, potential plugins and translations should
# 010639.python.modules_info.line56.comment be associated directly with the Qt python extension file instead of the Qt module's (non-existent) shared library.
# 010640.python.modules_info.line57.comment - it cannot (directly) handle differences between Qt5 and Qt6; we had to build a second dictionary
# 010641.python.modules_info.line58.comment - it cannot handle differences between the bindings themselves; for example, PyQt5 binds some Qt modules that
# 010642.python.modules_info.line59.comment PySide2 does not bind. Or, the binding's Qt python extension module is named differently in PyQt and PySide
# 010643.python.modules_info.line60.comment bindings (or just differently in PyQt5, while PySide2, PySide6, and PyQt6 use the same name).
# 010644.python.modules_info.line61.comment
# 010645.python.modules_info.line62.comment In order address the above shortcomings, we now store all information a list of structures that contain information
# 010646.python.modules_info.line63.comment for a particular Qt python extension and/or Qt module (shared library):
# 010647.python.modules_info.line64.comment - python extension name (if applicable)
# 010648.python.modules_info.line65.comment - Qt module name base (if applicable)
# 010649.python.modules_info.line66.comment - plugins
# 010650.python.modules_info.line67.comment - translation files base name
# 010651.python.modules_info.line68.comment - applicable Qt version (if necessary)
# 010652.python.modules_info.line69.comment - applicable Qt bindings (if necessary)
# 010653.python.modules_info.line70.comment
# 010654.python.modules_info.line71.comment This list is used to dynamically construct two dictionaries (based on the bindings name and Qt version):
# 010655.python.modules_info.line72.comment - mapping python extension names to associated module information
# 010656.python.modules_info.line73.comment - mapping Qt shared library names to associated module information
# 010657.python.modules_info.line74.comment This allows us to associate plugins and translations with either Qt python extension or with the Qt module's shared
# 010658.python.modules_info.line75.comment library (or both), whichever is applicable.
# 010659.python.modules_info.line76.comment
# 010660.python.modules_info.line77.comment The `qt_dynamic_dependencies_dict`_ from the original approach was constructed using several information sources, as
# 010661.python.modules_info.line78.comment documented `here
# 010662.python.modules_info.line79.comment <https://github.com/pyinstaller/pyinstaller/blob/fbf7948be85177dd44b41217e9f039e1d176de6b/PyInstaller/utils/hooks/qt.py#L266-L362>`_.
# 010663.python.modules_info.line80.comment
# 010664.python.modules_info.line81.comment In the current approach, the relations stored in the `QT_MODULES_INFO`_ list were determined directly, by inspecting
# 010665.python.modules_info.line82.comment the Qt source code. This requires some prior knowledge of how the Qt code is organized (repositories and individual Qt
# 010666.python.modules_info.line83.comment modules within them), as well as some searching based on guesswork. The procedure can be outlined as follows:
# 010667.python.modules_info.line84.comment * check out the `main Qt repository <git://code.qt.io/qt/qt5.git>`_. This repository contains references to all other
# 010668.python.modules_info.line85.comment Qt repositories in the form of git submodules.
# 010669.python.modules_info.line86.comment * for Qt5:
# 010670.python.modules_info.line87.comment * check out the latest release tag, e.g., v5.15.2, then check out the submodules.
# 010671.python.modules_info.line88.comment * search the Qt modules' qmake .pro files; for example, ``qtbase/src/network/network.pro`` for QtNetwork module.
# 010672.python.modules_info.line89.comment The plugin types associated with the module are listed in the ``MODULE_PLUGIN_TYPES`` variable (in this case,
# 010673.python.modules_info.line90.comment ``bearer``).
# 010674.python.modules_info.line91.comment * all translations are gathered in ``qttranslations`` sub-module/repository, and their association with
# 010675.python.modules_info.line92.comment individual repositories can be seen in ``qttranslations/translations/translations.pro``.
# 010676.python.modules_info.line93.comment * for Qt6:
# 010677.python.modules_info.line94.comment * check out the latest release tag, e.g., v6.3.1, then check out the submodules.
# 010678.python.modules_info.line95.comment * search the Qt modules' CMake files; for example, ``qtbase/src/network/CMakeLists.txt`` for QtNetwork module.
# 010679.python.modules_info.line96.comment The plugin types associated with the module are listed under ``PLUGIN_TYPES`` argument of the
# 010680.python.modules_info.line97.comment ``qt_internal_add_module()`` function that defines the Qt module.
# 010681.python.modules_info.line98.comment
# 010682.python.modules_info.line99.comment The idea is to make a list of all extension modules found in a Qt bindings package, as well as all available plugin
# 010683.python.modules_info.line100.comment directories (which correspond to plugin types) and translation files. For each extension, identify the corresponding
# 010684.python.modules_info.line101.comment Qt module (shared library name) and its associated plugins and translation files. Once this is done, most of available
# 010685.python.modules_info.line102.comment plugins and translations in the python bindings package should have a corresponding python Qt extension module
# 010686.python.modules_info.line103.comment available; this gives us associations based on the python extension module names as well as based on the Qt shared
# 010687.python.modules_info.line104.comment library names. For any plugins and translation files remaining unassociated, identify the corresponding Qt module;
# 010688.python.modules_info.line105.comment this gives us associations based only on Qt shared library names. While this second group of associations are never
# 010689.python.modules_info.line106.comment processed directly (due to lack of corresponding python extension), they may end up being processed during the
# 010690.python.modules_info.line107.comment recursive dependency analysis, if the corresponding Qt shared library is linked against by some Qt python extension
# 010691.python.modules_info.line108.comment or another Qt shared library.


# 010692.python.modules_info.line111.comment This structure is used to define Qt module information, such as python module/extension name, Qt module (shared
# 010693.python.modules_info.line112.comment library) name, translation files' base names, plugins, as well as associated python bindings (which implicitly
# 010694.python.modules_info.line113.comment also encode major Qt version).
class _QtModuleDef:
    def __init__(self, module, shared_lib=None, translations=None, plugins=None, bindings=None):
        # 010695.python.modules_info.line116.comment Python module (extension) name without package namespace. For example, `QtCore`.
        # 010696.python.modules_info.line117.comment Can be None if python bindings do not bind the module, but we still need to establish relationship between
        # 010697.python.modules_info.line118.comment the Qt module (shared library) and its plugins and translations.
        self.module = module
        # 010698.python.modules_info.line120.comment Associated Qt module (shared library), if any. Used during recursive dependency analysis, where a python
        # 010699.python.modules_info.line121.comment module (extension) is analyzed for linked Qt modules (shared libraries), and then their corresponding
        # 010700.python.modules_info.line122.comment python modules (extensions) are added to hidden imports. For example, the Qt module name is `Qt5Core` or
        # 010701.python.modules_info.line123.comment `Qt6Core`, depending on the Qt version. Can be None for python modules that are not tied to a particular
        # 010702.python.modules_info.line124.comment Qt shared library (for example, the corresponding Qt module is headers-only) and hence they cannot be
        # 010703.python.modules_info.line125.comment inferred from recursive link-time dependency analysis.
        self.shared_lib = shared_lib
        # 010704.python.modules_info.line127.comment List of base names of translation files (if any) associated with the Qt module. Multiple base names may be
        # 010705.python.modules_info.line128.comment associated with a single module.
        # 010706.python.modules_info.line129.comment For example, `['qt', 'qtbase']` for `QtCore` or `['qtmultimedia']` for `QtMultimedia`.
        self.translations = translations or []
        # 010707.python.modules_info.line131.comment List of plugins associated with the Qt module.
        self.plugins = plugins or []
        # 010708.python.modules_info.line133.comment List of bindings (PySide2, PyQt5, PySide6, PyQt6) that provide the python module. This allows association of
        # 010709.python.modules_info.line134.comment plugins and translations with shared libraries even for bindings that do not provide python module binding
        # 010710.python.modules_info.line135.comment for the Qt module.
        self.bindings = set(bindings or [])


# 010711.python.modules_info.line139.comment All Qt-based bindings.
ALL_QT_BINDINGS = {"PySide2", "PyQt5", "PySide6", "PyQt6"}

# 010712.python.modules_info.line142.comment Qt modules information - the core of our Qt collection approach.
# 010713.python.modules_info.line143.comment
# 010714.python.modules_info.line144.comment For every python module/extension (i.e., entry in the list below that has valid `module`), we need a corresponding
# 010715.python.modules_info.line145.comment hook, ensuring that the extension file is analyzed, so that we collect the associated plugins and translation
# 010716.python.modules_info.line146.comment files, as well as perform recursive analysis of link-time binary dependencies (so that plugins and translation files
# 010717.python.modules_info.line147.comment belonging to those dependencies are collected as well).
QT_MODULES_INFO = (
    # 010718.python.modules_info.line149.comment *** qt/qt3d ***
    _QtModuleDef("Qt3DAnimation", shared_lib="3DAnimation"),
    _QtModuleDef("Qt3DCore", shared_lib="3DCore"),
    _QtModuleDef("Qt3DExtras", shared_lib="3DExtras"),
    _QtModuleDef("Qt3DInput", shared_lib="3DInput", plugins=["3dinputdevices"]),
    _QtModuleDef("Qt3DLogic", shared_lib="3DLogic"),
    _QtModuleDef(
        "Qt3DRender", shared_lib="3DRender", plugins=["geometryloaders", "renderplugins", "renderers", "sceneparsers"]
    ),

    # 010719.python.modules_info.line159.comment *** qt/qtactiveqt ***
    # 010720.python.modules_info.line160.comment The python module is called QAxContainer in PyQt bindings, but QtAxContainer in PySide. The associated Qt module
    # 010721.python.modules_info.line161.comment is header-only, so there is no shared library.
    _QtModuleDef("QAxContainer", bindings=["PyQt*"]),
    _QtModuleDef("QtAxContainer", bindings=["PySide*"]),

    # 010722.python.modules_info.line165.comment *** qt/qtcharts ***
    # 010723.python.modules_info.line166.comment The python module is called QtChart in PyQt5, and QtCharts in PySide2, PySide6, and PyQt6 (which corresponds to
    # 010724.python.modules_info.line167.comment the associated Qt module name, QtCharts).
    _QtModuleDef("QtChart", shared_lib="Charts", bindings=["PyQt5"]),
    _QtModuleDef("QtCharts", shared_lib="Charts", bindings=["!PyQt5"]),

    # 010725.python.modules_info.line171.comment *** qt/qtbase ***
    # 010726.python.modules_info.line172.comment QtConcurrent python module is available only in PySide bindings.
    _QtModuleDef(None, shared_lib="Concurrent", bindings=["PyQt*"]),
    _QtModuleDef("QtConcurrent", shared_lib="Concurrent", bindings=["PySide*"]),
    _QtModuleDef("QtCore", shared_lib="Core", translations=["qt", "qtbase"]),
    # 010727.python.modules_info.line176.comment QtDBus python module is available in all bindings but PySide2.
    _QtModuleDef(None, shared_lib="DBus", bindings=["PySide2"]),
    _QtModuleDef("QtDBus", shared_lib="DBus", bindings=["!PySide2"]),
    # 010728.python.modules_info.line179.comment QtNetwork uses different plugins in Qt5 and Qt6.
    _QtModuleDef("QtNetwork", shared_lib="Network", plugins=["bearer"], bindings=["PySide2", "PyQt5"]),
    _QtModuleDef(
        "QtNetwork",
        shared_lib="Network",
        plugins=["networkaccess", "networkinformation", "tls"],
        bindings=["PySide6", "PyQt6"]
    ),
    _QtModuleDef(
        "QtGui",
        shared_lib="Gui",
        plugins=[
            "accessiblebridge",
            "egldeviceintegrations",
            "generic",
            "iconengines",
            "imageformats",
            "platforms",
            "platforms/darwin",
            "platforminputcontexts",
            "platformthemes",
            "xcbglintegrations",
            # 010729.python.modules_info.line201.comment The ``wayland-*`` plugins are part of QtWaylandClient Qt module, whose shared library
            # 010730.python.modules_info.line202.comment (e.g., libQt5WaylandClient.so) is linked by the wayland-related ``platforms`` plugins. Ideally, we would
            # 010731.python.modules_info.line203.comment collect these plugins based on the QtWaylandClient shared library entry, but as our Qt hook utilities do
            # 010732.python.modules_info.line204.comment not scan the plugins for dependencies, that would not work. So instead we list these plugins under QtGui
            # 010733.python.modules_info.line205.comment to achieve pretty much the same end result.
            "wayland-decoration-client",
            "wayland-graphics-integration-client",
            "wayland-shell-integration"
        ]
    ),
    _QtModuleDef("QtOpenGL", shared_lib="OpenGL"),
    # 010734.python.modules_info.line212.comment This python module is specific to PySide2 and has no associated Qt module.
    _QtModuleDef("QtOpenGLFunctions", bindings=["PySide2"]),
    # 010735.python.modules_info.line214.comment This Qt module was introduced with Qt6.
    _QtModuleDef("QtOpenGLWidgets", shared_lib="OpenGLWidgets", bindings=["PySide6", "PyQt6"]),
    _QtModuleDef("QtPrintSupport", shared_lib="PrintSupport", plugins=["printsupport"]),
    _QtModuleDef("QtSql", shared_lib="Sql", plugins=["sqldrivers"]),
    _QtModuleDef("QtTest", shared_lib="Test"),
    _QtModuleDef("QtWidgets", shared_lib="Widgets", plugins=["styles"]),
    _QtModuleDef("QtXml", shared_lib="Xml"),

    # 010736.python.modules_info.line222.comment *** qt/qtconnectivity ***
    _QtModuleDef("QtBluetooth", shared_lib="QtBluetooth", translations=["qtconnectivity"]),
    _QtModuleDef("QtNfc", shared_lib="Nfc", translations=["qtconnectivity"]),

    # 010737.python.modules_info.line226.comment *** qt/qtdatavis3d ***
    _QtModuleDef("QtDataVisualization", shared_lib="DataVisualization"),

    # 010738.python.modules_info.line229.comment *** qt/qtdeclarative ***
    _QtModuleDef("QtQml", shared_lib="Qml", translations=["qtdeclarative"], plugins=["qmltooling"]),
    # 010739.python.modules_info.line231.comment Have the Qt5 variant collect translations for qtquickcontrols (qt/qtquickcontrols provides only QtQuick plugins).
    _QtModuleDef(
        "QtQuick",
        shared_lib="Quick",
        translations=["qtquickcontrols"],
        plugins=["scenegraph"],
        bindings=["PySide2", "PyQt5"]
    ),
    _QtModuleDef("QtQuick", shared_lib="Quick", plugins=["scenegraph"], bindings=["PySide6", "PyQt6"]),
    # 010740.python.modules_info.line240.comment Qt6-only; in Qt5, this module is part of qt/qtquickcontrols2. Python module is available only in PySide6.
    _QtModuleDef(None, shared_lib="QuickControls2", bindings=["PyQt6"]),
    _QtModuleDef("QtQuickControls2", shared_lib="QuickControls2", bindings=["PySide6"]),
    _QtModuleDef("QtQuickWidgets", shared_lib="QuickWidgets"),

    # 010741.python.modules_info.line245.comment *** qt/qtgamepad ***
    # 010742.python.modules_info.line246.comment No python module; shared library -> plugins association entry.
    _QtModuleDef(None, shared_lib="Gamepad", plugins=["gamepads"]),

    # 010743.python.modules_info.line249.comment *** qt/qtgraphs ***
    # 010744.python.modules_info.line250.comment Qt6 >= 6.6.0; python module is available only in PySide6.
    _QtModuleDef("QtGraphs", shared_lib="Graphs", bindings=["PySide6"]),

    # 010745.python.modules_info.line253.comment *** qt/qthttpserver ***
    # 010746.python.modules_info.line254.comment Qt6 >= 6.4.0; python module is available only in PySide6.
    _QtModuleDef("QtHttpServer", shared_lib="HttpServer", bindings=["PySide6"]),

    # 010747.python.modules_info.line257.comment *** qt/qtlocation ***
    # 010748.python.modules_info.line258.comment QtLocation was reintroduced in Qt6 v6.5.0.
    _QtModuleDef(
        "QtLocation",
        shared_lib="Location",
        translations=["qtlocation"],
        plugins=["geoservices"],
        bindings=["PySide2", "PyQt5", "PySide6"]
    ),
    _QtModuleDef(
        "QtPositioning",
        shared_lib="Positioning",
        translations=["qtlocation"],
        plugins=["position"],
    ),

    # 010749.python.modules_info.line273.comment *** qt/qtmacextras ***
    # 010750.python.modules_info.line274.comment Qt5-only Qt module.
    _QtModuleDef("QtMacExtras", shared_lib="MacExtras", bindings=["PySide2", "PyQt5"]),

    # 010751.python.modules_info.line277.comment *** qt/qtmultimedia ***
    # 010752.python.modules_info.line278.comment QtMultimedia on Qt6 currently uses only a subset of plugin names from Qt5 counterpart.
    _QtModuleDef(
        "QtMultimedia",
        shared_lib="Multimedia",
        translations=["qtmultimedia"],
        plugins=[
            "mediaservice", "audio", "video/bufferpool", "video/gstvideorenderer", "video/videonode", "playlistformats",
            "resourcepolicy"
        ],
        bindings=["PySide2", "PyQt5"]
    ),
    _QtModuleDef(
        "QtMultimedia",
        shared_lib="Multimedia",
        translations=["qtmultimedia"],
        # 010753.python.modules_info.line293.comment `multimedia` plugins are available as of Qt6 >= 6.4.0; earlier versions had `video/gstvideorenderer` and
        # 010754.python.modules_info.line294.comment `video/videonode` plugins.
        plugins=["multimedia", "video/gstvideorenderer", "video/videonode"],
        bindings=["PySide6", "PyQt6"]
    ),
    _QtModuleDef("QtMultimediaWidgets", shared_lib="MultimediaWidgets"),
    # 010755.python.modules_info.line299.comment Qt6-only Qt module; python module is available in PySide6 >= 6.4.0 and PyQt6 >= 6.5.0
    _QtModuleDef("QtSpatialAudio", shared_lib="SpatialAudio", bindings=["PySide6", "PyQt6"]),

    # 010756.python.modules_info.line302.comment *** qt/qtnetworkauth ***
    # 010757.python.modules_info.line303.comment QtNetworkAuth python module is available in all bindings but PySide2.
    _QtModuleDef(None, shared_lib="NetworkAuth", bindings=["PySide2"]),
    _QtModuleDef("QtNetworkAuth", shared_lib="NetworkAuth", bindings=["!PySide2"]),

    # 010758.python.modules_info.line307.comment *** qt/qtpurchasing ***
    # 010759.python.modules_info.line308.comment Qt5-only Qt module, python module is available only in PyQt5.
    _QtModuleDef("QtPurchasing", shared_lib="Purchasing", bindings=["PyQt5"]),

    # 010760.python.modules_info.line311.comment *** qt/qtquick1 ***
    # 010761.python.modules_info.line312.comment This is an old, Qt 5.3-era module...
    _QtModuleDef(
        "QtDeclarative",
        shared_lib="Declarative",
        translations=["qtquick1"],
        plugins=["qml1tooling"],
        bindings=["PySide2", "PyQt5"]
    ),

    # 010762.python.modules_info.line321.comment *** qt/qtquick3d ***
    # 010763.python.modules_info.line322.comment QtQuick3D python module is available in all bindings but PySide2.
    _QtModuleDef(None, shared_lib="Quick3D", bindings=["PySide2"]),
    _QtModuleDef("QtQuick3D", shared_lib="Quick3D", bindings=["!PySide2"]),
    # 010764.python.modules_info.line325.comment No python module; shared library -> plugins association entry.
    _QtModuleDef(None, shared_lib="Quick3DAssetImport", plugins=["assetimporters"]),

    # 010765.python.modules_info.line328.comment *** qt/qtquickcontrols2 ***
    # 010766.python.modules_info.line329.comment Qt5-only module; in Qt6, this module is part of qt/declarative. Python module is available only in PySide2.
    _QtModuleDef(None, translations=["qtquickcontrols2"], shared_lib="QuickControls2", bindings=["PyQt5"]),
    _QtModuleDef(
        "QtQuickControls2", translations=["qtquickcontrols2"], shared_lib="QuickControls2", bindings=["PySide2"]
    ),

    # 010767.python.modules_info.line335.comment *** qt/qtremoteobjects ***
    _QtModuleDef("QtRemoteObjects", shared_lib="RemoteObjects"),

    # 010768.python.modules_info.line338.comment *** qt/qtscxml ***
    # 010769.python.modules_info.line339.comment Python module is available only in PySide bindings. Plugins are available only in Qt6.
    # 010770.python.modules_info.line340.comment PyQt wheels do not seem to ship the corresponding Qt modules (shared libs) at all.
    _QtModuleDef("QtScxml", shared_lib="Scxml", bindings=["PySide2"]),
    _QtModuleDef("QtScxml", shared_lib="Scxml", plugins=["scxmldatamodel"], bindings=["PySide6"]),
    # 010771.python.modules_info.line343.comment Qt6-only Qt module, python module is available only in PySide6.
    _QtModuleDef("QtStateMachine", shared_lib="StateMachine", bindings=["PySide6"]),

    # 010772.python.modules_info.line346.comment *** qt/qtsensors ***
    _QtModuleDef("QtSensors", shared_lib="Sensors", plugins=["sensors", "sensorgestures"]),

    # 010773.python.modules_info.line349.comment *** qt/qtserialport ***
    _QtModuleDef("QtSerialPort", shared_lib="SerialPort", translations=["qtserialport"]),

    # 010774.python.modules_info.line352.comment *** qt/qtscript ***
    # 010775.python.modules_info.line353.comment Qt5-only Qt module, python module is available only in PySide2. PyQt5 wheels do not seem to ship the corresponding
    # 010776.python.modules_info.line354.comment Qt modules (shared libs) at all.
    _QtModuleDef("QtScript", shared_lib="Script", translations=["qtscript"], plugins=["script"], bindings=["PySide2"]),
    _QtModuleDef("QtScriptTools", shared_lib="ScriptTools", bindings=["PySide2"]),

    # 010777.python.modules_info.line358.comment *** qt/qtserialbus ***
    # 010778.python.modules_info.line359.comment No python module; shared library -> plugins association entry.
    # 010779.python.modules_info.line360.comment PySide6 6.5.0 introduced python module.
    _QtModuleDef(None, shared_lib="SerialBus", plugins=["canbus"], bindings=["!PySide6"]),
    _QtModuleDef("QtSerialBus", shared_lib="SerialBus", plugins=["canbus"], bindings=["PySide6"]),

    # 010780.python.modules_info.line364.comment *** qt/qtsvg ***
    _QtModuleDef("QtSvg", shared_lib="Svg"),
    # 010781.python.modules_info.line366.comment Qt6-only Qt module.
    _QtModuleDef("QtSvgWidgets", shared_lib="SvgWidgets", bindings=["PySide6", "PyQt6"]),

    # 010782.python.modules_info.line369.comment *** qt/qtspeech ***
    _QtModuleDef("QtTextToSpeech", shared_lib="TextToSpeech", plugins=["texttospeech"]),

    # 010783.python.modules_info.line372.comment *** qt/qttools ***
    # 010784.python.modules_info.line373.comment QtDesigner python module is available in all bindings but PySide2.
    _QtModuleDef(None, shared_lib="Designer", plugins=["designer"], bindings=["PySide2"]),
    _QtModuleDef(
        "QtDesigner", shared_lib="Designer", translations=["designer"], plugins=["designer"], bindings=["!PySide2"]
    ),
    _QtModuleDef("QtHelp", shared_lib="Help", translations=["qt_help"]),
    # 010785.python.modules_info.line379.comment Python module is available only in PySide bindings.
    _QtModuleDef("QtUiTools", shared_lib="UiTools", bindings=["PySide*"]),

    # 010786.python.modules_info.line382.comment *** qt/qtvirtualkeyboard ***
    # 010787.python.modules_info.line383.comment No python module; shared library -> plugins association entry.
    _QtModuleDef(None, shared_lib="VirtualKeyboard", plugins=["virtualkeyboard"]),

    # 010788.python.modules_info.line386.comment *** qt/qtwebchannel ***
    _QtModuleDef("QtWebChannel", shared_lib="WebChannel"),

    # 010789.python.modules_info.line389.comment *** qt/qtwebengine ***
    # 010790.python.modules_info.line390.comment QtWebEngine is Qt5-only module (replaced by QtWebEngineQuick in Qt6).
    _QtModuleDef("QtWebEngine", shared_lib="WebEngine", bindings=["PySide2", "PyQt5"]),
    _QtModuleDef("QtWebEngineCore", shared_lib="WebEngineCore", translations=["qtwebengine"]),
    # 010791.python.modules_info.line393.comment QtWebEngineQuick is Qt6-only module (replacement for QtWebEngine in Qt5).
    _QtModuleDef("QtWebEngineQuick", shared_lib="WebEngineQuick", bindings=["PySide6", "PyQt6"]),
    _QtModuleDef("QtWebEngineWidgets", shared_lib="WebEngineWidgets"),
    # 010792.python.modules_info.line396.comment QtPdf and QtPdfWidgets have python module available in PySide6 and PyQt6 >= 6.4.0.
    _QtModuleDef("QtPdf", shared_lib="Pdf", bindings=["PySide6", "PyQt6"]),
    _QtModuleDef("QtPdfWidgets", shared_lib="PdfWidgets", bindings=["PySide6", "PyQt6"]),

    # 010793.python.modules_info.line400.comment *** qt/qtwebsockets ***
    _QtModuleDef("QtWebSockets", shared_lib="WebSockets", translations=["qtwebsockets"]),

    # 010794.python.modules_info.line403.comment *** qt/qtwebview ***
    # 010795.python.modules_info.line404.comment No python module; shared library -> plugins association entry.
    _QtModuleDef(None, shared_lib="WebView", plugins=["webview"]),

    # 010796.python.modules_info.line407.comment *** qt/qtwinextras ***
    # 010797.python.modules_info.line408.comment Qt5-only Qt module.
    _QtModuleDef("QtWinExtras", shared_lib="WinExtras", bindings=["PySide2", "PyQt5"]),

    # 010798.python.modules_info.line411.comment *** qt/qtx11extras ***
    # 010799.python.modules_info.line412.comment Qt5-only Qt module.
    _QtModuleDef("QtX11Extras", shared_lib="X11Extras", bindings=["PySide2", "PyQt5"]),

    # 010800.python.modules_info.line415.comment *** qt/qtxmlpatterns ***
    # 010801.python.modules_info.line416.comment Qt5-only Qt module.
    _QtModuleDef(
        "QtXmlPatterns", shared_lib="XmlPatterns", translations=["qtxmlpatterns"], bindings=["PySide2", "PyQt5"]
    ),

    # 010802.python.modules_info.line421.comment *** qscintilla ***
    # 010803.python.modules_info.line422.comment Python module is available only in PyQt bindings. No associated shared library.
    _QtModuleDef("Qsci", translations=["qscintilla"], bindings=["PyQt*"]),
)


# 010804.python.modules_info.line427.comment Helpers for turning Qt namespace specifiers, such as "!PySide2" or "PyQt*", into set of applicable
# 010805.python.modules_info.line428.comment namespaces.
def process_namespace_strings(namespaces):
    """"Process list of Qt namespace specifier strings into set of namespaces."""
    bindings = set()
    for namespace in namespaces:
        bindings |= _process_namespace_string(namespace)
    return bindings


def _process_namespace_string(namespace):
    """Expand a Qt namespace specifier string into set of namespaces."""
    if namespace.startswith("!"):
        bindings = _process_namespace_string(namespace[1:])
        return ALL_QT_BINDINGS - bindings
    else:
        if namespace == "PySide*":
            return {"PySide2", "PySide6"}
        elif namespace == "PyQt*":
            return {"PyQt5", "PyQt6"}
        elif namespace in ALL_QT_BINDINGS:
            return {namespace}
        else:
            raise ValueError(f"Invalid Qt namespace specifier: {namespace}!")
