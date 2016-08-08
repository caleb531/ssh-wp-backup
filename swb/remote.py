#!/usr/bin/env python3

import os
import os.path
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
    matches = re.finditer('define\(\s*\'DB_([A-Z]+)\',\s*\'(.*?)\'\s*\)',
                          wp_config_contents)
    for match in matches:
        key = match.group(1).lower()
        value = match.group(2)
        db_info[key] = value

    return db_info


# Dump MySQL database to compressed file
def dump_compressed_db(db_name, db_host, db_user, db_password,
                       backup_compressor, backup_path):

    mysqldump = subprocess.Popen([
        'mysqldump',
        db_name,
        '-h', db_host,
        '-u', db_user,
        '-p{}'.format(db_password),
        '--add-drop-table'
    ], stdout=subprocess.PIPE)

    # Create remote backup so as to write output of dump/compress to file
    with open(backup_path, 'w') as backup_file:

        compressor = subprocess.Popen(
            shlex.split(backup_compressor),
            stdin=mysqldump.stdout, stdout=backup_file)

        # Wait for remote to dump and compress database
        mysqldump.wait()
        compressor.wait()


# Verify integrity of remote backup by checking its size
def verify_backup_integrity(backup_path):

    if os.path.getsize(backup_path) < 1024:
        os.remove(backup_path)
        raise OSError('Backup is corrupted (too small). Aborting.')


# Purge remote backup (this is only run after download)
def purge_downloaded_backup(backup_path):

    os.remove(backup_path)


# Back up WordPress database or installation
def back_up(wordpress_path, backup_compressor, backup_path):

    backup_path = os.path.expanduser(backup_path)
    create_dir_structure(backup_path)
    db_info = get_db_info(wordpress_path)

    # backup_path is assumed to refer to SQL database file backup
    dump_compressed_db(
        db_name=db_info['name'], db_host=db_info['host'],
        db_user=db_info['user'], db_password=db_info['password'],
        backup_compressor=backup_compressor,
        backup_path=backup_path)

    verify_backup_integrity(backup_path)


# Decompress the given backup file to a database file in the same directory
def decompress_backup(backup_path, backup_decompressor):

    compressor = subprocess.Popen(
        shlex.split(backup_decompressor) + [backup_path])
    compressor.wait()


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
    except OSError:
        pass
    try:
        os.remove(backup_path)
    except OSError:
        pass


# Restore WordPress database using the given remote backup
def restore(wordpress_path, backup_path, backup_decompressor):

    wordpress_path = os.path.expanduser(wordpress_path)
    backup_path = os.path.expanduser(backup_path)
    verify_backup_integrity(backup_path)
    decompress_backup(
        backup_path=backup_path,
        backup_decompressor=backup_decompressor)

    db_info = get_db_info(wordpress_path)
    db_path = os.path.splitext(backup_path)[0]

    replace_db(
        db_name=db_info['name'], db_host=db_info['host'],
        db_user=db_info['user'], db_password=db_info['password'],
        db_path=db_path)

    purge_restored_backup(backup_path=backup_path, db_path=db_path)


def main():

    # Parse action to take as well as the action's respective arguments
    action, *action_args = sys.argv[1:]

    if action == 'restore':
        restore(*action_args)
    elif action == 'purge-backup':
        purge_downloaded_backup(*action_args)
    else:
        # Default action is to back up
        back_up(*action_args)


if __name__ == '__main__':
    main()
