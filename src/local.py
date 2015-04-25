#!/usr/bin/env python

import os
import os.path
import sys
import ConfigParser
import time


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
    remote_backup_path_patt = os.path.expanduser(
        config['paths']['remote_backup'])
    local_backup_path_patt = os.path.expanduser(
        config['paths']['local_backup'])
    # Evaluate date format sequences in paths
    remote_backup_path = time.strftime(remote_backup_path_patt)
    local_backup_path = time.strftime(local_backup_path_patt)

    try:
        os.makedirs(os.path.dirname(local_backup_path))
    except OSError:
        pass


if __name__ == '__main__':
    main()
