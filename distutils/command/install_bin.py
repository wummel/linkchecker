"""install_bin

Implement the Distutils "install_bin" command to install programs
and scripts."""

from distutils.core import Command
from distutils import util
import os,types,string

class install_bin(Command):

    description = "install programs and scripts"
    
    user_options = [
        ('install-dir=', 'd', "directory to install to"),
        ('destdir', None, 'destination directory'),
        ]

    def initialize_options (self):
        # let the 'install' command dictate our installation directory
        self.install_dir = None
        self.create_uninstall = None
        self.destdir = None

    def finalize_options (self):
        self.set_undefined_options ('install',
                                    ('install_bin', 'install_dir'),
				    ('create_uninstall', 'create_uninstall'),
				    ('destdir', 'destdir'))
        self.programs = self.get_platform_bins(self.distribution.programs)
        self.scripts = self.get_platform_bins(self.distribution.scripts)

    def get_platform_bins(self, bins):
        filtered = []
        if bins:
            for b in bins:
                if type(b)==types.TupleType:
                    if len(b)==2 and os.name==b[1]:
                        filtered.append(b[0])
                else:
                    filtered.append(b)
        return filtered

    def run (self):

        if not self.programs and not self.scripts:
            return

        # Copy specified programs and scripts to install_dir
        # Additionally replace in scripts some variables
	# (currently only @INSTALL_BIN@ with install_dir)
        real_install_dir = self.install_dir
        if self.destdir:
            self.install_dir = util.add_path_prefix(self.destdir,
	                  self.install_dir)
        # create the install directory
        outfiles = self.mkpath(self.install_dir)
        # copy the files
        if self.create_uninstall and not self.force:
            # turn on self.force to catch all previous installed files
            oldforce = self.force
            self.force = 1
            outfiles.extend(self.run_copy_files(real_install_dir))
            # restore previous options
            self.force = oldforce
        else:
            outfiles.extend(self.run_copy_files(real_install_dir))
        if self.destdir:
            for i in range(len(outfiles)):
                outfiles[i] = util.remove_path_prefix(self.destdir,
                              outfiles[i])
        self.distribution.outfiles.extend(outfiles)

    def run_copy_files(self, real_install_dir):
        outfiles = []
        for f in self.programs:
            if self.copy_file(f, self.install_dir):
                outfiles.append(os.path.join(real_install_dir, f))
        for f in self.scripts:
            if self.copy_file(f, self.install_dir):
                outfiles.append(os.path.join(real_install_dir, f))
                self.replace_vars(os.path.join(self.install_dir, f),
		                  real_install_dir)
        return outfiles

    def replace_vars(self, file, directory):
        data = open(file).read()
        data = string.replace(data, "@INSTALL_BIN@", directory)
        open(file,"w").write(data)

