#!/usr/bin/env python3

import os
import re
import shlex
import subprocess
import sys


# Read contents of wp-config.php for a WordPress installation
def read_wp_config(wordpress_path):

    wp_config_path = os.path.join(wordpress_path, 'wp-config.php')
    with open(wp_config_path, 'r') as wp_config:
        return wp_config.read()


# Create intermediate directories in remote backup path if necessary
def create_dir_structure(backup_path):

    try:
        os.makedirs(os.path.dirname(backup_path))
    except OSError:
        pass


# Retrieve database information for a WordPress installation
def get_db_info(wordpress_path):

    # Read contents of wp-config.php so as to search it for database info
    wp_config_contents = read_wp_config(wordpress_path)
    db_info = {}

    # Find all PHP constant definitions pertaining to database
    matches = re.finditer('define\(\'DB_([A-Z]+)\', \'(.*?)\'\)',
                          wp_config_contents)
    for match in matches:
        key = match.group(1).lower()
        value = match.group(2)
        db_info[key] = value

    return db_info


# Dump MySQL database to compressed file on remote
def dump_db(db_info, backup_compressor, backup_path):

    mysqldump = subprocess.Popen([
        'mysqldump',
        db_info['name'],
        '-h', db_info['host'],
        '-u', db_info['user'],
        '-p{0}'.format(db_info['password']),
        '--add-drop-table'
    ], stdout=subprocess.PIPE)

    # Create remote backup so as to write output of dump/compress to file
    # Binary mode (b) does nothing on Unix systems; only needed for Windows
    with open(backup_path, 'wb') as backup_file:

        compressor = subprocess.Popen(shlex.split(backup_compressor),
                                      stdin=mysqldump.stdout,
                                      stdout=backup_file)

        # Wait for remote to dump and compress database
        mysqldump.wait()
        compressor.wait()


# Verify integrity of remote backup by checking its size
def verify_backup_integrity(backup_path):

    if os.path.getsize(backup_path) < 1024:
        raise OSError('Backup is corrupted (too small). Aborting.')


# Purge remote backup (this is only run after download)
def purge_backup(backup_path):

    os.remove(backup_path)


def back_up(wordpress_path, backup_compressor, backup_path):

    backup_path = os.path.expanduser(backup_path)

    create_dir_structure(backup_path)

    db_info = get_db_info(wordpress_path)
    dump_db(db_info, backup_compressor, backup_path)
    verify_backup_integrity(backup_path)


# Decompress the given backup file and return database contents
def decompress_backup(backup_path, backup_decompressor):

    compressor = subprocess.Popen(shlex.split(backup_decompressor) +
                                  [backup_path])
    compressor.wait()


# Restore WordPress database using the given remote backup
def restore(wordpress_path, backup_path, backup_decompressor):

    backup_path = os.path.expanduser(backup_path)
    verify_backup_integrity(backup_path)
    decompress_backup(backup_path, backup_decompressor)

    db_info = get_db_info(wordpress_path)
    # Construct path to decompressed database file from given backup file
    db_path = re.sub('\.([A-Za-z0-9]+)$', '', backup_path)

    with open(db_path, 'r') as db_file:

        # Execute SQL script on the respective database
        mysql = subprocess.Popen([
            'mysql',
            db_info['name'],
            '-h', db_info['host'],
            '-u', db_info['user'],
            '-p{0}'.format(db_info['password'])
        ], stdin=db_file)

        mysql.wait()

    # Decompressed backup should always exist at this point
    os.remove(db_path)
    # Compressed backup may or may not be removed automatically by decompressor
    try:
        os.remove(backup_path)
    except OSError:
        pass


def main():

    # Parse action to take as well as its respective arguments
    action, *action_args = sys.argv[1:]

    if action == 'back-up':
        back_up(*action_args)
    elif action == 'restore':
        restore(*action_args)
    elif action == 'purge-backup':
        purge_backup(*action_args)

if __name__ == '__main__':
    main()
