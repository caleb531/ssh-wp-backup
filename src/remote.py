#!/usr/bin/env python

import re
import os
import subprocess
import sys


# Read contents of wp-config.php for a WordPress installation
def read_wp_config(wordpress_path):

    wp_config_path = os.path.join(wordpress_path, 'wp-config.php')
    with open(wp_config_path, 'r') as wp_config:
        return wp_config.read()


# Create intermediate directories in remote backup path if necessary
def create_directory_structure(remote_backup_path):

    try:
        os.makedirs(os.path.dirname(remote_backup_path))
    except OSError:
        pass


# Retrieve database information for a WordPress installation
def get_db_info(wordpress_path):

    # Read contents of wp-config.php so as to search it for database info
    wp_config_contents = read_wp_config(wordpress_path)
    db_info = {}

    # Find all PHP constant definitions pertaining to database
    matches = re.finditer('define\(\'(DB_[A-Z]+)\', \'(.*?)\'\)',
                          wp_config_contents)
    for match in matches:
        key = match.group(1)[3:].lower()
        value = match.group(2)
        db_info[key] = value

    return db_info


# Dump MySQL database to compressed file on remote
def dump_db(db_info, backup_compressor, remote_backup_path):
    pass
    mysqldump = subprocess.Popen([
        'mysqldump',
        db_info['name'],
        '-h', db_info['host'],
        '-u', db_info['user'],
        '-p{password}'.format(password=db_info['password']),
        '--add-drop-table'
    ], stdout=subprocess.PIPE)

    # Create remote backup so as to write output of dump/compress to file
    with open(remote_backup_path, 'wb') as remote_backup:

        compressor = subprocess.Popen(backup_compressor.split(' '),
                                      stdin=mysqldump.stdout,
                                      stdout=remote_backup)

        # Wait for remote to dump and compress database
        mysqldump.wait()
        compressor.wait()


def main():

    wordpress_path = sys.argv[1]
    remote_backup_path = sys.argv[2]
    backup_compressor = sys.argv[3]

    create_directory_structure(remote_backup_path)

    db_info = get_db_info(wordpress_path)
    dump_db(db_info, backup_compressor, remote_backup_path)

if __name__ == '__main__':
    main()
