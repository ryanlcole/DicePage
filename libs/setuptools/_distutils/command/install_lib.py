"""distutils.command.install_lib

Implements the Distutils 'install_lib' command
(install all Python modules)."""

from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, ClassVar

from ..core import Command
from ..errors import DistutilsOptionError

# 039878.python.install_lib.line16.comment Extension for Python source files.
PYTHON_SOURCE_EXTENSION = ".py"


class install_lib(Command):
    description = "install all Python modules (extensions and pure Python)"

    # 039879.python.install_lib.line23.comment The byte-compilation options are a tad confusing.  Here are the
    # 039880.python.install_lib.line24.comment possible scenarios:
    # 039881.python.install_lib.line25.comment 1) no compilation at all (--no-compile --no-optimize)
    # 039882.python.install_lib.line26.comment 2) compile .pyc only (--compile --no-optimize; default)
    # 039883.python.install_lib.line27.comment 3) compile .pyc and "opt-1" .pyc (--compile --optimize)
    # 039884.python.install_lib.line28.comment 4) compile "opt-1" .pyc only (--no-compile --optimize)
    # 039885.python.install_lib.line29.comment 5) compile .pyc and "opt-2" .pyc (--compile --optimize-more)
    # 039886.python.install_lib.line30.comment 6) compile "opt-2" .pyc only (--no-compile --optimize-more)
    # 039887.python.install_lib.line31.comment
    # 039888.python.install_lib.line32.comment The UI for this is two options, 'compile' and 'optimize'.
    # 039889.python.install_lib.line33.comment 'compile' is strictly boolean, and only decides whether to
    # 039890.python.install_lib.line34.comment generate .pyc files.  'optimize' is three-way (0, 1, or 2), and
    # 039891.python.install_lib.line35.comment decides both whether to generate .pyc files and what level of
    # 039892.python.install_lib.line36.comment optimization to use.

    user_options = [
        ('install-dir=', 'd', "directory to install to"),
        ('build-dir=', 'b', "build directory (where to install from)"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ('compile', 'c', "compile .py to .pyc [default]"),
        ('no-compile', None, "don't compile .py files"),
        (
            'optimize=',
            'O',
            "also compile with optimization: -O1 for \"python -O\", "
            "-O2 for \"python -OO\", and -O0 to disable [default: -O0]",
        ),
        ('skip-build', None, "skip the build steps"),
    ]

    boolean_options: ClassVar[list[str]] = ['force', 'compile', 'skip-build']
    negative_opt: ClassVar[dict[str, str]] = {'no-compile': 'compile'}

    def initialize_options(self):
        # 039893.python.install_lib.line57.comment let the 'install' command dictate our installation directory
        self.install_dir = None
        self.build_dir = None
        self.force = False
        self.compile = None
        self.optimize = None
        self.skip_build = None

    def finalize_options(self) -> None:
        # 039894.python.install_lib.line66.comment Get all the information we need to install pure Python modules
        # 039895.python.install_lib.line67.comment from the umbrella 'install' command -- build (source) directory,
        # 039896.python.install_lib.line68.comment install (target) directory, and whether to compile .py files.
        self.set_undefined_options(
            'install',
            ('build_lib', 'build_dir'),
            ('install_lib', 'install_dir'),
            ('force', 'force'),
            ('compile', 'compile'),
            ('optimize', 'optimize'),
            ('skip_build', 'skip_build'),
        )

        if self.compile is None:
            self.compile = True
        if self.optimize is None:
            self.optimize = False

        if not isinstance(self.optimize, int):
            try:
                self.optimize = int(self.optimize)
            except ValueError:
                pass
            if self.optimize not in (0, 1, 2):
                raise DistutilsOptionError("optimize must be 0, 1, or 2")

    def run(self) -> None:
        # 039897.python.install_lib.line93.comment Make sure we have built everything we need first
        self.build()

        # 039898.python.install_lib.line96.comment Install everything: simply dump the entire contents of the build
        # 039899.python.install_lib.line97.comment directory to the installation directory (that's the beauty of
        # 039900.python.install_lib.line98.comment having a build directory!)
        outfiles = self.install()

        # 039901.python.install_lib.line101.comment (Optionally) compile .py to .pyc
        if outfiles is not None and self.distribution.has_pure_modules():
            self.byte_compile(outfiles)

    # 039902.python.install_lib.line105.comment -- Top-level worker functions ------------------------------------
    # 039903.python.install_lib.line106.comment (called from 'run()')

    def build(self) -> None:
        if not self.skip_build:
            if self.distribution.has_pure_modules():
                self.run_command('build_py')
            if self.distribution.has_ext_modules():
                self.run_command('build_ext')

    # 039904.python.install_lib.line115.comment Any: https://typing.readthedocs.io/en/latest/guides/writing_stubs.html#the-any-trick
    def install(self) -> list[str] | Any:
        if os.path.isdir(self.build_dir):
            outfiles = self.copy_tree(self.build_dir, self.install_dir)
        else:
            self.warn(
                f"'{self.build_dir}' does not exist -- no Python modules to install"
            )
            return
        return outfiles

    def byte_compile(self, files) -> None:
        if sys.dont_write_bytecode:
            self.warn('byte-compiling is disabled, skipping.')
            return

        from ..util import byte_compile

        # 039905.python.install_lib.line133.comment Get the "--root" directory supplied to the "install" command,
        # 039906.python.install_lib.line134.comment and use it as a prefix to strip off the purported filename
        # 039907.python.install_lib.line135.comment encoded in bytecode files.  This is far from complete, but it
        # 039908.python.install_lib.line136.comment should at least generate usable bytecode in RPM distributions.
        install_root = self.get_finalized_command('install').root

        if self.compile:
            byte_compile(
                files,
                optimize=0,
                force=self.force,
                prefix=install_root,
                dry_run=self.dry_run,
            )
        if self.optimize > 0:
            byte_compile(
                files,
                optimize=self.optimize,
                force=self.force,
                prefix=install_root,
                verbose=self.verbose,
                dry_run=self.dry_run,
            )

    # 039909.python.install_lib.line157.comment -- Utility methods -----------------------------------------------

    def _mutate_outputs(self, has_any, build_cmd, cmd_option, output_dir):
        if not has_any:
            return []

        build_cmd = self.get_finalized_command(build_cmd)
        build_files = build_cmd.get_outputs()
        build_dir = getattr(build_cmd, cmd_option)

        prefix_len = len(build_dir) + len(os.sep)
        outputs = [os.path.join(output_dir, file[prefix_len:]) for file in build_files]

        return outputs

    def _bytecode_filenames(self, py_filenames):
        bytecode_files = []
        for py_file in py_filenames:
            # 039910.python.install_lib.line175.comment Since build_py handles package data installation, the
            # 039911.python.install_lib.line176.comment list of outputs can contain more than just .py files.
            # 039912.python.install_lib.line177.comment Make sure we only report bytecode for the .py files.
            ext = os.path.splitext(os.path.normcase(py_file))[1]
            if ext != PYTHON_SOURCE_EXTENSION:
                continue
            if self.compile:
                bytecode_files.append(
                    importlib.util.cache_from_source(py_file, optimization='')
                )
            if self.optimize > 0:
                bytecode_files.append(
                    importlib.util.cache_from_source(
                        py_file, optimization=self.optimize
                    )
                )

        return bytecode_files

    # 039913.python.install_lib.line194.comment -- External interface --------------------------------------------
    # 039914.python.install_lib.line195.comment (called by outsiders)

    def get_outputs(self):
        """Return the list of files that would be installed if this command
        were actually run.  Not affected by the "dry-run" flag or whether
        modules have actually been built yet.
        """
        pure_outputs = self._mutate_outputs(
            self.distribution.has_pure_modules(),
            'build_py',
            'build_lib',
            self.install_dir,
        )
        if self.compile:
            bytecode_outputs = self._bytecode_filenames(pure_outputs)
        else:
            bytecode_outputs = []

        ext_outputs = self._mutate_outputs(
            self.distribution.has_ext_modules(),
            'build_ext',
            'build_lib',
            self.install_dir,
        )

        return pure_outputs + bytecode_outputs + ext_outputs

    def get_inputs(self):
        """Get the list of files that are input to this command, ie. the
        files that get installed as they are named in the build tree.
        The files in this list correspond one-to-one to the output
        filenames returned by 'get_outputs()'.
        """
        inputs = []

        if self.distribution.has_pure_modules():
            build_py = self.get_finalized_command('build_py')
            inputs.extend(build_py.get_outputs())

        if self.distribution.has_ext_modules():
            build_ext = self.get_finalized_command('build_ext')
            inputs.extend(build_ext.get_outputs())

        return inputs
