import logging
import shutil
import os
import fnmatch
import time

class ArchiveDirectory(object):
    """A utility class to archive files from a source directory to a target directory

    Attributes:
    See yaml configuration file for details on attributes
    """


    def __init__(self, name, source, destination,
                 action='Move', retention_days=10, recursion_depth=0,
                 include_pattern='*', encrypt=False):
        """Return an ArchiveDirectory object

        Keyword arguments:
        See yaml configuration file for details on arguments
        """
        # Configure logger for this class
        self.logger = logging.getLogger('myapp.lib')
        self.logger.debug('ArchiveDirectory Constructor executing')
        # Set attributes
        self.name = name
        self.source = source
        self.destination = destination
        self.action = action
        self.retention_days = retention_days
        self.recursion_depth = recursion_depth
        self.include_pattern = include_pattern
        self.encrypt = encrypt
        # Log attributes to debug log
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
        self.logger.info('Validate config for %r' % self.name)
        if (
                len(self.name) > 0 and
                os.path.isdir(self.source) and
                len(self.destination) > 0 and
                self.action.lower() in ('move', 'copy', 'uniquecopy') and
                self.recursion_depth >= 0
            ):
            self.logger.debug('Config validation for %r passed' % self.name)
            return True
        else:
            self.logger.warn('Config validation for %r failed' % self.name)
            return False


    def validate_access(self):
        """Validates the correct level of access on source & destination"""
        # If we have read access to source
        self.logger.info('Validate access for %r' % self.name)
        if os.access(self.source,os.R_OK):
            self.logger.debug('Read access okay on source: %s' % self.source)
            # And if destination exists and we have write access
            if os.path.isdir(self.destination) and os.access(self.destination,os.W_OK):
                self.logger.debug('Write access okay on destination: %s' % self.destination)
                return True
            # Or if destination doesn't already exist (we'll create it later)
            elif not(os.path.isdir(self.destination)):
                self.logger.debug('Destination does\'t exist - we\'ll create it later: %s' % self.destination)
                return True
            else:
                self.logger.warn('Write access not okay on destination: %s' % self.destination)
                return False
        else:
            self.logger.warn('Read access not okay on source: %s' % self.source)
            return False


    def archive(self):
        """Returns success or failure on archive operation"""
        self.logger.info('Archive executing for %s' % self.name)
        # For all files in the source directory with specified recursion depth
        # and include pattern, perform the archive operation
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
            self.logger.info('Source file name: %s' % source_file_name)
            self.logger.debug('Destination file name: %s' % dest_file_name)
            self.logger.debug('Alternate destination file name: %s' % alternate_dest_file_name)

            # Perform either move, copy, or uniquecopy operation for the file
            if self.action.lower() == 'move':
                if os.path.exists(dest_file_name):
                    self.logger.info(
                            'Destination file already exists, moving to alternate location instead: %s',
                            alternate_dest_file_name)
                    shutil.move(source_file_name, alternate_dest_file_name)
                    encrypt_input_file = alternate_dest_file_name
                else:
                    self.logger.info('File moved to: %s' % dest_file_name)
                    shutil.move(source_file_name,dest_file_name)
                    encrypt_input_file = dest_file_name
            elif self.action.lower() == 'copy':
                # Copy only files that don't exist in the destination or files
                # that have changed (more recent last modified timestamp than
                # the destination file)
                if ((not os.path.exists(dest_file_name))
                        or (os.stat(source_file_name).st_mtime - os.stat(dest_file_name).st_mtime > 1)):
                    self.logger.info('File copied to: %s' % dest_file_name)
                    shutil.copy2(source_file_name, dest_file_name)
                    encrypt_input_file = dest_file_name
                else:
                    self.logger.info('Source already exists, copy not performed: %s' % source_file_name)
            elif self.action.lower() == 'uniquecopy':
                self.logger.info('File copied to unique filename: %s' % alternate_dest_file_name)
                shutil.copy2(source_file_name, alternate_dest_file_name)
                encrypt_input_file = alternate_dest_file_name
            else:
                # An invalid action was selected
                self.logger.warn('An invalid action was selected for %r' % self.name)
                self.logger.warn('    Action selected was %s' % self.action)
                # This case can be avoided by running this function after using
                # the validate_config() function to ensure the instance
                # has a valid config

            # If encryption is selected, perform encryption
            if self.encrypt == True and len(encrypt_input_file)>0:
                encrypt_output_file = self.__encrypt_file(encrypt_input_file)
                self.logger.info('File encrypted from: %s', encrypt_input_file)
                self.logger.info('File encrypted to:   %s', encrypt_output_file)


    def enforce_retention(self):
        """Removes files in the destination older than the specified retention age"""
        self.logger.info('Executing retention for %r' % self.name)
        if self.retention_days == -1:
            self.logger.info('Retention not run as config is set to retain files forever')
            return 'not run'
        else:
            # Delete files in dest directory matching include_pattern older
            # than retention_days # of days

            # Prep days ago variable - earlier than this, files will be deleted (time in seconds)
            delete_files_prior_age = time.time() - (60*60*24*self.retention_days)

            # Get all files in the destination directory that match specified
            # recursion depth and include pattern
            for root, basename in self.find_files(
                    self.destination, self.recursion_depth, self.include_pattern):
                # File to check age on
                retention_check_file_name = os.path.join(root, basename)
                mtime = os.path.getmtime(retention_check_file_name)
                if mtime < delete_files_prior_age:
                    self.logger.info('Removing file due to retention age: %s' % retention_check_file_name)
                    os.remove(retention_check_file_name)
            return 'complete'


    def find_files(self, find_source, level=0, pattern='*'):
        """Finds all the source files to the correct recursion depth and yields
        them as they are found."""
        # Cleanse the source directory path by removing any unnecessary path
        # separators ('\' or '/' as used by the OS)
        source_dir = find_source.rstrip(os.path.sep)

        try:
            # Verify that the source exists
            assert os.path.isdir(source_dir)
            # Determine original depth of the source directory
            original_depth = source_dir.count(os.path.sep)
            # Walk through the source directory & yield each filename until
            # recursion depth has been met
            for root, dirs, files in os.walk(source_dir):
                # Yields each filename (full path) in the current directory
                for basename in files:
                    # Match filename to the include pattern
                    if fnmatch.fnmatch(basename, pattern):
                        filename = os.path.join(root, basename)
                        self.logger.debug('Finding files in: %r' % root)
                        self.logger.debug('Found file:       %r' % basename)
                        yield root, basename
                # If original depth plus the amount of recursion desired is the same as
                # our current depth, delete the remaining dirs below this level,
                # thus breaking from the loop
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
