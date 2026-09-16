from ..dist import Distribution
from ..modified import newer_pairwise_group

import distutils.command.build_clib as orig
from distutils import log
from distutils.errors import DistutilsSetupError


class build_clib(orig.build_clib):
    """
    Override the default build_clib behaviour to do the following:

    1. Implement a rudimentary timestamp-based dependency system
       so 'compile()' doesn't run every time.
    2. Add more keys to the 'build_info' dictionary:
        * obj_deps - specify dependencies for each object compiled.
                     this should be a dictionary mapping a key
                     with the source filename to a list of
                     dependencies. Use an empty string for global
                     dependencies.
        * cflags   - specify a list of additional flags to pass to
                     the compiler.
    """

    distribution: Distribution  # override distutils.dist.Distribution with setuptools.dist.Distribution

    def build_libraries(self, libraries) -> None:
        for lib_name, build_info in libraries:
            sources = build_info.get('sources')
            if sources is None or not isinstance(sources, (list, tuple)):
                raise DistutilsSetupError(
                    f"in 'libraries' option (library '{lib_name}'), "
                    "'sources' must be present and must be "
                    "a list of source filenames"
                )
            sources = sorted(list(sources))

            log.info("building '%s' library", lib_name)

            # 044375.python.build_clib.line40.comment Make sure everything is the correct type.
            # 044376.python.build_clib.line41.comment obj_deps should be a dictionary of keys as sources
            # 044377.python.build_clib.line42.comment and a list/tuple of files that are its dependencies.
            obj_deps = build_info.get('obj_deps', dict())
            if not isinstance(obj_deps, dict):
                raise DistutilsSetupError(
                    f"in 'libraries' option (library '{lib_name}'), "
                    "'obj_deps' must be a dictionary of "
                    "type 'source: list'"
                )
            dependencies = []

            # 044378.python.build_clib.line52.comment Get the global dependencies that are specified by the '' key.
            # 044379.python.build_clib.line53.comment These will go into every source's dependency list.
            global_deps = obj_deps.get('', list())
            if not isinstance(global_deps, (list, tuple)):
                raise DistutilsSetupError(
                    f"in 'libraries' option (library '{lib_name}'), "
                    "'obj_deps' must be a dictionary of "
                    "type 'source: list'"
                )

            # 044380.python.build_clib.line62.comment Build the list to be used by newer_pairwise_group
            # 044381.python.build_clib.line63.comment each source will be auto-added to its dependencies.
            for source in sources:
                src_deps = [source]
                src_deps.extend(global_deps)
                extra_deps = obj_deps.get(source, list())
                if not isinstance(extra_deps, (list, tuple)):
                    raise DistutilsSetupError(
                        f"in 'libraries' option (library '{lib_name}'), "
                        "'obj_deps' must be a dictionary of "
                        "type 'source: list'"
                    )
                src_deps.extend(extra_deps)
                dependencies.append(src_deps)

            expected_objects = self.compiler.object_filenames(
                sources,
                output_dir=self.build_temp,
            )

            if newer_pairwise_group(dependencies, expected_objects) != ([], []):
                # 044382.python.build_clib.line83.comment First, compile the source code to object files in the library
                # 044383.python.build_clib.line84.comment directory.  (This should probably change to putting object
                # 044384.python.build_clib.line85.comment files in a temporary build directory.)
                macros = build_info.get('macros')
                include_dirs = build_info.get('include_dirs')
                cflags = build_info.get('cflags')
                self.compiler.compile(
                    sources,
                    output_dir=self.build_temp,
                    macros=macros,
                    include_dirs=include_dirs,
                    extra_postargs=cflags,
                    debug=self.debug,
                )

            # 044385.python.build_clib.line98.comment Now "link" the object files together into a static library.
            # 044386.python.build_clib.line99.comment (On Unix at least, this isn't really linking -- it just
            # 044387.python.build_clib.line100.comment builds an archive.  Whatever.)
            self.compiler.create_static_lib(
                expected_objects, lib_name, output_dir=self.build_clib, debug=self.debug
            )
