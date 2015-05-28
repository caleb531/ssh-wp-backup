#!/usr/bin/env python3

import configparser
import glob
import os.path
import re
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, ANY
import nose.tools as nose
import src.local as swb


class AttrObject(object):
    """instantiate an object of attributes"""
    pass


def mock_os_stat(path):
    date_ymd = re.search('\d+\-\d+\-\d+', path).group(0)
    stats = AttrObject()
    stats.st_mtime = datetime.strptime(date_ymd, '%Y-%m-%d')
    return stats


swb.os = MagicMock()
swb.os.makedirs = MagicMock()
swb.os.remove = MagicMock()
swb.os.stat = mock_os_stat
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
        os.path.expanduser('~/Backups/mysite.sql.bz2')],
        stdout=None, stderr=None)


def test_create_dir_structure():
    '''should create intermediate directories'''
    config = get_test_config()
    run_back_up(config)
    swb.os.makedirs.assert_any_call(os.path.expanduser('~/Backups'))


def test_purge_remote_backup():
    '''should purge remote backup after download'''
    config = get_test_config()
    run_back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'purge-backup',
        '~/\'backups/mysite.sql.bz2\''], stdin=ANY, stdout=None, stderr=None)


def test_purge_oldest_backups():
    '''should purge oldest local backups after download'''
    config = get_test_config()
    config.set('paths', 'local_backup', '~/Backups/%Y-%m-%d/mysite.sql.bz2')
    mock_backups = [
        '~/Backups/2011-02-03/mysite.sql.bz2',
        '~/Backups/2012-03-04/mysite.sql.bz2',
        '~/Backups/2013-04-05/mysite.sql.bz2',
        '~/Backups/2014-05-06/mysite.sql.bz2',
        '~/Backups/2015-06-07/mysite.sql.bz2'
    ]
    swb.glob.iglob = MagicMock(return_value=mock_backups)
    run_back_up(config)
    for path in mock_backups[:-3]:
        swb.os.remove.assert_any_call(path)
    swb.glob.iglob = glob.iglob
