#!/usr/bin/env python3

import configparser
import os.path
from unittest.mock import MagicMock, ANY
import nose.tools as nose
import src.local as swb

swb.os = MagicMock()
swb.os.path.expanduser = os.path.expanduser
swb.os.path.dirname = os.path.dirname
swb.subprocess = MagicMock()

fake_stdout = MagicMock()
fake_stderr = MagicMock()


@nose.nottest
def get_test_config():
    config = configparser.RawConfigParser()
    config.read('tests/config/testconfig.ini')
    return config


@nose.nottest
def run_back_up(config):
    swb.back_up(config.get('ssh', 'user'),
                config.get('ssh', 'hostname'),
                config.get('ssh', 'port'),
                config.get('paths', 'wordpress'),
                config.get('paths', 'remote_backup'),
                config.get('backup', 'compressor'),
                config.get('paths', 'local_backup'),
                config.getint('backup', 'max_local_backups'),
                stdout=None, stderr=None)


def test_config_parser():
    '''should parse configuration file correctly'''
    config = swb.parse_config('tests/config/testconfig.ini')
    nose.assert_is_instance(config, configparser.RawConfigParser)


def test_create_remote_backup():
    '''should create remote backup via SSH'''
    config = get_test_config()
    run_back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'back-up',
        '~/\'public_html/mysite\'',
        'bzip2',
        '~/\'backups/mysite.sql.bz2\''], stdin=ANY, stdout=None, stderr=None)


def test_download_remote_backup():
    '''should download remote backup via SCP'''
    config = get_test_config()
    run_back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'scp', '-P 2222', 'myname@mysite.com:~/\'backups/mysite.sql.bz2\'',
        os.path.expanduser('~/Documents/Backups/mysite.sql.bz2')],
        stdout=None, stderr=None)


def test_create_dir_structure():
    '''should create intermediate directories'''
    config = get_test_config()
    run_back_up(config)
    swb.os.makedirs.assert_any_call(os.path.expanduser('~/Documents/Backups'))


def test_purge_remote_backup():
    '''should purge remote backup after download'''
    config = get_test_config()
    run_back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'purge-backup',
        '~/\'backups/mysite.sql.bz2\''], stdin=ANY, stdout=None, stderr=None)
