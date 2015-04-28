#!/usr/bin/env python

import argparse
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


# Parse command line arguments to the utility
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
def exec_cmd_via_ssh(user, hostname, port, cmd, cmd_args, **streams):

    # Construct Popen args by combining both lists of command arguments
    ssh_args = [
        'ssh',
        '-p {port}'.format(port=port),
        '{user}@{hostname}'.format(
            user=user,
            hostname=hostname),
        cmd
    ] + list(cmd_args)

    ssh = subprocess.Popen(ssh_args, **streams)
    # Wait for command to finish execution
    ssh.wait()

    return ssh


# Execute remote backup script to create remote backup
def create_remote_backup(user, hostname, port, wordpress_path,
                         remote_backup_path, backup_compressor):

    # Read remote script so as to pass contents to SSH session
    with open(os.path.join(program_dir, 'remote.py')) as remote_script:

        script_args = [wordpress_path, remote_backup_path, backup_compressor]
        ssh = exec_cmd_via_ssh(user, hostname, port, 'python -', script_args,
                               stdin=remote_script)

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

    exec_cmd_via_ssh(user, hostname, port, 'rm -f',
                     cmd_args=[remote_backup_path])


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
                         config.get('paths', 'remote_backup'),
                         config.get('backup', 'compressor'))

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


# Run restore script on remote
def restore(config, backup_path):

    # Read remote script so as to pass contents to SSH session
    with open(os.path.join(program_dir, 'restore.py')) as restore_script:

        script_args = [
            config.get('paths', 'wordpress')
            config.get('paths', 'remote_backup')
            config.get('backup', 'decompressor')
        ]
        ssh = exec_cmd_via_ssh(config.get('ssh', 'user'),
                               config.get('ssh', 'hostname'),
                               config.get('ssh', 'port'),
                               'python -', script_args, stdin=restore_script)

        if ssh.returncode != 0:
            sys.exit(ssh.returncode)


def main():

    cli_args = parse_cli_args()

    default_config_path = os.path.join(program_dir, 'config', 'defaults.ini')
    config_path = cli_args.config_path
    config = parse_config([default_config_path, config_path])

    if 'restore' in cli_args:
        restore(config, cli_args.restore)
    else:
        back_up(config)

if __name__ == '__main__':
    main()
