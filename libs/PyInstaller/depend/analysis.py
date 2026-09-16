# 001907.python.analysis.line1.comment -----------------------------------------------------------------------------
# 001908.python.analysis.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 001909.python.analysis.line3.comment
# 001910.python.analysis.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 001911.python.analysis.line5.comment or later) with exception for distributing the bootloader.
# 001912.python.analysis.line6.comment
# 001913.python.analysis.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 001914.python.analysis.line8.comment
# 001915.python.analysis.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 001916.python.analysis.line10.comment -----------------------------------------------------------------------------
"""
Define a modified ModuleGraph that can return its contents as a TOC and in other ways act like the old ImpTracker.
TODO: This class, along with TOC and Tree, should be in a separate module.

For reference, the ModuleGraph node types and their contents:

 nodetype         identifier        filename

 Script           full path to .py  full path to .py
 SourceModule     basename          full path to .py
 BuiltinModule    basename          None
 CompiledModule   basename          full path to .pyc
 Extension        basename          full path to .so
 MissingModule    basename          None
 Package          basename          full path to __init__.py
        packagepath is ['path to package']
        globalnames is set of global names __init__.py defines
 ExtensionPackage basename          full path to __init__.{so,dll}
        packagepath is ['path to package']

The main extension here over ModuleGraph is a method to extract nodes from the flattened graph and return them as a
TOC, or added to a TOC. Other added methods look up nodes by identifier and return facts about them, replacing what
the old ImpTracker list could do.
"""

import ast
import os
import sys
import traceback
from collections import defaultdict
from copy import deepcopy

from PyInstaller import HOMEPATH, PACKAGEPATH
from PyInstaller import log as logging
from PyInstaller.building.utils import destination_name_for_extension
from PyInstaller.compat import (
    BAD_MODULE_TYPES, BINARY_MODULE_TYPES, MODULE_TYPES_TO_TOC_DICT, PURE_PYTHON_MODULE_TYPES, PY3_BASE_MODULES,
    VALID_MODULE_TYPES, importlib_load_source, is_win
)
from PyInstaller.depend import bytecode
from PyInstaller.depend.imphook import AdditionalFilesCache, ModuleHookCache
from PyInstaller.depend.imphookapi import (PreFindModulePathAPI, PreSafeImportModuleAPI)
from PyInstaller.lib.modulegraph.find_modules import get_implies
from PyInstaller.lib.modulegraph.modulegraph import ModuleGraph, DEFAULT_IMPORT_LEVEL, ABSOLUTE_IMPORT_LEVEL, Package
from PyInstaller.log import DEBUG, INFO, TRACE
from PyInstaller.utils.hooks import collect_submodules, is_package

logger = logging.getLogger(__name__)

# 001917.python.analysis.line60.comment Location-based hook priority constants
HOOK_PRIORITY_BUILTIN_HOOKS = -2000  # Built-in hooks. Lowest priority.
HOOK_PRIORITY_CONTRIBUTED_HOOKS = -1000  # Hooks from pyinstaller-hooks-contrib package.
HOOK_PRIORITY_UPSTREAM_HOOKS = 0  # Hooks provided by packages themselves, via entry-points.
HOOK_PRIORITY_USER_HOOKS = 1000  # User-supplied hooks (command-line / spec file). Highest priority.


class PyiModuleGraph(ModuleGraph):
    """
    Directed graph whose nodes represent modules and edges represent dependencies between these modules.

    This high-level subclass wraps the lower-level `ModuleGraph` class with support for graph and runtime hooks.
    While each instance of `ModuleGraph` represents a set of disconnected trees, each instance of this class *only*
    represents a single connected tree whose root node is the Python script originally passed by the user on the
    command line. For that reason, while there may (and typically do) exist more than one `ModuleGraph` instance,
    there typically exists only a singleton instance of this class.

    Attributes
    ----------
    _hooks : ModuleHookCache
        Dictionary mapping the fully-qualified names of all modules with normal (post-graph) hooks to the absolute paths
        of such hooks. See the the `_find_module_path()` method for details.
    _hooks_pre_find_module_path : ModuleHookCache
        Dictionary mapping the fully-qualified names of all modules with pre-find module path hooks to the absolute
        paths of such hooks. See the the `_find_module_path()` method for details.
    _hooks_pre_safe_import_module : ModuleHookCache
        Dictionary mapping the fully-qualified names of all modules with pre-safe import module hooks to the absolute
        paths of such hooks. See the `_safe_import_module()` method for details.
    _user_hook_dirs : list
        List of the absolute paths of all directories containing user-defined hooks for the current application.
    _excludes : list
        List of module names to be excluded when searching for dependencies.
    _additional_files_cache : AdditionalFilesCache
        Cache of all external dependencies (e.g., binaries, datas) listed in hook scripts for imported modules.
    _module_collection_mode : dict
        A dictionary of module/package collection mode settings set by hook scripts for their modules.
    _bindepend_symlink_suppression : set
        A set of paths or path patterns corresponding to shared libraries for which binary dependency analysis should
        not create symbolic links into top-level application directory.
    _base_modules: list
        Dependencies for `base_library.zip` (which remain the same for every executable).
    """

    # 001922.python.analysis.line103.comment Note: these levels are completely arbitrary and may be adjusted if needed.
    LOG_LEVEL_MAPPING = {0: INFO, 1: DEBUG, 2: TRACE, 3: TRACE, 4: TRACE}

    def __init__(self, pyi_homepath, user_hook_dirs=(), excludes=(), **kwargs):
        super().__init__(excludes=excludes, **kwargs)
        # 001923.python.analysis.line108.comment Homepath to the place where is PyInstaller located.
        self._homepath = pyi_homepath
        # 001924.python.analysis.line110.comment modulegraph Node for the main python script that is analyzed by PyInstaller.
        self._top_script_node = None

        # 001925.python.analysis.line113.comment Absolute paths of all user-defined hook directories.
        self._excludes = excludes
        self._reset(user_hook_dirs)
        self._analyze_base_modules()

    def _reset(self, user_hook_dirs):
        """
        Reset for another set of scripts. This is primary required for running the test-suite.
        """
        self._top_script_node = None
        self._additional_files_cache = AdditionalFilesCache()
        self._module_collection_mode = dict()
        self._bindepend_symlink_suppression = set()
        # 001926.python.analysis.line126.comment Hook sources: user-supplied (command-line / spec file), entry-point (upstream hooks, contributed hooks), and
        # 001927.python.analysis.line127.comment built-in hooks. The order does not really matter anymore, because each entry is now a (location, priority)
        # 001928.python.analysis.line128.comment tuple, and order is determined from assigned priority (which may also be overridden by hooks themselves).
        self._user_hook_dirs = [
            *user_hook_dirs,
            (os.path.join(PACKAGEPATH, 'hooks'), HOOK_PRIORITY_BUILTIN_HOOKS),
        ]
        # 001929.python.analysis.line133.comment Hook-specific lookup tables. These need to reset when reusing cached PyiModuleGraph to avoid hooks to refer to
        # 001930.python.analysis.line134.comment files or data from another test-case.
        logger.info('Initializing module graph hook caches...')
        self._hooks = self._cache_hooks("")
        self._hooks_pre_safe_import_module = self._cache_hooks('pre_safe_import_module')
        self._hooks_pre_find_module_path = self._cache_hooks('pre_find_module_path')

        # 001931.python.analysis.line140.comment Search for run-time hooks in all hook directories.
        self._available_rthooks = defaultdict(list)
        for uhd, _ in self._user_hook_dirs:
            uhd_path = os.path.abspath(os.path.join(uhd, 'rthooks.dat'))
            try:
                with open(uhd_path, 'r', encoding='utf-8') as f:
                    rthooks = ast.literal_eval(f.read())
            except FileNotFoundError:
                # 001932.python.analysis.line148.comment Ignore if this hook path doesn't have run-time hooks.
                continue
            except Exception as e:
                logger.error('Unable to read run-time hooks from %r: %s' % (uhd_path, e))
                continue

            self._merge_rthooks(rthooks, uhd, uhd_path)

        # 001933.python.analysis.line156.comment Convert back to a standard dict.
        self._available_rthooks = dict(self._available_rthooks)

    def _merge_rthooks(self, rthooks, uhd, uhd_path):
        """
        The expected data structure for a run-time hook file is a Python dictionary of type ``Dict[str, List[str]]``,
        where the dictionary keys are module names and the sequence strings are Python file names.

        Check then merge this data structure, updating the file names to be absolute.
        """
        # 001934.python.analysis.line166.comment Check that the root element is a dict.
        assert isinstance(rthooks, dict), 'The root element in %s must be a dict.' % uhd_path
        for module_name, python_file_name_list in rthooks.items():
            # 001935.python.analysis.line169.comment Ensure the key is a string.
            assert isinstance(module_name, str), \
                '%s must be a dict whose keys are strings; %s is not a string.' % (uhd_path, module_name)
            # 001936.python.analysis.line172.comment Ensure the value is a list.
            assert isinstance(python_file_name_list, list), \
                'The value of %s key %s must be a list.' % (uhd_path, module_name)
            if module_name in self._available_rthooks:
                logger.warning(
                    'Runtime hooks for %s have already been defined. Skipping the runtime hooks for %s that are '
                    'defined in %s.', module_name, module_name, os.path.join(uhd, 'rthooks')
                )
                # 001937.python.analysis.line180.comment Skip this module
                continue
            # 001938.python.analysis.line182.comment Merge this with existing run-time hooks.
            for python_file_name in python_file_name_list:
                # 001939.python.analysis.line184.comment Ensure each item in the list is a string.
                assert isinstance(python_file_name, str), \
                    '%s key %s, item %r must be a string.' % (uhd_path, module_name, python_file_name)
                # 001940.python.analysis.line187.comment Transform it into an absolute path.
                abs_path = os.path.join(uhd, 'rthooks', python_file_name)
                # 001941.python.analysis.line189.comment Make sure this file exists.
                assert os.path.exists(abs_path), \
                    'In %s, key %s, the file %r expected to be located at %r does not exist.' % \
                    (uhd_path, module_name, python_file_name, abs_path)
                # 001942.python.analysis.line193.comment Merge it.
                self._available_rthooks[module_name].append(abs_path)

    @staticmethod
    def _findCaller(*args, **kwargs):
        # 001943.python.analysis.line198.comment Used to add an additional stack-frame above logger.findCaller. findCaller expects the caller to be three
        # 001944.python.analysis.line199.comment stack-frames above itself.
        return logger.findCaller(*args, **kwargs)

    def msg(self, level, s, *args):
        """
        Print a debug message with the given level.

        1. Map the msg log level to a logger log level.
        2. Generate the message format (the same format as ModuleGraph)
        3. Find the caller, which findCaller expects three stack-frames above itself:
            [3] caller -> [2] msg (here) -> [1] _findCaller -> [0] logger.findCaller
        4. Create a logRecord with the caller's information.
        5. Handle the logRecord.
        """
        try:
            level = self.LOG_LEVEL_MAPPING[level]
        except KeyError:
            return
        if not logger.isEnabledFor(level):
            return

        msg = "%s %s" % (s, ' '.join(map(repr, args)))

        try:
            fn, lno, func, sinfo = self._findCaller()
        except ValueError:  # pragma: no cover
            fn, lno, func, sinfo = "(unknown file)", 0, "(unknown function)", None
        record = logger.makeRecord(logger.name, level, fn, lno, msg, [], None, func, None, sinfo)

        logger.handle(record)

    # 001946.python.analysis.line230.comment Set logging methods so that the stack is correctly detected.
    msgin = msg
    msgout = msg

    def _cache_hooks(self, hook_type):
        """
        Create a cache of all hooks of the specified type.

        The cache will include all official hooks defined by the PyInstaller codebase _and_ all unofficial hooks
        defined for the current application.

        Parameters
        ----------
        hook_type : str
            Type of hooks to be cached, equivalent to the basename of the subpackage of the `PyInstaller.hooks`
            package containing such hooks (e.g., empty string for standard hooks, `pre_safe_import_module` for
            pre-safe-import-module hooks, `pre_find_module_path` for pre-find-module-path hooks).
        """
        # 001947.python.analysis.line248.comment Cache of this type of hooks.
        hook_dirs = []
        for user_hook_dir, priority in self._user_hook_dirs:
            # 001948.python.analysis.line251.comment Absolute path of the user-defined subdirectory of this hook type. If this directory exists, add it to the
            # 001949.python.analysis.line252.comment list to be cached.
            user_hook_type_dir = os.path.join(user_hook_dir, hook_type)
            if os.path.isdir(user_hook_type_dir):
                hook_dirs.append((user_hook_type_dir, priority))

        return ModuleHookCache(self, hook_dirs)

    def _analyze_base_modules(self):
        """
        Analyze dependencies of the the modules in base_library.zip.
        """
        logger.info('Analyzing modules for base_library.zip ...')
        required_mods = []
        # 001950.python.analysis.line265.comment Collect submodules from required modules in base_library.zip.
        for m in PY3_BASE_MODULES:
            if is_package(m):
                required_mods += collect_submodules(m)
            else:
                required_mods.append(m)
        # 001951.python.analysis.line271.comment Initialize ModuleGraph.
        self._base_modules = [mod for req in required_mods for mod in self.import_hook(req)]

    def add_script(self, pathname, caller=None):
        """
        Wrap the parent's 'run_script' method and create graph from the first script in the analysis, and save its
        node to use as the "caller" node for all others. This gives a connected graph rather than a collection of
        unrelated trees.
        """
        if self._top_script_node is None:
            # 001952.python.analysis.line281.comment Remember the node for the first script.
            try:
                self._top_script_node = super().add_script(pathname)
            except SyntaxError:
                print("\nSyntax error in", pathname, file=sys.stderr)
                formatted_lines = traceback.format_exc().splitlines(True)
                print(*formatted_lines[-4:], file=sys.stderr)
                sys.exit(1)
            # 001953.python.analysis.line289.comment Create references from the top script to the base_modules in graph.
            for node in self._base_modules:
                self.add_edge(self._top_script_node, node)
            # 001954.python.analysis.line292.comment Return top-level script node.
            return self._top_script_node
        else:
            if not caller:
                # 001955.python.analysis.line296.comment Defaults to as any additional script is called from the top-level script.
                caller = self._top_script_node
            return super().add_script(pathname, caller=caller)

    def process_post_graph_hooks(self, analysis):
        """
        For each imported module, run this module's post-graph hooks if any.

        Parameters
        ----------
        analysis: build_main.Analysis
            The Analysis that calls the hooks

        """
        # 001956.python.analysis.line310.comment For each iteration of the infinite "while" loop below:
        # 001957.python.analysis.line311.comment
        # 001958.python.analysis.line312.comment 1. All hook() functions defined in cached hooks for imported modules are called. This may result in new
        # 001959.python.analysis.line313.comment modules being imported (e.g., as hidden imports) that were ignored earlier in the current iteration: if
        # 001960.python.analysis.line314.comment this is the case, all hook() functions defined in cached hooks for these modules will be called by the next
        # 001961.python.analysis.line315.comment iteration.
        # 001962.python.analysis.line316.comment 2. All cached hooks whose hook() functions were called are removed from this cache. If this cache is empty, no
        # 001963.python.analysis.line317.comment hook() functions will be called by the next iteration and this loop will be terminated.
        # 001964.python.analysis.line318.comment 3. If no hook() functions were called, this loop is terminated.
        logger.info('Processing module hooks (post-graph stage)...')
        while True:
            # 001965.python.analysis.line321.comment Set of the names of all imported modules whose post-graph hooks are run by this iteration, preventing the
            # 001966.python.analysis.line322.comment next iteration from re- running these hooks. If still empty at the end of this iteration, no post-graph
            # 001967.python.analysis.line323.comment hooks were run; thus, this loop will be terminated.
            hooked_module_names = set()

            # 001968.python.analysis.line326.comment For each remaining hookable module and corresponding hooks...
            for module_name, module_hook in self._hooks.items():
                # 001969.python.analysis.line328.comment Graph node for this module if imported or "None" otherwise.
                module_node = self.find_node(module_name, create_nspkg=False)

                # 001970.python.analysis.line331.comment If this module has not been imported, temporarily ignore it. This module is retained in the cache, as
                # 001971.python.analysis.line332.comment a subsequently run post-graph hook could import this module as a hidden import.
                if module_node is None:
                    continue

                # 001972.python.analysis.line336.comment If this module is unimportable, permanently ignore it.
                if type(module_node).__name__ not in VALID_MODULE_TYPES:
                    hooked_module_names.add(module_name)
                    continue

                # 001973.python.analysis.line341.comment Run this script's post-graph hook.
                module_hook.post_graph(analysis)

                # 001974.python.analysis.line344.comment Cache all external dependencies listed by this script after running this hook, which could add
                # 001975.python.analysis.line345.comment dependencies.
                self._additional_files_cache.add(module_name, module_hook.binaries, module_hook.datas)

                # 001976.python.analysis.line348.comment Update package collection mode settings.
                self._module_collection_mode.update(module_hook.module_collection_mode)

                # 001977.python.analysis.line351.comment Update symbolic link suppression patterns for binary dependency analysis.
                self._bindepend_symlink_suppression.update(module_hook.bindepend_symlink_suppression)

                # 001978.python.analysis.line354.comment Prevent this module's hooks from being run again.
                hooked_module_names.add(module_name)

            # 001979.python.analysis.line357.comment Prevent all post-graph hooks run above from being run again by the next iteration.
            self._hooks.remove_modules(*hooked_module_names)

            # 001980.python.analysis.line360.comment If no post-graph hooks were run, terminate iteration.
            if not hooked_module_names:
                break

    def _find_all_excluded_imports(self, module_name):
        """
        Collect excludedimports from the hooks of the specified module and all its parents.
        """
        excluded_imports = set()
        while module_name:
            # 001981.python.analysis.line370.comment Gather excluded imports from hook belonging to the module.
            module_hook = self._hooks.get(module_name, None)
            if module_hook:
                excluded_imports.update(module_hook.excludedimports)
            # 001982.python.analysis.line374.comment Change module name to the module's parent name
            module_name = module_name.rpartition('.')[0]
        return excluded_imports

    def _safe_import_hook(
        self, target_module_partname, source_module, target_attr_names, level=DEFAULT_IMPORT_LEVEL, edge_attr=None
    ):
        if source_module is not None:
            # 001983.python.analysis.line382.comment Gather all excluded imports for the referring modules, as well as its parents.
            # 001984.python.analysis.line383.comment For example, we want the excluded imports specified by hook for PIL to be also applied when the referring
            # 001985.python.analysis.line384.comment module is its submodule, PIL.Image.
            excluded_imports = self._find_all_excluded_imports(source_module.identifier)

            # 001986.python.analysis.line387.comment Apply extra processing only if we have any excluded-imports rules
            if excluded_imports:
                # 001987.python.analysis.line389.comment Resolve the base module name. Level can be ABSOLUTE_IMPORT_LEVEL (= 0) for absolute imports, or an
                # 001988.python.analysis.line390.comment integer indicating the relative level. We do not use equality comparison just in case we ever happen
                # 001989.python.analysis.line391.comment to get ABSOLUTE_OR_RELATIVE_IMPORT_LEVEL (-1), which is a remnant of python2 days.
                if level > ABSOLUTE_IMPORT_LEVEL:
                    if isinstance(source_module, Package):
                        # 001990.python.analysis.line394.comment Package
                        base_module_name = source_module.identifier
                    else:
                        # 001991.python.analysis.line397.comment Module in a package; base name must be the parent package name!
                        base_module_name = '.'.join(source_module.identifier.split('.')[:-1])

                    # 001992.python.analysis.line400.comment Adjust the base module name based on level
                    if level > 1:
                        base_module_name = '.'.join(base_module_name.split('.')[:-(level - 1)])

                    if target_module_partname:
                        base_module_name += '.' + target_module_partname
                else:
                    base_module_name = target_module_partname

                def _exclude_module(module_name, excluded_imports, referrer_name):
                    """
                    Helper for checking whether given module should be excluded.
                    Returns the name of exclusion rule if module should be excluded, None otherwise.
                    """
                    module_name_parts = module_name.split('.')
                    for excluded_import in excluded_imports:
                        excluded_import_parts = excluded_import.split('.')
                        match = module_name_parts[:len(excluded_import_parts)] == excluded_import_parts
                        if match:
                            # 001993.python.analysis.line419.comment Check if the referrer is (was!) subject to the same rule. Because if it was and was
                            # 001994.python.analysis.line420.comment analyzed anyway, some other import chain must have overrode the exclusion, and we should
                            # 001995.python.analysis.line421.comment waive it here. A package hook might exclude a part (a subpackage) of the said package to
                            # 001996.python.analysis.line422.comment prevent its collection when there are no external references; but when they are (for
                            # 001997.python.analysis.line423.comment example, user explicitly imports the said subpackage in their program), we must let the
                            # 001998.python.analysis.line424.comment subpackage import its submodules.
                            referrer_name_parts = referrer_name.split('.')
                            referrer_match = referrer_name_parts[:len(excluded_import_parts)] == excluded_import_parts
                            if referrer_match:
                                logger.debug(
                                    "Deactivating suppression rule %r for module %r because it also applies to the "
                                    "referrer (%r)...", excluded_import, module_name, referrer_name
                                )
                                continue

                            return excluded_import
                    return None

                # 001999.python.analysis.line437.comment First, check if base module name is to be excluded.
                # 002000.python.analysis.line438.comment This covers both basic `import a` and `import a.b.c`, as well as `from d import e, f` where base
                # 002001.python.analysis.line439.comment module `d` is excluded.
                excluded_import_rule = _exclude_module(
                    base_module_name,
                    excluded_imports,
                    source_module.identifier,
                )
                if excluded_import_rule:
                    logger.debug(
                        "Suppressing import of %r from module %r due to excluded import %r specified in a hook for %r "
                        "(or its parent package(s)).", base_module_name, source_module.identifier, excluded_import_rule,
                        source_module.identifier
                    )
                    return []

                # 002002.python.analysis.line453.comment If we have target attribute names, check each of them, and remove excluded ones from the
                # 002003.python.analysis.line454.comment `target_attr_names` list.
                if target_attr_names:
                    filtered_target_attr_names = []
                    for target_attr_name in target_attr_names:
                        submodule_name = base_module_name + '.' + target_attr_name
                        excluded_import_rule = _exclude_module(
                            submodule_name,
                            excluded_imports,
                            source_module.identifier,
                        )
                        if excluded_import_rule:
                            logger.debug(
                                "Suppressing import of %r from module %r due to excluded import %r specified in a hook "
                                "for %r (or its parent package(s)).", submodule_name, source_module.identifier,
                                excluded_import_rule, source_module.identifier
                            )
                        else:
                            filtered_target_attr_names.append(target_attr_name)

                    # 002004.python.analysis.line473.comment Swap with filtered target attribute names list; if no elements remain after the filtering, pass
                    # 002005.python.analysis.line474.comment None...
                    target_attr_names = filtered_target_attr_names or None

        ret_modules = super()._safe_import_hook(
            target_module_partname, source_module, target_attr_names, level, edge_attr
        )

        # 002006.python.analysis.line481.comment Ensure that hooks are pre-loaded for returned module(s), in an attempt to ensure that hooks are called in the
        # 002007.python.analysis.line482.comment order of imports. The hooks are cached, so there should be no downsides to pre-loading hooks early (as opposed
        # 002008.python.analysis.line483.comment to loading them in post-graph analysis). When modules are imported from other modules, the hooks for those
        # 002009.python.analysis.line484.comment referring (source) modules and their parent package(s) are loaded by the exclusion mechanism that takes place
        # 002010.python.analysis.line485.comment before the above `super()._safe_import_hook` call. The code below attempts to complement that, but for the
        # 002011.python.analysis.line486.comment referred (target) modules and their parent package(s).
        for ret_module in ret_modules:
            if type(ret_module).__name__ not in VALID_MODULE_TYPES:
                continue
            # 002012.python.analysis.line490.comment (Ab)use the `_find_all_excluded_imports` helper to load all hooks for the given module and its parent
            # 002013.python.analysis.line491.comment package(s).
            self._find_all_excluded_imports(ret_module.identifier)

        return ret_modules

    def _safe_import_module(self, module_basename, module_name, parent_package):
        """
        Create a new graph node for the module with the passed name under the parent package signified by the passed
        graph node.

        This method wraps the superclass method with support for pre-import module hooks. If such a hook exists for
        this module (e.g., a script `PyInstaller.hooks.hook-{module_name}` containing a function
        `pre_safe_import_module()`), that hook will be run _before_ the superclass method is called.

        Pre-Safe-Import-Hooks are performed just *prior* to importing the module. When running the hook, the modules
        parent package has already been imported and ti's `__path__` is set up. But the module is just about to be
        imported.

        See the superclass method for description of parameters and return value.
        """
        # 002014.python.analysis.line511.comment If this module has a pre-safe import module hook, run it. Make sure to remove it first, to prevent subsequent
        # 002015.python.analysis.line512.comment calls from running it again.
        hook = self._hooks_pre_safe_import_module.pop(module_name, None)
        if hook is not None:
            # 002016.python.analysis.line515.comment Dynamically import this hook as a fabricated module.
            hook_path, hook_basename = os.path.split(hook.hook_filename)
            logger.info('Processing pre-safe-import-module hook %r from %r', hook_basename, hook_path)
            hook_module_name = 'PyInstaller_hooks_pre_safe_import_module_' + module_name.replace('.', '_')
            hook_module = importlib_load_source(hook_module_name, hook.hook_filename)

            # 002017.python.analysis.line521.comment Object communicating changes made by this hook back to us.
            hook_api = PreSafeImportModuleAPI(
                module_graph=self,
                module_basename=module_basename,
                module_name=module_name,
                parent_package=parent_package,
            )

            # 002018.python.analysis.line529.comment Run this hook, passed this object.
            if not hasattr(hook_module, 'pre_safe_import_module'):
                raise NameError('pre_safe_import_module() function not defined by hook %r.' % hook_module)
            hook_module.pre_safe_import_module(hook_api)

            # 002019.python.analysis.line534.comment Respect method call changes requested by this hook.
            module_basename = hook_api.module_basename
            module_name = hook_api.module_name

        # 002020.python.analysis.line538.comment Call the superclass method.
        return super()._safe_import_module(module_basename, module_name, parent_package)

    def _find_module_path(self, fullname, module_name, search_dirs):
        """
        Get a 3-tuple detailing the physical location of the module with the passed name if that module exists _or_
        raise `ImportError` otherwise.

        This method wraps the superclass method with support for pre-find module path hooks. If such a hook exists
        for this module (e.g., a script `PyInstaller.hooks.hook-{module_name}` containing a function
        `pre_find_module_path()`), that hook will be run _before_ the superclass method is called.

        See superclass method for parameter and return value descriptions.
        """
        # 002021.python.analysis.line552.comment If this module has a pre-find module path hook, run it. Make sure to remove it first, to prevent subsequent
        # 002022.python.analysis.line553.comment calls from running it again.
        hook = self._hooks_pre_find_module_path.pop(fullname, None)
        if hook is not None:
            # 002023.python.analysis.line556.comment Dynamically import this hook as a fabricated module.
            hook_path, hook_basename = os.path.split(hook.hook_filename)
            logger.info('Processing pre-find-module-path hook %r from %r', hook_basename, hook_path)
            hook_fullname = 'PyInstaller_hooks_pre_find_module_path_' + fullname.replace('.', '_')
            hook_module = importlib_load_source(hook_fullname, hook.hook_filename)

            # 002024.python.analysis.line562.comment Object communicating changes made by this hook back to us.
            hook_api = PreFindModulePathAPI(
                module_graph=self,
                module_name=fullname,
                search_dirs=search_dirs,
            )

            # 002025.python.analysis.line569.comment Run this hook, passed this object.
            if not hasattr(hook_module, 'pre_find_module_path'):
                raise NameError('pre_find_module_path() function not defined by hook %r.' % hook_module)
            hook_module.pre_find_module_path(hook_api)

            # 002026.python.analysis.line574.comment Respect search-directory changes requested by this hook.
            search_dirs = hook_api.search_dirs

        # 002027.python.analysis.line577.comment Call the superclass method.
        return super()._find_module_path(fullname, module_name, search_dirs)

    def get_code_objects(self):
        """
        Get code objects from ModuleGraph for pure Python modules. This allows to avoid writing .pyc/pyo files to hdd
        at later stage.

        :return: Dict with module name and code object.
        """
        code_dict = {}
        mod_types = PURE_PYTHON_MODULE_TYPES
        for node in self.iter_graph(start=self._top_script_node):
            # 002028.python.analysis.line590.comment TODO This is terrible. To allow subclassing, types should never be directly compared. Use isinstance()
            # 002029.python.analysis.line591.comment instead, which is safer, simpler, and accepts sets. Most other calls to type() in the codebase should also
            # 002030.python.analysis.line592.comment be refactored to call isinstance() instead.

            # 002031.python.analysis.line594.comment get node type e.g. Script
            mg_type = type(node).__name__
            if mg_type in mod_types:
                if node.code:
                    code_dict[node.identifier] = node.code
        return code_dict

    def _make_toc(self, typecode=None):
        """
        Return the name, path and type of selected nodes as a TOC. The selection is determined by the given list
        of PyInstaller TOC typecodes. If that list is empty we return the complete flattened graph as a TOC with the
        ModuleGraph note types in place of typecodes -- meant for debugging only. Normally we return ModuleGraph
        nodes whose types map to the requested PyInstaller typecode(s) as indicated in the MODULE_TYPES_TO_TOC_DICT.

        We use the ModuleGraph (really, ObjectGraph) flatten() method to scan all the nodes. This is patterned after
        ModuleGraph.report().
        """
        toc = list()
        for node in self.iter_graph(start=self._top_script_node):
            entry = self._node_to_toc(node, typecode)
            # 002032.python.analysis.line614.comment Append the entry. We do not check for duplicates here; the TOC normalization is left to caller.
            # 002033.python.analysis.line615.comment However, as entries are obtained from modulegraph, there should not be any duplicates at this stage.
            if entry is not None:
                toc.append(entry)
        return toc

    def make_pure_toc(self):
        """
        Return all pure Python modules formatted as TOC.
        """
        # 002034.python.analysis.line624.comment PyInstaller should handle special module types without code object.
        return self._make_toc(PURE_PYTHON_MODULE_TYPES)

    def make_binaries_toc(self):
        """
        Return all binary Python modules formatted as TOC.
        """
        return self._make_toc(BINARY_MODULE_TYPES)

    def make_missing_toc(self):
        """
        Return all MISSING Python modules formatted as TOC.
        """
        return self._make_toc(BAD_MODULE_TYPES)

    @staticmethod
    def _node_to_toc(node, typecode=None):
        # 002035.python.analysis.line641.comment TODO This is terrible. Everything in Python has a type. It is nonsensical to even speak of "nodes [that] are
        # 002036.python.analysis.line642.comment not typed." How would that even occur? After all, even "None" has a type! (It is "NoneType", for the curious.)
        # 002037.python.analysis.line643.comment Remove this, please.

        # 002038.python.analysis.line645.comment Get node type, e.g., Script
        mg_type = type(node).__name__
        assert mg_type is not None

        if typecode and mg_type not in typecode:
            # 002039.python.analysis.line650.comment Type is not a to be selected one, skip this one
            return None
        # 002040.python.analysis.line652.comment Extract the identifier and a path if any.
        if mg_type == 'Script':
            # 002041.python.analysis.line654.comment for Script nodes only, identifier is a whole path
            (name, ext) = os.path.splitext(node.filename)
            name = os.path.basename(name)
        elif mg_type == 'ExtensionPackage':
            # 002042.python.analysis.line658.comment Package with __init__ module being an extension module. This needs to end up as e.g. 'mypkg/__init__.so'.
            # 002043.python.analysis.line659.comment Convert the packages name ('mypkg') into the module name ('mypkg.__init__') *here* to keep special cases
            # 002044.python.analysis.line660.comment away elsewhere (where the module name is converted to a filename).
            name = node.identifier + ".__init__"
        else:
            name = node.identifier
        path = node.filename if node.filename is not None else ''
        # 002045.python.analysis.line665.comment Ensure name is really 'str'. Module graph might return object type 'modulegraph.Alias' which inherits fromm
        # 002046.python.analysis.line666.comment 'str'. But 'marshal.dumps()' function is able to marshal only 'str'. Otherwise on Windows PyInstaller might
        # 002047.python.analysis.line667.comment fail with message like:
        # 002048.python.analysis.line668.comment ValueError: unmarshallable object
        name = str(name)
        # 002049.python.analysis.line670.comment Translate to the corresponding TOC typecode.
        toc_type = MODULE_TYPES_TO_TOC_DICT[mg_type]
        return name, path, toc_type

    def nodes_to_toc(self, nodes):
        """
        Given a list of nodes, create a TOC representing those nodes. This is mainly used to initialize a TOC of
        scripts with the ones that are runtime hooks. The process is almost the same as _make_toc(), but the caller
        guarantees the nodes are valid, so minimal checking.
        """
        return [self._node_to_toc(node) for node in nodes]

    # 002050.python.analysis.line682.comment Return true if the named item is in the graph as a BuiltinModule node. The passed name is a basename.
    def is_a_builtin(self, name):
        node = self.find_node(name)
        if node is None:
            return False
        return type(node).__name__ == 'BuiltinModule'

    def get_importers(self, name):
        """
        List all modules importing the module with the passed name.

        Returns a list of (identifier, DependencyIinfo)-tuples. If the names module has not yet been imported, this
        method returns an empty list.

        Parameters
        ----------
        name : str
            Fully-qualified name of the module to be examined.

        Returns
        ----------
        list
            List of (fully-qualified names, DependencyIinfo)-tuples of all modules importing the module with the passed
            fully-qualified name.

        """
        def get_importer_edge_data(importer):
            edge = self.graph.edge_by_node(importer, name)
            # 002051.python.analysis.line710.comment edge might be None in case an AliasModule was added.
            if edge is not None:
                return self.graph.edge_data(edge)

        node = self.find_node(name)
        if node is None:
            return []
        _, importers = self.get_edges(node)
        importers = (importer.identifier for importer in importers if importer is not None)
        return [(importer, get_importer_edge_data(importer)) for importer in importers]

    # 002052.python.analysis.line721.comment TODO: create a class from this function.
    def analyze_runtime_hooks(self, custom_runhooks):
        """
        Analyze custom run-time hooks and run-time hooks implied by found modules.

        :return : list of Graph nodes.
        """
        rthooks_nodes = []
        logger.info('Analyzing run-time hooks ...')
        # 002053.python.analysis.line730.comment Process custom runtime hooks (from --runtime-hook options). The runtime hooks are order dependent. First hooks
        # 002054.python.analysis.line731.comment in the list are executed first. Put their graph nodes at the head of the priority_scripts list Pyinstaller
        # 002055.python.analysis.line732.comment defined rthooks and thus they are executed first.
        if custom_runhooks:
            for hook_file in custom_runhooks:
                logger.info("Including custom run-time hook %r", hook_file)
                hook_file = os.path.abspath(hook_file)
                # 002056.python.analysis.line737.comment Not using "try" here because the path is supposed to exist, if it does not, the raised error will
                # 002057.python.analysis.line738.comment explain.
                rthooks_nodes.append(self.add_script(hook_file))

        # 002058.python.analysis.line741.comment Find runtime hooks that are implied by packages already imported. Get a temporary TOC listing all the scripts
        # 002059.python.analysis.line742.comment and packages graphed so far. Assuming that runtime hooks apply only to modules and packages.
        temp_toc = self._make_toc(VALID_MODULE_TYPES)
        for (mod_name, path, typecode) in temp_toc:
            # 002060.python.analysis.line745.comment Look if there is any run-time hook for given module.
            if mod_name in self._available_rthooks:
                # 002061.python.analysis.line747.comment There could be several run-time hooks for a module.
                for abs_path in self._available_rthooks[mod_name]:
                    hook_path, hook_basename = os.path.split(abs_path)
                    logger.info("Including run-time hook %r from %r", hook_basename, hook_path)
                    rthooks_nodes.append(self.add_script(abs_path))

        return rthooks_nodes

    def add_hiddenimports(self, module_list):
        """
        Add hidden imports that are either supplied as CLI option --hidden-import=MODULENAME or as dependencies from
        some PyInstaller features when enabled (e.g., crypto feature).
        """
        assert self._top_script_node is not None
        # 002062.python.analysis.line761.comment Analyze the script's hidden imports (named on the command line).
        for modnm in module_list:
            node = self.find_node(modnm)
            if node is not None:
                logger.debug('Hidden import %r already found', modnm)
            else:
                logger.info("Analyzing hidden import %r", modnm)
                # 002063.python.analysis.line768.comment ModuleGraph throws ImportError if import not found.
                try:
                    nodes = self.import_hook(modnm)
                    assert len(nodes) == 1
                    node = nodes[0]
                except ImportError:
                    logger.error("Hidden import %r not found", modnm)
                    continue
            # 002064.python.analysis.line776.comment Create references from the top script to the hidden import, even if found otherwise. Do not waste time
            # 002065.python.analysis.line777.comment checking whether it is actually added by this (test-) script.
            self.add_edge(self._top_script_node, node)

    def get_code_using(self, module: str) -> dict:
        """
        Find modules that import a given **module**.
        """
        co_dict = {}
        pure_python_module_types = PURE_PYTHON_MODULE_TYPES | {
            'Script',
        }
        node = self.find_node(module)
        if node:
            referrers = self.incoming(node)
            for r in referrers:
                # 002066.python.analysis.line792.comment Under python 3.7 and earlier, if `module` is added to hidden imports, one of referrers ends up being
                # 002067.python.analysis.line793.comment None, causing #3825. Work around it.
                if r is None:
                    continue
                # 002068.python.analysis.line796.comment Ensure that modulegraph objects have 'code' attribute.
                if type(r).__name__ not in pure_python_module_types:
                    continue
                identifier = r.identifier
                if identifier == module or identifier.startswith(module + '.'):
                    # 002069.python.analysis.line801.comment Skip self references or references from `modules`'s own submodules.
                    continue
                # 002070.python.analysis.line803.comment The code object may be None if referrer ends up shadowed by eponymous directory that ends up treated
                # 002071.python.analysis.line804.comment as a namespace package. See #6873 for an example.
                if r.code is None:
                    continue
                co_dict[r.identifier] = r.code
        return co_dict

    def metadata_required(self) -> set:
        """
        Collect metadata for all packages that appear to need it.
        """

        # 002072.python.analysis.line815.comment List every function that we can think of which is known to require metadata.
        out = set()

        out |= self._metadata_from(
            "pkg_resources",
            ["get_distribution"],  # Requires metadata for one distribution.
            ["require"],  # Requires metadata for all dependencies.
        )

        # 002075.python.analysis.line824.comment importlib.metadata is often `import ... as`  aliased to importlib_metadata for compatibility with < py38.
        # 002076.python.analysis.line825.comment Assume both are valid.
        for importlib_metadata in ["importlib.metadata", "importlib_metadata"]:
            out |= self._metadata_from(
                importlib_metadata,
                ["metadata", "distribution", "version", "files", "requires"],
                [],
            )

        return out

    def _metadata_from(self, package, methods=(), recursive_methods=()) -> set:
        """
        Collect metadata whose requirements are implied by given function names.

        Args:
            package:
                The module name that must be imported in a source file to trigger the search.
            methods:
                Function names from **package** which take a distribution name as an argument and imply that metadata
                is required for that distribution.
            recursive_methods:
                Like **methods** but also implies that a distribution's dependencies' metadata must be collected too.
        Returns:
            Required metadata in hook data ``(source, dest)`` format as returned by
            :func:`PyInstaller.utils.hooks.copy_metadata()`.

        Scan all source code to be included for usage of particular *key* functions which imply that that code will
        require metadata for some distribution (which may not be its own) at runtime. In the case of a match,
        collect the required metadata.
        """
        from PyInstaller.utils.hooks import copy_metadata
        from PyInstaller.compat import importlib_metadata

        # 002077.python.analysis.line858.comment Generate sets of possible function names to search for.
        need_metadata = set()
        need_recursive_metadata = set()
        for method in methods:
            need_metadata.update(bytecode.any_alias(package + "." + method))
        for method in recursive_methods:
            need_recursive_metadata.update(bytecode.any_alias(package + "." + method))

        out = set()

        for name, code in self.get_code_using(package).items():
            for calls in bytecode.recursive_function_calls(code).values():
                for function_name, args in calls:
                    # 002078.python.analysis.line871.comment Only consider function calls taking one argument.
                    if len(args) != 1:
                        continue
                    package = args[0]
                    try:
                        if function_name in need_metadata:
                            out.update(copy_metadata(package))
                        elif function_name in need_recursive_metadata:
                            out.update(copy_metadata(package, recursive=True))

                    except importlib_metadata.PackageNotFoundError:
                        # 002079.python.analysis.line882.comment Currently, we opt to silently skip over missing metadata.
                        continue

        return out

    def get_collected_packages(self) -> list:
        """
        Return the list of collected python packages.
        """
        # 002080.python.analysis.line891.comment `node.identifier` might be an instance of `modulegraph.Alias`, hence explicit conversion to `str`.
        return [
            str(node.identifier) for node in self.iter_graph(start=self._top_script_node)
            if type(node).__name__ == 'Package'
        ]

    def make_hook_binaries_toc(self) -> list:
        """
        Return the TOC list of binaries collected by hooks."
        """
        toc = []
        for node in self.iter_graph(start=self._top_script_node):
            module_name = str(node.identifier)
            for dest_name, src_name in self._additional_files_cache.binaries(module_name):
                toc.append((dest_name, src_name, 'BINARY'))

        return toc

    def make_hook_datas_toc(self) -> list:
        """
        Return the TOC list of data files collected by hooks."
        """
        toc = []
        for node in self.iter_graph(start=self._top_script_node):
            module_name = str(node.identifier)
            for dest_name, src_name in self._additional_files_cache.datas(module_name):
                toc.append((dest_name, src_name, 'DATA'))

        return toc


_cached_module_graph_ = None


def initialize_modgraph(excludes=(), user_hook_dirs=()):
    """
    Create the cached module graph.

    This function might appear weird but is necessary for speeding up test runtime because it allows caching basic
    ModuleGraph object that gets created for 'base_library.zip'.

    Parameters
    ----------
    excludes : list
        List of the fully-qualified names of all modules to be "excluded" and hence _not_ frozen into the executable.
    user_hook_dirs : list
        List of the absolute paths of all directories containing user-defined hooks for the current application or
        `None` if no such directories were specified.

    Returns
    ----------
    PyiModuleGraph
        Module graph with core dependencies.
    """
    # 002081.python.analysis.line945.comment Normalize parameters to ensure tuples and make comparison work.
    user_hook_dirs = user_hook_dirs or ()
    excludes = excludes or ()

    # 002082.python.analysis.line949.comment Ensure that __main__ is always excluded from the modulegraph, to prevent accidentally pulling PyInstaller itself
    # 002083.python.analysis.line950.comment into the modulegraph. This seems to happen on Windows, because modulegraph is able to resolve `__main__` as
    # 002084.python.analysis.line951.comment `.../PyInstaller.exe/__main__.py` and analyze it. The `__main__` has a different meaning during analysis compared
    # 002085.python.analysis.line952.comment to the program run-time, when it refers to the program's entry-point (which would always be part of the
    # 002086.python.analysis.line953.comment modulegraph anyway, by virtue of being the starting point of the analysis).
    if "__main__" not in excludes:
        excludes += ("__main__",)

    # 002087.python.analysis.line957.comment If there is a graph cached with the same excludes, reuse it. See ``PyiModulegraph._reset()`` for what is
    # 002088.python.analysis.line958.comment reset. This cache is used primarily to speed up the test-suite. Fixture `pyi_modgraph` calls this function with
    # 002089.python.analysis.line959.comment empty excludes, creating a graph suitable for the huge majority of tests.
    global _cached_module_graph_
    if _cached_module_graph_ and _cached_module_graph_._excludes == excludes:
        logger.info('Reusing cached module dependency graph...')
        graph = deepcopy(_cached_module_graph_)
        graph._reset(user_hook_dirs)
        return graph

    logger.info('Initializing module dependency graph...')

    # 002090.python.analysis.line969.comment Construct the initial module graph by analyzing all import statements.
    graph = PyiModuleGraph(
        HOMEPATH,
        excludes=excludes,
        # 002091.python.analysis.line973.comment get_implies() are hidden imports known by modulgraph.
        implies=get_implies(),
        user_hook_dirs=user_hook_dirs,
    )

    if not _cached_module_graph_:
        # 002092.python.analysis.line979.comment Only cache the first graph, see above for explanation.
        logger.info('Caching module dependency graph...')
        # 002093.python.analysis.line981.comment cache a deep copy of the graph
        _cached_module_graph_ = deepcopy(graph)
        # 002094.python.analysis.line983.comment Clear data which does not need to be copied from the cached graph since it will be reset by
        # 002095.python.analysis.line984.comment ``PyiModulegraph._reset()`` anyway.
        _cached_module_graph_._hooks = None
        _cached_module_graph_._hooks_pre_safe_import_module = None
        _cached_module_graph_._hooks_pre_find_module_path = None

    return graph


def get_bootstrap_modules():
    """
    Get TOC with the bootstrapping modules and their dependencies.
    :return: TOC with modules
    """
    # 002096.python.analysis.line997.comment Import 'struct' modules to get real paths to module file names.
    mod_struct = __import__('struct')
    # 002097.python.analysis.line999.comment Basic modules necessary for the bootstrap process.
    loader_mods = list()
    loaderpath = os.path.join(HOMEPATH, 'PyInstaller', 'loader')
    # 002098.python.analysis.line1002.comment On some platforms (Windows, Debian/Ubuntu) '_struct' and zlib modules are built-in modules (linked statically)
    # 002099.python.analysis.line1003.comment and thus does not have attribute __file__. 'struct' module is required for reading Python bytecode from
    # 002100.python.analysis.line1004.comment executable. 'zlib' is required to decompress this bytecode.
    for mod_name in ['_struct', 'zlib']:
        mod = __import__(mod_name)  # C extension.
        if hasattr(mod, '__file__'):
            mod_file = os.path.abspath(mod.__file__)
            # 002102.python.analysis.line1009.comment Resolve full destination name for extension, diverting it into python3.x/lib-dynload directory if
            # 002103.python.analysis.line1010.comment necessary (to match behavior for extension collection introduced in #5604).
            mod_dest = destination_name_for_extension(mod_name, mod_file, 'EXTENSION')
            loader_mods.append((mod_dest, mod_file, 'EXTENSION'))
    loader_mods.append(('struct', os.path.abspath(mod_struct.__file__), 'PYMODULE'))
    # 002104.python.analysis.line1014.comment Loader/bootstrap modules.
    # 002105.python.analysis.line1015.comment NOTE: These modules should be kept simple without any complicated dependencies.
    loader_mods += [
        ('pyimod01_archive', os.path.join(loaderpath, 'pyimod01_archive.py'), 'PYMODULE'),
        ('pyimod02_importers', os.path.join(loaderpath, 'pyimod02_importers.py'), 'PYMODULE'),
        ('pyimod03_ctypes', os.path.join(loaderpath, 'pyimod03_ctypes.py'), 'PYMODULE'),
    ]
    if is_win:
        loader_mods.append(('pyimod04_pywin32', os.path.join(loaderpath, 'pyimod04_pywin32.py'), 'PYMODULE'))
    # 002106.python.analysis.line1023.comment The bootstrap script
    loader_mods.append(('pyiboot01_bootstrap', os.path.join(loaderpath, 'pyiboot01_bootstrap.py'), 'PYSOURCE'))
    return loader_mods
