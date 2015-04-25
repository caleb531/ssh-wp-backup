#!/usr/bin/env python

import os
import os.path
import sys
import ConfigParser
import time
import subprocess


def parse_config(config_path):

    parser = ConfigParser.ConfigParser()
    parser.read(config_path)
    config = {}

    for section in parser.sections():
        config[section] = dict(parser.items(section))

    return config


def main():

    config_path = sys.argv[1]
    program_dir = os.path.realpath('src')
    default_config_path = os.path.join(program_dir, 'defaults.ini')

    config = parse_config([default_config_path, config_path])

    # Expand ~ to full home folder path for all backup paths
    config['paths']['local_backup'] = os.path.expanduser(
        config['paths']['local_backup'])
    # Evaluate date format sequences in paths
    remote_backup_path = time.strftime(config['paths']['remote_backup'])
    local_backup_path = time.strftime(config['paths']['local_backup'])

    try:
        os.makedirs(os.path.dirname(local_backup_path))
    except OSError:
        pass

    with open(os.path.join(program_dir, 'remote.sh'), 'r') as remote:
        remote_script_contents = remote.read()

    cat = subprocess.Popen([
        'cat',
        os.path.join(program_dir, 'remote.sh')
    ], shell=False, stdout=subprocess.PIPE)

    ssh = subprocess.Popen([
        'ssh',
        '-p {}'.format(config['ssh']['port']),
        '{}@{}'.format(config['ssh']['user'], config['ssh']['hostname']),
        'bash -s -',
        config['paths']['wordpress'],
        config['paths']['remote_backup'],
        config['backup']['compressor']
    ], shell=False, stdout=subprocess.PIPE,
       stderr=subprocess.PIPE, stdin=cat.stdout)

    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print >>sys.stderr, "ERROR: %s" % error
    else:
        print result

if __name__ == '__main__':
    main()
