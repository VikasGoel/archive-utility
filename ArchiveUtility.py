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
from logging.handlers import TimedRotatingFileHandler

from ArchiveDirectory import ArchiveDirectory

def main():
    # Read configuration from YAML
    with open('ArchiveJobConfig.yaml', 'r') as stream:
        global_config = yaml.load(stream)

    logging.config.dictConfig(global_config['logging'])
    # Create logger
    logger = logging.getLogger('myapp.main')

    list_of_archive_args = global_config['archives']
    #print list_of_archives

    logger.info('---------- PROCESS STARTING ----------')

    # Create list of archive objects
    archive_objects = []

    if len(list_of_archive_args) > 0:
        # create a list of all the objects to be processed
        for archive_args in list_of_archive_args:
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


if __name__ == '__main__':
    main()
