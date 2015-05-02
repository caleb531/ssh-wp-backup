#!/usr/bin/env python3

import argparse
import configparser
import glob
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
        '--quiet',
        '-q',
        action='store_true',
        help='silences stdout and stderr')

    parser.add_argument(
        'config_path',
        help='the path to a configuration file (.ini)')

    parser.add_argument(
        '--restore',
        '-r',
        help='the path to a compressed backup file from which to restore')

    parser.add_argument(
        '--force',
        '-f',
        action='store_true',
        help='bypasses the confirmation prompt when restoring from backup')

    cli_args = parser.parse_args()
    return cli_args


# Parse configuration files at given paths into object
def parse_config(config_paths):

    config = configparser.RawConfigParser()
    config.read(config_paths)

    return config


# Create intermediate directories in local backup path if necessary
def create_dir_structure(path):

    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass


# Escape command line argument (currently only escapes spaces)
def escape_cli_arg(string):

    return string.replace(' ', '\\ ')


# Connect to remote via SSH and execute remote script
def exec_on_remote(user, hostname, port, action, action_args, stdout, stderr):

    # Read remote script so as to pass contents to SSH session
    with open(os.path.join(program_dir, 'remote.py')) as remote_script:

        action_args = [escape_cli_arg(arg) for arg in action_args]

        # Construct Popen args by combining both lists of command arguments
        ssh_args = [
            'ssh',
            '-p {0}'.format(port),
            '{0}@{1}'.format(user, hostname),
            'python3',
            '-',
            action  # The action to run on remote
        ] + action_args

        ssh = subprocess.Popen(ssh_args, stdin=remote_script,
                               stdout=stdout, stderr=stderr)

        # Wait for command to finish execution
        ssh.wait()

        if ssh.returncode != 0:
            sys.exit(ssh.returncode)


# Execute remote backup script to create remote backup
def create_remote_backup(user, hostname, port, wordpress_path,
                         remote_backup_path, backup_compressor,
                         stdout, stderr):

    exec_on_remote(user, hostname, port, 'back-up', [
        wordpress_path,
        backup_compressor,
        remote_backup_path
    ], stdout, stderr)


# Download remote backup to local system
def download_remote_backup(user, hostname, port, remote_backup_path,
                           local_backup_path, stdout, stderr):

    # Download backup to specified path
    # Send download progress to stdout
    scp = subprocess.Popen([
        'scp',
        '-P {0}'.format(port),
        '{0}@{1}:{2}'.format(user, hostname,
                             escape_cli_arg(remote_backup_path)),
        local_backup_path
    ], stdout=stdout, stderr=stderr)

    # Wait for local backup to finish downloading
    scp.wait()


# Forcefully remove backup from remote
def purge_remote_backup(user, hostname, port, remote_backup_path,
                        stdout, stderr):

    exec_on_remote(user, hostname, port, 'purge-backup', [remote_backup_path],
                   stdout, stderr)


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
def back_up(config, stdout, stderr):

    # Expand home directory for local backup path
    config.set('paths', 'local_backup', os.path.expanduser(
        config.get('paths', 'local_backup')))
    # Expand date format sequences in both backup paths
    expanded_local_backup_path = time.strftime(
        config.get('paths', 'local_backup'))
    expanded_remote_backup_path = time.strftime(
        config.get('paths', 'remote_backup'))

    create_dir_structure(expanded_local_backup_path)

    create_remote_backup(config.get('ssh', 'user'),
                         config.get('ssh', 'hostname'),
                         config.get('ssh', 'port'),
                         config.get('paths', 'wordpress'),
                         config.get('paths', 'remote_backup'),
                         config.get('backup', 'compressor'),
                         stdout, stderr)

    download_remote_backup(config.get('ssh', 'user'),
                           config.get('ssh', 'hostname'),
                           config.get('ssh', 'port'),
                           expanded_remote_backup_path,
                           expanded_local_backup_path,
                           stdout, stderr)

    purge_remote_backup(config.get('ssh', 'user'),
                        config.get('ssh', 'hostname'),
                        config.get('ssh', 'port'),
                        expanded_remote_backup_path,
                        stdout, stderr)

    if config.has_option('backup', 'max_local_backups') and not os.path.isdir(
       config.get('paths', 'local_backup')):
        purge_oldest_backups(config.get('paths', 'local_backup'),
                             config.getint('backup', 'max_local_backups'))


# Restore the chosen database revision to the Wordpress install on remote
def restore(config, local_backup_path, stdout, stderr):

    scp = subprocess.Popen([
        'scp',
        '-P {0}'.format(config.get('ssh', 'port')),
        local_backup_path,
        '{0}@{1}:{2}'.format(
            config.get('ssh', 'user'),
            config.get('ssh', 'hostname'),
            escape_cli_arg(config.get('paths', 'remote_backup')))
    ], stdout=stdout, stderr=stderr)
    scp.wait()

    action_args = [
        config.get('paths', 'wordpress'),
        config.get('paths', 'remote_backup'),
        config.get('backup', 'decompressor')
    ]
    ssh = exec_on_remote(config.get('ssh', 'user'),
                         config.get('ssh', 'hostname'),
                         config.get('ssh', 'port'),
                         'restore', action_args,
                         stdout, stderr)


def main():

    cli_args = parse_cli_args()

    default_config_path = os.path.join(program_dir, 'config', 'defaults.ini')
    config_path = cli_args.config_path
    config = parse_config([default_config_path, config_path])

    # Open /dev/null to redirect stdout/stderr if necessary
    with open(os.devnull, 'wb') as devnull:

        if cli_args.quiet:
            stdout = stderr = devnull
        else:
            stdout = stderr = None

        if cli_args.restore:
            # Prompt user for confirmation before restoring from backup
            if not cli_args.force:
                print('Backup will overwrite WordPress database')
                answer = input('Do you want to continue? (y/n) ')
                if 'y' not in answer.lower():
                    raise Exception('User canceled. Aborting.')
            restore(config, cli_args.restore, stdout, stderr)
        else:
            back_up(config, stdout, stderr)

if __name__ == '__main__':
    main()
