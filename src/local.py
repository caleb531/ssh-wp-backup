#!/usr/bin/env python

import ConfigParser
import glob
import os
import os.path
import re
import subprocess
import sys
import time


# Make program directory globally accessible to script
program_dir = os.path.dirname(os.path.realpath(__file__))


# Parse configuration files at given paths into dictionary
def parse_config(config_paths):

    config = ConfigParser.ConfigParser()
    config.read(config_paths)

    return config


# Create intermediate directories in local backup path if necessary
def create_directory_structure(config):

    try:
        os.makedirs(os.path.dirname(os.path.expanduser(
            config.get('paths', 'local_backup'))))
    except OSError:
        pass


# Execute remote backup script to create remote backup
def create_remote_backup(config):

    # Read remote script so as to pass contents to SSH session
    with open(os.path.join(program_dir, 'remote.py')) as remote_script:

        # Connect to remote via SSH and execute remote script
        ssh = subprocess.Popen([
            'ssh',
            '-p {port}'.format(port=config.get('ssh', 'port')),
            '{user}@{hostname}'.format(
                user=config.get('ssh', 'user'),
                hostname=config.get('ssh', 'hostname')),
            # Execute script passed to stdin with the following arguments
            'python -',
            config.get('paths', 'wordpress'),
            time.strftime(config.get('paths', 'remote_backup')),
            config.get('backup', 'compressor')
        ], stdin=remote_script)

        # Wait for remote backup to be created
        ssh.wait()


# Download remote backup to local system
def download_remote_backup(config):

    # Download backup to specified path
    # Send download progress to stdout
    scp = subprocess.Popen([
        'scp',
        '-P {port}'.format(port=config.get('ssh', 'port')),
        '{user}@{hostname}:{remote_path}'.format(
            user=config.get('ssh', 'user'),
            hostname=config.get('ssh', 'hostname'),
            remote_path=time.strftime(config.get('paths', 'remote_backup'))),
        time.strftime(config.get('paths', 'local_backup'))
    ])

    # Wait for local backup to finish downloading
    scp.wait()


# Forcefully remove backup from remote
def purge_remote_backup(config):

    ssh = subprocess.Popen([
        'ssh',
        '-p {port}'.format(port=config.get('ssh', 'port')),
        '{user}@{hostname}'.format(
            user=config.get('ssh', 'user'),
            hostname=config.get('ssh', 'hostname')),
        'rm -f',
        config.get('paths', 'remote_backup')
    ])

    # Wait for backup to be removed from remote
    ssh.wait()


# Purge oldest backups to keep number of backups within specified limit
def purge_oldest_backups(config):

    # Convert date format sequences to wildcards
    local_backup_path = re.sub('%[A-Za-z]', '*',
                               config.get('paths', 'local_backup'))

    # Retrieve list of local backups sorted from oldest to newest
    local_backups = sorted(glob.iglob(local_backup_path),
                           key=lambda path: os.stat(path).st_mtime)
    backups_to_purge = local_backups[:-config.getint('backup',
                                                     'max_local_backups')]

    for backup in backups_to_purge:
        os.remove(backup)


def main():

    default_config_path = os.path.join(program_dir, 'defaults.ini')
    config_path = sys.argv[1]
    config = parse_config([default_config_path, config_path])

    config.set('paths', 'local_backup', os.path.expanduser(
        config.get('paths', 'local_backup')))
    create_directory_structure(config)

    create_remote_backup(config)
    download_remote_backup(config)

    if config.getboolean('backup', 'purge_remote'):
        purge_remote_backup(config)

    if config.has_option('backup', 'max_local_backups') and not os.path.isdir(
       config.get('paths', 'local_backup')):
        purge_oldest_backups(config)

if __name__ == '__main__':
    main()
