"""
Find modules used by a script, using bytecode analysis.

Based on the stdlib modulefinder by Thomas Heller and Just van Rossum,
but uses a graph data structure and 2.3 features

XXX: Verify all calls to _import_hook (and variants) to ensure that
imports are done in the right way.
"""
# 008707.python.modulegraph.line10.comment FIXME: To decrease the likelihood of ModuleGraph exceeding the recursion limit
# 008708.python.modulegraph.line11.comment and hence unpredictably raising fatal exceptions, increase the recursion
# 008709.python.modulegraph.line12.comment limit at PyInstaller startup (i.e., in the
# 008710.python.modulegraph.line13.comment PyInstaller.building.build_main.build() function). For details, see:
# 008711.python.modulegraph.line14.comment https://github.com/pyinstaller/pyinstaller/issues/1919#issuecomment-216016176

import ast
import os
import pkgutil
import sys
import re
from collections import deque, namedtuple, defaultdict
import urllib.request
import warnings
import importlib.util
import importlib.machinery

# 008712.python.modulegraph.line27.comment The logic in PyInstaller.compat ensures that these are available and
# 008713.python.modulegraph.line28.comment of correct version.
if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata

# 008714.python.modulegraph.line34.comment The latest version of altgraph at the time of writing (v0.17.4) still
# 008715.python.modulegraph.line35.comment uses pkg_resources to query its own version. With setuptools >= 80.9.0,
# 008716.python.modulegraph.line36.comment this triggers deprecation warnings. For now, suppress them.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        message="pkg_resources is deprecated",
    )
    from altgraph.ObjectGraph import ObjectGraph
    from altgraph import GraphError

from . import util


class BUILTIN_MODULE:
    def is_package(fqname):
        return False


class NAMESPACE_PACKAGE:
    def __init__(self, namespace_dirs):
        self.namespace_dirs = namespace_dirs

    def is_package(self, fqname):
        return True


# 008717.python.modulegraph.line62.comment FIXME: Leverage this rather than magic numbers below.
ABSOLUTE_OR_RELATIVE_IMPORT_LEVEL = -1
"""
Constant instructing the builtin `__import__()` function to attempt both
absolute and relative imports.
"""


# 008718.python.modulegraph.line70.comment FIXME: Leverage this rather than magic numbers below.
ABSOLUTE_IMPORT_LEVEL = 0
"""
Constant instructing the builtin `__import__()` function to attempt only
absolute imports.
"""


# 008719.python.modulegraph.line78.comment FIXME: Leverage this rather than magic numbers below.
DEFAULT_IMPORT_LEVEL = ABSOLUTE_IMPORT_LEVEL
"""
Constant instructing the builtin `__import__()` function to attempt the default
import style specific to the active Python interpreter.

Specifically, under:

* Python 2, this defaults to attempting both absolute and relative imports.
* Python 3, this defaults to attempting only absolute imports.
"""


class InvalidRelativeImportError (ImportError):
    pass


def _path_from_importerror(exc, default):
    # 008720.python.modulegraph.line96.comment This is a hack, but sadly enough the necessary information
    # 008721.python.modulegraph.line97.comment isn't available otherwise.
    m = re.match(r'^No module named (\S+)$', str(exc))
    if m is not None:
        return m.group(1)

    return default


# 008722.python.modulegraph.line105.comment FIXME: What is this? Do we actually need this? This appears to provide
# 008723.python.modulegraph.line106.comment significantly more fine-grained metadata than PyInstaller will ever require.
# 008724.python.modulegraph.line107.comment It consumes a great deal of space (slots or no slots), since we store an
# 008725.python.modulegraph.line108.comment instance of this class for each edge of the graph.
class DependencyInfo (namedtuple("DependencyInfo",
                      ["conditional", "function", "tryexcept", "fromlist"])):
    __slots__ = ()

    def _merged(self, other):
        if (not self.conditional and not self.function and not self.tryexcept) \
           or (not other.conditional and not other.function and not other.tryexcept):
            return DependencyInfo(
                conditional=False,
                function=False,
                tryexcept=False,
                fromlist=self.fromlist and other.fromlist)

        else:
            return DependencyInfo(
                    conditional=self.conditional or other.conditional,
                    function=self.function or other.function,
                    tryexcept=self.tryexcept or other.tryexcept,
                    fromlist=self.fromlist and other.fromlist)


# 008726.python.modulegraph.line130.comment FIXME: Shift the following Node class hierarchy into a new
# 008727.python.modulegraph.line131.comment "PyInstaller.lib.modulegraph.node" module. This module is much too long.
# 008728.python.modulegraph.line132.comment FIXME: Refactor "_deferred_imports" from a tuple into a proper lightweight
# 008729.python.modulegraph.line133.comment class leveraging "__slots__". If not for backward compatibility, we'd just
# 008730.python.modulegraph.line134.comment leverage a named tuple -- but this should do just as well.
# 008731.python.modulegraph.line135.comment FIXME: Move the "packagepath" attribute into the "Package" class. Only
# 008732.python.modulegraph.line136.comment packages define the "__path__" special attribute. The codebase currently
# 008733.python.modulegraph.line137.comment erroneously tests whether "module.packagepath is not None" to determine
# 008734.python.modulegraph.line138.comment whether a node is a package or not. However, "isinstance(module, Package)" is
# 008735.python.modulegraph.line139.comment a significantly more reliable test. Refactor the former into the latter.
class Node:
    """
    Abstract base class (ABC) of all objects added to a `ModuleGraph`.

    Attributes
    ----------
    code : codeobject
        Code object of the pure-Python module corresponding to this graph node
        if any _or_ `None` otherwise.
    graphident : str
        Synonym of `identifier` required by the `ObjectGraph` superclass of the
        `ModuleGraph` class. For readability, the `identifier` attribute should
        typically be used instead.
    filename : str
        Absolute path of this graph node's corresponding module, package, or C
        extension if any _or_ `None` otherwise.
    identifier : str
        Fully-qualified name of this graph node's corresponding module,
        package, or C extension.
    packagepath : str
        List of the absolute paths of all directories comprising this graph
        node's corresponding package. If this is a:
        * Non-namespace package, this list contains exactly one path.
        * Namespace package, this list contains one or more paths.
    _deferred_imports : list
        List of all target modules imported by the source module corresponding
        to this graph node whole importations have been deferred for subsequent
        processing in between calls to the `_ModuleGraph._scan_code()` and
        `_ModuleGraph._process_imports()` methods for this source module _or_
        `None` otherwise. Each element of this list is a 3-tuple
        `(have_star, _safe_import_hook_args, _safe_import_hook_kwargs)`
        collecting the importation of a target module from this source module
        for subsequent processing, where:
        * `have_star` is a boolean `True` only if this is a `from`-style star
          import (e.g., resembling `from {target_module_name} import *`).
        * `_safe_import_hook_args` is a (typically non-empty) sequence of all
          positional arguments to be passed to the `_safe_import_hook()` method
          to add this importation to the graph.
        * `_safe_import_hook_kwargs` is a (typically empty) dictionary of all
          keyword arguments to be passed to the `_safe_import_hook()` method
          to add this importation to the graph.
        Unlike functional languages, Python imposes a maximum depth on the
        interpreter stack (and hence recursion). On breaching this depth,
        Python raises a fatal `RuntimeError` exception. Since `ModuleGraph`
        parses imports recursively rather than iteratively, this depth _was_
        commonly breached before the introduction of this list. Python
        environments installing a large number of modules (e.g., Anaconda) were
        particularly susceptible. Why? Because `ModuleGraph` concurrently
        descended through both the abstract syntax trees (ASTs) of all source
        modules being parsed _and_ the graph of all target modules imported by
        these source modules being built. The stack thus consisted of
        alternating layers of AST and graph traversal. To unwind such
        alternation and effectively halve the stack depth, `ModuleGraph` now
        descends through the abstract syntax tree (AST) of each source module
        being parsed and adds all importations originating within this module
        to this list _before_ descending into the graph of these importations.
        See pyinstaller/pyinstaller/#1289 for further details.
    _global_attr_names : set
        Set of the unqualified names of all global attributes (e.g., classes,
        variables) defined in the pure-Python module corresponding to this
        graph node if any _or_ the empty set otherwise. This includes the names
        of all attributes imported via `from`-style star imports from other
        existing modules (e.g., `from {target_module_name} import *`). This
        set is principally used to differentiate the non-ignorable importation
        of non-existent submodules in a package from the ignorable importation
        of existing global attributes defined in that package's pure-Python
        `__init__` submodule in `from`-style imports (e.g., `bar` in
        `from foo import bar`, which may be either a submodule or attribute of
        `foo`), as such imports ambiguously allow both. This set is _not_ used
        to differentiate submodules from attributes in `import`-style imports
        (e.g., `bar` in `import foo.bar`, which _must_ be a submodule of
        `foo`), as such imports unambiguously allow only submodules.
    _starimported_ignored_module_names : set
        Set of the fully-qualified names of all existing unparsable modules
        that the existing parsable module corresponding to this graph node
        attempted to perform one or more "star imports" from. If this module
        either does _not_ exist or does but is unparsable, this is the empty
        set. Equivalently, this set contains each fully-qualified name
        `{trg_module_name}` for which:
        * This module contains an import statement of the form
          `from {trg_module_name} import *`.
        * The module whose name is `{trg_module_name}` exists but is _not_
          parsable by `ModuleGraph` (e.g., due to _not_ being pure-Python).
        **This set is currently defined but otherwise ignored.**
    _submodule_basename_to_node : dict
        Dictionary mapping from the unqualified name of each submodule
        contained by the parent module corresponding to this graph node to that
        submodule's graph node. If this dictionary is non-empty, this parent
        module is typically but _not_ always a package (e.g., the non-package
        `os` module containing the `os.path` submodule).
    """

    __slots__ = [
        'code',
        'filename',
        'graphident',
        'identifier',
        'packagepath',
        '_deferred_imports',
        '_global_attr_names',
        '_starimported_ignored_module_names',
        '_submodule_basename_to_node',
    ]

    def __init__(self, identifier):
        """
        Initialize this graph node.

        Parameters
        ----------
        identifier : str
            Fully-qualified name of this graph node's corresponding module,
            package, or C extension.
        """

        self.code = None
        self.filename = None
        self.graphident = identifier
        self.identifier = identifier
        self.packagepath = None
        self._deferred_imports = None
        self._global_attr_names = set()
        self._starimported_ignored_module_names = set()
        self._submodule_basename_to_node = dict()


    def is_global_attr(self, attr_name):
        """
        `True` only if the pure-Python module corresponding to this graph node
        defines a global attribute (e.g., class, variable) with the passed
        name.

        If this module is actually a package, this method instead returns
        `True` only if this package's pure-Python `__init__` submodule defines
        such a global attribute. In this case, note that this package may still
        contain an importable submodule of the same name. Callers should
        attempt to import this attribute as a submodule of this package
        _before_ assuming this attribute to be an ignorable global. See
        "Examples" below for further details.

        Parameters
        ----------
        attr_name : str
            Unqualified name of the attribute to be tested.

        Returns
        ----------
        bool
            `True` only if this module defines this global attribute.

        Examples
        ----------
        Consider a hypothetical module `foo` containing submodules `bar` and
        `__init__` where the latter assigns `bar` to be a global variable
        (possibly star-exported via the special `__all__` global variable):

        >>> # In "foo.__init__":
        >>> bar = 3.1415

        Python 2 and 3 both permissively permit this. This method returns
        `True` in this case (i.e., when called on the `foo` package's graph
        node, passed the attribute name `bar`) despite the importability of the
        `foo.bar` submodule.
        """

        return attr_name in self._global_attr_names


    def is_submodule(self, submodule_basename):
        """
        `True` only if the parent module corresponding to this graph node
        contains the submodule with the passed name.

        If `True`, this parent module is typically but _not_ always a package
        (e.g., the non-package `os` module containing the `os.path` submodule).

        Parameters
        ----------
        submodule_basename : str
            Unqualified name of the submodule to be tested.

        Returns
        ----------
        bool
            `True` only if this parent module contains this submodule.
        """

        return submodule_basename in self._submodule_basename_to_node


    def add_global_attr(self, attr_name):
        """
        Record the global attribute (e.g., class, variable) with the passed
        name to be defined by the pure-Python module corresponding to this
        graph node.

        If this module is actually a package, this method instead records this
        attribute to be defined by this package's pure-Python `__init__`
        submodule.

        Parameters
        ----------
        attr_name : str
            Unqualified name of the attribute to be added.
        """

        self._global_attr_names.add(attr_name)


    def add_global_attrs_from_module(self, target_module):
        """
        Record all global attributes (e.g., classes, variables) defined by the
        target module corresponding to the passed graph node to also be defined
        by the source module corresponding to this graph node.

        If the source module is actually a package, this method instead records
        these attributes to be defined by this package's pure-Python `__init__`
        submodule.

        Parameters
        ----------
        target_module : Node
            Graph node of the target module to import attributes from.
        """

        self._global_attr_names.update(target_module._global_attr_names)


    def add_submodule(self, submodule_basename, submodule_node):
        """
        Add the submodule with the passed name and previously imported graph
        node to the parent module corresponding to this graph node.

        This parent module is typically but _not_ always a package (e.g., the
        non-package `os` module containing the `os.path` submodule).

        Parameters
        ----------
        submodule_basename : str
            Unqualified name of the submodule to add to this parent module.
        submodule_node : Node
            Graph node of this submodule.
        """

        self._submodule_basename_to_node[submodule_basename] = submodule_node


    def get_submodule(self, submodule_basename):
        """
        Graph node of the submodule with the passed name in the parent module
        corresponding to this graph node.

        If this parent module does _not_ contain this submodule, an exception
        is raised. Else, this parent module is typically but _not_ always a
        package (e.g., the non-package `os` module containing the `os.path`
        submodule).

        Parameters
        ----------
        module_basename : str
            Unqualified name of the submodule to retrieve.

        Returns
        ----------
        Node
            Graph node of this submodule.
        """

        return self._submodule_basename_to_node[submodule_basename]


    def get_submodule_or_none(self, submodule_basename):
        """
        Graph node of the submodule with the passed unqualified name in the
        parent module corresponding to this graph node if this module contains
        this submodule _or_ `None`.

        This parent module is typically but _not_ always a package (e.g., the
        non-package `os` module containing the `os.path` submodule).

        Parameters
        ----------
        submodule_basename : str
            Unqualified name of the submodule to retrieve.

        Returns
        ----------
        Node
            Graph node of this submodule if this parent module contains this
            submodule _or_ `None`.
        """

        return self._submodule_basename_to_node.get(submodule_basename)


    def remove_global_attr_if_found(self, attr_name):
        """
        Record the global attribute (e.g., class, variable) with the passed
        name if previously recorded as defined by the pure-Python module
        corresponding to this graph node to be subsequently undefined by the
        same module.

        If this module is actually a package, this method instead records this
        attribute to be undefined by this package's pure-Python `__init__`
        submodule.

        This method is intended to be called on globals previously defined by
        this module that are subsequently undefined via the `del` built-in by
        this module, thus "forgetting" or "undoing" these globals.

        For safety, there exists no corresponding `remove_global_attr()`
        method. While defining this method is trivial, doing so would invite
        `KeyError` exceptions on scanning valid Python that lexically deletes a
        global in a scope under this module's top level (e.g., in a function)
        _before_ defining this global at this top level. Since `ModuleGraph`
        cannot and should not (re)implement a full-blown Python interpreter,
        ignoring out-of-order deletions is the only sane policy.

        Parameters
        ----------
        attr_name : str
            Unqualified name of the attribute to be removed.
        """

        if self.is_global_attr(attr_name):
            self._global_attr_names.remove(attr_name)

    def __eq__(self, other):
        try:
            otherIdent = getattr(other, 'graphident')
        except AttributeError:
            return False

        return self.graphident == otherIdent

    def __ne__(self, other):
        try:
            otherIdent = getattr(other, 'graphident')
        except AttributeError:
            return True

        return self.graphident != otherIdent

    def __lt__(self, other):
        try:
            otherIdent = getattr(other, 'graphident')
        except AttributeError:
            return NotImplemented

        return self.graphident < otherIdent

    def __le__(self, other):
        try:
            otherIdent = getattr(other, 'graphident')
        except AttributeError:
            return NotImplemented

        return self.graphident <= otherIdent

    def __gt__(self, other):
        try:
            otherIdent = getattr(other, 'graphident')
        except AttributeError:
            return NotImplemented

        return self.graphident > otherIdent

    def __ge__(self, other):
        try:
            otherIdent = getattr(other, 'graphident')
        except AttributeError:
            return NotImplemented

        return self.graphident >= otherIdent

    def __hash__(self):
        return hash(self.graphident)

    def infoTuple(self):
        return (self.identifier,)

    def __repr__(self):
        return '%s%r' % (type(self).__name__, self.infoTuple())


class Alias(str):
    """
    Placeholder aliasing an existing source module to a non-existent target
    module (i.e., the desired alias).

    For obscure reasons, this class subclasses `str`. Each instance of this
    class is the fully-qualified name of the existing source module being
    aliased. Unlike the related `AliasNode` class, instances of this class are
    _not_ actual nodes and hence _not_ added to the graph; they only facilitate
    communication between the `ModuleGraph.alias_module()` and
    `ModuleGraph.find_node()` methods.
    """


class AliasNode(Node):
    """
    Graph node representing the aliasing of an existing source module under a
    non-existent target module name (i.e., the desired alias).
    """

    def __init__(self, name, node=None):
        """
        Initialize this alias.

        Parameters
        ----------
        name : str
            Fully-qualified name of the non-existent target module to be
            created (as an alias of the existing source module).
        node : Node
            Graph node of the existing source module being aliased. Optional;
            if not provided here, the attributes from referred node should
            be copied later using `copyAttributesFromReferredNode` method.
        """
        super(AliasNode, self).__init__(name)

        # 008736.python.modulegraph.line561.comment Copy attributes from referred node, if provided
        self.copyAttributesFromReferredNode(node)

    def copyAttributesFromReferredNode(self, node):
        """
        Copy a subset of attributes from referred node (source module) into this target alias.
        """
        # 008737.python.modulegraph.line568.comment FIXME: Why only some? Why not *EVERYTHING* except "graphident", which
        # 008738.python.modulegraph.line569.comment must remain equal to "name" for lookup purposes? This is, after all,
        # 008739.python.modulegraph.line570.comment an alias. The idea is for the two nodes to effectively be the same.
        for attr_name in (
            'identifier', 'packagepath',
            '_global_attr_names', '_starimported_ignored_module_names',
            '_submodule_basename_to_node'):
            if hasattr(node, attr_name):
                setattr(self, attr_name, getattr(node, attr_name))

    def infoTuple(self):
        return (self.graphident, self.identifier)


class BadModule(Node):
    pass


class ExcludedModule(BadModule):
    pass


class MissingModule(BadModule):
    pass


class InvalidRelativeImport (BadModule):
    def __init__(self, relative_path, from_name):
        identifier = relative_path
        if relative_path.endswith('.'):
            identifier += from_name
        else:
            identifier += '.' + from_name
        super(InvalidRelativeImport, self).__init__(identifier)
        self.relative_path = relative_path
        self.from_name = from_name

    def infoTuple(self):
        return (self.relative_path, self.from_name)


class Script(Node):
    def __init__(self, filename):
        super(Script, self).__init__(filename)
        self.filename = filename

    def infoTuple(self):
        return (self.filename,)


class BaseModule(Node):
    def __init__(self, name, filename=None, path=None):
        super(BaseModule, self).__init__(name)
        self.filename = filename
        self.packagepath = path

    def infoTuple(self):
        return tuple(filter(None, (self.identifier, self.filename, self.packagepath)))


class BuiltinModule(BaseModule):
    pass


class SourceModule(BaseModule):
    pass


class InvalidSourceModule(SourceModule):
    pass


class CompiledModule(BaseModule):
    pass


class InvalidCompiledModule(BaseModule):
    pass


class Extension(BaseModule):
    pass


class Package(BaseModule):
    """
    Graph node representing a non-namespace package.
    """
    pass


class ExtensionPackage(Extension, Package):
    """
    Graph node representing a package where the __init__ module is an extension
    module.
    """
    pass


class NamespacePackage(Package):
    """
    Graph node representing a namespace package.
    """
    pass


class RuntimeModule(BaseModule):
    """
    Graph node representing a non-package Python module dynamically defined at
    runtime.

    Most modules are statically defined on-disk as standard Python files.
    Some modules, however, are dynamically defined in-memory at runtime
    (e.g., `gi.repository.Gst`, dynamically defined by the statically
    defined `gi.repository.__init__` module).

    This node represents such a runtime module. Since this is _not_ a package,
    all attempts to import submodules from this module in `from`-style import
    statements (e.g., the `queue` submodule in `from six.moves import queue`)
    will be silently ignored.

    To ensure that the parent package of this module if any is also imported
    and added to the graph, this node is typically added to the graph by
    calling the `ModuleGraph.add_module()` method.
    """
    pass


class RuntimePackage(Package):
    """
    Graph node representing a non-namespace Python package dynamically defined
    at runtime.

    Most packages are statically defined on-disk as standard subdirectories
    containing `__init__.py` files. Some packages, however, are dynamically
    defined in-memory at runtime (e.g., `six.moves`, dynamically defined by
    the statically defined `six` module).

    This node represents such a runtime package. All attributes imported from
    this package in `from`-style import statements that are submodules of this
    package (e.g., the `queue` submodule in `from six.moves import queue`) will
    be imported rather than ignored.

    To ensure that the parent package of this package if any is also imported
    and added to the graph, this node is typically added to the graph by
    calling the `ModuleGraph.add_module()` method.
    """
    pass


# 008740.python.modulegraph.line718.comment FIXME: Safely removable. We don't actually use this anywhere. After removing
# 008741.python.modulegraph.line719.comment this class, remove the corresponding entry from "compat".
class FlatPackage(BaseModule):
    def __init__(self, *args, **kwds):
        warnings.warn(
            "This class will be removed in a future version of modulegraph",
            DeprecationWarning)
        super(FlatPackage, *args, **kwds)


# 008742.python.modulegraph.line728.comment FIXME: Safely removable. We don't actually use this anywhere. After removing
# 008743.python.modulegraph.line729.comment this class, remove the corresponding entry from "compat".
class ArchiveModule(BaseModule):
    def __init__(self, *args, **kwds):
        warnings.warn(
            "This class will be removed in a future version of modulegraph",
            DeprecationWarning)
        super(FlatPackage, *args, **kwds)


# 008744.python.modulegraph.line738.comment HTML templates for ModuleGraph generator
header = """\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>%(TITLE)s</title>
    <style>
      .node { padding: 0.5em 0 0.5em; border-top: thin grey dotted; }
      .moduletype { font: smaller italic }
      .node a { text-decoration: none; color: #006699; }
      .node a:visited { text-decoration: none; color: #2f0099; }
    </style>
  </head>
  <body>
    <h1>%(TITLE)s</h1>"""
entry = """
<div class="node">
  <a name="%(NAME)s"></a>
  %(CONTENT)s
</div>"""
contpl = """<tt>%(NAME)s</tt> <span class="moduletype">%(TYPE)s</span>"""
contpl_linked = """\
<a target="code" href="%(URL)s" type="text/plain"><tt>%(NAME)s</tt></a>
<span class="moduletype">%(TYPE)s</span>"""
imports = """\
  <div class="import">
%(HEAD)s:
  %(LINKS)s
  </div>
"""
footer = """
  </body>
</html>"""


def _ast_names(names):
    result = []
    for nm in names:
        if isinstance(nm, ast.alias):
            result.append(nm.name)
        else:
            result.append(nm)

    result = [r for r in result if r != '__main__']
    return result


def uniq(seq):
    """Remove duplicates from a list, preserving order"""
    # 008745.python.modulegraph.line788.comment Taken from https://stackoverflow.com/questions/480214
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


DEFAULT_IMPORT_LEVEL = 0


class _Visitor(ast.NodeVisitor):
    def __init__(self, graph, module):
        self._graph = graph
        self._module = module
        self._level = DEFAULT_IMPORT_LEVEL
        self._in_if = [False]
        self._in_def = [False]
        self._in_tryexcept = [False]

    @property
    def in_if(self):
        return self._in_if[-1]

    @property
    def in_def(self):
        return self._in_def[-1]

    @property
    def in_tryexcept(self):
        return self._in_tryexcept[-1]


    def _collect_import(self, name, fromlist, level):
        have_star = False
        if fromlist is not None:
            fromlist = uniq(fromlist)
            if '*' in fromlist:
                fromlist.remove('*')
                have_star = True

        # 008746.python.modulegraph.line827.comment Record this import as originating from this module for subsequent
        # 008747.python.modulegraph.line828.comment handling by the _process_imports() method.
        self._module._deferred_imports.append(
            (have_star,
             (name, self._module, fromlist, level),
             {'edge_attr': DependencyInfo(
                 conditional=self.in_if,
                 tryexcept=self.in_tryexcept,
                 function=self.in_def,
                 fromlist=False)}))


    def visit_Import(self, node):
        for nm in _ast_names(node.names):
            self._collect_import(nm, None, self._level)

    def visit_ImportFrom(self, node):
        level = node.level if node.level != 0 else self._level
        self._collect_import(node.module or '', _ast_names(node.names), level)

    def visit_If(self, node):
        self._in_if.append(True)
        self.generic_visit(node)
        self._in_if.pop()

    def visit_FunctionDef(self, node):
        self._in_def.append(True)
        self.generic_visit(node)
        self._in_def.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Try(self, node):
        self._in_tryexcept.append(True)
        self.generic_visit(node)
        self._in_tryexcept.pop()

    def visit_TryExcept(self, node):
        self._in_tryexcept.append(True)
        self.generic_visit(node)
        self._in_tryexcept.pop()

    def visit_Expression(self, node):
        # 008748.python.modulegraph.line870.comment Expression node's cannot contain import statements or
        # 008749.python.modulegraph.line871.comment other nodes that are relevant for us.
        pass

    # 008750.python.modulegraph.line874.comment Expression isn't actually used as such in AST trees,
    # 008751.python.modulegraph.line875.comment therefore define visitors for all kinds of expression nodes.
    visit_BoolOp = visit_Expression
    visit_BinOp = visit_Expression
    visit_UnaryOp = visit_Expression
    visit_Lambda = visit_Expression
    visit_IfExp = visit_Expression
    visit_Dict = visit_Expression
    visit_Set = visit_Expression
    visit_ListComp = visit_Expression
    visit_SetComp = visit_Expression
    visit_ListComp = visit_Expression
    visit_GeneratorExp = visit_Expression
    visit_Compare = visit_Expression
    visit_Yield = visit_Expression
    visit_YieldFrom = visit_Expression
    visit_Await = visit_Expression
    visit_Call = visit_Expression
    visit_Await = visit_Expression


class ModuleGraph(ObjectGraph):
    """
    Directed graph whose nodes represent modules and edges represent
    dependencies between these modules.
    """


    def createNode(self, cls, name, *args, **kw):
        m = self.find_node(name)

        if m is None:
            # 008752.python.modulegraph.line906.comment assert m is None, m
            m = super(ModuleGraph, self).createNode(cls, name, *args, **kw)

        return m


    def __init__(self, path=None, excludes=(), replace_paths=(), implies=(), graph=None, debug=0):
        super(ModuleGraph, self).__init__(graph=graph, debug=debug)
        if path is None:
            path = sys.path
        self.path = path
        self.lazynodes = {}
        # 008753.python.modulegraph.line918.comment excludes is stronger than implies
        self.lazynodes.update(dict(implies))
        for m in excludes:
            self.lazynodes[m] = None
        self.replace_paths = replace_paths

        # 008754.python.modulegraph.line924.comment Maintain own list of package path mappings in the scope of Modulegraph
        # 008755.python.modulegraph.line925.comment object.
        self._package_path_map = {}

        # 008756.python.modulegraph.line928.comment Legacy namespace-package paths. Initialized by scan_legacy_namespace_packages.
        self._legacy_ns_packages = {}

    def scan_legacy_namespace_packages(self):
        """
        Resolve extra package `__path__` entries for legacy setuptools-based
        namespace packages, by reading `namespace_packages.txt` from dist
        metadata.
        """
        legacy_ns_packages = defaultdict(lambda: set())

        for dist in importlib_metadata.distributions():
            ns_packages = dist.read_text("namespace_packages.txt")
            if ns_packages is None:
                continue
            ns_packages = ns_packages.splitlines()
            # 008757.python.modulegraph.line944.comment Obtain path to dist metadata directory
            dist_path = getattr(dist, '_path')
            if dist_path is None:
                continue
            for package_name in ns_packages:
                path = os.path.join(
                    str(dist_path.parent),  # might be zipfile.Path if in zipped .egg
                    *package_name.split('.'),
                )
                legacy_ns_packages[package_name].add(path)

        # 008759.python.modulegraph.line955.comment Convert into dictionary of lists
        self._legacy_ns_packages = {
            package_name: list(paths)
            for package_name, paths in legacy_ns_packages.items()
        }

    def implyNodeReference(self, node, other, edge_data=None):
        """
        Create a reference from the passed source node to the passed other node,
        implying the former to depend upon the latter.

        While the source node _must_ be an existing graph node, the target node
        may be either an existing graph node _or_ a fully-qualified module name.
        In the latter case, the module with that name and all parent packages of
        that module will be imported _without_ raising exceptions and for each
        newly imported module or package:

        * A new graph node will be created for that module or package.
        * A reference from the passed source node to that module or package will
          be created.

        This method allows dependencies between Python objects _not_ importable
        with standard techniques (e.g., module aliases, C extensions).

        Parameters
        ----------
        node : str
            Graph node for this reference's source module or package.
        other : {Node, str}
            Either a graph node _or_ fully-qualified name for this reference's
            target module or package.
        """

        if isinstance(other, Node):
            self._updateReference(node, other, edge_data)
        else:
            if isinstance(other, tuple):
                raise ValueError(other)
            others = self._safe_import_hook(other, node, None)
            for other in others:
                self._updateReference(node, other, edge_data)

    def outgoing(self, fromnode):
        """
        Yield all nodes that `fromnode` dependes on (that is,
        all modules that `fromnode` imports.
        """

        node = self.find_node(fromnode)
        out_edges, _ = self.get_edges(node)
        return out_edges

    getReferences = outgoing

    def incoming(self, tonode, collapse_missing_modules=True):
        node = self.find_node(tonode)
        _, in_edges = self.get_edges(node)

        if collapse_missing_modules:
            for n in in_edges:
                if isinstance(n, MissingModule):
                    for n in self.incoming(n, False):
                        yield n

                else:
                    yield n

        else:
            for n in in_edges:
                yield n

    getReferers = incoming

    def hasEdge(self, fromnode, tonode):
        """ Return True iff there is an edge from 'fromnode' to 'tonode' """
        fromnode = self.find_node(fromnode)
        tonode = self.find_node(tonode)

        return self.graph.edge_by_node(fromnode, tonode) is not None

    def foldReferences(self, packagenode):
        """
        Create edges to/from `packagenode` based on the edges to/from all
        submodules of that package _and_ then hide the graph nodes
        corresponding to those submodules.
        """

        pkg = self.find_node(packagenode)

        for n in self.nodes():
            if not n.identifier.startswith(pkg.identifier + '.'):
                continue

            iter_out, iter_inc = self.get_edges(n)
            for other in iter_out:
                if other.identifier.startswith(pkg.identifier + '.'):
                    continue

                if not self.hasEdge(pkg, other):
                    # 008760.python.modulegraph.line1054.comment Ignore circular dependencies
                    self._updateReference(pkg, other, 'pkg-internal-import')

            for other in iter_inc:
                if other.identifier.startswith(pkg.identifier + '.'):
                    # 008761.python.modulegraph.line1059.comment Ignore circular dependencies
                    continue

                if not self.hasEdge(other, pkg):
                    self._updateReference(other, pkg, 'pkg-import')

            self.graph.hide_node(n)

    # 008762.python.modulegraph.line1067.comment TODO: unfoldReferences(pkg) that restore the submodule nodes and
    # 008763.python.modulegraph.line1068.comment removes 'pkg-import' and 'pkg-internal-import' edges. Care should
    # 008764.python.modulegraph.line1069.comment be taken to ensure that references are correct if multiple packages
    # 008765.python.modulegraph.line1070.comment are folded and then one of them in unfolded

    def _updateReference(self, fromnode, tonode, edge_data):
        try:
            ed = self.edgeData(fromnode, tonode)
        except (KeyError, GraphError):  # XXX: Why 'GraphError'
            return self.add_edge(fromnode, tonode, edge_data)

        if not (isinstance(ed, DependencyInfo) and isinstance(edge_data, DependencyInfo)):
            self.updateEdgeData(fromnode, tonode, edge_data)
        else:
            self.updateEdgeData(fromnode, tonode, ed._merged(edge_data))

    def add_edge(self, fromnode, tonode, edge_data='direct'):
        """
        Create a reference from fromnode to tonode
        """
        return super(ModuleGraph, self).createReference(fromnode, tonode, edge_data=edge_data)

    createReference = add_edge

    def find_node(self, name, create_nspkg=True):
        """
        Graph node uniquely identified by the passed fully-qualified module
        name if this module has been added to the graph _or_ `None` otherwise.

        If (in order):

        . A namespace package with this identifier exists _and_ the passed
          `create_nspkg` parameter is `True`, this package will be
          instantiated and returned.
        . A lazy node with this identifier and:
          * No dependencies exists, this node will be instantiated and
            returned.
          * Dependencies exists, this node and all transitive dependencies of
            this node be instantiated and this node returned.
        . A non-lazy node with this identifier exists, this node will be
          returned as is.

        Parameters
        ----------
        name : str
            Fully-qualified name of the module whose graph node is to be found.
        create_nspkg : bool
            Ignored.

        Returns
        ----------
        Node
            Graph node of this module if added to the graph _or_ `None`
            otherwise.
        """

        data = super(ModuleGraph, self).findNode(name)

        if data is not None:
            return data

        if name in self.lazynodes:
            deps = self.lazynodes.pop(name)

            if deps is None:
                # 008767.python.modulegraph.line1132.comment excluded module
                m = self.createNode(ExcludedModule, name)
            elif isinstance(deps, Alias):
                # 008768.python.modulegraph.line1135.comment NOTE: the AliasNode must be created and added to graph
                # 008769.python.modulegraph.line1136.comment before trying to create the referred node; that might
                # 008770.python.modulegraph.line1137.comment (due to recursive import analysis) lead to another
                # 008771.python.modulegraph.line1138.comment attempt to resolve the aliased node (and if there is
                # 008772.python.modulegraph.line1139.comment a real node that we are trying to shadow with the alias,
                # 008773.python.modulegraph.line1140.comment that will end up added to the graph and prevent the
                # 008774.python.modulegraph.line1141.comment alias node from being added).
                m = self.createNode(AliasNode, name)

                # 008775.python.modulegraph.line1144.comment Create the referred node.
                other = self._safe_import_hook(deps, None, None).pop()

                # 008776.python.modulegraph.line1147.comment Copy attributes; this used to be done by AliasNode
                # 008777.python.modulegraph.line1148.comment constructor, back when referred node was created before
                # 008778.python.modulegraph.line1149.comment the AliasNode (and could thus be passed to its constructor).
                m.copyAttributesFromReferredNode(other)

                self.implyNodeReference(m, other)
            else:
                m = self._safe_import_hook(name, None, None).pop()
                for dep in deps:
                    self.implyNodeReference(m, dep)

            return m

        return None

    findNode = find_node
    iter_graph = ObjectGraph.flatten

    def add_script(self, pathname, caller=None):
        """
        Create a node by path (not module name).  It is expected to be a Python
        source file, and will be scanned for dependencies.
        """
        self.msg(2, "run_script", pathname)

        pathname = os.path.realpath(pathname)
        m = self.find_node(pathname)
        if m is not None:
            return m

        with open(pathname, 'rb') as fp:
            contents = fp.read()
        contents = importlib.util.decode_source(contents)

        co_ast = compile(contents, pathname, 'exec', ast.PyCF_ONLY_AST, True)
        co = compile(co_ast, pathname, 'exec', 0, True)
        m = self.createNode(Script, pathname)
        self._updateReference(caller, m, None)
        n = self._scan_code(m, co, co_ast)
        self._process_imports(n)
        m.code = co
        if self.replace_paths:
            m.code = self._replace_paths_in_code(m.code)
        return m


    # 008779.python.modulegraph.line1193.comment FIXME: For safety, the "source_module" parameter should default to the
    # 008780.python.modulegraph.line1194.comment root node of the current graph if unpassed. This parameter currently
    # 008781.python.modulegraph.line1195.comment defaults to None, thus disconnected modules imported in this manner (e.g.,
    # 008782.python.modulegraph.line1196.comment hidden imports imported by depend.analysis.initialize_modgraph()).
    def import_hook(
        self,
        target_module_partname,
        source_module=None,
        target_attr_names=None,
        level=DEFAULT_IMPORT_LEVEL,
        edge_attr=None,
    ):
        """
        Import the module with the passed name, all parent packages of this
        module, _and_ all submodules and attributes in this module with the
        passed names from the previously imported caller module signified by
        the passed graph node.

        Unlike most import methods (e.g., `_safe_import_hook()`), this method
        is designed to be publicly called by both external and internal
        callers and hence is public.

        Parameters
        ----------
        target_module_partname : str
            Partially-qualified name of the target module to be imported. See
            `_safe_import_hook()` for further details.
        source_module : Node
            Graph node for the previously imported **source module** (i.e.,
            module containing the `import` statement triggering the call to
            this method) _or_ `None` if this module is to be imported in a
            "disconnected" manner. **Passing `None` is _not_ recommended.**
            Doing so produces a disconnected graph in which the graph node
            created for the module to be imported will be disconnected and
            hence unreachable from all other nodes -- which frequently causes
            subtle issues in external callers (namely PyInstaller, which
            silently ignores unreachable nodes).
        target_attr_names : list
            List of the unqualified names of all submodules and attributes to
            be imported from the module to be imported if this is a "from"-
            style import (e.g., `[encode_base64, encode_noop]` for the import
            `from email.encoders import encode_base64, encode_noop`) _or_
            `None` otherwise.
        level : int
            Whether to perform an absolute or relative import. See
            `_safe_import_hook()` for further details.

        Returns
        ----------
        list
            List of the graph nodes created for all modules explicitly imported
            by this call, including the passed module and all submodules listed
            in `target_attr_names` _but_ excluding all parent packages
            implicitly imported by this call. If `target_attr_names` is `None`
            or the empty list, this is guaranteed to be a list of one element:
            the graph node created for the passed module.

        Raises
        ----------
        ImportError
            If the target module to be imported is unimportable.
        """
        self.msg(3, "_import_hook", target_module_partname, source_module, source_module, level)

        source_package = self._determine_parent(source_module)
        target_package, target_module_partname = self._find_head_package(
            source_package, target_module_partname, level)

        self.msgin(4, "load_tail", target_package, target_module_partname)

        submodule = target_package
        while target_module_partname:
            i = target_module_partname.find('.')
            if i < 0:
                i = len(target_module_partname)
            head, target_module_partname = target_module_partname[
                :i], target_module_partname[i+1:]
            mname = "%s.%s" % (submodule.identifier, head)
            submodule = self._safe_import_module(head, mname, submodule)

            if submodule is None:
                # 008783.python.modulegraph.line1274.comment FIXME: Why do we no longer return a MissingModule instance?
                # 008784.python.modulegraph.line1275.comment result = self.createNode(MissingModule, mname)
                self.msgout(4, "raise ImportError: No module named", mname)
                raise ImportError("No module named " + repr(mname))

        self.msgout(4, "load_tail ->", submodule)

        target_module = submodule
        target_modules = [target_module]

        # 008785.python.modulegraph.line1284.comment If this is a "from"-style import *AND* this target module is
        # 008786.python.modulegraph.line1285.comment actually a package, import all submodules of this package specified
        # 008787.python.modulegraph.line1286.comment by the "import" half of this import (e.g., the submodules "bar" and
        # 008788.python.modulegraph.line1287.comment "car" of the target package "foo" in "from foo import bar, car").
        # 008789.python.modulegraph.line1288.comment
        # 008790.python.modulegraph.line1289.comment If this target module is a non-package, it could still contain
        # 008791.python.modulegraph.line1290.comment importable submodules (e.g., the non-package `os` module containing
        # 008792.python.modulegraph.line1291.comment the `os.path` submodule). In this case, these submodules are already
        # 008793.python.modulegraph.line1292.comment imported by this target module's pure-Python code. Since our import
        # 008794.python.modulegraph.line1293.comment scanner already detects such imports, these submodules need *NOT* be
        # 008795.python.modulegraph.line1294.comment reimported here.
        if target_attr_names and isinstance(target_module,
                                            (Package, AliasNode)):
            for target_submodule in self._import_importable_package_submodules(
                target_module, target_attr_names):
                if target_submodule not in target_modules:
                    target_modules.append(target_submodule)

        # 008796.python.modulegraph.line1302.comment Add an edge from this source module to each target module.
        for target_module in target_modules:
            self._updateReference(
                source_module, target_module, edge_data=edge_attr)

        return target_modules


    def _determine_parent(self, caller):
        """
        Determine the package containing a node.
        """
        self.msgin(4, "determine_parent", caller)

        parent = None
        if caller:
            pname = caller.identifier

            if isinstance(caller, Package):
                parent = caller

            elif '.' in pname:
                pname = pname[:pname.rfind('.')]
                parent = self.find_node(pname)

            elif caller.packagepath:
                # 008797.python.modulegraph.line1328.comment XXX: I have no idea why this line
                # 008798.python.modulegraph.line1329.comment is necessary.
                parent = self.find_node(pname)

        self.msgout(4, "determine_parent ->", parent)
        return parent


    def _find_head_package(
        self,
        source_package,
        target_module_partname,
        level=DEFAULT_IMPORT_LEVEL):
        """
        Import the target package providing the target module with the passed
        name to be subsequently imported from the previously imported source
        package corresponding to the passed graph node.

        Parameters
        ----------
        source_package : Package
            Graph node for the previously imported **source package** (i.e.,
            package containing the module containing the `import` statement
            triggering the call to this method) _or_ `None` if this module is
            to be imported in a "disconnected" manner. **Passing `None` is
            _not_ recommended.** See the `_import_hook()` method for further
            details.
        target_module_partname : str
            Partially-qualified name of the target module to be imported. See
            `_safe_import_hook()` for further details.
        level : int
            Whether to perform absolute or relative imports. See the
            `_safe_import_hook()` method for further details.

        Returns
        ----------
        (target_package, target_module_tailname)
            2-tuple describing the imported target package, where:
            * `target_package` is the graph node created for this package.
            * `target_module_tailname` is the unqualified name of the target
              module to be subsequently imported (e.g., `text` when passed a
              `target_module_partname` of `email.mime.text`).

        Raises
        ----------
        ImportError
            If the package to be imported is unimportable.
        """
        self.msgin(4, "find_head_package", source_package, target_module_partname, level)

        # 008799.python.modulegraph.line1378.comment FIXME: Rename all local variable names to something sensible. No,
        # 008800.python.modulegraph.line1379.comment "p_fqdn" is not a sensible name.

        # 008801.python.modulegraph.line1381.comment If this target module is a submodule...
        if '.' in target_module_partname:
            target_module_headname, target_module_tailname = (
                target_module_partname.split('.', 1))
        # 008802.python.modulegraph.line1385.comment Else, this target module is a top-level module.
        else:
            target_module_headname = target_module_partname
            target_module_tailname = ''

        # 008803.python.modulegraph.line1390.comment If attempting both absolute and relative imports...
        if level == ABSOLUTE_OR_RELATIVE_IMPORT_LEVEL:
            if source_package:
                target_package_name = source_package.identifier + '.' + target_module_headname
            else:
                target_package_name = target_module_headname
        # 008804.python.modulegraph.line1396.comment Else if attempting only absolute imports...
        elif level == ABSOLUTE_IMPORT_LEVEL:
            target_package_name = target_module_headname

            # 008805.python.modulegraph.line1400.comment Absolute import, ignore the parent
            source_package = None
        # 008806.python.modulegraph.line1402.comment Else if attempting only relative imports...
        else:
            if source_package is None:
                self.msg(2, "Relative import outside of package")
                raise InvalidRelativeImportError(
                    "Relative import outside of package (name=%r, parent=%r, level=%r)" % (
                        target_module_partname, source_package, level))

            for i in range(level - 1):
                if '.' not in source_package.identifier:
                    self.msg(2, "Relative import outside of package")
                    raise InvalidRelativeImportError(
                        "Relative import outside of package (name=%r, parent=%r, level=%r)" % (
                            target_module_partname, source_package, level))

                p_fqdn = source_package.identifier.rsplit('.', 1)[0]
                new_parent = self.find_node(p_fqdn)
                if new_parent is None:
                    # 008807.python.modulegraph.line1420.comment FIXME: Repetition detected. Exterminate. Exterminate.
                    self.msg(2, "Relative import outside of package")
                    raise InvalidRelativeImportError(
                        "Relative import outside of package (name=%r, parent=%r, level=%r)" % (
                            target_module_partname, source_package, level))

                assert new_parent is not source_package, (
                    new_parent, source_package)
                source_package = new_parent

            if target_module_headname:
                target_package_name = (
                    source_package.identifier + '.' + target_module_headname)
            else:
                target_package_name = source_package.identifier

        # 008808.python.modulegraph.line1436.comment Graph node of this target package.
        target_package = self._safe_import_module(
            target_module_headname, target_package_name, source_package)

        # 008809.python.modulegraph.line1440.comment If this target package is *NOT* importable and a source package was
        # 008810.python.modulegraph.line1441.comment passed, attempt to import this target package as an absolute import.
        # 008811.python.modulegraph.line1442.comment
        # 008812.python.modulegraph.line1443.comment ADDENDUM: but do this only if the passed "level" is either
        # 008813.python.modulegraph.line1444.comment ABSOLUTE_IMPORT_LEVEL (0) or ABSOLUTE_OR_RELATIVE_IMPORT_LEVEL (-1).
        # 008814.python.modulegraph.line1445.comment Otherwise, an attempt at relative import of a missing sub-module
        # 008815.python.modulegraph.line1446.comment (from .module import something) might pull in an unrelated
        # 008816.python.modulegraph.line1447.comment but eponymous top-level module, which should not happen.
        if target_package is None and source_package is not None and level <= ABSOLUTE_IMPORT_LEVEL:
            target_package_name = target_module_headname
            source_package = None

            # 008817.python.modulegraph.line1452.comment Graph node for the target package, again.
            target_package = self._safe_import_module(
                target_module_headname, target_package_name, source_package)

        # 008818.python.modulegraph.line1456.comment If this target package is importable, return this package.
        if target_package is not None:
            self.msgout(4, "find_head_package ->", (target_package, target_module_tailname))
            return target_package, target_module_tailname

        # 008819.python.modulegraph.line1461.comment Else, raise an exception.
        self.msgout(4, "raise ImportError: No module named", target_package_name)
        raise ImportError("No module named " + target_package_name)




    # 008820.python.modulegraph.line1468.comment FIXME: Refactor from a generator yielding graph nodes into a non-generator
    # 008821.python.modulegraph.line1469.comment returning a list or tuple of all yielded graph nodes. This method is only
    # 008822.python.modulegraph.line1470.comment called once above and the return value of that call is only iterated over
    # 008823.python.modulegraph.line1471.comment as a list or tuple. There's no demonstrable reason for this to be a
    # 008824.python.modulegraph.line1472.comment generator. Generators are great for their intended purposes (e.g., as
    # 008825.python.modulegraph.line1473.comment continuations). This isn't one of those purposes.
    def _import_importable_package_submodules(self, package, attr_names):
        """
        Generator importing and yielding each importable submodule (of the
        previously imported package corresponding to the passed graph node)
        whose unqualified name is in the passed list.

        Elements of this list that are _not_ importable submodules of this
        package are either:

        * Ignorable attributes (e.g., classes, globals) defined at the top
          level of this package's `__init__` submodule, which will be ignored.
        * Else, unignorable unimportable submodules, in which case an
          exception is raised.

        Parameters
        ----------
        package : Package
            Graph node of the previously imported package containing the
            modules to be imported and yielded.

        attr_names : list
            List of the unqualified names of all attributes of this package to
            attempt to import as submodules. This list will be internally
            converted into a set, safely ignoring any duplicates in this list
            (e.g., reducing the "from"-style import
            `from foo import bar, car, far, bar, car, far` to merely
            `from foo import bar, car, far`).

        Yields
        ----------
        Node
            Graph node created for the currently imported submodule.

        Raises
        ----------
        ImportError
            If any attribute whose name is in `attr_names` is neither:
            * An importable submodule of this package.
            * An ignorable global attribute (e.g., class, variable) defined at
              the top level of this package's `__init__` submodule.
            In this case, this attribute _must_ be an unimportable submodule of
            this package.
        """

        # 008826.python.modulegraph.line1518.comment Ignore duplicate submodule names in the passed list.
        attr_names = set(attr_names)
        self.msgin(4, "_import_importable_package_submodules", package, attr_names)

        # 008827.python.modulegraph.line1522.comment FIXME: This test *SHOULD* be superfluous and hence safely removable.
        # 008828.python.modulegraph.line1523.comment The higher-level _scan_bytecode() and _collect_import() methods
        # 008829.python.modulegraph.line1524.comment already guarantee "*" characters to be removed from fromlists.
        if '*' in attr_names:
            attr_names.update(self._find_all_submodules(package))
            attr_names.remove('*')

        # 008830.python.modulegraph.line1529.comment self.msg(4, '_import_importable_package_submodules (global attrs)', package.identifier, package._global_attr_names)

        # 008831.python.modulegraph.line1531.comment For the name of each attribute to be imported from this package...
        for attr_name in attr_names:
            # 008832.python.modulegraph.line1533.comment self.msg(4, '_import_importable_package_submodules (fromlist attr)', package.identifier, attr_name)

            # 008833.python.modulegraph.line1535.comment Graph node of this attribute if this attribute is a previously
            # 008834.python.modulegraph.line1536.comment imported module or None otherwise.
            submodule = package.get_submodule_or_none(attr_name)

            # 008835.python.modulegraph.line1539.comment If this attribute is *NOT* a previously imported module, attempt
            # 008836.python.modulegraph.line1540.comment to import this attribute as a submodule of this package.
            if submodule is None:
                # 008837.python.modulegraph.line1542.comment Fully-qualified name of this submodule.
                submodule_name = package.identifier + '.' + attr_name

                # 008838.python.modulegraph.line1545.comment Graph node of this submodule if importable or None otherwise.
                submodule = self._safe_import_module(
                    attr_name, submodule_name, package)

                # 008839.python.modulegraph.line1549.comment If this submodule is unimportable...
                if submodule is None:
                    # 008840.python.modulegraph.line1551.comment If this attribute is a global (e.g., class, variable)
                    # 008841.python.modulegraph.line1552.comment defined at the top level of this package's "__init__"
                    # 008842.python.modulegraph.line1553.comment submodule, this importation is safely ignorable. Do so
                    # 008843.python.modulegraph.line1554.comment and skip to the next attribute.
                    # 008844.python.modulegraph.line1555.comment
                    # 008845.python.modulegraph.line1556.comment This behaviour is non-conformant with Python behaviour,
                    # 008846.python.modulegraph.line1557.comment which is bad, but is required to sanely handle all
                    # 008847.python.modulegraph.line1558.comment possible edge cases, which is good. In Python, a global
                    # 008848.python.modulegraph.line1559.comment attribute defined at the top level of a package's
                    # 008849.python.modulegraph.line1560.comment "__init__" submodule shadows a submodule of the same name
                    # 008850.python.modulegraph.line1561.comment in that package. Attempting to import that submodule
                    # 008851.python.modulegraph.line1562.comment instead imports that attribute; thus, that submodule is
                    # 008852.python.modulegraph.line1563.comment effectively unimportable. In this method and elsewhere,
                    # 008853.python.modulegraph.line1564.comment that submodule is tested for first and hence shadows that
                    # 008854.python.modulegraph.line1565.comment attribute -- the opposite logic. Attempts to import that
                    # 008855.python.modulegraph.line1566.comment attribute are mistakenly seen as attempts to import that
                    # 008856.python.modulegraph.line1567.comment submodule! Why?
                    # 008857.python.modulegraph.line1568.comment
                    # 008858.python.modulegraph.line1569.comment Edge cases. PyInstaller (and by extension ModuleGraph)
                    # 008859.python.modulegraph.line1570.comment only cares about module imports. Global attribute imports
                    # 008860.python.modulegraph.line1571.comment are parsed only as the means to this ends and are
                    # 008861.python.modulegraph.line1572.comment otherwise ignorable. The cost of erroneously shadowing:
                    # 008862.python.modulegraph.line1573.comment
                    # 008863.python.modulegraph.line1574.comment * Submodules by attributes is significant. Doing so
                    # 008864.python.modulegraph.line1575.comment prevents such submodules from being frozen and hence
                    # 008865.python.modulegraph.line1576.comment imported at application runtime.
                    # 008866.python.modulegraph.line1577.comment * Attributes by submodules is insignificant. Doing so
                    # 008867.python.modulegraph.line1578.comment could erroneously freeze such submodules despite their
                    # 008868.python.modulegraph.line1579.comment never being imported at application runtime. However,
                    # 008869.python.modulegraph.line1580.comment ModuleGraph is incapable of determining with certainty
                    # 008870.python.modulegraph.line1581.comment that Python logic in another module other than the
                    # 008871.python.modulegraph.line1582.comment "__init__" submodule containing these attributes does
                    # 008872.python.modulegraph.line1583.comment *NOT* delete these attributes and hence unshadow these
                    # 008873.python.modulegraph.line1584.comment submodules, which would then become importable at
                    # 008874.python.modulegraph.line1585.comment runtime and require freezing. Hence, ModuleGraph *MUST*
                    # 008875.python.modulegraph.line1586.comment permissively assume submodules of the same name as
                    # 008876.python.modulegraph.line1587.comment attributes to be unshadowed elsewhere and require
                    # 008877.python.modulegraph.line1588.comment freezing -- even if they do not.
                    # 008878.python.modulegraph.line1589.comment
                    # 008879.python.modulegraph.line1590.comment It is practically difficult (albeit technically feasible)
                    # 008880.python.modulegraph.line1591.comment for ModuleGraph to determine whether or not the target
                    # 008881.python.modulegraph.line1592.comment attribute names of "from"-style import statements (e.g.,
                    # 008882.python.modulegraph.line1593.comment "bar" and "car" in "from foo import bar, car") refer to
                    # 008883.python.modulegraph.line1594.comment non-ignorable submodules or ignorable non-module globals
                    # 008884.python.modulegraph.line1595.comment during opcode scanning. Distinguishing these two cases
                    # 008885.python.modulegraph.line1596.comment during opcode scanning would require a costly call to the
                    # 008886.python.modulegraph.line1597.comment _find_module() method, which would subsequently be
                    # 008887.python.modulegraph.line1598.comment repeated during import-graph construction. This could be
                    # 008888.python.modulegraph.line1599.comment ameliorated with caching, which itself would require
                    # 008889.python.modulegraph.line1600.comment costly space consumption and developer time.
                    # 008890.python.modulegraph.line1601.comment
                    # 008891.python.modulegraph.line1602.comment Since opcode scanning fails to distinguish these two
                    # 008892.python.modulegraph.line1603.comment cases, this and other methods subsequently called at
                    # 008893.python.modulegraph.line1604.comment import-graph construction time (e.g.,
                    # 008894.python.modulegraph.line1605.comment _safe_import_hook()) must do so. Since submodules of the
                    # 008895.python.modulegraph.line1606.comment same name as attributes must assume to be unshadowed
                    # 008896.python.modulegraph.line1607.comment elsewhere and require freezing, the only solution is to
                    # 008897.python.modulegraph.line1608.comment attempt to import an attribute as a non-ignorable module
                    # 008898.python.modulegraph.line1609.comment *BEFORE* assuming an attribute to be an ignorable
                    # 008899.python.modulegraph.line1610.comment non-module. Which is what this and other methods do.
                    # 008900.python.modulegraph.line1611.comment
                    # 008901.python.modulegraph.line1612.comment See Package.is_global_attr() for similar discussion.
                    if package.is_global_attr(attr_name):
                        self.msg(4, '_import_importable_package_submodules: ignoring from-imported global', package.identifier, attr_name)
                        continue
                    # 008902.python.modulegraph.line1616.comment Else, this attribute is an unimportable submodule. Since
                    # 008903.python.modulegraph.line1617.comment this is *NOT* safely ignorable, raise an exception.
                    else:
                        raise ImportError("No module named " + submodule_name)

            # 008904.python.modulegraph.line1621.comment Yield this submodule's graph node to the caller.
            yield submodule

        self.msgin(4, "_import_importable_package_submodules ->")


    def _find_all_submodules(self, m):
        if not m.packagepath:
            return
        # 008905.python.modulegraph.line1630.comment 'suffixes' used to be a list hardcoded to [".py", ".pyc", ".pyo"].
        # 008906.python.modulegraph.line1631.comment But we must also collect Python extension modules - although
        # 008907.python.modulegraph.line1632.comment we cannot separate normal dlls from Python extensions.
        for path in m.packagepath:
            try:
                names = os.listdir(path)
            except (os.error, IOError):
                self.msg(2, "can't list directory", path)
                continue
            for name in names:
                for suffix in importlib.machinery.all_suffixes():
                    if path.endswith(suffix):
                        name = os.path.basename(path)[:-len(suffix)]
                        break
                else:
                    continue
                if name != '__init__':
                    yield name


    def alias_module(self, src_module_name, trg_module_name):
        """
        Alias the source module to the target module with the passed names.

        This method ensures that the next call to findNode() given the target
        module name will resolve this alias. This includes importing and adding
        a graph node for the source module if needed as well as adding a
        reference from the target to source module.

        Parameters
        ----------
        src_module_name : str
            Fully-qualified name of the existing **source module** (i.e., the
            module being aliased).
        trg_module_name : str
            Fully-qualified name of the non-existent **target module** (i.e.,
            the alias to be created).
        """
        self.msg(3, 'alias_module "%s" -> "%s"' % (src_module_name, trg_module_name))
        # 008908.python.modulegraph.line1669.comment print('alias_module "%s" -> "%s"' % (src_module_name, trg_module_name))
        assert isinstance(src_module_name, str), '"%s" not a module name.' % str(src_module_name)
        assert isinstance(trg_module_name, str), '"%s" not a module name.' % str(trg_module_name)

        # 008909.python.modulegraph.line1673.comment If the target module has already been added to the graph as either a
        # 008910.python.modulegraph.line1674.comment non-alias or as a different alias, raise an exception.
        trg_module = self.find_node(trg_module_name)
        if trg_module is not None and not (
           isinstance(trg_module, AliasNode) and
           trg_module.identifier == src_module_name):
            raise ValueError(
                'Target module "%s" already imported as "%s".' % (
                    trg_module_name, trg_module))

        # 008911.python.modulegraph.line1683.comment See findNode() for details.
        self.lazynodes[trg_module_name] = Alias(src_module_name)


    def add_module(self, module):
        """
        Add the passed module node to the graph if not already added.

        If that module has a parent module or package with a previously added
        node, this method also adds a reference from this module node to its
        parent node and adds this module node to its parent node's namespace.

        This high-level method wraps the low-level `addNode()` method, but is
        typically _only_ called by graph hooks adding runtime module nodes. For
        all other node types, the `import_module()` method should be called.

        Parameters
        ----------
        module : BaseModule
            Graph node of the module to be added.
        """
        self.msg(3, 'add_module', module)

        # 008912.python.modulegraph.line1706.comment If no node exists for this module, add such a node.
        module_added = self.find_node(module.identifier)
        if module_added is None:
            self.addNode(module)
        else:
            assert module == module_added, 'New module %r != previous %r.' % (module, module_added)

        # 008913.python.modulegraph.line1713.comment If this module has a previously added parent, reference this module to
        # 008914.python.modulegraph.line1714.comment its parent and add this module to its parent's namespace.
        parent_name, _, module_basename = module.identifier.rpartition('.')
        if parent_name:
            parent = self.find_node(parent_name)
            if parent is None:
                self.msg(4, 'add_module parent not found:', parent_name)
            else:
                self.add_edge(module, parent)
                parent.add_submodule(module_basename, module)


    def append_package_path(self, package_name, directory):
        """
        Modulegraph does a good job at simulating Python's, but it can not
        handle packagepath '__path__' modifications packages make at runtime.

        Therefore there is a mechanism whereby you can register extra paths
        in this map for a package, and it will be honored.

        NOTE: This method has to be called before a package is resolved by
              modulegraph.

        Parameters
        ----------
        module : str
            Fully-qualified module name.
        directory : str
            Absolute or relative path of the directory to append to the
            '__path__' attribute.
        """

        paths = self._package_path_map.setdefault(package_name, [])
        paths.append(directory)


    def _safe_import_module(
        self, module_partname, module_name, parent_module):
        """
        Create a new graph node for the module with the passed name under the
        parent package signified by the passed graph node _without_ raising
        `ImportError` exceptions.

        If this module has already been imported, this module's existing graph
        node will be returned; else if this module is importable, a new graph
        node will be added for this module and returned; else this module is
        unimportable, in which case `None` will be returned. Like the
        `_safe_import_hook()` method, this method does _not_ raise
        `ImportError` exceptions when this module is unimportable.

        Parameters
        ----------
        module_partname : str
            Unqualified name of the module to be imported (e.g., `text`).
        module_name : str
            Fully-qualified name of this module (e.g., `email.mime.text`).
        parent_module : Package
            Graph node of the previously imported parent module containing this
            submodule _or_ `None` if this is a top-level module (i.e.,
            `module_name` contains no `.` delimiters). This parent module is
            typically but _not_ always a package (e.g., the `os.path` submodule
            contained by the `os` module).

        Returns
        ----------
        Node
            Graph node created for this module _or_ `None` if this module is
            unimportable.
        """
        self.msgin(3, "safe_import_module", module_partname, module_name, parent_module)

        # 008915.python.modulegraph.line1784.comment If this module has *NOT* already been imported, do so.
        module = self.find_node(module_name)
        if module is None:
            # 008916.python.modulegraph.line1787.comment List of the absolute paths of all directories to be searched for
            # 008917.python.modulegraph.line1788.comment this module. This effectively defaults to "sys.path".
            search_dirs = None

            # 008918.python.modulegraph.line1791.comment If this module has a parent package...
            if parent_module is not None:
                # 008919.python.modulegraph.line1793.comment ...with a list of the absolute paths of all directories
                # 008920.python.modulegraph.line1794.comment comprising this package, prefer that to "sys.path".
                if parent_module.packagepath is not None:
                    search_dirs = parent_module.packagepath
                # 008921.python.modulegraph.line1797.comment Else, something is horribly wrong. Return emptiness.
                else:
                    self.msgout(3, "safe_import_module -> None (parent_parent.packagepath is None)")
                    return None

            try:
                pathname, loader = self._find_module(
                    module_partname, search_dirs, parent_module)
            except ImportError as exc:
                self.msgout(3, "safe_import_module -> None (%r)" % exc)
                return None

            (module, co) = self._load_module(module_name, pathname, loader)
            if co is not None:
                try:
                    if isinstance(co, ast.AST):
                        co_ast = co
                        co = compile(co_ast, pathname, 'exec', 0, True)
                    else:
                        co_ast = None
                    n = self._scan_code(module, co, co_ast)
                    self._process_imports(n)

                    if self.replace_paths:
                        co = self._replace_paths_in_code(co)
                    module.code = co
                except SyntaxError:
                    self.msg(
                        1, "safe_import_module: SyntaxError in ", pathname,
                    )
                    cls = InvalidSourceModule
                    module = self.createNode(cls, module_name)

        # 008922.python.modulegraph.line1830.comment If this is a submodule rather than top-level module...
        if parent_module is not None:
            self.msg(4, "safe_import_module create reference", module, "->", parent_module)

            # 008923.python.modulegraph.line1834.comment Add an edge from this submodule to its parent module.
            self._updateReference(
                module, parent_module, edge_data=DependencyInfo(
                    conditional=False,
                    fromlist=False,
                    function=False,
                    tryexcept=False,
            ))

            # 008924.python.modulegraph.line1843.comment Add this submodule to its parent module.
            parent_module.add_submodule(module_partname, module)

        # 008925.python.modulegraph.line1846.comment Return this module.
        self.msgout(3, "safe_import_module ->", module)
        return module

    def _load_module(self, fqname, pathname, loader):
        from importlib._bootstrap_external import ExtensionFileLoader
        self.msgin(2, "load_module", fqname, pathname,
                   loader.__class__.__name__)
        partname = fqname.rpartition(".")[-1]

        if loader.is_package(partname):
            if isinstance(loader, NAMESPACE_PACKAGE):
                # 008926.python.modulegraph.line1858.comment This is a PEP-420 namespace package.
                m = self.createNode(NamespacePackage, fqname)
                m.filename = '-'
                m.packagepath = loader.namespace_dirs[:]  # copy for safety
            else:
                # 008928.python.modulegraph.line1863.comment Regular package.
                # 008929.python.modulegraph.line1864.comment
                # 008930.python.modulegraph.line1865.comment NOTE: this might be a legacy setuptools (pkg_resources)
                # 008931.python.modulegraph.line1866.comment based namespace package (with __init__.py, but calling
                # 008932.python.modulegraph.line1867.comment `pkg_resources.declare_namespace(__name__)`). To properly
                # 008933.python.modulegraph.line1868.comment handle the case when such a package is split across
                # 008934.python.modulegraph.line1869.comment multiple locations, we need to resolve the package
                # 008935.python.modulegraph.line1870.comment paths via metadata.
                ns_pkgpaths = self._legacy_ns_packages.get(fqname, [])

                if isinstance(loader, ExtensionFileLoader):
                    m = self.createNode(ExtensionPackage, fqname)
                else:
                    m = self.createNode(Package, fqname)
                m.filename = pathname
                # 008936.python.modulegraph.line1878.comment PEP-302-compliant loaders return the pathname of the
                # 008937.python.modulegraph.line1879.comment `__init__`-file, not the package directory.
                assert os.path.basename(pathname).startswith('__init__.')
                m.packagepath = [os.path.dirname(pathname)] + ns_pkgpaths

            # 008938.python.modulegraph.line1883.comment As per comment at top of file, simulate runtime packagepath
            # 008939.python.modulegraph.line1884.comment additions
            m.packagepath = m.packagepath + self._package_path_map.get(
                fqname, [])

            if isinstance(m, NamespacePackage):
                return (m, None)

        co = None
        if loader is BUILTIN_MODULE:
            cls = BuiltinModule
        elif isinstance(loader, ExtensionFileLoader):
            cls = Extension

            # 008940.python.modulegraph.line1897.comment Look for accompanying .py or .pyi file, which might allow
            # 008941.python.modulegraph.line1898.comment us to perform basic import analysis for the extension.
            def _co_from_accompanying_source(extension_filename):
                path = os.path.dirname(extension_filename)
                basename = os.path.basename(extension_filename).split('.')[0]

                for ext in {'.py', '.pyi'}:
                    src_filename = os.path.join(path, basename + ext)
                    if not os.path.isfile(src_filename):
                        continue

                    try:
                        with open(src_filename, 'rb') as fp:
                            src = fp.read()
                        co = compile(src, src_filename, 'exec', ast.PyCF_ONLY_AST, True)
                        return co
                    except Exception as e:
                        pass

            co = _co_from_accompanying_source(pathname)
        else:
            try:
                src = loader.get_source(partname)
            except (UnicodeDecodeError, SyntaxError) as e:
                # 008942.python.modulegraph.line1921.comment The `UnicodeDecodeError` is typically raised here when the
                # 008943.python.modulegraph.line1922.comment source file contains non-ASCII characters in some local
                # 008944.python.modulegraph.line1923.comment encoding that is different from UTF-8, but fails to
                # 008945.python.modulegraph.line1924.comment declare it via PEP361 encoding header. Python seems to
                # 008946.python.modulegraph.line1925.comment be able to load and run such module, but we cannot retrieve
                # 008947.python.modulegraph.line1926.comment the source for it via the `loader.get_source()`.
                # 008948.python.modulegraph.line1927.comment
                # 008949.python.modulegraph.line1928.comment The `UnicodeDecoreError` in turn triggers a `SyntaxError`
                # 008950.python.modulegraph.line1929.comment when such invalid character appears on the first line of
                # 008951.python.modulegraph.line1930.comment the source file (and interrupts the scan for PEP361
                # 008952.python.modulegraph.line1931.comment encoding header).
                # 008953.python.modulegraph.line1932.comment
                # 008954.python.modulegraph.line1933.comment In such cases, we try to fall back to reading the source
                # 008955.python.modulegraph.line1934.comment as raw data file.

                # 008956.python.modulegraph.line1936.comment If `SyntaxError` was not raised during handling of
                # 008957.python.modulegraph.line1937.comment a `UnicodeDecodeError`, it was likely a genuine syntax
                # 008958.python.modulegraph.line1938.comment error, so re-raise it.
                if isinstance(e, SyntaxError):
                    if not isinstance(e.__context__, UnicodeDecodeError):
                        raise

                self.msg(2, "load_module: failed to obtain source for "
                         f"{partname}: {e}! Falling back to reading as "
                         "raw data!")

                path = loader.get_filename(partname)
                src = loader.get_data(path)

            if src is not None:
                try:
                    co = compile(src, pathname, 'exec', ast.PyCF_ONLY_AST, True)
                    cls = SourceModule
                except SyntaxError:
                    co = None
                    cls = InvalidSourceModule
                except Exception as exc:  # FIXME: more specific?
                    cls = InvalidSourceModule
                    self.msg(2, "load_module: InvalidSourceModule", pathname,
                             exc)
            else:
                # 008960.python.modulegraph.line1962.comment no src available
                try:
                    co = loader.get_code(partname)
                    cls = (CompiledModule if co is not None
                           else InvalidCompiledModule)
                except Exception as exc:  # FIXME: more specific?
                    self.msg(2, "load_module: InvalidCompiledModule, "
                             "Cannot load code", pathname, exc)
                    cls = InvalidCompiledModule

        m = self.createNode(cls, fqname)
        m.filename = pathname

        self.msgout(2, "load_module ->", m)
        return (m, co)

    def _safe_import_hook(
        self, target_module_partname, source_module, target_attr_names,
        level=DEFAULT_IMPORT_LEVEL, edge_attr=None):
        """
        Import the module with the passed name and all parent packages of this
        module from the previously imported caller module signified by the
        passed graph node _without_ raising `ImportError` exceptions.

        This method wraps the lowel-level `_import_hook()` method. On catching
        an `ImportError` exception raised by that method, this method creates
        and adds a `MissingNode` instance describing the unimportable module to
        the graph instead.

        Parameters
        ----------
        target_module_partname : str
            Partially-qualified name of the module to be imported. If `level`
            is:
            * `ABSOLUTE_OR_RELATIVE_IMPORT_LEVEL` (e.g., the Python 2 default)
              or a positive integer (e.g., an explicit relative import), the
              fully-qualified name of this module is the concatenation of the
              fully-qualified name of the caller module's package and this
              parameter.
            * `ABSOLUTE_IMPORT_LEVEL` (e.g., the Python 3 default), this name
              is already fully-qualified.
            * A non-negative integer (e.g., `1`), this name is typically the
              empty string. In this case, this is a "from"-style relative
              import (e.g., "from . import bar") and the fully-qualified name
              of this module is dynamically resolved by import machinery.
        source_module : Node
            Graph node for the previously imported **caller module** (i.e.,
            module containing the `import` statement triggering the call to
            this method) _or_ `None` if this module is to be imported in a
            "disconnected" manner. **Passing `None` is _not_ recommended.**
            Doing so produces a disconnected graph in which the graph node
            created for the module to be imported will be disconnected and
            hence unreachable from all other nodes -- which frequently causes
            subtle issues in external callers (e.g., PyInstaller, which
            silently ignores unreachable nodes).
        target_attr_names : list
            List of the unqualified names of all submodules and attributes to
            be imported via a `from`-style import statement from this target
            module if any (e.g., the list `[encode_base64, encode_noop]` for
            the import `from email.encoders import encode_base64, encode_noop`)
            _or_ `None` otherwise. Ignored unless `source_module` is the graph
            node of a package (i.e., is an instance of the `Package` class).
            Why? Because:
            * Consistency. The `_import_importable_package_submodules()`
              method accepts a similar list applicable only to packages.
            * Efficiency. Unlike packages, modules cannot physically contain
              submodules. Hence, any target module imported via a `from`-style
              import statement as an attribute from another target parent
              module must itself have been imported in that target parent
              module. The import statement responsible for that import must
              already have been previously parsed by `ModuleGraph`, in which
              case that target module will already be frozen by PyInstaller.
              These imports are safely ignorable here.
        level : int
            Whether to perform an absolute or relative import. This parameter
            corresponds exactly to the parameter of the same name accepted by
            the `__import__()` built-in: "The default is -1 which indicates
            both absolute and relative imports will be attempted. 0 means only
            perform absolute imports. Positive values for level indicate the
            number of parent directories to search relative to the directory of
            the module calling `__import__()`." Defaults to -1 under Python 2
            and 0 under Python 3. Since this default depends on the major
            version of the current Python interpreter, depending on this
            default can result in unpredictable and non-portable behaviour.
            Callers are strongly recommended to explicitly pass this parameter
            rather than implicitly accept this default.

        Returns
        ----------
        list
            List of the graph nodes created for all modules explicitly imported
            by this call, including the passed module and all submodules listed
            in `target_attr_names` _but_ excluding all parent packages
            implicitly imported by this call. If `target_attr_names` is either
            `None` or the empty list, this is guaranteed to be a list of one
            element: the graph node created for the passed module. As above,
            `MissingNode` instances are created for all unimportable modules.
        """
        self.msg(3, "_safe_import_hook", target_module_partname, source_module, target_attr_names, level)

        def is_swig_candidate():
            return (source_module is not None and
                    target_attr_names is None and
                    level == ABSOLUTE_IMPORT_LEVEL and
                    type(source_module) is SourceModule and
                    target_module_partname ==
                      '_' + source_module.identifier.rpartition('.')[2])

        def is_swig_wrapper(source_module):
            with open(source_module.filename, 'rb') as fp:
                contents = fp.read()
            contents = importlib.util.decode_source(contents)
            first_line = contents.splitlines()[0] if contents else ''
            self.msg(5, 'SWIG wrapper candidate first line: %r' % (first_line))
            return "automatically generated by SWIG" in first_line


        # 008962.python.modulegraph.line2079.comment List of the graph nodes created for all target modules both
        # 008963.python.modulegraph.line2080.comment imported by and returned from this call, whose:
        # 008964.python.modulegraph.line2081.comment
        # 008965.python.modulegraph.line2082.comment * First element is the graph node for the core target module
        # 008966.python.modulegraph.line2083.comment specified by the "target_module_partname" parameter.
        # 008967.python.modulegraph.line2084.comment * Remaining elements are the graph nodes for all target submodules
        # 008968.python.modulegraph.line2085.comment specified by the "target_attr_names" parameter.
        target_modules = None

        # 008969.python.modulegraph.line2088.comment True if this is a Python 2-style implicit relative import of a
        # 008970.python.modulegraph.line2089.comment SWIG-generated C extension. False if we checked and it is not SWIG.
        # 008971.python.modulegraph.line2090.comment None if we haven't checked yet.
        is_swig_import = None

        # 008972.python.modulegraph.line2093.comment Attempt to import this target module in the customary way.
        try:
            target_modules = self.import_hook(
                target_module_partname, source_module,
                target_attr_names=None, level=level, edge_attr=edge_attr)
        # 008973.python.modulegraph.line2098.comment Failing that, defer to custom module importers handling non-standard
        # 008974.python.modulegraph.line2099.comment import schemes (namely, SWIG).
        except InvalidRelativeImportError:
            self.msgout(2, "Invalid relative import", level,
                        target_module_partname, target_attr_names)
            result = []
            for sub in target_attr_names or '*':
                m = self.createNode(InvalidRelativeImport,
                                    '.' * level + target_module_partname, sub)
                self._updateReference(source_module, m, edge_data=edge_attr)
                result.append(m)
            return result
        except ImportError as msg:
            # 008975.python.modulegraph.line2111.comment If this is an absolute top-level import under Python 3 and if the
            # 008976.python.modulegraph.line2112.comment name to be imported is the caller's name prefixed by "_", this
            # 008977.python.modulegraph.line2113.comment could be a SWIG-generated Python 2-style implicit relative import.
            # 008978.python.modulegraph.line2114.comment SWIG-generated files contain functions named swig_import_helper()
            # 008979.python.modulegraph.line2115.comment importing dynamic libraries residing in the same directory. For
            # 008980.python.modulegraph.line2116.comment example, a SWIG-generated caller module "csr.py" might resemble:
            # 008981.python.modulegraph.line2117.comment
            # 008982.python.modulegraph.line2118.comment # This file was automatically generated by SWIG (http://www.swig.org).
            # 008983.python.modulegraph.line2119.comment ...
            # 008984.python.modulegraph.line2120.comment def swig_import_helper():
            # 008985.python.modulegraph.line2121.comment ...
            # 008986.python.modulegraph.line2122.comment try:
            # 008987.python.modulegraph.line2123.comment fp, pathname, description = imp.find_module('_csr',
            # 008988.python.modulegraph.line2124.comment [dirname(__file__)])
            # 008989.python.modulegraph.line2125.comment except ImportError:
            # 008990.python.modulegraph.line2126.comment import _csr
            # 008991.python.modulegraph.line2127.comment return _csr
            # 008992.python.modulegraph.line2128.comment
            # 008993.python.modulegraph.line2129.comment While there exists no reasonable means for modulegraph to parse
            # 008994.python.modulegraph.line2130.comment the call to imp.find_module(), the subsequent implicit relative
            # 008995.python.modulegraph.line2131.comment import is trivially parsable. This import is prohibited under
            # 008996.python.modulegraph.line2132.comment Python 3, however, and thus parsed only if the caller's file is
            # 008997.python.modulegraph.line2133.comment parsable plaintext (as indicated by a filetype of ".py") and the
            # 008998.python.modulegraph.line2134.comment first line of this file is the above SWIG header comment.
            # 008999.python.modulegraph.line2135.comment
            # 009000.python.modulegraph.line2136.comment The constraint that this library's name be the caller's name
            # 009001.python.modulegraph.line2137.comment prefixed by '_' is explicitly mandated by SWIG and thus a
            # 009002.python.modulegraph.line2138.comment reliable indicator of "SWIG-ness". The SWIG documentation states:
            # 009003.python.modulegraph.line2139.comment "When linking the module, the name of the output file has to match
            # 009004.python.modulegraph.line2140.comment the name of the module prefixed by an underscore."
            # 009005.python.modulegraph.line2141.comment
            # 009006.python.modulegraph.line2142.comment Only source modules (e.g., ".py"-suffixed files) are SWIG import
            # 009007.python.modulegraph.line2143.comment candidates. All other node types are safely ignorable.
            if is_swig_candidate():
                self.msg(
                    4,
                    'SWIG import candidate (name=%r, caller=%r, level=%r)' % (
                        target_module_partname, source_module, level))
                is_swig_import = is_swig_wrapper(source_module)
                if is_swig_import:
                    # 009008.python.modulegraph.line2151.comment Convert this Python 2-compliant implicit relative
                    # 009009.python.modulegraph.line2152.comment import prohibited by Python 3 into a Python
                    # 009010.python.modulegraph.line2153.comment 3-compliant explicit relative "from"-style import for
                    # 009011.python.modulegraph.line2154.comment the duration of this function call by overwriting the
                    # 009012.python.modulegraph.line2155.comment original parameters passed to this call.
                    target_attr_names = [target_module_partname]
                    target_module_partname = ''
                    level = 1
                    self.msg(2,
                             'SWIG import (caller=%r, fromlist=%r, level=%r)'
                             % (source_module, target_attr_names, level))
                    # 009013.python.modulegraph.line2162.comment Import this target SWIG C extension's package.
                    try:
                        target_modules = self.import_hook(
                            target_module_partname, source_module,
                            target_attr_names=None,
                            level=level,
                            edge_attr=edge_attr)
                    except ImportError as msg:
                        self.msg(2, "SWIG ImportError:", str(msg))

            # 009014.python.modulegraph.line2172.comment If this module remains unimportable...
            if target_modules is None:
                self.msg(2, "ImportError:", str(msg))

                # 009015.python.modulegraph.line2176.comment Add this module as a MissingModule node.
                target_module = self.createNode(
                    MissingModule,
                    _path_from_importerror(msg, target_module_partname))
                self._updateReference(
                    source_module, target_module, edge_data=edge_attr)

                # 009016.python.modulegraph.line2183.comment Initialize this list to this node.
                target_modules = [target_module]

        # 009017.python.modulegraph.line2186.comment Ensure that the above logic imported exactly one target module.
        assert len(target_modules) == 1, (
            'Expected import_hook() to'
            'return only one module but received: {}'.format(target_modules))

        # 009018.python.modulegraph.line2191.comment Target module imported above.
        target_module = target_modules[0]

        if isinstance(target_module, MissingModule) \
           and is_swig_import is None and is_swig_candidate() \
           and is_swig_wrapper(source_module):
            # 009019.python.modulegraph.line2197.comment if this possible swig C module was previously imported from
            # 009020.python.modulegraph.line2198.comment a python module other than its corresponding swig python
            # 009021.python.modulegraph.line2199.comment module, then it may have been considered a MissingModule.
            # 009022.python.modulegraph.line2200.comment Try to reimport it now. For details see pull-request #2578
            # 009023.python.modulegraph.line2201.comment and issue #1522.
            # 009024.python.modulegraph.line2202.comment
            # 009025.python.modulegraph.line2203.comment If this module was takes as a SWIG candidate above, but failed
            # 009026.python.modulegraph.line2204.comment to import, this would be a MissingModule, too. Thus check if
            # 009027.python.modulegraph.line2205.comment this was the case (is_swig_import would be not None) to avoid
            # 009028.python.modulegraph.line2206.comment recursion error. If `is_swig_import` is None and we are still a
            # 009029.python.modulegraph.line2207.comment swig candidate then that means we haven't properly imported this
            # 009030.python.modulegraph.line2208.comment swig module yet so do that below.
            # 009031.python.modulegraph.line2209.comment
            # 009032.python.modulegraph.line2210.comment Remove the MissingModule node from the graph so that we can
            # 009033.python.modulegraph.line2211.comment attempt a reimport and avoid collisions. This node should be
            # 009034.python.modulegraph.line2212.comment fine to remove because the proper module will be imported and
            # 009035.python.modulegraph.line2213.comment added to the graph in the next line (call to _safe_import_hook).
            self.removeNode(target_module)
            # 009036.python.modulegraph.line2215.comment Reimport the SWIG C module relative to the wrapper
            target_modules = self._safe_import_hook(
                target_module_partname, source_module,
                target_attr_names=None, level=1, edge_attr=edge_attr)
            # 009037.python.modulegraph.line2219.comment return the output regardless because it would just be
            # 009038.python.modulegraph.line2220.comment duplicating the processing below
            return target_modules

        if isinstance(edge_attr, DependencyInfo):
            edge_attr = edge_attr._replace(fromlist=True)

        # 009039.python.modulegraph.line2226.comment If this is a "from"-style import *AND* this target module is a
        # 009040.python.modulegraph.line2227.comment package, import all attributes listed by the "import" clause of this
        # 009041.python.modulegraph.line2228.comment import that are submodules of this package. If this target module is
        # 009042.python.modulegraph.line2229.comment *NOT* a package, these attributes are always ignorable globals (e.g.,
        # 009043.python.modulegraph.line2230.comment classes, variables) defined at the top level of this module.
        # 009044.python.modulegraph.line2231.comment
        # 009045.python.modulegraph.line2232.comment If this target module is a non-package, it could still contain
        # 009046.python.modulegraph.line2233.comment importable submodules (e.g., the non-package `os` module containing
        # 009047.python.modulegraph.line2234.comment the `os.path` submodule). In this case, these submodules are already
        # 009048.python.modulegraph.line2235.comment imported by this target module's pure-Python code. Since our import
        # 009049.python.modulegraph.line2236.comment scanner already detects these imports, these submodules need *NOT* be
        # 009050.python.modulegraph.line2237.comment reimported here. (Doing so would be harmless but inefficient.)
        if target_attr_names and isinstance(target_module,
                                            (Package, AliasNode)):
            # 009051.python.modulegraph.line2240.comment For the name of each attribute imported from this target package
            # 009052.python.modulegraph.line2241.comment into this source module...
            for target_submodule_partname in target_attr_names:
                # 009053.python.modulegraph.line2243.comment FIXME: Is this optimization *REALLY* an optimization or at all
                # 009054.python.modulegraph.line2244.comment necessary? The findNode() method called below should already
                # 009055.python.modulegraph.line2245.comment be heavily optimized, in which case this optimization here is
                # 009056.python.modulegraph.line2246.comment premature, senseless, and should be eliminated.

                # 009057.python.modulegraph.line2248.comment If this attribute is a previously imported submodule of this
                # 009058.python.modulegraph.line2249.comment target module, optimize this edge case.
                if target_module.is_submodule(target_submodule_partname):
                    # 009059.python.modulegraph.line2251.comment Graph node for this submodule.
                    target_submodule = target_module.get_submodule(
                        target_submodule_partname)

                    # 009060.python.modulegraph.line2255.comment FIXME: What? Shouldn't "target_submodule" *ALWAYS* be
                    # 009061.python.modulegraph.line2256.comment non-None here? Assert this to be non-None instead.
                    if target_submodule is not None:
                        # 009062.python.modulegraph.line2258.comment FIXME: Why does duplication matter? List searches are
                        # 009063.python.modulegraph.line2259.comment mildly expensive.

                        # 009064.python.modulegraph.line2261.comment If this submodule has not already been added to the
                        # 009065.python.modulegraph.line2262.comment list of submodules to be returned, do so.
                        if target_submodule not in target_modules:
                            self._updateReference(
                                source_module,
                                target_submodule,
                                edge_data=edge_attr)
                            target_modules.append(target_submodule)
                        continue

                # 009066.python.modulegraph.line2271.comment Fully-qualified name of this submodule.
                target_submodule_name = (
                    target_module.identifier + '.' + target_submodule_partname)

                # 009067.python.modulegraph.line2275.comment Graph node of this submodule if previously imported or None.
                target_submodule = self.find_node(target_submodule_name)

                # 009068.python.modulegraph.line2278.comment If this submodule has not been imported, do so as if this
                # 009069.python.modulegraph.line2279.comment submodule were the only attribute listed by the "import"
                # 009070.python.modulegraph.line2280.comment clause of this import (e.g., as "from foo import bar" rather
                # 009071.python.modulegraph.line2281.comment than "from foo import car, far, bar").
                if target_submodule is None:
                    # 009072.python.modulegraph.line2283.comment Attempt to import this submodule.
                    try:
                        # 009073.python.modulegraph.line2285.comment Ignore the list of graph nodes returned by this
                        # 009074.python.modulegraph.line2286.comment method. If both this submodule's package and this
                        # 009075.python.modulegraph.line2287.comment submodule are importable, this method returns a
                        # 009076.python.modulegraph.line2288.comment 2-element list whose second element is this
                        # 009077.python.modulegraph.line2289.comment submodule's graph node. However, if this submodule's
                        # 009078.python.modulegraph.line2290.comment package is importable but this submodule is not,
                        # 009079.python.modulegraph.line2291.comment this submodule is either:
                        # 009080.python.modulegraph.line2292.comment
                        # 009081.python.modulegraph.line2293.comment * An ignorable global attribute defined at the top
                        # 009082.python.modulegraph.line2294.comment level of this package's "__init__" submodule. In
                        # 009083.python.modulegraph.line2295.comment this case, this method returns a 1-element list
                        # 009084.python.modulegraph.line2296.comment without raising an exception.
                        # 009085.python.modulegraph.line2297.comment * A non-ignorable unimportable submodule. In this
                        # 009086.python.modulegraph.line2298.comment case, this method raises an "ImportError".
                        # 009087.python.modulegraph.line2299.comment
                        # 009088.python.modulegraph.line2300.comment While the first two cases are disambiguatable by the
                        # 009089.python.modulegraph.line2301.comment length of this list, doing so would render this code
                        # 009090.python.modulegraph.line2302.comment dependent on import_hook() details subject to change.
                        # 009091.python.modulegraph.line2303.comment Instead, call findNode() to decide the truthiness.
                        self.import_hook(
                            target_module_partname, source_module,
                            target_attr_names=[target_submodule_partname],
                            level=level,
                            edge_attr=edge_attr)

                        # 009092.python.modulegraph.line2310.comment Graph node of this submodule imported by the prior
                        # 009093.python.modulegraph.line2311.comment call if importable or None otherwise.
                        target_submodule = self.find_node(target_submodule_name)

                        # 009094.python.modulegraph.line2314.comment If this submodule does not exist, this *MUST* be an
                        # 009095.python.modulegraph.line2315.comment ignorable global attribute defined at the top level
                        # 009096.python.modulegraph.line2316.comment of this package's "__init__" submodule.
                        if target_submodule is None:
                            # 009097.python.modulegraph.line2318.comment Assert this to actually be the case.
                            assert target_module.is_global_attr(
                                target_submodule_partname), (
                                'No global named {} in {}.__init__'.format(
                                    target_submodule_partname,
                                    target_module.identifier))

                            # 009098.python.modulegraph.line2325.comment Skip this safely ignorable importation to the
                            # 009099.python.modulegraph.line2326.comment next attribute. See similar logic in the body of
                            # 009100.python.modulegraph.line2327.comment _import_importable_package_submodules().
                            self.msg(4, '_safe_import_hook', 'ignoring imported non-module global', target_module.identifier, target_submodule_partname)
                            continue

                        # 009101.python.modulegraph.line2331.comment If this is a SWIG C extension, instruct PyInstaller
                        # 009102.python.modulegraph.line2332.comment to freeze this extension under its unqualified rather
                        # 009103.python.modulegraph.line2333.comment than qualified name (e.g., as "_csr" rather than
                        # 009104.python.modulegraph.line2334.comment "scipy.sparse.sparsetools._csr"), permitting the
                        # 009105.python.modulegraph.line2335.comment implicit relative import in its parent SWIG module to
                        # 009106.python.modulegraph.line2336.comment successfully find this extension.
                        if is_swig_import:
                            # 009107.python.modulegraph.line2338.comment If a graph node with this name already exists,
                            # 009108.python.modulegraph.line2339.comment avoid collisions by emitting an error instead.
                            if self.find_node(target_submodule_partname):
                                self.msg(
                                    2,
                                    'SWIG import error: %r basename %r '
                                    'already exists' % (
                                        target_submodule_name,
                                        target_submodule_partname))
                            else:
                                self.msg(
                                    4,
                                    'SWIG import renamed from %r to %r' % (
                                        target_submodule_name,
                                        target_submodule_partname))
                                target_submodule.identifier = (
                                    target_submodule_partname)
                    # 009109.python.modulegraph.line2355.comment If this submodule is unimportable, add a MissingModule.
                    except ImportError as msg:
                        self.msg(2, "ImportError:", str(msg))
                        target_submodule = self.createNode(
                            MissingModule, target_submodule_name)

                # 009110.python.modulegraph.line2361.comment Add this submodule to its package.
                target_module.add_submodule(
                    target_submodule_partname, target_submodule)
                if target_submodule is not None:
                    self._updateReference(
                        target_module, target_submodule, edge_data=edge_attr)
                    self._updateReference(
                        source_module, target_submodule, edge_data=edge_attr)

                    if target_submodule not in target_modules:
                        target_modules.append(target_submodule)

        # 009111.python.modulegraph.line2373.comment Return the list of all target modules imported by this call.
        return target_modules


    def _scan_code(
        self,
        module,
        module_code_object,
        module_code_object_ast=None):
        """
        Parse and add all import statements from the passed code object of the
        passed source module to this graph, recursively.

        **This method is at the root of all `ModuleGraph` recursion.**
        Recursion begins here and ends when all import statements in all code
        objects of all modules transitively imported by the source module
        passed to the first call to this method have been added to the graph.
        Specifically, this method:

        1. If the passed `module_code_object_ast` parameter is non-`None`,
           parses all import statements from this object.
        2. Else, parses all import statements from the passed
           `module_code_object` parameter.
        1. For each such import statement:
           1. Adds to this `ModuleGraph` instance:
              1. Nodes for all target modules of these imports.
              1. Directed edges from this source module to these target
                 modules.
           2. Recursively calls this method with these target modules.

        Parameters
        ----------
        module : Node
            Graph node of the module to be parsed.
        module_code_object : PyCodeObject
            Code object providing this module's disassembled Python bytecode.
            Ignored unless `module_code_object_ast` is `None`.
        module_code_object_ast : optional[ast.AST]
            Optional abstract syntax tree (AST) of this module if any or `None`
            otherwise. Defaults to `None`, in which case the passed
            `module_code_object` is parsed instead.
        Returns
        ----------
        module : Node
            Graph node of the module to be parsed.
        """

        # 009112.python.modulegraph.line2420.comment For safety, guard against multiple scans of the same module by
        # 009113.python.modulegraph.line2421.comment resetting this module's list of deferred target imports.
        module._deferred_imports = []

        # 009114.python.modulegraph.line2424.comment Parse all imports from this module *BEFORE* adding these imports to
        # 009115.python.modulegraph.line2425.comment the graph. If an AST is provided, parse that rather than this
        # 009116.python.modulegraph.line2426.comment module's code object.
        if module_code_object_ast is not None:
            # 009117.python.modulegraph.line2428.comment Parse this module's AST for imports.
            self._scan_ast(module, module_code_object_ast)

            # 009118.python.modulegraph.line2431.comment Parse this module's code object for all relevant non-imports
            # 009119.python.modulegraph.line2432.comment (e.g., global variable declarations and undeclarations).
            self._scan_bytecode(
                module, module_code_object, is_scanning_imports=False)
        # 009120.python.modulegraph.line2435.comment Else, parse this module's code object for imports.
        else:
            self._scan_bytecode(
                module, module_code_object, is_scanning_imports=True)

        return module

    def _scan_ast(self, module, module_code_object_ast):
        """
        Parse and add all import statements from the passed abstract syntax
        tree (AST) of the passed source module to this graph, non-recursively.

        Parameters
        ----------
        module : Node
            Graph node of the module to be parsed.
        module_code_object_ast : ast.AST
            Abstract syntax tree (AST) of this module to be parsed.
        """

        visitor = _Visitor(self, module)
        visitor.visit(module_code_object_ast)

    # 009121.python.modulegraph.line2458.comment FIXME: Optimize. Global attributes added by this method are tested by
    # 009122.python.modulegraph.line2459.comment other methods *ONLY* for packages, implying this method should scan and
    # 009123.python.modulegraph.line2460.comment handle opcodes pertaining to global attributes (e.g.,
    # 009124.python.modulegraph.line2461.comment "STORE_NAME", "DELETE_GLOBAL") only if the passed "module"
    # 009125.python.modulegraph.line2462.comment object is an instance of the "Package" class. For all other module types,
    # 009126.python.modulegraph.line2463.comment these opcodes should simply be ignored.
    # 009127.python.modulegraph.line2464.comment
    # 009128.python.modulegraph.line2465.comment After doing so, the "Node._global_attr_names" attribute and all methods
    # 009129.python.modulegraph.line2466.comment using this attribute (e.g., Node.is_global()) should be moved from the
    # 009130.python.modulegraph.line2467.comment "Node" superclass to the "Package" subclass.
    def _scan_bytecode(
        self, module, module_code_object, is_scanning_imports):
        """
        Parse and add all import statements from the passed code object of the
        passed source module to this graph, non-recursively.

        This method parses all reasonably parsable operations (i.e., operations
        that are both syntactically and semantically parsable _without_
        requiring Turing-complete interpretation) directly or indirectly
        involving module importation from this code object. This includes:

        * `IMPORT_NAME`, denoting an import statement. Ignored unless
          the passed `is_scanning_imports` parameter is `True`.
        * `STORE_NAME` and `STORE_GLOBAL`, denoting the
          declaration of a global attribute (e.g., class, variable) in this
          module. This method stores each such declaration for subsequent
          lookup. While global attributes are usually irrelevant to import
          parsing, they remain the only means of distinguishing erroneous
          non-ignorable attempts to import non-existent submodules of a package
          from successful ignorable attempts to import existing global
          attributes of a package's `__init__` submodule (e.g., the `bar` in
          `from foo import bar`, which is either a non-ignorable submodule of
          `foo` or an ignorable global attribute of `foo.__init__`).
        * `DELETE_NAME` and `DELETE_GLOBAL`, denoting the
          undeclaration of a previously declared global attribute in this
          module.

        Since `ModuleGraph` is _not_ intended to replicate the behaviour of a
        full-featured Turing-complete Python interpreter, this method ignores
        operations that are _not_ reasonably parsable from this code object --
        even those directly or indirectly involving module importation. This
        includes:

        * `STORE_ATTR(namei)`, implementing `TOS.name = TOS1`. If `TOS` is the
          name of a target module currently imported into the namespace of the
          passed source module, this opcode would ideally be parsed to add that
          global attribute to that target module. Since this addition only
          conditionally occurs on the importation of this source module and
          execution of the code branch in this module performing this addition,
          however, that global _cannot_ be unconditionally added to that target
          module. In short, only Turing-complete behaviour suffices.
        * `DELETE_ATTR(namei)`, implementing `del TOS.name`. If `TOS` is the
          name of a target module currently imported into the namespace of the
          passed source module, this opcode would ideally be parsed to remove
          that global attribute from that target module. Again, however, only
          Turing-complete behaviour suffices.

        Parameters
        ----------
        module : Node
            Graph node of the module to be parsed.
        module_code_object : PyCodeObject
            Code object of the module to be parsed.
        is_scanning_imports : bool
            `True` only if this method is parsing import statements from
            `IMPORT_NAME` opcodes. If `False`, no import statements will be
            parsed. This parameter is typically:
            * `True` when parsing this module's code object for such imports.
            * `False` when parsing this module's abstract syntax tree (AST)
              (rather than code object) for such imports. In this case, that
              parsing will have already parsed import statements, which this
              parsing must avoid repeating.
        """
        level = None
        fromlist = None

        # 009131.python.modulegraph.line2534.comment 'deque' is a list-like container with fast appends, pops on
        # 009132.python.modulegraph.line2535.comment either end, and automatically discarding elements too much.
        prev_insts = deque(maxlen=2)
        for inst in util.iterate_instructions(module_code_object):
            if not inst:
                continue
            # 009133.python.modulegraph.line2540.comment If this is an import statement originating from this module,
            # 009134.python.modulegraph.line2541.comment parse this import.
            # 009135.python.modulegraph.line2542.comment
            # 009136.python.modulegraph.line2543.comment Note that the related "IMPORT_FROM" opcode need *NOT* be parsed.
            # 009137.python.modulegraph.line2544.comment "IMPORT_NAME" suffices. For further details, see
            # 009138.python.modulegraph.line2545.comment http://probablyprogramming.com/2008/04/14/python-import_name
            if inst.opname == 'IMPORT_NAME':
                # 009139.python.modulegraph.line2547.comment If this method is ignoring import statements, skip to the
                # 009140.python.modulegraph.line2548.comment next opcode.
                if not is_scanning_imports:
                    continue

                # 009141.python.modulegraph.line2552.comment Python >=2.5: LOAD_CONST flags, LOAD_CONST names, IMPORT_NAME name
                # 009142.python.modulegraph.line2553.comment
                # 009143.python.modulegraph.line2554.comment Python 3.14 split LOAD_CONST into LOAD_CONST, LOAD_CONST_IMMORTAL,
                # 009144.python.modulegraph.line2555.comment and LOAD_SMALL_INT. The former two can be used to load the names,
                # 009145.python.modulegraph.line2556.comment while LOAD_SMALL_INT can be also used to load the flags.
                if sys.version_info >= (3, 14):
                    assert prev_insts[-2].opname in {'LOAD_CONST', 'LOAD_CONST_IMMORTAL', 'LOAD_SMALL_INT'}
                    assert prev_insts[-1].opname in {'LOAD_CONST', 'LOAD_CONST_IMMORTAL'}
                else:
                    assert prev_insts[-2].opname == 'LOAD_CONST'
                    assert prev_insts[-1].opname == 'LOAD_CONST'

                level = prev_insts[-2].argval
                fromlist = prev_insts[-1].argval

                assert fromlist is None or type(fromlist) is tuple
                target_module_partname = inst.argval

                # 009146.python.modulegraph.line2570.comment FIXME: The exact same logic appears in _collect_import(),
                # 009147.python.modulegraph.line2571.comment which isn't particularly helpful. Instead, defer this logic
                # 009148.python.modulegraph.line2572.comment until later by:
                # 009149.python.modulegraph.line2573.comment
                # 009150.python.modulegraph.line2574.comment * Refactor the "_deferred_imports" list to contain 2-tuples
                # 009151.python.modulegraph.line2575.comment "(_safe_import_hook_args, _safe_import_hook_kwargs)" rather
                # 009152.python.modulegraph.line2576.comment than 3-tuples "(have_star, _safe_import_hook_args,
                # 009153.python.modulegraph.line2577.comment _safe_import_hook_kwargs)".
                # 009154.python.modulegraph.line2578.comment * Stop prepending these tuples by a "have_star" boolean both
                # 009155.python.modulegraph.line2579.comment here, in _collect_import(), and in _process_imports().
                # 009156.python.modulegraph.line2580.comment * Shift the logic below to _process_imports().
                # 009157.python.modulegraph.line2581.comment * Remove the same logic from _collect_import().
                have_star = False
                if fromlist is not None:
                    fromlist = uniq(fromlist)
                    if '*' in fromlist:
                        fromlist.remove('*')
                        have_star = True

                # 009158.python.modulegraph.line2589.comment Record this import as originating from this module for
                # 009159.python.modulegraph.line2590.comment subsequent handling by the _process_imports() method.
                module._deferred_imports.append((
                    have_star,
                    (target_module_partname, module, fromlist, level),
                    {}
                ))

            elif inst.opname in ('STORE_NAME', 'STORE_GLOBAL'):
                # 009160.python.modulegraph.line2598.comment If this is the declaration of a global attribute (e.g.,
                # 009161.python.modulegraph.line2599.comment class, variable) in this module, store this declaration for
                # 009162.python.modulegraph.line2600.comment subsequent lookup. See method docstring for further details.
                # 009163.python.modulegraph.line2601.comment
                # 009164.python.modulegraph.line2602.comment Global attributes are usually irrelevant to import parsing, but
                # 009165.python.modulegraph.line2603.comment remain the only means of distinguishing erroneous non-ignorable
                # 009166.python.modulegraph.line2604.comment attempts to import non-existent submodules of a package from
                # 009167.python.modulegraph.line2605.comment successful ignorable attempts to import existing global
                # 009168.python.modulegraph.line2606.comment attributes of a package's "__init__" submodule (e.g., the "bar"
                # 009169.python.modulegraph.line2607.comment in "from foo import bar", which is either a non-ignorable
                # 009170.python.modulegraph.line2608.comment submodule of "foo" or an ignorable global attribute of
                # 009171.python.modulegraph.line2609.comment "foo.__init__").
                name = inst.argval
                module.add_global_attr(name)

            elif inst.opname in ('DELETE_NAME', 'DELETE_GLOBAL'):
                # 009172.python.modulegraph.line2614.comment If this is the undeclaration of a previously declared global
                # 009173.python.modulegraph.line2615.comment attribute (e.g., class, variable) in this module, remove that
                # 009174.python.modulegraph.line2616.comment declaration to prevent subsequent lookup. See method docstring
                # 009175.python.modulegraph.line2617.comment for further details.
                name = inst.argval
                module.remove_global_attr_if_found(name)

            prev_insts.append(inst)


    def _process_imports(self, source_module):
        """
        Graph all target modules whose importations were previously parsed from
        the passed source module by a prior call to the `_scan_code()` method
        and methods call by that method (e.g., `_scan_ast()`,
        `_scan_bytecode()`, `_scan_bytecode_stores()`).

        Parameters
        ----------
        source_module : Node
            Graph node of the source module to graph target imports for.
        """

        # 009176.python.modulegraph.line2637.comment If this source module imported no target modules, noop.
        if not source_module._deferred_imports:
            return

        # 009177.python.modulegraph.line2641.comment For each target module imported by this source module...
        for have_star, import_info, kwargs in source_module._deferred_imports:
            # 009178.python.modulegraph.line2643.comment Graph node of the target module specified by the "from" portion
            # 009179.python.modulegraph.line2644.comment of this "from"-style star import (e.g., an import resembling
            # 009180.python.modulegraph.line2645.comment "from {target_module_name} import *") or ignored otherwise.
            target_modules = self._safe_import_hook(*import_info, **kwargs)
            if not target_modules:
                # 009181.python.modulegraph.line2648.comment If _safe_import_hook suppressed the module, quietly drop it.
                # 009182.python.modulegraph.line2649.comment Do not create an ExcludedModule instance, because that might
                # 009183.python.modulegraph.line2650.comment completely suppress the module whereas it might need to be
                # 009184.python.modulegraph.line2651.comment included due to reference from another module (that does
                # 009185.python.modulegraph.line2652.comment not exclude it via hook).
                continue
            target_module = target_modules[0]

            # 009186.python.modulegraph.line2656.comment If this is a "from"-style star import, process this import.
            if have_star:
                # 009187.python.modulegraph.line2658.comment FIXME: Sadly, the current approach to importing attributes
                # 009188.python.modulegraph.line2659.comment from "from"-style star imports is... simplistic. This should
                # 009189.python.modulegraph.line2660.comment be revised as follows. If this target module is:
                # 009190.python.modulegraph.line2661.comment
                # 009191.python.modulegraph.line2662.comment * A package:
                # 009192.python.modulegraph.line2663.comment * Whose "__init__" submodule defines the "__all__" global
                # 009193.python.modulegraph.line2664.comment attribute, only attributes listed by this attribute should
                # 009194.python.modulegraph.line2665.comment be imported.
                # 009195.python.modulegraph.line2666.comment * Else, *NO* attributes should be imported.
                # 009196.python.modulegraph.line2667.comment * A non-package:
                # 009197.python.modulegraph.line2668.comment * Defining the "__all__" global attribute, only attributes
                # 009198.python.modulegraph.line2669.comment listed by this attribute should be imported.
                # 009199.python.modulegraph.line2670.comment * Else, only public attributes whose names are *NOT*
                # 009200.python.modulegraph.line2671.comment prefixed by "_" should be imported.
                source_module.add_global_attrs_from_module(target_module)

                source_module._starimported_ignored_module_names.update(
                    target_module._starimported_ignored_module_names)

                # 009201.python.modulegraph.line2677.comment If this target module has no code object and hence is
                # 009202.python.modulegraph.line2678.comment unparsable, record its name for posterity.
                if target_module.code is None:
                    target_module_name = import_info[0]
                    source_module._starimported_ignored_module_names.add(
                        target_module_name)

        # 009203.python.modulegraph.line2684.comment For safety, prevent these imports from being reprocessed.
        source_module._deferred_imports = None


    def _find_module(self, name, path, parent=None):
        """
        3-tuple describing the physical location of the module with the passed
        name if this module is physically findable _or_ raise `ImportError`.

        This high-level method wraps the low-level `modulegraph.find_module()`
        function with additional support for graph-based module caching.

        Parameters
        ----------
        name : str
            Fully-qualified name of the Python module to be found.
        path : list
            List of the absolute paths of all directories to search for this
            module _or_ `None` if the default path list `self.path` is to be
            searched.
        parent : Node
            Package containing this module if this module is a submodule of a
            package _or_ `None` if this is a top-level module.

        Returns
        ----------
        (filename, loader)
            See `modulegraph._find_module()` for details.

        Raises
        ----------
        ImportError
            If this module is _not_ found.
        """

        if parent is not None:
            # 009204.python.modulegraph.line2720.comment assert path is not None
            fullname = parent.identifier + '.' + name
        else:
            fullname = name

        node = self.find_node(fullname)
        if node is not None:
            self.msg(3, "find_module: already included?", node)
            raise ImportError(name)

        if path is None:
            if name in sys.builtin_module_names:
                return (None, BUILTIN_MODULE)

            path = self.path

        return self._find_module_path(fullname, name, path)


    def _find_module_path(self, fullname, module_name, search_dirs):
        """
        3-tuple describing the physical location of the module with the passed
        name if this module is physically findable _or_ raise `ImportError`.

        This low-level function is a variant on the standard `imp.find_module()`
        function with additional support for:

        * Multiple search paths. The passed list of absolute paths will be
          iteratively searched for the first directory containing a file
          corresponding to this module.
        * Compressed (e.g., zipped) packages.

        For efficiency, the higher level `ModuleGraph._find_module()` method
        wraps this function with support for module caching.

        Parameters
        ----------
        module_name : str
            Fully-qualified name of the module to be found.
        search_dirs : list
            List of the absolute paths of all directories to search for this
            module (in order). Searching will halt at the first directory
            containing this module.

        Returns
        ----------
        (filename, loader)
            2-tuple describing the physical location of this module, where:
            * `filename` is the absolute path of this file.
            * `loader` is the import loader.
              In case of a namespace package, this is a NAMESPACE_PACKAGE
              instance

        Raises
        ----------
        ImportError
            If this module is _not_ found.
        """
        self.msgin(4, "_find_module_path <-", fullname, search_dirs)

        # 009205.python.modulegraph.line2780.comment Top-level 2-tuple to be returned.
        path_data = None

        # 009206.python.modulegraph.line2783.comment List of the absolute paths of all directories comprising the
        # 009207.python.modulegraph.line2784.comment namespace package to which this module belongs if any.
        namespace_dirs = []

        try:
            for search_dir in search_dirs:
                # 009208.python.modulegraph.line2789.comment PEP 302-compliant importer making loaders for this directory.
                importer = pkgutil.get_importer(search_dir)

                # 009209.python.modulegraph.line2792.comment If this directory is not importable, continue.
                if importer is None:
                    # 009210.python.modulegraph.line2794.comment self.msg(4, "_find_module_path importer not found", search_dir)
                    continue

                # 009211.python.modulegraph.line2797.comment Get the PEP 302-compliant loader object loading this module.
                # 009212.python.modulegraph.line2798.comment
                # 009213.python.modulegraph.line2799.comment If this importer defines the PEP 451-compliant find_spec()
                # 009214.python.modulegraph.line2800.comment method, use that, and obtain loader from spec. This should
                # 009215.python.modulegraph.line2801.comment be available on python >= 3.4.
                if hasattr(importer, 'find_spec'):
                    loader = None
                    spec = importer.find_spec(module_name)
                    if spec is not None:
                        loader = spec.loader
                        namespace_dirs.extend(spec.submodule_search_locations or [])
                # 009216.python.modulegraph.line2808.comment Else if this importer defines the PEP 302-compliant find_loader()
                # 009217.python.modulegraph.line2809.comment method, use that.
                elif hasattr(importer, 'find_loader'):
                    loader, loader_namespace_dirs = importer.find_loader(
                        module_name)
                    namespace_dirs.extend(loader_namespace_dirs)
                # 009218.python.modulegraph.line2814.comment Else if this importer defines the Python 2-specific
                # 009219.python.modulegraph.line2815.comment find_module() method, fall back to that. Despite the method
                # 009220.python.modulegraph.line2816.comment name, this method returns a loader rather than a module.
                elif hasattr(importer, 'find_module'):
                    loader = importer.find_module(module_name)
                # 009221.python.modulegraph.line2819.comment Else, raise an exception.
                else:
                    raise ImportError(
                        "Module %r importer %r loader unobtainable" % (module_name, importer))

                # 009222.python.modulegraph.line2824.comment If this module is not loadable from this directory, continue.
                if loader is None:
                    # 009223.python.modulegraph.line2826.comment self.msg(4, "_find_module_path loader not found", search_dir)
                    continue

                # 009224.python.modulegraph.line2829.comment Absolute path of this module. If this module resides in a
                # 009225.python.modulegraph.line2830.comment compressed archive, this is the absolute path of this module
                # 009226.python.modulegraph.line2831.comment after extracting this module from that archive and hence
                # 009227.python.modulegraph.line2832.comment should not exist; else, this path should typically exist.
                pathname = None

                # 009228.python.modulegraph.line2835.comment If this loader defines the PEP 302-compliant get_filename()
                # 009229.python.modulegraph.line2836.comment method, preferably call that method first. Most if not all
                # 009230.python.modulegraph.line2837.comment loaders (including zipimporter objects) define this method.
                if hasattr(loader, 'get_filename'):
                    pathname = loader.get_filename(module_name)
                # 009231.python.modulegraph.line2840.comment Else if this loader provides a "path" attribute, defer to that.
                elif hasattr(loader, 'path'):
                    pathname = loader.path
                # 009232.python.modulegraph.line2843.comment Else, raise an exception.
                else:
                    raise ImportError(
                        "Module %r loader %r path unobtainable" % (module_name, loader))

                # 009233.python.modulegraph.line2848.comment If no path was found, this is probably a namespace package. In
                # 009234.python.modulegraph.line2849.comment such case, continue collecting namespace directories.
                if pathname is None:
                    self.msg(4, "_find_module_path path not found", pathname)
                    continue

                # 009235.python.modulegraph.line2854.comment Return such metadata.
                path_data = (pathname, loader)
                break
            # 009236.python.modulegraph.line2857.comment Else if this is a namespace package, return such metadata.
            else:
                if namespace_dirs:
                    path_data = (namespace_dirs[0],
                                 NAMESPACE_PACKAGE(namespace_dirs))
        except UnicodeDecodeError as exc:
            self.msgout(1, "_find_module_path -> unicode error", exc)
        # 009237.python.modulegraph.line2864.comment Ensure that exceptions are logged, as this function is typically
        # 009238.python.modulegraph.line2865.comment called by the import_module() method which squelches ImportErrors.
        except Exception as exc:
            self.msgout(4, "_find_module_path -> exception", exc)
            raise

        # 009239.python.modulegraph.line2870.comment If this module was not found, raise an exception.
        self.msgout(4, "_find_module_path ->", path_data)
        if path_data is None:
            raise ImportError("No module named " + repr(module_name))

        return path_data


    def create_xref(self, out=None):
        global header, footer, entry, contpl, contpl_linked, imports
        if out is None:
            out = sys.stdout
        scripts = []
        mods = []
        for mod in self.iter_graph():
            name = os.path.basename(mod.graphident)
            if isinstance(mod, Script):
                scripts.append((name, mod))
            else:
                mods.append((name, mod))
        scripts.sort()
        mods.sort()
        scriptnames = [sn for sn, m in scripts]
        scripts.extend(mods)
        mods = scripts

        title = "modulegraph cross reference for " + ', '.join(scriptnames)
        print(header % {"TITLE": title}, file=out)

        def sorted_namelist(mods):
            lst = [os.path.basename(mod.graphident) for mod in mods if mod]
            lst.sort()
            return lst
        for name, m in mods:
            content = ""
            if isinstance(m, BuiltinModule):
                content = contpl % {"NAME": name,
                                    "TYPE": "<i>(builtin module)</i>"}
            elif isinstance(m, Extension):
                content = contpl % {"NAME": name,
                                    "TYPE": "<tt>%s</tt>" % m.filename}
            else:
                url = urllib.request.pathname2url(m.filename or "")
                content = contpl_linked % {"NAME": name, "URL": url,
                                           'TYPE': m.__class__.__name__}
            oute, ince = map(sorted_namelist, self.get_edges(m))
            if oute:
                links = []
                for n in oute:
                    links.append("""  <a href="#%s">%s</a>\n""" % (n, n))
                # 009240.python.modulegraph.line2920.comment #8226 = bullet-point; can't use html-entities since the
                # 009241.python.modulegraph.line2921.comment test-suite uses xml.etree.ElementTree.XMLParser, which
                # 009242.python.modulegraph.line2922.comment does't supprot them.
                links = " &#8226; ".join(links)
                content += imports % {"HEAD": "imports", "LINKS": links}
            if ince:
                links = []
                for n in ince:
                    links.append("""  <a href="#%s">%s</a>\n""" % (n, n))
                # 009243.python.modulegraph.line2929.comment #8226 = bullet-point; can't use html-entities since the
                # 009244.python.modulegraph.line2930.comment test-suite uses xml.etree.ElementTree.XMLParser, which
                # 009245.python.modulegraph.line2931.comment does't supprot them.
                links = " &#8226; ".join(links)
                content += imports % {"HEAD": "imported by", "LINKS": links}
            print(entry % {"NAME": name, "CONTENT": content}, file=out)
        print(footer, file=out)

    def itergraphreport(self, name='G', flatpackages=()):
        # 009246.python.modulegraph.line2938.comment XXX: Can this be implemented using Dot()?
        nodes = list(map(self.graph.describe_node, self.graph.iterdfs(self)))
        describe_edge = self.graph.describe_edge
        edges = deque()
        packagenodes = set()
        packageidents = {}
        nodetoident = {}
        inpackages = {}
        mainedges = set()

        # 009247.python.modulegraph.line2948.comment XXX - implement
        flatpackages = dict(flatpackages)

        def nodevisitor(node, data, outgoing, incoming):
            if not isinstance(data, Node):
                return {'label': str(node)}
            # 009248.python.modulegraph.line2954.comment if isinstance(d, (ExcludedModule, MissingModule, BadModule)):
            # 009249.python.modulegraph.line2955.comment return None
            s = '<f0> ' + type(data).__name__
            for i, v in enumerate(data.infoTuple()[:1], 1):
                s += '| <f%d> %s' % (i, v)
            return {'label': s, 'shape': 'record'}


        def edgevisitor(edge, data, head, tail):
            # 009250.python.modulegraph.line2963.comment XXX: This method nonsense, the edge
            # 009251.python.modulegraph.line2964.comment data is never initialized.
            if data == 'orphan':
                return {'style': 'dashed'}
            elif data == 'pkgref':
                return {'style': 'dotted'}
            return {}

        yield 'digraph %s {\ncharset="UTF-8";\n' % (name,)
        attr = dict(rankdir='LR', concentrate='true')
        cpatt = '%s="%s"'
        for item in attr.items():
            yield '\t%s;\n' % (cpatt % item,)

        # 009252.python.modulegraph.line2977.comment find all packages (subgraphs)
        for (node, data, outgoing, incoming) in nodes:
            nodetoident[node] = getattr(data, 'graphident', None)
            if isinstance(data, Package):
                packageidents[data.graphident] = node
                inpackages[node] = set([node])
                packagenodes.add(node)

        # 009253.python.modulegraph.line2985.comment create sets for subgraph, write out descriptions
        for (node, data, outgoing, incoming) in nodes:
            # 009254.python.modulegraph.line2987.comment update edges
            for edge in (describe_edge(e) for e in outgoing):
                edges.append(edge)

            # 009255.python.modulegraph.line2991.comment describe node
            yield '\t"%s" [%s];\n' % (
                node,
                ','.join([
                    (cpatt % item) for item in
                    nodevisitor(node, data, outgoing, incoming).items()
                ]),
            )

            inside = inpackages.get(node)
            if inside is None:
                inside = inpackages[node] = set()
            ident = nodetoident[node]
            if ident is None:
                continue
            pkgnode = packageidents.get(ident[:ident.rfind('.')])
            if pkgnode is not None:
                inside.add(pkgnode)

        graph = []
        subgraphs = {}
        for key in packagenodes:
            subgraphs[key] = []

        while edges:
            edge, data, head, tail = edges.popleft()
            if ((head, tail)) in mainedges:
                continue
            mainedges.add((head, tail))
            tailpkgs = inpackages[tail]
            common = inpackages[head] & tailpkgs
            if not common and tailpkgs:
                usepkgs = sorted(tailpkgs)
                if len(usepkgs) != 1 or usepkgs[0] != tail:
                    edges.append((edge, data, head, usepkgs[0]))
                    edges.append((edge, 'pkgref', usepkgs[-1], tail))
                    continue
            if common:
                common = common.pop()
                if tail == common:
                    edges.append((edge, data, tail, head))
                elif head == common:
                    subgraphs[common].append((edge, 'pkgref', head, tail))
                else:
                    edges.append((edge, data, common, head))
                    edges.append((edge, data, common, tail))

            else:
                graph.append((edge, data, head, tail))

        def do_graph(edges, tabs):
            edgestr = tabs + '"%s" -> "%s" [%s];\n'
            # 009256.python.modulegraph.line3043.comment describe edge
            for (edge, data, head, tail) in edges:
                attribs = edgevisitor(edge, data, head, tail)
                yield edgestr % (
                    head,
                    tail,
                    ','.join([(cpatt % item) for item in attribs.items()]),
                )

        for g, edges in subgraphs.items():
            yield '\tsubgraph "cluster_%s" {\n' % (g,)
            yield '\t\tlabel="%s";\n' % (nodetoident[g],)
            for s in do_graph(edges, '\t\t'):
                yield s
            yield '\t}\n'

        for s in do_graph(graph, '\t'):
            yield s

        yield '}\n'

    def graphreport(self, fileobj=None, flatpackages=()):
        if fileobj is None:
            fileobj = sys.stdout
        fileobj.writelines(self.itergraphreport(flatpackages=flatpackages))

    def report(self):
        """Print a report to stdout, listing the found modules with their
        paths, as well as modules that are missing, or seem to be missing.
        """
        print()
        print("%-15s %-25s %s" % ("Class", "Name", "File"))
        print("%-15s %-25s %s" % ("-----", "----", "----"))
        for m in sorted(self.iter_graph(), key=lambda n: n.graphident):
            if isinstance(m, AliasNode):
                print("%-15s %-25s %s" % (type(m).__name__, m.graphident, m.identifier))
            else:
                print("%-15s %-25s %s" % (type(m).__name__, m.graphident, m.filename or ""))

    def _replace_paths_in_code(self, co):
        new_filename = original_filename = os.path.normpath(co.co_filename)
        for f, r in self.replace_paths:
            f = os.path.join(f, '')
            r = os.path.join(r, '')
            if original_filename.startswith(f):
                new_filename = r + original_filename[len(f):]
                break

        else:
            return co

        consts = list(co.co_consts)
        for i in range(len(consts)):
            if isinstance(consts[i], type(co)):
                consts[i] = self._replace_paths_in_code(consts[i])

        return co.replace(co_consts=tuple(consts), co_filename=new_filename)
