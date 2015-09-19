# Script to do something
#
# Do something:
# - step 1
# - step 2
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

    logging.config.dictConfig(global_config['logging'])
    # Create logger
    logger = logging.getLogger('myapp.main')

    list_of_archive_args = global_config['archives']
    #print list_of_archives

    logger.info('---------- PROCESS STARTING ----------')

    # Create list of archive objects
    archive_objects = []

    command_line_args = sys.argv[1:]
    print command_line_args
    print len(command_line_args)
    process_archive_args = []
    index = -1;
    if len(command_line_args) > 0:
        print 'using only configs where name matches a command line arg'
        for arg_name in command_line_args:
            # find the index of each arg_name in the list_of_archive_args
            index = find(list_of_archive_args, 'name', arg_name)
            # if item is found, then add it to the temp_archive_args list, else produce an error
            if index >= 0:
                process_archive_args.append(list_of_archive_args[index])
            else:
                logger.error('couldn\'t find %s in yaml file', arg_name)
    else:
        print 'no command line args received - all configs in yaml file used'
        process_archive_args = list_of_archive_args

    if len(process_archive_args) > 0:
        # create a list of all the objects to be processed
        for archive_args in process_archive_args:
            logger.debug( '%r' % archive_args )
            archive_objects.append(ArchiveDirectory(**archive_args))

        # Execute archive operation
        for archive_object in archive_objects:

            if archive_object.validate_config() and archive_object.validate_access():
                status = archive_object.archive()
                logger.debug('Returned from Archive operation: %s', status)
                status = archive_object.enforce_retention()
                logger.debug('Returned from Retention operation: %s', status)
            else:
                logger.warning('Invalid parameters or access on %s', archive_object.name)
    # else there were no archive objects to process
    else:
        print 'nothing to archive'



    #logger.debug('This message should go to the log file')
    #logger.info('So should this')
    #logger.warning('And this, too')
    #logger.error('And this, too')

    logger.info('---------- PROCESS ENDING ----------')


def find(list_to_search, key, value):
    for i, dic in enumerate(list_to_search):
        if dic[key] == value:
            return i
    return -1


if __name__ == '__main__':
    main()
