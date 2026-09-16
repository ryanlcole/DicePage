# 002575.python.imphook.line1.comment -----------------------------------------------------------------------------
# 002576.python.imphook.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 002577.python.imphook.line3.comment
# 002578.python.imphook.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 002579.python.imphook.line5.comment or later) with exception for distributing the bootloader.
# 002580.python.imphook.line6.comment
# 002581.python.imphook.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002582.python.imphook.line8.comment
# 002583.python.imphook.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 002584.python.imphook.line10.comment -----------------------------------------------------------------------------
"""
Code related to processing of import hooks.
"""

import glob
import os.path
import sys
import weakref
import re

from PyInstaller import log as logging
from PyInstaller.building.utils import format_binaries_and_datas
from PyInstaller.compat import importlib_load_source
from PyInstaller.depend.imphookapi import PostGraphAPI
from PyInstaller.exceptions import ImportErrorWhenRunningHook

logger = logging.getLogger(__name__)


class ModuleHookCache(dict):
    """
    Cache of lazily loadable hook script objects.

    This cache is implemented as a `dict` subclass mapping from the fully-qualified names of all modules with at
    least one hook script to lists of `ModuleHook` instances encapsulating these scripts. As a `dict` subclass,
    all cached module names and hook scripts are accessible via standard dictionary operations.

    Attributes
    ----------
    module_graph : ModuleGraph
        Current module graph.
    _hook_module_name_prefix : str
        String prefixing the names of all in-memory modules lazily loaded from cached hook scripts. See also the
        `hook_module_name_prefix` parameter passed to the `ModuleHook.__init__()` method.
    """

    _cache_id_next = 0
    """
    0-based identifier unique to the next `ModuleHookCache` to be instantiated.

    This identifier is incremented on each instantiation of a new `ModuleHookCache` to isolate in-memory modules of
    lazily loaded hook scripts in that cache to the same cache-specific namespace, preventing edge-case collisions
    with existing in-memory modules in other caches.

    """
    def __init__(self, module_graph, hook_dirs):
        """
        Cache all hook scripts in the passed directories.

        **Order of caching is significant** with respect to hooks for the same module, as the values of this
        dictionary are lists. Hooks for the same module will be run in the order in which they are cached. Previously
        cached hooks are always preserved rather than overridden.

        By default, official hooks are cached _before_ user-defined hooks. For modules with both official and
        user-defined hooks, this implies that the former take priority over and hence will be loaded _before_ the
        latter.

        Parameters
        ----------
        module_graph : ModuleGraph
            Current module graph.
        hook_dirs : list
            List of the absolute or relative paths of all directories containing **hook scripts** (i.e.,
            Python scripts with filenames matching `hook-{module_name}.py`, where `{module_name}` is the module
            hooked by that script) to be cached.
        """
        super().__init__()

        # 002585.python.imphook.line79.comment To avoid circular references and hence increased memory consumption, a weak rather than strong reference is
        # 002586.python.imphook.line80.comment stored to the passed graph. Since this graph is guaranteed to live longer than this cache,
        # 002587.python.imphook.line81.comment this is guaranteed to be safe.
        self.module_graph = weakref.proxy(module_graph)

        # 002588.python.imphook.line84.comment String unique to this cache prefixing the names of all in-memory modules lazily loaded from cached hook
        # 002589.python.imphook.line85.comment scripts, privatized for safety.
        self._hook_module_name_prefix = '__PyInstaller_hooks_{}_'.format(ModuleHookCache._cache_id_next)
        ModuleHookCache._cache_id_next += 1

        # 002590.python.imphook.line89.comment Cache all hook scripts in the passed directories.
        self._cache_hook_dirs(hook_dirs)

    def _cache_hook_dirs(self, hook_dirs):
        """
        Cache all hook scripts in the passed directories.

        Parameters
        ----------
        hook_dirs : list
            List of the absolute or relative paths of all directories containing hook scripts to be cached.
        """

        for hook_dir, default_priority in hook_dirs:
            # 002591.python.imphook.line103.comment Canonicalize this directory's path and validate its existence.
            hook_dir = os.path.abspath(hook_dir)
            if not os.path.isdir(hook_dir):
                raise FileNotFoundError('Hook directory "{}" not found.'.format(hook_dir))

            # 002592.python.imphook.line108.comment For each hook script in this directory...
            hook_filenames = glob.glob(os.path.join(hook_dir, 'hook-*.py'))
            for hook_filename in hook_filenames:
                # 002593.python.imphook.line111.comment Fully-qualified name of this hook's corresponding module, constructed by removing the "hook-" prefix
                # 002594.python.imphook.line112.comment and ".py" suffix.
                module_name = os.path.basename(hook_filename)[5:-3]

                # 002595.python.imphook.line115.comment Lazily loadable hook object.
                module_hook = ModuleHook(
                    module_graph=self.module_graph,
                    module_name=module_name,
                    hook_filename=hook_filename,
                    hook_module_name_prefix=self._hook_module_name_prefix,
                    default_priority=default_priority,
                )

                # 002596.python.imphook.line124.comment Add this hook to this module's list of hooks.
                module_hooks = self.setdefault(module_name, [])
                module_hooks.append(module_hook)

        # 002597.python.imphook.line128.comment Post-processing: we allow only one instance of hook per module. Currently, the priority order is defined
        # 002598.python.imphook.line129.comment implicitly, via order of hook directories, so the first hook in the list has the highest priority.
        for module_name in self.keys():
            hooks = self[module_name]
            if len(hooks) == 1:
                self[module_name] = hooks[0]
            else:
                # 002599.python.imphook.line135.comment Order by priority value, in descending order.
                sorted_hooks = sorted(hooks, key=lambda hook: hook.priority, reverse=True)
                self[module_name] = sorted_hooks[0]

    def remove_modules(self, *module_names):
        """
        Remove the passed modules and all hook scripts cached for these modules from this cache.

        Parameters
        ----------
        module_names : list
            List of all fully-qualified module names to be removed.
        """

        for module_name in module_names:
            # 002600.python.imphook.line150.comment Unload this module's hook script modules from memory. Since these are top-level pure-Python modules cached
            # 002601.python.imphook.line151.comment only in the "sys.modules" dictionary, popping these modules from this dictionary suffices to garbage
            # 002602.python.imphook.line152.comment collect them.
            module_hook = self.pop(module_name, None)  # Remove our reference, if available.
            if module_hook is not None:
                sys.modules.pop(module_hook.hook_module_name, None)


def _module_collection_mode_sanitizer(value):
    if isinstance(value, dict):
        # 002604.python.imphook.line160.comment Hook set a dictionary; use it as-is
        return value
    elif isinstance(value, str):
        # 002605.python.imphook.line163.comment Hook set a mode string; convert to a dictionary and assign the string to `None` (= the hooked module).
        return {None: value}

    raise ValueError(f"Invalid module collection mode setting value: {value!r}")


def _bindepend_symlink_suppression_sanitizer(value):
    if isinstance(value, (list, set)):
        # 002606.python.imphook.line171.comment Hook set a list or a set; use it as-is
        return set(value)
    elif isinstance(value, str):
        # 002607.python.imphook.line174.comment Hook set a string; create a set with single element.
        return set([value])

    raise ValueError(f"Invalid value for bindepend_symlink_suppression: {value!r}")


# 002608.python.imphook.line180.comment Dictionary mapping the names of magic attributes required by the "ModuleHook" class to 2-tuples "(default_type,
# 002609.python.imphook.line181.comment sanitizer_func)", where:
# 002610.python.imphook.line182.comment
# 002611.python.imphook.line183.comment * "default_type" is the type to which that attribute will be initialized when that hook is lazily loaded.
# 002612.python.imphook.line184.comment * "sanitizer_func" is the callable sanitizing the original value of that attribute defined by that hook into a
# 002613.python.imphook.line185.comment safer value consumable by "ModuleHook" callers if any or "None" if the original value requires no sanitization.
# 002614.python.imphook.line186.comment
# 002615.python.imphook.line187.comment To avoid subtleties in the ModuleHook.__getattr__() method, this dictionary is declared as a module rather than a
# 002616.python.imphook.line188.comment class attribute. If declared as a class attribute and then undefined (...for whatever reason), attempting to access
# 002617.python.imphook.line189.comment this attribute from that method would produce infinite recursion.
_MAGIC_MODULE_HOOK_ATTRS = {
    # 002618.python.imphook.line191.comment Collections in which order is insignificant. This includes:
    # 002619.python.imphook.line192.comment
    # 002620.python.imphook.line193.comment * "datas", sanitized from hook-style 2-tuple lists defined by hooks into TOC-style 2-tuple sets consumable by
    # 002621.python.imphook.line194.comment "ModuleHook" callers.
    # 002622.python.imphook.line195.comment * "binaries", sanitized in the same way.
    'datas': (set, format_binaries_and_datas),
    'binaries': (set, format_binaries_and_datas),
    'excludedimports': (set, None),

    # 002623.python.imphook.line200.comment Collections in which order is significant. This includes:
    # 002624.python.imphook.line201.comment
    # 002625.python.imphook.line202.comment * "hiddenimports", as order of importation is significant. On module importation, hook scripts are loaded and hook
    # 002626.python.imphook.line203.comment functions declared by these scripts are called. As these scripts and functions can have side effects dependent
    # 002627.python.imphook.line204.comment on module importation order, module importation itself can have side effects dependent on this order!
    'hiddenimports': (list, None),

    # 002628.python.imphook.line207.comment Flags
    'warn_on_missing_hiddenimports': (lambda: True, bool),

    # 002629.python.imphook.line210.comment Package/module collection mode dictionary.
    'module_collection_mode': (dict, _module_collection_mode_sanitizer),

    # 002630.python.imphook.line213.comment Path patterns for suppression of symbolic links created by binary dependency analysis.
    'bindepend_symlink_suppression': (set, _bindepend_symlink_suppression_sanitizer),
}


class ModuleHook:
    """
    Cached object encapsulating a lazy loadable hook script.

    This object exposes public attributes (e.g., `datas`) of the underlying hook script as attributes of the same
    name of this object. On the first access of any such attribute, this hook script is lazily loaded into an
    in-memory private module reused on subsequent accesses. These dynamic attributes are referred to as "magic." All
    other static attributes of this object (e.g., `hook_module_name`) are referred to as "non-magic."

    Attributes (Magic)
    ----------
    datas : set
        Set of `TOC`-style 2-tuples `(target_file, source_file)` for all external non-executable files required by
        the module being hooked, converted from the `datas` list of hook-style 2-tuples `(source_dir_or_glob,
        target_dir)` defined by this hook script.
    binaries : set
        Set of `TOC`-style 2-tuples `(target_file, source_file)` for all external executable files required by the
        module being hooked, converted from the `binaries` list of hook-style 2-tuples `(source_dir_or_glob,
        target_dir)` defined by this hook script.
    excludedimports : set
        Set of the fully-qualified names of all modules imported by the module being hooked to be ignored rather than
        imported from that module, converted from the `excludedimports` list defined by this hook script. These
        modules will only be "locally" rather than "globally" ignored. These modules will remain importable from all
        modules other than the module being hooked.
    hiddenimports : set
        Set of the fully-qualified names of all modules imported by the module being hooked that are _not_
        automatically detectable by PyInstaller (usually due to being dynamically imported in that module),
        converted from the `hiddenimports` list defined by this hook script.
    warn_on_missing_hiddenimports : bool
        Boolean flag indicating whether missing hidden imports from the hook should generate warnings or not. This
        behavior is enabled by default, but individual hooks can opt out of it.
    module_collection_mode : dict
        A dictionary of package/module names and their corresponding collection mode strings ('pyz', 'pyc', 'py',
        'pyz+py', 'py+pyz').
    bindepend_symlink_suppression : set
        A set of paths or path patterns corresponding to shared libraries for which binary dependency analysis should
        not create symbolic links into top-level application directory.

    Attributes (Non-magic)
    ----------
    module_graph : ModuleGraph
        Current module graph.
    module_name : str
        Name of the module hooked by this hook script.
    hook_filename : str
        Absolute or relative path of this hook script.
    hook_module_name : str
        Name of the in-memory module of this hook script's interpreted contents.
    _hook_module : module
        In-memory module of this hook script's interpreted contents, lazily loaded on the first call to the
        `_load_hook_module()` method _or_ `None` if this method has yet to be accessed.
    _default_priority : int
        Default (location-based) priority for this hook.
    priority : int
        Actual priority for this hook. Might be different from `_default_priority` if hook file specifies the hook
        priority override.
    """

    # 002631.python.imphook.line276.comment -- Magic --

    def __init__(self, module_graph, module_name, hook_filename, hook_module_name_prefix, default_priority):
        """
        Initialize this metadata.

        Parameters
        ----------
        module_graph : ModuleGraph
            Current module graph.
        module_name : str
            Name of the module hooked by this hook script.
        hook_filename : str
            Absolute or relative path of this hook script.
        hook_module_name_prefix : str
            String prefixing the name of the in-memory module for this hook script. To avoid namespace clashes with
            similar modules created by other `ModuleHook` objects in other `ModuleHookCache` containers, this string
            _must_ be unique to the `ModuleHookCache` container containing this `ModuleHook` object. If this string
            is non-unique, an existing in-memory module will be erroneously reused when lazily loading this hook
            script, thus erroneously resanitizing previously sanitized hook script attributes (e.g., `datas`) with
            the `format_binaries_and_datas()` helper.
        default_priority : int
            Default, location-based priority for this hook. Used to select active hook when multiple hooks are defined
            for the same module.
        """
        # 002632.python.imphook.line301.comment Note that the passed module graph is already a weak reference, avoiding circular reference issues. See
        # 002633.python.imphook.line302.comment ModuleHookCache.__init__(). TODO: Add a failure message
        assert isinstance(module_graph, weakref.ProxyTypes)
        self.module_graph = module_graph
        self.module_name = module_name
        self.hook_filename = hook_filename

        # 002634.python.imphook.line308.comment Default priority; used as fall-back for dynamic `hook_priority` attribute.
        self._default_priority = default_priority

        # 002635.python.imphook.line311.comment Name of the in-memory module fabricated to refer to this hook script.
        self.hook_module_name = hook_module_name_prefix + self.module_name.replace('.', '_')

        # 002636.python.imphook.line314.comment Attributes subsequently defined by the _load_hook_module() method.
        self._loaded = False
        self._has_hook_function = False
        self._hook_module = None

    def __getattr__(self, attr_name):
        """
        Get the magic attribute with the passed name (e.g., `datas`) from this lazily loaded hook script if any _or_
        raise `AttributeError` otherwise.

        This special method is called only for attributes _not_ already defined by this object. This includes
        undefined attributes and the first attempt to access magic attributes.

        This special method is _not_ called for subsequent attempts to access magic attributes. The first attempt to
        access magic attributes defines corresponding instance variables accessible via the `self.__dict__` instance
        dictionary (e.g., as `self.datas`) without calling this method. This approach also allows magic attributes to
        be deleted from this object _without_ defining the `__delattr__()` special method.

        See Also
        ----------
        Class docstring for supported magic attributes.
        """

        if attr_name == 'priority':
            # 002637.python.imphook.line338.comment If attribute is part of hook metadata, read metadata from hook script and return the attribute value.
            self._load_hook_metadata()
            return getattr(self, attr_name)
        if attr_name in _MAGIC_MODULE_HOOK_ATTRS and not self._loaded:
            # 002638.python.imphook.line342.comment If attribute is hook's magic attribute, load and run the hook script, and return the attribute value.
            self._load_hook_module()
            return getattr(self, attr_name)
        else:
            # 002639.python.imphook.line346.comment This is an undefined attribute. Raise an exception.
            raise AttributeError(attr_name)

    def __setattr__(self, attr_name, attr_value):
        """
        Set the attribute with the passed name to the passed value.

        If this is a magic attribute, this hook script will be lazily loaded before setting this attribute. Unlike
        `__getattr__()`, this special method is called to set _any_ attribute -- including magic, non-magic,
        and undefined attributes.

        See Also
        ----------
        Class docstring for supported magic attributes.
        """

        # 002640.python.imphook.line362.comment If this is a magic attribute, initialize this attribute by lazy loading this hook script before overwriting
        # 002641.python.imphook.line363.comment this attribute.
        if attr_name in _MAGIC_MODULE_HOOK_ATTRS:
            self._load_hook_module()

        # 002642.python.imphook.line367.comment Set this attribute to the passed value. To avoid recursion, the superclass method rather than setattr() is
        # 002643.python.imphook.line368.comment called.
        return super().__setattr__(attr_name, attr_value)

    # 002644.python.imphook.line371.comment -- Loading --

    def _load_hook_metadata(self):
        """
        Load hook metadata from its source file.
        """
        self.priority = self._default_priority

        # 002645.python.imphook.line379.comment Priority override pattern: `# $PyInstaller-Hook-Priority: <value>`
        priority_pattern = re.compile(r"^\s*#\s*\$PyInstaller-Hook-Priority:\s*(?P<value>[\S]+)")

        with open(self.hook_filename, "r", encoding="utf-8") as f:
            for line in f:
                # 002646.python.imphook.line384.comment Attempt to match and parse hook priority directive
                m = priority_pattern.match(line)
                if m is not None:
                    try:
                        self.priority = int(m.group('value'))
                    except Exception:
                        logger.warning(
                            "Failed to parse hook priority value string: %r!", m.group('value'), exc_info=True
                        )
                    # 002647.python.imphook.line393.comment Currently, this is our only line of interest, so we can stop the search here.
                    return

    def _load_hook_module(self, keep_module_ref=False):
        """
        Lazily load this hook script into an in-memory private module.

        This method (and, indeed, this class) preserves all attributes and functions defined by this hook script as
        is, ensuring sane behaviour in hook functions _not_ expecting unplanned external modification. Instead,
        this method copies public attributes defined by this hook script (e.g., `binaries`) into private attributes
        of this object, which the special `__getattr__()` and `__setattr__()` methods safely expose to external
        callers. For public attributes _not_ defined by this hook script, the corresponding private attributes will
        be assigned sane defaults. For some public attributes defined by this hook script, the corresponding private
        attributes will be transformed into objects more readily and safely consumed elsewhere by external callers.

        See Also
        ----------
        Class docstring for supported attributes.
        """

        # 002648.python.imphook.line413.comment If this hook script module has already been loaded, noop.
        if self._loaded and (self._hook_module is not None or not keep_module_ref):
            return

        # 002649.python.imphook.line417.comment Load and execute the hook script. Even if mechanisms from the import machinery are used, this does not import
        # 002650.python.imphook.line418.comment the hook as the module.
        hook_path, hook_basename = os.path.split(self.hook_filename)
        logger.info('Processing standard module hook %r from %r', hook_basename, hook_path)
        try:
            self._hook_module = importlib_load_source(self.hook_module_name, self.hook_filename)
        except ImportError:
            logger.debug("Hook failed with:", exc_info=True)
            raise ImportErrorWhenRunningHook(self.hook_module_name, self.hook_filename)

        # 002651.python.imphook.line427.comment Mark as loaded
        self._loaded = True

        # 002652.python.imphook.line430.comment Check if module has hook() function.
        self._has_hook_function = hasattr(self._hook_module, 'hook')

        # 002653.python.imphook.line433.comment Copy hook script attributes into magic attributes exposed as instance variables of the current "ModuleHook"
        # 002654.python.imphook.line434.comment instance.
        for attr_name, (default_type, sanitizer_func) in _MAGIC_MODULE_HOOK_ATTRS.items():
            # 002655.python.imphook.line436.comment Unsanitized value of this attribute.
            attr_value = getattr(self._hook_module, attr_name, None)

            # 002656.python.imphook.line439.comment If this attribute is undefined, expose a sane default instead.
            if attr_value is None:
                attr_value = default_type()
            # 002657.python.imphook.line442.comment Else if this attribute requires sanitization, do so.
            elif sanitizer_func is not None:
                attr_value = sanitizer_func(attr_value)
            # 002658.python.imphook.line445.comment Else, expose the unsanitized value of this attribute.

            # 002659.python.imphook.line447.comment Expose this attribute as an instance variable of the same name.
            setattr(self, attr_name, attr_value)

        # 002660.python.imphook.line450.comment If module_collection_mode has an entry with None key, reassign it to the hooked module's name.
        setattr(
            self, 'module_collection_mode', {
                key if key is not None else self.module_name: value
                for key, value in getattr(self, 'module_collection_mode').items()
            }
        )

        # 002661.python.imphook.line458.comment Release the module if we do not need the reference. This is the case when hook is loaded during the analysis
        # 002662.python.imphook.line459.comment rather as part of the post-graph operations.
        if not keep_module_ref:
            self._hook_module = None

    # 002663.python.imphook.line463.comment -- Hooks --

    def post_graph(self, analysis):
        """
        Call the **post-graph hook** (i.e., `hook()` function) defined by this hook script, if any.

        Parameters
        ----------
        analysis: build_main.Analysis
            Analysis that calls the hook

        This method is intended to be called _after_ the module graph for this application is constructed.
        """

        # 002664.python.imphook.line477.comment Lazily load this hook script into an in-memory module.
        # 002665.python.imphook.line478.comment The script might have been loaded before during modulegraph analysis; in that case, it needs to be reloaded
        # 002666.python.imphook.line479.comment only if it provides a hook() function.
        if not self._loaded or self._has_hook_function:
            # 002667.python.imphook.line481.comment Keep module reference when loading the hook, so we can call its hook function!
            self._load_hook_module(keep_module_ref=True)

            # 002668.python.imphook.line484.comment Call this hook script's hook() function, which modifies attributes accessed by subsequent methods and
            # 002669.python.imphook.line485.comment hence must be called first.
            self._process_hook_func(analysis)

        # 002670.python.imphook.line488.comment Order is insignificant here.
        self._process_hidden_imports()

    def _process_hook_func(self, analysis):
        """
        Call this hook's `hook()` function if defined.

        Parameters
        ----------
        analysis: build_main.Analysis
            Analysis that calls the hook
        """

        # 002671.python.imphook.line501.comment If this hook script defines no hook() function, noop.
        if not hasattr(self._hook_module, 'hook'):
            return

        # 002672.python.imphook.line505.comment Call this hook() function.
        hook_api = PostGraphAPI(module_name=self.module_name, module_graph=self.module_graph, analysis=analysis)
        try:
            self._hook_module.hook(hook_api)
        except ImportError:
            logger.debug("Hook failed with:", exc_info=True)
            raise ImportErrorWhenRunningHook(self.hook_module_name, self.hook_filename)

        # 002673.python.imphook.line513.comment Update all magic attributes modified by the prior call.
        self.datas.update(set(hook_api._added_datas))
        self.binaries.update(set(hook_api._added_binaries))
        self.hiddenimports.extend(hook_api._added_imports)
        self.module_collection_mode.update(hook_api._module_collection_mode)
        self.bindepend_symlink_suppression.update(hook_api._bindepend_symlink_suppression)

        # 002674.python.imphook.line520.comment FIXME: `hook_api._deleted_imports` should be appended to `self.excludedimports` and used to suppress module
        # 002675.python.imphook.line521.comment import during the modulegraph construction rather than handled here. However, for that to work, the `hook()`
        # 002676.python.imphook.line522.comment function needs to be ran during modulegraph construction instead of in post-processing (and this in turn
        # 002677.python.imphook.line523.comment requires additional code refactoring in order to be able to pass `analysis` to `PostGraphAPI` object at
        # 002678.python.imphook.line524.comment that point). So once the modulegraph rewrite is complete, remove the code block below.
        for deleted_module_name in hook_api._deleted_imports:
            # 002679.python.imphook.line526.comment Remove the graph link between the hooked module and item. This removes the 'item' node from the graph if
            # 002680.python.imphook.line527.comment no other links go to it (no other modules import it)
            self.module_graph.removeReference(hook_api.node, deleted_module_name)

    def _process_hidden_imports(self):
        """
        Add all imports listed in this hook script's `hiddenimports` attribute to the module graph as if directly
        imported by this hooked module.

        These imports are typically _not_ implicitly detectable by PyInstaller and hence must be explicitly defined
        by hook scripts.
        """

        # 002681.python.imphook.line539.comment For each hidden import required by the module being hooked...
        for import_module_name in self.hiddenimports:
            try:
                # 002682.python.imphook.line542.comment Graph node for this module. Do not implicitly create namespace packages for non-existent packages.
                caller = self.module_graph.find_node(self.module_name, create_nspkg=False)

                # 002683.python.imphook.line545.comment Manually import this hidden import from this module.
                self.module_graph.import_hook(import_module_name, caller)
            # 002684.python.imphook.line547.comment If this hidden import is unimportable, print a non-fatal warning. Hidden imports often become
            # 002685.python.imphook.line548.comment desynchronized from upstream packages and hence are only "soft" recommendations.
            except ImportError:
                if self.warn_on_missing_hiddenimports:
                    logger.warning('Hidden import "%s" not found!', import_module_name)


class AdditionalFilesCache:
    """
    Cache for storing what binaries and datas were pushed by what modules when import hooks were processed.
    """
    def __init__(self):
        self._binaries = {}
        self._datas = {}

    def add(self, modname, binaries, datas):

        self._binaries.setdefault(modname, [])
        self._binaries[modname].extend(binaries or [])
        self._datas.setdefault(modname, [])
        self._datas[modname].extend(datas or [])

    def __contains__(self, name):
        return name in self._binaries or name in self._datas

    def binaries(self, modname):
        """
        Return list of binaries for given module name.
        """
        return self._binaries.get(modname, [])

    def datas(self, modname):
        """
        Return list of datas for given module name.
        """
        return self._datas.get(modname, [])
