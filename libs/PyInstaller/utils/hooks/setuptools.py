# 010806.python.setuptools.line1.comment ----------------------------------------------------------------------------
# 010807.python.setuptools.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 010808.python.setuptools.line3.comment
# 010809.python.setuptools.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 010810.python.setuptools.line5.comment or later) with exception for distributing the bootloader.
# 010811.python.setuptools.line6.comment
# 010812.python.setuptools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 010813.python.setuptools.line8.comment
# 010814.python.setuptools.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 010815.python.setuptools.line10.comment -----------------------------------------------------------------------------
from PyInstaller import log as logging
from PyInstaller import isolated

logger = logging.getLogger(__name__)


# 010816.python.setuptools.line17.comment Import setuptools and analyze its properties in an isolated subprocess. This function is called by `SetuptoolsInfo`
# 010817.python.setuptools.line18.comment to initialize its properties.
@isolated.decorate
def _retrieve_setuptools_info():
    import importlib

    try:
        setuptools = importlib.import_module("setuptools")  # noqa: F841
    except ModuleNotFoundError:
        return None

    # 010819.python.setuptools.line28.comment Delay these imports until after we have confirmed that setuptools is importable.
    import pathlib

    import packaging.version

    from PyInstaller.compat import importlib_metadata
    from PyInstaller.utils.hooks import (
        collect_data_files,
        collect_submodules,
    )

    # 010820.python.setuptools.line39.comment Try to retrieve the version. At this point, failure is consider an error.
    version_string = importlib_metadata.version("setuptools")
    version = packaging.version.Version(version_string).release  # Use the version tuple

    # 010822.python.setuptools.line43.comment setuptools >= 60.0 its vendored copy of distutils (mainly due to its removal from stdlib in python >= 3.12).
    distutils_vendored = False
    distutils_modules = []
    if version >= (60, 0):
        distutils_vendored = True
        distutils_modules += ["_distutils_hack"]
        distutils_modules += collect_submodules(
            "setuptools._distutils",
            # 010823.python.setuptools.line51.comment setuptools 71.0.1 ~ 71.0.4 include `setuptools._distutils.tests`; avoid explicitly collecting it
            # 010824.python.setuptools.line52.comment (t was not included in earlier setuptools releases).
            filter=lambda name: name != 'setuptools._distutils.tests',
        )

    # 010825.python.setuptools.line56.comment Check if `setuptools._vendor` exists. Some linux distributions opt to de-vendor `setuptools` and remove the
    # 010826.python.setuptools.line57.comment `setuptools._vendor` directory altogether. If this is the case, most of additional processing below should be
    # 010827.python.setuptools.line58.comment skipped to avoid errors and warnings about non-existent `setuptools._vendor` module.
    try:
        setuptools_vendor = importlib.import_module("setuptools._vendor")
    except ModuleNotFoundError:
        setuptools_vendor = None

    # 010828.python.setuptools.line64.comment Check for exposed packages/modules that are vendored by setuptools. If stand-alone version is not provided in the
    # 010829.python.setuptools.line65.comment environment, setuptools-vendored version is exposed (due to location of `setuptools._vendor` being appended to
    # 010830.python.setuptools.line66.comment `sys.path`. Applicable to v71.0.0 and later.
    vendored_status = dict()
    if version >= (71, 0) and setuptools_vendor is not None:
        VENDORED_CANDIDATES = (
            "autocommand",
            "backports.tarfile",
            "importlib_metadata",
            "importlib_resources",
            "inflect",
            "jaraco.context",
            "jaraco.functools",
            "jaraco.text",
            "more_itertools",
            "ordered_set",
            "packaging",
            "platformdirs",
            "tomli",
            "typeguard",
            "typing_extensions",
            "wheel",
            "zipp",
        )

        # 010831.python.setuptools.line89.comment Resolve path(s) of `setuptools_vendor` package.
        setuptools_vendor_paths = [pathlib.Path(path).resolve() for path in setuptools_vendor.__path__]

        # 010832.python.setuptools.line92.comment Process each candidate
        for candidate_name in VENDORED_CANDIDATES:
            try:
                candidate = importlib.import_module(candidate_name)
            except ImportError:
                continue

            # 010833.python.setuptools.line99.comment Check the __file__ attribute (modules and regular packages). Will not work with namespace packages, but
            # 010834.python.setuptools.line100.comment at the moment, there are none.
            candidate_file_attr = getattr(candidate, '__file__', None)
            if candidate_file_attr is not None:
                candidate_path = pathlib.Path(candidate_file_attr).parent.resolve()
                is_vendored = any([
                    setuptools_vendor_path in candidate_path.parents or candidate_path == setuptools_vendor_path
                    for setuptools_vendor_path in setuptools_vendor_paths
                ])
                vendored_status[candidate_name] = is_vendored

    # 010835.python.setuptools.line110.comment Collect submodules from `setuptools._vendor`, regardless of whether the vendored package is exposed or
    # 010836.python.setuptools.line111.comment not (because setuptools might need/use it either way).
    vendored_modules = []
    if setuptools_vendor is not None:
        EXCLUDED_VENDORED_MODULES = (
            # 010837.python.setuptools.line115.comment Prevent recursing into setuptools._vendor.pyparsing.diagram, which typically fails to be imported due
            # 010838.python.setuptools.line116.comment to missing dependencies (railroad, pyparsing (?), jinja2) and generates a warning... As the module is
            # 010839.python.setuptools.line117.comment usually unimportable, it is likely not to be used by setuptools. NOTE: pyparsing was removed from
            # 010840.python.setuptools.line118.comment vendored packages in setuptools v67.0.0; keep this exclude around for earlier versions.
            'setuptools._vendor.pyparsing.diagram',
            # 010841.python.setuptools.line120.comment Setuptools >= 71 started shipping vendored dependencies that include tests; avoid collecting those via
            # 010842.python.setuptools.line121.comment hidden imports. (Note that this also prevents creation of aliases for these module, but that should
            # 010843.python.setuptools.line122.comment not be an issue, as they should not be referenced from anywhere).
            'setuptools._vendor.importlib_resources.tests',
            # 010844.python.setuptools.line124.comment These appear to be utility scripts bundled with the jaraco.text package - exclude them.
            'setuptools._vendor.jaraco.text.show-newlines',
            'setuptools._vendor.jaraco.text.strip-prefix',
            'setuptools._vendor.jaraco.text.to-dvorak',
            'setuptools._vendor.jaraco.text.to-qwerty',
        )
        vendored_modules += collect_submodules(
            'setuptools._vendor',
            filter=lambda name: name not in EXCLUDED_VENDORED_MODULES,
        )

        # 010845.python.setuptools.line135.comment `collect_submodules` (and its underlying `pkgutil.iter_modules` do not discover namespace sub-packages, in
        # 010846.python.setuptools.line136.comment this case `setuptools._vendor.jaraco`. So force a manual scan of modules/packages inside it.
        vendored_modules += collect_submodules(
            'setuptools._vendor.jaraco',
            filter=lambda name: name not in EXCLUDED_VENDORED_MODULES,
        )

    # 010847.python.setuptools.line142.comment *** Data files for vendored packages ***
    vendored_data = []

    if version >= (71, 0) and setuptools_vendor is not None:
        # 010848.python.setuptools.line146.comment Since the vendored dependencies from `setuptools/_vendor` are now visible to the outside world, make
        # 010849.python.setuptools.line147.comment sure we collect their metadata. (We cannot use copy_metadata here, because we need to collect data
        # 010850.python.setuptools.line148.comment files to their original locations).
        vendored_data += collect_data_files('setuptools._vendor', includes=['**/*.dist-info'])
        # 010851.python.setuptools.line150.comment Similarly, ensure that `Lorem ipsum.txt` from vendored jaraco.text is collected
        vendored_data += collect_data_files('setuptools._vendor.jaraco.text', includes=['**/Lorem ipsum.txt'])

    # 010852.python.setuptools.line153.comment Return dictionary with collected information
    return {
        "available": True,
        "version": version,
        "distutils_vendored": distutils_vendored,
        "distutils_modules": distutils_modules,
        "vendored_status": vendored_status,
        "vendored_modules": vendored_modules,
        "vendored_data": vendored_data,
    }


class SetuptoolsInfo:
    def __init__(self):
        pass

    def __repr__(self):
        return "SetuptoolsInfo"

    # 010853.python.setuptools.line172.comment Delay initialization of setuptools information until until the corresponding attributes are first requested.
    def __getattr__(self, name):
        if 'available' in self.__dict__:
            # 010854.python.setuptools.line175.comment Initialization was already done, but requested attribute is not available.
            raise AttributeError(name)

        # 010855.python.setuptools.line178.comment Load setuptools info...
        self._load_setuptools_info()
        # 010856.python.setuptools.line180.comment ... and return the requested attribute
        return getattr(self, name)

    def _load_setuptools_info(self):
        logger.info("%s: initializing cached setuptools info...", self)

        # 010857.python.setuptools.line186.comment Initialize variables so that they might be accessed even if setuptools is unavailable or if initialization
        # 010858.python.setuptools.line187.comment fails for some reason.
        self.available = False
        self.version = None
        self.distutils_vendored = False
        self.distutils_modules = []
        self.vendored_status = dict()
        self.vendored_modules = []
        self.vendored_data = []

        try:
            setuptools_info = _retrieve_setuptools_info()
        except Exception as e:
            logger.warning("%s: failed to obtain setuptools info: %s", self, e)
            return

        # 010859.python.setuptools.line202.comment If package could not be imported, `_retrieve_setuptools_info` returns None. In such cases, emit a debug
        # 010860.python.setuptools.line203.comment message instead of a warning, because this initialization might be triggered by a helper function that is
        # 010861.python.setuptools.line204.comment trying to determine availability of `setuptools` by inspecting the `available` attribute.
        if setuptools_info is None:
            logger.debug("%s: failed to obtain setuptools info: setuptools could not be imported.", self)
            return

        # 010862.python.setuptools.line209.comment Copy properties
        for key, value in setuptools_info.items():
            setattr(self, key, value)

    def is_vendored(self, module_name):
        return self.vendored_status.get(module_name, False)

    @staticmethod
    def _create_vendored_aliases(vendored_name, module_name, modules_list):
        # 010863.python.setuptools.line218.comment Create aliases for all submodules
        prefix_len = len(vendored_name)  # Length of target-name prefix to remove
        return ((module_name + vendored_module[prefix_len:], vendored_module) for vendored_module in modules_list
                if vendored_module.startswith(vendored_name))

    def get_vendored_aliases(self, module_name):
        vendored_name = f"setuptools._vendor.{module_name}"
        return self._create_vendored_aliases(vendored_name, module_name, self.vendored_modules)

    def get_distutils_aliases(self):
        vendored_name = "setuptools._distutils"
        return self._create_vendored_aliases(vendored_name, "distutils", self.distutils_modules)


setuptools_info = SetuptoolsInfo()


def pre_safe_import_module(api):
    """
    A common implementation of pre_safe_import_module hook function.

    This function can be either called from the `pre_safe_import_module` function in a pre-safe-import-module hook, or
    just imported into the hook.
    """
    module_name = api.module_name

    # 010865.python.setuptools.line244.comment Check if the package/module is a vendored copy. This also returns False is setuptools is unavailable, because
    # 010866.python.setuptools.line245.comment vendored module status dictionary will be empty.
    if not setuptools_info.is_vendored(module_name):
        return

    vendored_name = f"setuptools._vendor.{module_name}"
    logger.info(
        "Setuptools: %r appears to be a setuptools-vendored copy - creating alias to %r!", module_name, vendored_name
    )

    # 010867.python.setuptools.line254.comment Create aliases for all (sub)modules
    for aliased_name, real_vendored_name in setuptools_info.get_vendored_aliases(module_name):
        api.add_alias_module(real_vendored_name, aliased_name)
