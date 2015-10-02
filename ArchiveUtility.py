# A utility to archive files from a source directory to a target directory with flexible configuration
#
# Details on the configuration options can be found in the YAML configuration file
#
# Author: Timothy Ubbens
# Date: Aug 2015

import logging
import logging.config
import yaml
import sys
from logging.handlers import TimedRotatingFileHandler

from ArchiveDirectory import ArchiveDirectory

def main():
    # Read configuration from YAML
    with open('ArchiveUtilityConfig.yaml', 'r') as stream:
        global_config = yaml.load(stream)
    # Create logger with parameters from YAML file
    logging.config.dictConfig(global_config['logging'])
    logger = logging.getLogger('myapp.main')
    # Create list of items to archive from YAML file
    list_of_archive_args = global_config['archives']
    logger.info('---------- ARCHIVE PROCESS STARTING ----------')
    # Create list of archive objects
    archive_objects = []
    # Get command line arguments
    command_line_args = sys.argv[1:]
    logger.debug('Command line arguments: %s' % command_line_args)
    logger.debug('Number of command line arguments: %r' % len(command_line_args))
    process_archive_args = []
    index = -1;
    if len(command_line_args) > 0:
        logger.debug('Using only configs where name matches a command line arg')
        for arg_name in command_line_args:
            # Find the index of each arg_name in the list_of_archive_args
            index = find(list_of_archive_args, 'name', arg_name)
            # If item is found, then add it to the temp_archive_args list, else produce an error
            if index >= 0:
                process_archive_args.append(list_of_archive_args[index])
            else:
                logger.error('Couldn\'t find %s in yaml file', arg_name)
    else:
        logger.debug('No command line args received - all configs in YAML file used')
        process_archive_args = list_of_archive_args

    # If there are items to archive
    if len(process_archive_args) > 0:
        # Create a list of all the objects to be processed
        for archive_args in process_archive_args:
            logger.debug('%r' % archive_args )
            archive_objects.append(ArchiveDirectory(**archive_args))
        # Execute archive operation
        for archive_object in archive_objects:
            # If archive item is valid, then archive it and enforce retention
            if archive_object.validate_config() and archive_object.validate_access():
                logger.info('Archiving %s', archive_object.name)
                archive_object.archive()
                logger.debug('Returned from Archive operation')
                status = archive_object.enforce_retention()
                logger.debug('Returned from Retention operation: %s', status)
            else:
                logger.warning('Invalid parameters or access on %s', archive_object.name)
    # Else there were no archive objects to process
    else:
        logger.warning('There was nothing to archive')

    logger.info('---------- ARCHIVE PROCESS ENDING ----------')


def find(list_to_search, key, value):
    """Finds the index of an item in a list"""
    for i, dic in enumerate(list_to_search):
        if dic[key] == value:
            return i
    return -1


if __name__ == '__main__':
    main()
