#!/usr/bin/env python

import argparse
import ConfigParser
import glob
import gzip
import os
import os.path
import re
import subprocess
import sys
import time


# Make program directory globally accessible to script
program_dir = os.path.dirname(os.path.realpath(__file__))


# Parse command line arguments passed to the local driver
def parse_cli_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'config_path',
        help='the path to a configuration file (.ini)')

    parser.add_argument(
        '--restore',
        '-r',
        help='the path to a compressed backup file from which to restore')

    cli_args = parser.parse_args()
    return cli_args


# Parse configuration files at given paths into object
def parse_config(config_paths):

    config = ConfigParser.RawConfigParser()
    config.read(config_paths)

    return config


# Create intermediate directories in local backup path if necessary
def create_dir_structure(path):

    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass


# Connect to remote via SSH and execute remote script
def exec_on_remote(user, hostname, port, action, action_args, **streams):

    # Read remote script so as to pass contents to SSH session
    with open(os.path.join(program_dir, 'remote.py')) as remote_script:

        # Construct Popen args by combining both lists of command arguments
        ssh_args = [
            'ssh',
            '-p {}'.format(port),
            '{}@{}'.format(user, hostname),
            'python -',
            '--{}'.format(action)  # The action to run on remote
        ] + action_args

        ssh = subprocess.Popen(ssh_args, stdin=remote_script)
        # Wait for command to finish execution
        ssh.wait()

        if ssh.returncode != 0:
            sys.exit(ssh.returncode)


# Execute remote backup script to create remote backup
def create_remote_backup(user, hostname, port, wordpress_path,
                         remote_backup_path):

    exec_on_remote(user, hostname, port, 'back-up', [
        wordpress_path,
        remote_backup_path
    ])


# Download remote backup to local system
def download_remote_backup(user, hostname, port, remote_backup_path,
                           local_backup_path):

    # Download backup to specified path
    # Send download progress to stdout
    scp = subprocess.Popen([
        'scp',
        '-P {}'.format(port),
        '{}@{}:{}'.format(user, hostname, remote_backup_path),
        local_backup_path
    ])

    # Wait for local backup to finish downloading
    scp.wait()


# Forcefully remove backup from remote
def purge_remote_backup(user, hostname, port, remote_backup_path):

    exec_on_remote(user, hostname, port, 'purge-backup', [remote_backup_path])


# Purge oldest backups to keep number of backups within specified limit
def purge_oldest_backups(local_backup_path, max_local_backups):

    # Convert date format sequences to wildcards
    local_backup_path = re.sub('%[A-Za-z]', '*', local_backup_path)

    # Retrieve list of local backups sorted from oldest to newest
    local_backups = sorted(glob.iglob(local_backup_path),
                           key=lambda path: os.stat(path).st_mtime)
    backups_to_purge = local_backups[:-max_local_backups]

    for backup in backups_to_purge:
        os.remove(backup)


# Run backup script on remote
def back_up(config):

    # Expand date format sequences in both backup paths
    # Also expand home directory for local backup path
    expanded_local_backup_path = os.path.expanduser(time.strftime(
        config.get('paths', 'local_backup')))
    # Home directory in remote backup path will be expanded by remote script
    expanded_remote_backup_path = time.strftime(
        config.get('paths', 'remote_backup'))

    create_dir_structure(expanded_local_backup_path)

    create_remote_backup(config.get('ssh', 'user'),
                         config.get('ssh', 'hostname'),
                         config.get('ssh', 'port'),
                         config.get('paths', 'wordpress'),
                         config.get('paths', 'remote_backup'))

    download_remote_backup(config.get('ssh', 'user'),
                           config.get('ssh', 'hostname'),
                           config.get('ssh', 'port'),
                           expanded_remote_backup_path,
                           expanded_local_backup_path)

    if config.getboolean('backup', 'purge_remote'):
        purge_remote_backup(config.get('ssh', 'user'),
                            config.get('ssh', 'hostname'),
                            config.get('ssh', 'port'),
                            expanded_remote_backup_path)

    if config.has_option('backup', 'max_local_backups') and not os.path.isdir(
       config.get('paths', 'local_backup')):
        purge_oldest_backups(config.get('paths', 'local_backup'),
                             config.getint('backup', 'max_local_backups'))


# Decompress the given backup file and return database contents
def get_db_contents(backup_path):

    with gzip.open(backup_path, 'rb') as gzip_file:
        db_contents = gzip_file.read()

    return db_contents


# Run restore script on remote
def restore(config, backup_path):

    # Read remote script so as to pass contents to SSH session
    with open(os.path.join(program_dir, 'restore.py')) as restore_script:

        db_contents = get_db_contents(os.path.expanduser(backup_path))

        action_args = [
            config.get('paths', 'wordpress')
        ]
        ssh = exec_on_remote(config.get('ssh', 'user'),
                             config.get('ssh', 'hostname'),
                             config.get('ssh', 'port'),
                             'restore', action_args,
                             stdin=restore_script)


def main():

    cli_args = parse_cli_args()

    default_config_path = os.path.join(program_dir, 'config', 'defaults.ini')
    config_path = cli_args.config_path
    config = parse_config([default_config_path, config_path])

    if cli_args.restore:
        restore(config, cli_args.restore)
    else:
        back_up(config)

if __name__ == '__main__':
    main()
