#!/usr/bin/env python3

import argparse
import configparser
import glob
import os
import os.path
import pipes
import re
import shlex
import subprocess
import sys
import time


# Make program-related paths globally accessible to script
program_dir = os.path.dirname(os.path.realpath(__file__))
remote_driver_path = os.path.join(program_dir, 'remote.py')


# Create intermediate directories in local backup path if necessary
def create_dir_structure(local_backup_path):

    try:
        os.makedirs(os.path.dirname(local_backup_path))
    except OSError:
        pass


# Unquote ~ at beginning of path so it can be evaluated to home directory path
def unquote_home_dir(path):

    return re.sub('^\'~/', '~/\'', path)


# Quote shell arguments in a backwards-compatible manner
def quote_arg(arg):

    if hasattr(shlex, 'quote'):
        # shlex.quote was introduced in v3.3
        quoted_arg = shlex.quote(str(arg))
    else:
        # pipes.quote is deprecated, but use it if shlex.quote is unavailable
        quoted_arg = pipes.quote(str(arg))

    quoted_arg = unquote_home_dir(quoted_arg)
    return quoted_arg


# Connect to remote via SSH and execute remote script
def exec_on_remote(ssh_user, ssh_hostname, ssh_port, *,
                   action, action_args, stdout, stderr):

    # Read remote script so as to pass contents to SSH session
    with open(remote_driver_path, 'r') as remote_script:

        action_args = [quote_arg(arg) for arg in action_args]

        # Construct Popen args by combining both lists of command arguments
        ssh_args = [
            'ssh',
            '-p {}'.format(ssh_port),
            '{}@{}'.format(ssh_user, ssh_hostname),
            'python3',
            '-',
            action  # The action to run on remote
        ] + action_args

        ssh = subprocess.Popen(
            ssh_args, stdin=remote_script, stdout=stdout, stderr=stderr)

        # Wait for command to finish execution
        ssh.wait()

        if ssh.returncode != 0:
            sys.exit(ssh.returncode)


# Transfer a file from remote to local (or vice-versa) using SCP
def transfer_file(ssh_user, ssh_hostname, ssh_port, *,
                  src_path, dest_path, action, stdout, stderr):

    scp_args = ['scp', '-P {}'.format(ssh_port)]

    if action == 'upload':
        scp_args += [
            src_path,
            '{}@{}:{}'.format(ssh_user, ssh_hostname, quote_arg(dest_path))
        ]
    else:
        # Default action is to download file
        scp_args += [
            '{}@{}:{}'.format(ssh_user, ssh_hostname, quote_arg(src_path)),
            dest_path
        ]

    scp = subprocess.Popen(scp_args, stdout=stdout, stderr=stderr)

    scp.wait()


# Execute remote backup script to create remote backup
def create_remote_backup(ssh_user, ssh_hostname, ssh_port, *,
                         wordpress_path, remote_backup_path,
                         backup_compressor, full_backup, stdout, stderr):

    exec_on_remote(
        ssh_user=ssh_user,
        ssh_hostname=ssh_hostname,
        ssh_port=ssh_port,
        action='back-up',
        action_args=[
            wordpress_path,
            backup_compressor,
            remote_backup_path,
            full_backup
        ],
        stdout=stdout, stderr=stderr)


# Download remote backup to local system
def download_remote_backup(ssh_user, ssh_hostname, ssh_port, *,
                           remote_backup_path, local_backup_path,
                           stdout, stderr):

    transfer_file(
        ssh_user=ssh_user,
        ssh_hostname=ssh_hostname,
        ssh_port=ssh_port,
        src_path=remote_backup_path,
        dest_path=local_backup_path,
        action='download',
        stdout=stdout, stderr=stderr)


# Uploads the given local backup to the given remote destination
def upload_local_backup(ssh_user, ssh_hostname, ssh_port, *,
                        local_backup_path, remote_backup_path,
                        stdout, stderr):

    transfer_file(
        ssh_user=ssh_user,
        ssh_hostname=ssh_hostname,
        ssh_port=ssh_port,
        src_path=local_backup_path,
        dest_path=remote_backup_path,
        action='upload',
        stdout=stdout, stderr=stderr)


# Restores the local backup after upload to remote
def restore_remote_backup(ssh_user, ssh_hostname, ssh_port, *,
                          wordpress_path, remote_backup_path,
                          backup_decompressor, full_backup, stdout, stderr):

    exec_on_remote(
        ssh_user=ssh_user,
        ssh_hostname=ssh_hostname,
        ssh_port=ssh_port,
        action='restore',
        action_args=[
            wordpress_path,
            remote_backup_path,
            backup_decompressor,
            full_backup
        ],
        stdout=stdout, stderr=stderr)


# Forcefully remove backup from remote
def purge_remote_backup(ssh_user, ssh_hostname, ssh_port, *,
                        remote_backup_path, stdout, stderr):

    exec_on_remote(
        ssh_user=ssh_user,
        ssh_hostname=ssh_hostname,
        ssh_port=ssh_port,
        action='purge-backup',
        action_args=[remote_backup_path],
        stdout=stdout, stderr=stderr)


# Retrieve a file's last modified time in seconds
def get_last_modified_time(path):

    return os.stat(path).st_mtime


# Purge empty directories originally created to store now-purged backups
def purge_empty_dirs(dir_path):

    while dir_path != '/':
        dir_path = os.path.dirname(dir_path)
        dir_name = os.path.basename(dir_path)
        # If next parent directory represents a timestamped directory
        if '*' in dir_name:
            expanded_dir_paths = glob.iglob(dir_path)
            # Purge all empty timestamped directories
            for expanded_dir_path in expanded_dir_paths:
                try:
                    os.rmdir(expanded_dir_path)
                except OSError:
                    pass


# Purge oldest backups to keep number of backups within specified limit
def purge_oldest_backups(local_backup_path, *, max_local_backups):

    # Convert date format sequences to wildcards
    local_backup_path = re.sub(r'%\-?[A-Za-z]', '*', local_backup_path)

    # Retrieve list of local backups sorted from oldest to newest
    local_backups = sorted(glob.iglob(local_backup_path),
                           key=get_last_modified_time)
    backups_to_purge = local_backups[:-max_local_backups]

    for backup in backups_to_purge:
        os.remove(backup)

    # Purge timestamped directories that are now empty
    purge_empty_dirs(local_backup_path)


# Run backup script on remote
def back_up(config, *, stdout=None, stderr=None):

    # Expand home directory for local backup path
    config.set('paths', 'local_backup', os.path.expanduser(
        config.get('paths', 'local_backup')))

    # Expand date format sequences in both backup paths
    expanded_local_backup_path = time.strftime(
        config.get('paths', 'local_backup'))
    expanded_remote_backup_path = time.strftime(
        config.get('paths', 'remote_backup'))

    create_remote_backup(
        ssh_user=config.get('ssh', 'user'),
        ssh_hostname=config.get('ssh', 'hostname'),
        ssh_port=config.get('ssh', 'port'),
        wordpress_path=config.get('paths', 'wordpress'),
        remote_backup_path=expanded_remote_backup_path,
        backup_compressor=config.get('backup', 'compressor'),
        full_backup=config.getboolean('backup', 'full_backup', fallback=False),
        stdout=stdout, stderr=stderr)

    create_dir_structure(local_backup_path=expanded_local_backup_path)

    download_remote_backup(
        ssh_user=config.get('ssh', 'user'),
        ssh_hostname=config.get('ssh', 'hostname'),
        ssh_port=config.get('ssh', 'port'),
        remote_backup_path=expanded_remote_backup_path,
        local_backup_path=expanded_local_backup_path,
        stdout=stdout, stderr=stderr)

    purge_remote_backup(
        ssh_user=config.get('ssh', 'user'),
        ssh_hostname=config.get('ssh', 'hostname'),
        ssh_port=config.get('ssh', 'port'),
        remote_backup_path=expanded_remote_backup_path,
        stdout=stdout, stderr=stderr)

    if config.has_option('backup', 'max_local_backups'):
        purge_oldest_backups(
            local_backup_path=config.get('paths', 'local_backup'),
            max_local_backups=config.getint('backup', 'max_local_backups'))


# Restore the chosen database revision to the Wordpress install on remote
def restore(config, *, local_backup_path, stdout=None, stderr=None):

    expanded_remote_backup_path = time.strftime(
        config.get('paths', 'remote_backup'))

    upload_local_backup(
        ssh_user=config.get('ssh', 'user'),
        ssh_hostname=config.get('ssh', 'hostname'),
        ssh_port=config.get('ssh', 'port'),
        local_backup_path=local_backup_path,
        remote_backup_path=expanded_remote_backup_path,
        backup_compressor=config.get('backup', 'compressor'),
        stdout=stdout, stderr=stderr)

    restore_remote_backup(
        ssh_user=config.get('ssh', 'user'),
        ssh_hostname=config.get('ssh', 'hostname'),
        ssh_port=config.get('ssh', 'port'),
        action='restore',
        wordpress_path=config.get('paths', 'wordpress'),
        remote_backup_path=config.get('paths', 'remote_backup'),
        backup_decompressor=config.get('backup', 'decompressor'),
        full_backup=config.getboolean('backup', 'full_backup', fallback=False),
        stdout=stdout, stderr=stderr)


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
def parse_config(config_path):

    config = configparser.RawConfigParser()
    config.read(config_path)

    return config


def main():

    cli_args = parse_cli_args()
    config = parse_config(cli_args.config_path)

    # Open /dev/null to redirect stdout/stderr if necessary
    with open(os.devnull, 'w') as devnull:

        if cli_args.quiet:
            stdout = stderr = devnull
        else:
            stdout = stderr = None

        if cli_args.restore:
            # Prompt user for confirmation before restoring from backup
            if not cli_args.force:
                print('Backup will overwrite WordPress database')
                answer = input('Do you want to continue? (y/n) ')
                if not answer.lower().lstrip().startswith('y'):
                    raise Exception('User canceled. Aborting.')
            restore(
                config, local_backup_path=cli_args.restore,
                stdout=stdout, stderr=stderr)
        else:
            back_up(config, stdout=stdout, stderr=stderr)


if __name__ == '__main__':
    main()
