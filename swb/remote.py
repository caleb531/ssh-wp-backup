#!/usr/bin/env python3

import io
import os
import os.path
import re
import shlex
import subprocess
import sys
import tarfile


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


# Dump MySQL database to file and return subprocess
def get_mysqldump(db_name, db_host, db_user, db_password):

    mysqldump = subprocess.Popen([
        'mysqldump',
        db_name,
        '-h', db_host,
        '-u', db_user,
        '-p{}'.format(db_password),
        '--add-drop-table'
    ], stdout=subprocess.PIPE)

    return mysqldump


# Dump MySQL database to compressed file
def dump_compressed_db(db_name, db_host, db_user, db_password,
                       backup_compressor, backup_path):

    mysqldump = get_mysqldump(db_name, db_host, db_user, db_password)

    # Create remote backup so as to write output of dump/compress to file
    with open(backup_path, 'w') as backup_file:

        compressor = subprocess.Popen(
            shlex.split(backup_compressor),
            stdin=mysqldump.stdout, stdout=backup_file)

        # Wait for remote to dump and compress database
        mysqldump.wait()
        compressor.wait()


# Dump MySQL database to uncompressed file at the given path
def dump_uncompressed_db(db_name, db_host, db_user, db_password):

    mysqldump = get_mysqldump(db_name, db_host, db_user, db_password)
    db_contents = mysqldump.communicate()[0]
    mysqldump.wait()

    return db_contents


# Verify integrity of remote backup by checking its size
def verify_backup_integrity(backup_path):

    if os.path.getsize(backup_path) < 1024:
        raise OSError('Backup is corrupted (too small). Aborting.')


# Purge remote backup (this is only run after download)
def purge_downloaded_backup(backup_path):

    os.remove(backup_path)


# Compressed an existing tar backup file using the chosen compressor
def compress_tar(tar_path, backup_path, backup_compressor):

    compressor = subprocess.Popen(
        shlex.split(backup_compressor) + [backup_path, tar_path])
    compressor.wait()


# Add a database to the given tar file under the given name
def add_db_to_tar(tar_file, db_file_name, db_contents):

    db_file_obj = io.BytesIO()
    db_file_obj.write(db_contents)
    db_tar_info = tarfile.TarInfo(db_file_name)
    db_tar_info.size = len(db_file_obj.getvalue())
    db_file_obj.seek(0)
    tar_file.addfile(db_tar_info, db_file_obj)


# Create the full backup file by tar'ing both the wordpress site directory and
# the the dumped database contents
def create_full_backup(wordpress_path, db_contents,
                       backup_path, backup_compressor):

    backup_name = os.path.basename(backup_path)
    tar_name = os.path.splitext(backup_name)[0]

    wordpress_site_name = os.path.basename(wordpress_path)
    db_file_name = '{}.sql'.format(wordpress_site_name)

    backup_pwd_path = os.path.dirname(backup_path)
    tar_path = os.path.join(backup_pwd_path, tar_name)

    tar_file = tarfile.open(tar_path, 'w')
    tar_file.add(wordpress_path, arcname=wordpress_site_name)
    add_db_to_tar(tar_file, db_file_name, db_contents)
    tar_file.close()

    compress_tar(tar_path, backup_path, backup_compressor)


# Back up WordPress database or installation
def back_up(wordpress_path, backup_compressor, backup_path, full_backup):

    backup_path = os.path.expanduser(backup_path)
    create_dir_structure(backup_path)
    db_info = get_db_info(wordpress_path)

    if full_backup == 'True':

        # backup_path is assumed to refer to entire site directory backup
        db_contents = dump_uncompressed_db(
            db_info['name'], db_info['host'],
            db_info['user'], db_info['password'])
        create_full_backup(
            wordpress_path, db_contents,
            backup_path, backup_compressor)

    else:

        # backup_path is assumed to refer to SQL database file backup
        db_info = get_db_info(wordpress_path)
        dump_compressed_db(
            db_info['name'], db_info['host'],
            db_info['user'], db_info['password'],
            backup_compressor, backup_path)

    verify_backup_integrity(backup_path)


# Decompress the given backup file to a database file in the same directory
def decompress_backup(backup_path, backup_decompressor):

    compressor = subprocess.Popen(
        shlex.split(backup_decompressor) + [backup_path])
    compressor.wait()


# Construct path to decompressed database file from given backup file
def get_db_path(backup_path):

    return os.path.splitext(backup_path)[0]


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

    backup_path = os.path.expanduser(backup_path)
    verify_backup_integrity(backup_path)
    decompress_backup(backup_path, backup_decompressor)

    db_info = get_db_info(wordpress_path)
    db_path = get_db_path(backup_path)

    replace_db(
        db_info['name'], db_info['host'],
        db_info['user'], db_info['password'], db_path)

    purge_restored_backup(backup_path, db_path)


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
