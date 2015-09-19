import logging
import shutil
import os
import fnmatch
import time

class ArchiveDirectory(object):
    """A utility class to archive and encrypt

    Attributes:
    source -- the source directory that can be archived
        string directory expected
    destination -- the destination to archive files from the source
        string directory expected
    encrypt -- flag to track whether to encrypt files as they are archived.
        boolean expected
    retention_days -- number of days to retain archived files.
        integer number of days expected
    """


    def __init__(self, name, source, destination,
                 action='Move', retention_days=10, recursion_depth=0,
                 include_pattern='*', encrypt=False):
        """Return an ArchiveDirectory object

        Keyword arguments:
        name --
        source --
        destination --
        action --  (default 'Move')
        retention_days --  (default 10)
        recursion_depth --  (default 0)
        include_pattern --  (default '*')
        encrypt --  (default False)
        """
        self.logger = logging.getLogger('myapp.lib')
        self.logger.debug('ArchiveDirectory Constructor ran')

        self.name = name
        self.source = source
        self.destination = destination
        self.action = action
        self.retention_days = retention_days
        self.recursion_depth = recursion_depth
        self.include_pattern = include_pattern
        self.encrypt = encrypt

        self.logger.debug('name            %r' % self.name)
        self.logger.debug('source          %s' % self.source)
        self.logger.debug('destination     %s' % self.destination)
        self.logger.debug('action          %s' % self.action)
        self.logger.debug('retention days  %r' % self.retention_days)
        self.logger.debug('recursion depth %r' % self.recursion_depth)
        self.logger.debug('include pattern %r' % self.include_pattern)
        self.logger.debug('encrypt         %r' % self.encrypt)


    def validate_config(self):
        """Validates the parameters used for an instance of this class

        Instance must have a name
        Source must exist
        Must have read access to source
        Destination must be specified
        Action must be either 'Move', 'Copy', or 'UniqueCopy'
        Recursion depth must be a non-negative integer
        """
        if (
                len(self.name) > 0 and
                os.path.isdir(self.source) and
                len(self.destination) > 0 and
                self.action.lower() in ('move', 'copy', 'uniquecopy') and
                self.recursion_depth >= 0
            ):
            return True
        else:
            return False


    def validate_access(self):
        """Validates the correct level of access on source & destination"""
        # if we have read access to source
        if os.access(self.source,os.R_OK):
            # and if destination exists and we have write access
            self.logger.debug('read access okay on source')
            if os.path.isdir(self.destination) and os.access(self.destination,os.W_OK):
                self.logger.debug('write access okay on destination')
                return True
            # or if destination doesn't already exist (we'll create it later)
            elif not(os.path.isdir(self.destination)):
                self.logger.debug('destination does\'t exist - we\'ll create it later')
                return True
            else:
                self.logger.debug('write access not okay on destination')
                return False
        else:
            self.logger.debug('read access not okay on source')
            return False


    def archive(self):
        """Returns success or failure on archive operation"""
        self.logger.debug('archive ran')

        for root, basename in self.find_files(self.source, self.recursion_depth,
                                              self.include_pattern):

            # Destination needs to include any folders found by recursion in
            # find_files - this is done by removing the source from root returned
            # from the fild_files method
            recurse_dest = self.destination + root[len(self.source):]

            # Create destination if it doesn't exist.  Called within the loop as
            # we have to check for each directory as we recurse
            if not os.path.exists(recurse_dest):
                os.makedirs(recurse_dest)

            # Create the new source & destination file names
            source_file_name = os.path.join(root, basename)
            dest_file_name = os.path.join(recurse_dest, basename)
            alternate_dest_basename = time.strftime('%Y%m%d-%H%M%S-') + basename
            alternate_dest_file_name = os.path.join(recurse_dest,alternate_dest_basename)
            encrypt_input_file = ''

            # Copy or Move
            if self.action.lower() == 'move':
                if os.path.exists(dest_file_name):
                    self.logger.warning(
                            'destination file already exists, moving to %s instead',
                            alternate_dest_file_name)
                    shutil.move(source_file_name, alternate_dest_file_name)
                    encrypt_input_file = alternate_dest_file_name
                else:
                    shutil.move(source_file_name,dest_file_name)
                    encrypt_input_file = dest_file_name
            elif self.action.lower() == 'copy':
                # Copy only files that don't exist in the destination or files
                # that have changed (more recent last modified timestamp than
                # the destination file)
                if ((not os.path.exists(dest_file_name))
                        or (os.stat(source_file_name).st_mtime - os.stat(dest_file_name).st_mtime > 1)):
                    shutil.copy2(source_file_name, dest_file_name)
                    encrypt_input_file = dest_file_name
            elif self.action.lower() == 'uniquecopy':
                shutil.copy2(source_file_name, alternate_dest_file_name)
                encrypt_input_file = alternate_dest_file_name
            else:
                print 'pick a valid option, dummy!'
                # you should have run validate_config() function first!

            if self.encrypt == True and len(encrypt_input_file)>0:
                encrypt_output_file = self.__encrypt_file(encrypt_input_file)
                self.logger.info('file encrypted from: %s', encrypt_input_file)
                print encrypt_input_file
                print 'file encrypted from: ' + encrypt_input_file
                self.logger.info('file encrypted to:   %s', encrypt_output_file)
                print 'file encrypted to:   ' + encrypt_output_file

        return 'success'


    def enforce_retention(self):
        if self.retention_days == -1:
            self.logger.info('retention not run as config is to retain files forever')
            return 'retention not run'
        else:
            # delete files in dest directory matching include_pattern older
            # than retention_days # of days

            # prep days ago variable - earlier than this, files will be deleted (time in seconds)
            delete_files_prior_age = time.time() - (60*60*24*self.retention_days)

            for root, basename in self.find_files(
                    self.destination, self.recursion_depth, self.include_pattern):
                # file to check age on
                retention_check_file_name = os.path.join(root, basename)
                mtime = os.path.getmtime(retention_check_file_name)
                if mtime < delete_files_prior_age:
                    print 'removing ' +  retention_check_file_name
                    os.remove(retention_check_file_name)
            return 'retention complete'


    def find_files(self, find_source, level=0, pattern='*'):
        """Finds all the source files to the correct recursion depth and yields
        them as they are found."""
        #level = self.recursion_depth
        #pattern = self.include_pattern
        # cleanse the source directory path by removing any unnecessary path
        # separators ('\' or '/' as used by the OS)
        source_dir = find_source.rstrip(os.path.sep)

        try:
            assert os.path.isdir(source_dir)

            # determine original depth of the source directory
            original_depth = source_dir.count(os.path.sep)

            # walk through the source directory & yield each filename until
            # recursion depth has been met
            for root, dirs, files in os.walk(source_dir):
                # yields each filename (full path) in the current directory
                for basename in files:
                    if fnmatch.fnmatch(basename, pattern):
                        filename = os.path.join(root, basename)
                        #yield filename
                        yield root, basename

                # if original depth plus the amount of recursion desired is the same as
                # our current depth, delete the remaining dirs, thus breaking from the loop
                current_depth = root.count(os.path.sep)
                if original_depth + level <= current_depth:
                    del dirs[:]

        except AssertionError as e:
            self.logger.warning('Source not found: %s' % source_dir)
            yield 'Source not found: %s' % source_dir
            # Don't cause the exception to stop app execution
            pass


    def __encrypt_file(self, input_encrypt_file):
        # This stub should be completed with your encryption solution of choice
        # This method should return the encrypted file name
        return ''


    @staticmethod
    def func(x):
        return x + 1
