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

    config = ConfigParser.RawConfigParser()
    config.read(config_paths)

    return config


# Create intermediate directories in local backup path if necessary
def create_dir_structure(path):

    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass


# Execute remote backup script to create remote backup
def create_remote_backup(user, hostname, port, wordpress_path,
                         remote_backup_path, backup_compressor):

    # Read remote script so as to pass contents to SSH session
    with open(os.path.join(program_dir, 'remote.py')) as remote_script:

        # Connect to remote via SSH and execute remote script
        ssh = subprocess.Popen([
            'ssh',
            '-p {port}'.format(port=port),
            '{user}@{hostname}'.format(
                user=user,
                hostname=hostname),
            # Execute script passed to stdin with the following arguments
            'python -',
            wordpress_path,
            remote_backup_path,
            backup_compressor
        ], stdin=remote_script)

        # Wait for remote backup to be created
        ssh.wait()

        # If remote backup script encountered an exception
        if ssh.returncode != 0:
            sys.exit(ssh.returncode)


# Download remote backup to local system
def download_remote_backup(user, hostname, port, remote_backup_path,
                           local_backup_path):

    # Download backup to specified path
    # Send download progress to stdout
    scp = subprocess.Popen([
        'scp',
        '-P {port}'.format(port=port),
        '{user}@{hostname}:{remote_path}'.format(
            user=user,
            hostname=hostname,
            remote_path=remote_backup_path),
        local_backup_path
    ])

    # Wait for local backup to finish downloading
    scp.wait()


# Forcefully remove backup from remote
def purge_remote_backup(user, hostname, port, remote_backup_path):

    ssh = subprocess.Popen([
        'ssh',
        '-p {port}'.format(port=port),
        '{user}@{hostname}'.format(
            user=user,
            hostname=hostname),
        'rm -f',
        remote_backup_path
    ])

    # Wait for backup to be removed from remote
    ssh.wait()


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


def main():

    default_config_path = os.path.join(program_dir, 'config', 'defaults.ini')
    config_path = sys.argv[1]
    config = parse_config([default_config_path, config_path])

    config.set('paths', 'local_backup', os.path.expanduser(
        config.get('paths', 'local_backup')))
    create_dir_structure(time.strftime(config.get('paths', 'local_backup')))

    create_remote_backup(config.get('ssh', 'user'),
                         config.get('ssh', 'hostname'),
                         config.get('ssh', 'port'),
                         config.get('paths', 'wordpress'),
                         time.strftime(config.get('paths', 'remote_backup')),
                         config.get('backup', 'compressor'))

    download_remote_backup(config.get('ssh', 'user'),
                           config.get('ssh', 'hostname'),
                           config.get('ssh', 'port'),
                           time.strftime(config.get('paths', 'remote_backup')),
                           time.strftime(config.get('paths', 'local_backup')))

    if config.getboolean('backup', 'purge_remote'):
        purge_remote_backup(config.get('ssh', 'user'),
                            config.get('ssh', 'hostname'),
                            config.get('ssh', 'port'),
                            time.strftime(config.get('paths',
                                                     'remote_backup')))

    if config.has_option('backup', 'max_local_backups') and not os.path.isdir(
       config.get('paths', 'local_backup')):
        purge_oldest_backups(config.get('paths', 'local_backup'),
                             config.getint('backup', 'max_local_backups'))

if __name__ == '__main__':
    main()
