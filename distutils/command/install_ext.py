"""install_ext

Implement the Distutils "install_ext" command to install extension modules."""

# created 1999/09/12, Greg Ward

__revision__ = "$Id$"

from distutils.core import Command
from distutils.util import copy_tree

class install_ext (Command):

    description = "install C/C++ extension modules"
    
    user_options = [
        ('install-dir=', 'd', "directory to install to"),
        ('build-dir=','b', "build directory (where to install from)"),
        ('destdir', None, "destination directory")
        ]

    def initialize_options (self):
        # let the 'install' command dictate our installation directory
        self.install_dir = None
        self.build_dir = None
        self.create_uninstall = None
        self.destdir = None

    def finalize_options (self):
        self.set_undefined_options ('install',
                                    ('build_platlib', 'build_dir'),
                                    ('install_platlib', 'install_dir'),
				    ('create_uninstall', 'create_uninstall'),
				    ('destdir', 'destdir'))

    def run (self):

        # Make sure we have built all extension modules first
        self.run_peer ('build_ext')

        # Dump the entire "build/platlib" directory (or whatever it really
        # is; "build/platlib" is the default) to the installation target
        # (eg. "/usr/local/lib/python1.5/site-packages").  Note that
        # putting files in the right package dir is already done when we
        # build.
        if self.destdir:
            self.install_dir = util.add_path_prefix(self.destdir,
	                       self.install_dir)
        if self.create_uninstall and not self.force:
            # turn on self.force to catch all previous installed files
            oldforce = self.force
            self.force = 1
            outfiles = self.copy_tree (self.build_dir, self.install_dir)
            # restore previous options
            self.force = oldforce
        else:
            outfiles = self.copy_tree (self.build_dir, self.install_dir)
        if self.destdir:
            for i in range(len(outfiles)):
                outfiles[i] = util.remove_path_prefix(self.destdir,
                              outfiles[i])
        self.distribution.outfiles.extend(outfiles)

# class InstallExt
