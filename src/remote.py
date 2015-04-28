#!/usr/bin/env python

import argparse
import gzip
import os
import re
import subprocess
import sys


# Parse command line arguments passed to the remote driver
def parse_cli_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('--back-up', action='store_true')
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--purge-backup', action='store_true')
    parser.add_argument('action_args', nargs='*')

    cli_args = parser.parse_args()
    return cli_args


# Read contents of wp-config.php for a WordPress installation
def read_wp_config(wordpress_path):

    wp_config_path = os.path.join(wordpress_path, 'wp-config.php')
    with open(wp_config_path, 'r') as wp_config:
        return wp_config.read()


# Create intermediate directories in remote backup path if necessary
def create_dir_structure(remote_backup_path):

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
def dump_db(db_info, remote_backup_path):
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

        compressor = subprocess.Popen('gzip',
                                      stdin=mysqldump.stdout,
                                      stdout=remote_backup)

        # Wait for remote to dump and compress database
        mysqldump.wait()
        compressor.wait()


# Verify integrity of remote backup by checking its size
def verify_backup_integrity(remote_backup_path):

    if os.path.getsize(remote_backup_path) < 1024:
        raise OSError('Backup is corrupted (too small). Aborting.')


# Purge remote backup (this is only run after download)
def purge_backup(backup_path):

    os.remove(backup_path)


def back_up(wordpress_path, backup_path):

    backup_path = os.path.expanduser(backup_path)

    create_dir_structure(backup_path)

    db_info = get_db_info(wordpress_path)
    dump_db(db_info, backup_path)
    verify_backup_integrity(backup_path)


# Decompress the given backup file and return database contents
def get_db_contents(backup_path):

    try:
        gzip_file = gzip.open(backup_path, 'rb')
        db_contents = gzip_file.read()
    finally:
        gzip_file.close()

    return db_contents


# Restore WordPress database using the given remote backup
def restore(wordpress_path, backup_path):

    backup_path = os.path.expanduser(backup_path)

    db_info = get_db_info(wordpress_path)
    db_contents = get_db_contents(backup_path)

    os.remove(backup_path)


def main():

    cli_args = parse_cli_args()

    if cli_args.back_up:
        back_up(*cli_args.action_args)
    elif cli_args.restore:
        restore(*cli_args.action_args)
    elif cli_args.purge_backup:
        purge_backup(*cli_args.action_args)

if __name__ == '__main__':
    main()
