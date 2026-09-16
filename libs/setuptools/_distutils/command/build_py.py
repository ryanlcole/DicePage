"""distutils.command.build_py

Implements the Distutils 'build_py' command."""

import glob
import importlib.util
import os
import sys
from distutils._log import log
from typing import ClassVar

from ..core import Command
from ..errors import DistutilsFileError, DistutilsOptionError
from ..util import convert_path


class build_py(Command):
    description = "\"build\" pure Python modules (copy to build directory)"

    user_options = [
        ('build-lib=', 'd', "directory to \"build\" (copy) to"),
        ('compile', 'c', "compile .py to .pyc"),
        ('no-compile', None, "don't compile .py files [default]"),
        (
            'optimize=',
            'O',
            "also compile with optimization: -O1 for \"python -O\", "
            "-O2 for \"python -OO\", and -O0 to disable [default: -O0]",
        ),
        ('force', 'f', "forcibly build everything (ignore file timestamps)"),
    ]

    boolean_options: ClassVar[list[str]] = ['compile', 'force']
    negative_opt: ClassVar[dict[str, str]] = {'no-compile': 'compile'}

    def initialize_options(self):
        self.build_lib = None
        self.py_modules = None
        self.package = None
        self.package_data = None
        self.package_dir = None
        self.compile = False
        self.optimize = 0
        self.force = None

    def finalize_options(self) -> None:
        self.set_undefined_options(
            'build', ('build_lib', 'build_lib'), ('force', 'force')
        )

        # 039616.python.build_py.line51.comment Get the distribution options that are aliases for build_py
        # 039617.python.build_py.line52.comment options -- list of packages and list of modules.
        self.packages = self.distribution.packages
        self.py_modules = self.distribution.py_modules
        self.package_data = self.distribution.package_data
        self.package_dir = {}
        if self.distribution.package_dir:
            for name, path in self.distribution.package_dir.items():
                self.package_dir[name] = convert_path(path)
        self.data_files = self.get_data_files()

        # 039618.python.build_py.line62.comment Ick, copied straight from install_lib.py (fancy_getopt needs a
        # 039619.python.build_py.line63.comment type system!  Hell, *everything* needs a type system!!!)
        if not isinstance(self.optimize, int):
            try:
                self.optimize = int(self.optimize)
                assert 0 <= self.optimize <= 2
            except (ValueError, AssertionError):
                raise DistutilsOptionError("optimize must be 0, 1, or 2")

    def run(self) -> None:
        # 039620.python.build_py.line72.comment XXX copy_file by default preserves atime and mtime.  IMHO this is
        # 039621.python.build_py.line73.comment the right thing to do, but perhaps it should be an option -- in
        # 039622.python.build_py.line74.comment particular, a site administrator might want installed files to
        # 039623.python.build_py.line75.comment reflect the time of installation rather than the last
        # 039624.python.build_py.line76.comment modification time before the installed release.

        # 039625.python.build_py.line78.comment XXX copy_file by default preserves mode, which appears to be the
        # 039626.python.build_py.line79.comment wrong thing to do: if a file is read-only in the working
        # 039627.python.build_py.line80.comment directory, we want it to be installed read/write so that the next
        # 039628.python.build_py.line81.comment installation of the same module distribution can overwrite it
        # 039629.python.build_py.line82.comment without problems.  (This might be a Unix-specific issue.)  Thus
        # 039630.python.build_py.line83.comment we turn off 'preserve_mode' when copying to the build directory,
        # 039631.python.build_py.line84.comment since the build directory is supposed to be exactly what the
        # 039632.python.build_py.line85.comment installation will look like (ie. we preserve mode when
        # 039633.python.build_py.line86.comment installing).

        # 039634.python.build_py.line88.comment Two options control which modules will be installed: 'packages'
        # 039635.python.build_py.line89.comment and 'py_modules'.  The former lets us work with whole packages, not
        # 039636.python.build_py.line90.comment specifying individual modules at all; the latter is for
        # 039637.python.build_py.line91.comment specifying modules one-at-a-time.

        if self.py_modules:
            self.build_modules()
        if self.packages:
            self.build_packages()
            self.build_package_data()

        self.byte_compile(self.get_outputs(include_bytecode=False))

    def get_data_files(self):
        """Generate list of '(package,src_dir,build_dir,filenames)' tuples"""
        data = []
        if not self.packages:
            return data
        for package in self.packages:
            # 039638.python.build_py.line107.comment Locate package source directory
            src_dir = self.get_package_dir(package)

            # 039639.python.build_py.line110.comment Compute package build directory
            build_dir = os.path.join(*([self.build_lib] + package.split('.')))

            # 039640.python.build_py.line113.comment Length of path to strip from found files
            plen = 0
            if src_dir:
                plen = len(src_dir) + 1

            # 039641.python.build_py.line118.comment Strip directory from globbed filenames
            filenames = [file[plen:] for file in self.find_data_files(package, src_dir)]
            data.append((package, src_dir, build_dir, filenames))
        return data

    def find_data_files(self, package, src_dir):
        """Return filenames for package's data files in 'src_dir'"""
        globs = self.package_data.get('', []) + self.package_data.get(package, [])
        files = []
        for pattern in globs:
            # 039642.python.build_py.line128.comment Each pattern has to be converted to a platform-specific path
            filelist = glob.glob(
                os.path.join(glob.escape(src_dir), convert_path(pattern))
            )
            # 039643.python.build_py.line132.comment Files that match more than one pattern are only added once
            files.extend([
                fn for fn in filelist if fn not in files and os.path.isfile(fn)
            ])
        return files

    def build_package_data(self) -> None:
        """Copy data files into build directory"""
        for _package, src_dir, build_dir, filenames in self.data_files:
            for filename in filenames:
                target = os.path.join(build_dir, filename)
                self.mkpath(os.path.dirname(target))
                self.copy_file(
                    os.path.join(src_dir, filename), target, preserve_mode=False
                )

    def get_package_dir(self, package):
        """Return the directory, relative to the top of the source
        distribution, where package 'package' should be found
        (at least according to the 'package_dir' option, if any)."""
        path = package.split('.')

        if not self.package_dir:
            if path:
                return os.path.join(*path)
            else:
                return ''
        else:
            tail = []
            while path:
                try:
                    pdir = self.package_dir['.'.join(path)]
                except KeyError:
                    tail.insert(0, path[-1])
                    del path[-1]
                else:
                    tail.insert(0, pdir)
                    return os.path.join(*tail)
            else:
                # 039644.python.build_py.line171.comment Oops, got all the way through 'path' without finding a
                # 039645.python.build_py.line172.comment match in package_dir.  If package_dir defines a directory
                # 039646.python.build_py.line173.comment for the root (nameless) package, then fallback on it;
                # 039647.python.build_py.line174.comment otherwise, we might as well have not consulted
                # 039648.python.build_py.line175.comment package_dir at all, as we just use the directory implied
                # 039649.python.build_py.line176.comment by 'tail' (which should be the same as the original value
                # 039650.python.build_py.line177.comment of 'path' at this point).
                pdir = self.package_dir.get('')
                if pdir is not None:
                    tail.insert(0, pdir)

                if tail:
                    return os.path.join(*tail)
                else:
                    return ''

    def check_package(self, package, package_dir):
        # 039651.python.build_py.line188.comment Empty dir name means current directory, which we can probably
        # 039652.python.build_py.line189.comment assume exists.  Also, os.path.exists and isdir don't know about
        # 039653.python.build_py.line190.comment my "empty string means current dir" convention, so we have to
        # 039654.python.build_py.line191.comment circumvent them.
        if package_dir != "":
            if not os.path.exists(package_dir):
                raise DistutilsFileError(
                    f"package directory '{package_dir}' does not exist"
                )
            if not os.path.isdir(package_dir):
                raise DistutilsFileError(
                    f"supposed package directory '{package_dir}' exists, "
                    "but is not a directory"
                )

        # 039655.python.build_py.line203.comment Directories without __init__.py are namespace packages (PEP 420).
        if package:
            init_py = os.path.join(package_dir, "__init__.py")
            if os.path.isfile(init_py):
                return init_py

        # 039656.python.build_py.line209.comment Either not in a package at all (__init__.py not expected), or
        # 039657.python.build_py.line210.comment __init__.py doesn't exist -- so don't return the filename.
        return None

    def check_module(self, module, module_file):
        if not os.path.isfile(module_file):
            log.warning("file %s (for module %s) not found", module_file, module)
            return False
        else:
            return True

    def find_package_modules(self, package, package_dir):
        self.check_package(package, package_dir)
        module_files = glob.glob(os.path.join(glob.escape(package_dir), "*.py"))
        modules = []
        setup_script = os.path.abspath(self.distribution.script_name)

        for f in module_files:
            abs_f = os.path.abspath(f)
            if abs_f != setup_script:
                module = os.path.splitext(os.path.basename(f))[0]
                modules.append((package, module, f))
            else:
                self.debug_print(f"excluding {setup_script}")
        return modules

    def find_modules(self):
        """Finds individually-specified Python modules, ie. those listed by
        module name in 'self.py_modules'.  Returns a list of tuples (package,
        module_base, filename): 'package' is a tuple of the path through
        package-space to the module; 'module_base' is the bare (no
        packages, no dots) module name, and 'filename' is the path to the
        ".py" file (relative to the distribution root) that implements the
        module.
        """
        # 039658.python.build_py.line244.comment Map package names to tuples of useful info about the package:
        # 039659.python.build_py.line245.comment (package_dir, checked)
        # 039660.python.build_py.line246.comment package_dir - the directory where we'll find source files for
        # 039661.python.build_py.line247.comment this package
        # 039662.python.build_py.line248.comment checked - true if we have checked that the package directory
        # 039663.python.build_py.line249.comment is valid (exists, contains __init__.py, ... ?)
        packages = {}

        # 039664.python.build_py.line252.comment List of (package, module, filename) tuples to return
        modules = []

        # 039665.python.build_py.line255.comment We treat modules-in-packages almost the same as toplevel modules,
        # 039666.python.build_py.line256.comment just the "package" for a toplevel is empty (either an empty
        # 039667.python.build_py.line257.comment string or empty list, depending on context).  Differences:
        # 039668.python.build_py.line258.comment - don't check for __init__.py in directory for empty package
        for module in self.py_modules:
            path = module.split('.')
            package = '.'.join(path[0:-1])
            module_base = path[-1]

            try:
                (package_dir, checked) = packages[package]
            except KeyError:
                package_dir = self.get_package_dir(package)
                checked = False

            if not checked:
                init_py = self.check_package(package, package_dir)
                packages[package] = (package_dir, 1)
                if init_py:
                    modules.append((package, "__init__", init_py))

            # 039669.python.build_py.line276.comment XXX perhaps we should also check for just .pyc files
            # 039670.python.build_py.line277.comment (so greedy closed-source bastards can distribute Python
            # 039671.python.build_py.line278.comment modules too)
            module_file = os.path.join(package_dir, module_base + ".py")
            if not self.check_module(module, module_file):
                continue

            modules.append((package, module_base, module_file))

        return modules

    def find_all_modules(self):
        """Compute the list of all modules that will be built, whether
        they are specified one-module-at-a-time ('self.py_modules') or
        by whole packages ('self.packages').  Return a list of tuples
        (package, module, module_file), just like 'find_modules()' and
        'find_package_modules()' do."""
        modules = []
        if self.py_modules:
            modules.extend(self.find_modules())
        if self.packages:
            for package in self.packages:
                package_dir = self.get_package_dir(package)
                m = self.find_package_modules(package, package_dir)
                modules.extend(m)
        return modules

    def get_source_files(self):
        return [module[-1] for module in self.find_all_modules()]

    def get_module_outfile(self, build_dir, package, module):
        outfile_path = [build_dir] + list(package) + [module + ".py"]
        return os.path.join(*outfile_path)

    def get_outputs(self, include_bytecode: bool = True) -> list[str]:
        modules = self.find_all_modules()
        outputs = []
        for package, module, _module_file in modules:
            package = package.split('.')
            filename = self.get_module_outfile(self.build_lib, package, module)
            outputs.append(filename)
            if include_bytecode:
                if self.compile:
                    outputs.append(
                        importlib.util.cache_from_source(filename, optimization='')
                    )
                if self.optimize > 0:
                    outputs.append(
                        importlib.util.cache_from_source(
                            filename, optimization=self.optimize
                        )
                    )

        outputs += [
            os.path.join(build_dir, filename)
            for package, src_dir, build_dir, filenames in self.data_files
            for filename in filenames
        ]

        return outputs

    def build_module(self, module, module_file, package):
        if isinstance(package, str):
            package = package.split('.')
        elif not isinstance(package, (list, tuple)):
            raise TypeError(
                "'package' must be a string (dot-separated), list, or tuple"
            )

        # 039672.python.build_py.line345.comment Now put the module source file into the "build" area -- this is
        # 039673.python.build_py.line346.comment easy, we just copy it somewhere under self.build_lib (the build
        # 039674.python.build_py.line347.comment directory for Python source).
        outfile = self.get_module_outfile(self.build_lib, package, module)
        dir = os.path.dirname(outfile)
        self.mkpath(dir)
        return self.copy_file(module_file, outfile, preserve_mode=False)

    def build_modules(self) -> None:
        modules = self.find_modules()
        for package, module, module_file in modules:
            # 039675.python.build_py.line356.comment Now "build" the module -- ie. copy the source file to
            # 039676.python.build_py.line357.comment self.build_lib (the build directory for Python source).
            # 039677.python.build_py.line358.comment (Actually, it gets copied to the directory for this package
            # 039678.python.build_py.line359.comment under self.build_lib.)
            self.build_module(module, module_file, package)

    def build_packages(self) -> None:
        for package in self.packages:
            # 039679.python.build_py.line364.comment Get list of (package, module, module_file) tuples based on
            # 039680.python.build_py.line365.comment scanning the package directory.  'package' is only included
            # 039681.python.build_py.line366.comment in the tuple so that 'find_modules()' and
            # 039682.python.build_py.line367.comment 'find_package_tuples()' have a consistent interface; it's
            # 039683.python.build_py.line368.comment ignored here (apart from a sanity check).  Also, 'module' is
            # 039684.python.build_py.line369.comment the *unqualified* module name (ie. no dots, no package -- we
            # 039685.python.build_py.line370.comment already know its package!), and 'module_file' is the path to
            # 039686.python.build_py.line371.comment the .py file, relative to the current directory
            # 039687.python.build_py.line372.comment (ie. including 'package_dir').
            package_dir = self.get_package_dir(package)
            modules = self.find_package_modules(package, package_dir)

            # 039688.python.build_py.line376.comment Now loop over the modules we found, "building" each one (just
            # 039689.python.build_py.line377.comment copy it to self.build_lib).
            for package_, module, module_file in modules:
                assert package == package_
                self.build_module(module, module_file, package)

    def byte_compile(self, files) -> None:
        if sys.dont_write_bytecode:
            self.warn('byte-compiling is disabled, skipping.')
            return

        from ..util import byte_compile

        prefix = self.build_lib
        if prefix[-1] != os.sep:
            prefix = prefix + os.sep

        # 039690.python.build_py.line393.comment XXX this code is essentially the same as the 'byte_compile()
        # 039691.python.build_py.line394.comment method of the "install_lib" command, except for the determination
        # 039692.python.build_py.line395.comment of the 'prefix' string.  Hmmm.
        if self.compile:
            byte_compile(
                files, optimize=0, force=self.force, prefix=prefix, dry_run=self.dry_run
            )
        if self.optimize > 0:
            byte_compile(
                files,
                optimize=self.optimize,
                force=self.force,
                prefix=prefix,
                dry_run=self.dry_run,
            )
