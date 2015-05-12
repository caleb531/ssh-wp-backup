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
        '-p{}'.format(db_info['password']),
        '--add-drop-table'
    ], stdout=subprocess.PIPE)

    # Create remote backup so as to write output of dump/compress to file
    with open(backup_path, 'w') as backup_file:

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
def purge_downloaded_backup(backup_path):

    os.remove(backup_path)


def back_up(wordpress_path, backup_compressor, backup_path):

    create_dir_structure(backup_path)

    db_info = get_db_info(wordpress_path)
    dump_db(db_info, backup_compressor, backup_path)
    verify_backup_integrity(backup_path)


# Decompress the given backup file to a database file in the same directory
def decompress_backup(backup_path, backup_decompressor):

    compressor = subprocess.Popen(shlex.split(backup_decompressor) +
                                  [backup_path])
    compressor.wait()


# Construct path to decompressed database file from given backup file
def get_db_path(backup_path):

    return re.sub('\.([A-Za-z0-9]+)$', '', backup_path)


# Replace a WordPress database with the database at the given path
def replace_db(db_name, db_host, db_user, db_password, db_path):

    with open(db_path, 'r') as db_file:

        # Execute SQL script on the respective database
        mysql = subprocess.Popen([
            'mysql',
            db_name,
            '-h', db_host,
            '-u', db_user,
            '-p{}'.format(db_password)
        ], stdin=db_file)

        mysql.wait()


# Purge backup and the decompressed database after it has been restored
def purge_restored_backup(backup_path, db_path):

    try:
        os.remove(db_path)
        os.remove(backup_path)
    except OSError:
        pass


# Restore WordPress database using the given remote backup
def restore(wordpress_path, backup_path, backup_decompressor):

    verify_backup_integrity(backup_path)
    decompress_backup(backup_path, backup_decompressor)

    db_info = get_db_info(wordpress_path)
    db_path = get_db_path(backup_path)

    replace_db(db_info['name'], db_info['host'],
               db_info['user'], db_info['password'], db_path)

    purge_restored_backup(backup_path, db_path)


def main():

    # Parse action to take as well as the action's respective arguments
    action, *action_args = sys.argv[1:]

    if action == 'back-up':
        back_up(*action_args)
    elif action == 'restore':
        restore(*action_args)
    elif action == 'purge-backup':
        purge_downloaded_backup(*action_args)

if __name__ == '__main__':
    main()
