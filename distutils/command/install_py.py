# created 1999/03/13, Greg Ward

__revision__ = "$Id$"

import sys, string
from distutils.core import Command
from distutils import util

class install_py (Command):

    description = "install pure Python modules"

    user_options = [
        ('install-dir=', 'd', "directory to install to"),
        ('build-dir=','b', "build directory (where to install from)"),
        ('compile', 'c', "compile .py to .pyc"),
        ('optimize', 'o', "compile .py to .pyo (optimized)"),
        ('destdir', None, 'destination directory'),
        ]
               

    def initialize_options (self):
        # let the 'install' command dictate our installation directory
        self.install_dir = None
        self.build_dir = None
        self.compile = 1
        self.optimize = 1
        self.create_uninstall = None
        self.destdir = None

    def finalize_options (self):

        # Get all the information we need to install pure Python modules
        # from the umbrella 'install' command -- build (source) directory,
        # install (target) directory, and whether to compile .py files.
        self.set_undefined_options ('install',
                                    ('build_lib', 'build_dir'),
                                    ('install_lib', 'install_dir'),
                                    ('create_uninstall', 'create_uninstall'),
                                    ('compile_py', 'compile'),
                                    ('optimize_py', 'optimize'),
				    ('destdir', 'destdir'))


    def run (self):

        # Make sure we have "built" all pure Python modules first
        self.run_peer ('build_py')

        # Install everything: simply dump the entire contents of the build
        # directory to the installation directory (that's the beauty of
        # having a build directory!)
        if self.destdir:
            self.install_dir = util.add_path_prefix(self.destdir,
                               self.install_dir)
        if self.create_uninstall and not self.force:
            # turn on self.force to catch all previous installed files
            oldforce = self.force
            self.force = 1
            outfiles = self.copy_tree (self.build_dir, self.install_dir)
            self.force = oldforce
        else:
            outfiles = self.copy_tree (self.build_dir, self.install_dir)
                   
        # (Optionally) compile .py to .pyc
        # XXX hey! we can't control whether we optimize or not; that's up
        # to the invocation of the current Python interpreter (at least
        # according to the py_compile docs).  That sucks.

        if self.compile:
            from py_compile import compile
            import __builtin__

            for f in outfiles:
                # XXX we can determine if we run python -O by looking
                # at __builtin__.__debug__, but we can not change it

                # only compile the file if it is actually a .py file
                if f[-3:] == '.py':
                    out_fn = f + (__builtin__.__debug__ and "c" or "o")
                    outfiles.append(out_fn)
                    self.make_file (f, out_fn, compile, (f,),
                                    "byte-compiling %s" % f,
                                    "byte-compilation of %s skipped" % f)
                    
        # XXX ignore self.optimize for now, since we don't really know if
        # we're compiling optimally or not, and couldn't pick what to do
        # even if we did know.  ;-(
        if self.destdir:
            for i in range(len(outfiles)):
                outfiles[i] = util.remove_path_prefix(self.destdir,
                              outfiles[i])
        self.distribution.outfiles.extend(outfiles)

    # run ()

# class InstallPy
