#!/usr/bin/env python3

import configparser
import os
import sys
import nose.tools as nose
import mocks
import src.local as swb

mocks.mock_module_imports(swb)
TEST_CONFIG_PATH = 'tests/config/testconfig.ini'


@nose.nottest
def get_test_config():
    config = configparser.RawConfigParser()
    config.read(TEST_CONFIG_PATH)
    return config


def test_config_parser():
    '''should parse configuration file correctly'''
    config = swb.parse_config('tests/config/testconfig.ini')
    nose.assert_is_instance(config, configparser.RawConfigParser)


def test_create_remote_backup():
    '''should create remote backup via SSH'''
    config = get_test_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'back-up',
        '~/\'public_html/mysite\'',
        'bzip2',
        '~/\'backups/mysite.sql.bz2\''],
        stdin=mocks.ANY, stdout=None, stderr=None)


def test_download_remote_backup():
    '''should download remote backup via SCP'''
    config = get_test_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'scp', '-P 2222', 'myname@mysite.com:~/\'backups/mysite.sql.bz2\'',
        os.path.expanduser('~/Backups/mysite.sql.bz2')],
        stdout=None, stderr=None)


def test_create_dir_structure():
    '''should create intermediate directories'''
    config = get_test_config()
    swb.back_up(config)
    swb.os.makedirs.assert_any_call(os.path.expanduser('~/Backups'))


def test_create_dir_structure_silent_fail():
    '''should fail silently if intermediate directories already exist'''
    config = get_test_config()
    with mocks.patch('src.local.os.makedirs', side_effect=OSError):
        swb.back_up(config)
        swb.os.makedirs.assert_any_call(os.path.expanduser('~/Backups'))
        swb.os.makedirs = mocks.MagicMock()


def test_purge_remote_backup():
    '''should purge remote backup after download'''
    config = get_test_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'purge-backup',
        '~/\'backups/mysite.sql.bz2\''],
        stdin=mocks.ANY, stdout=None, stderr=None)


def test_purge_oldest_backups():
    '''should purge oldest local backups after download'''
    config = get_test_config()
    config.set('paths', 'local_backup', '~/Backups/%Y/%m/%d/mysite.sql.bz2')
    swb.back_up(config)
    for path in mocks.mock_backups[:-3]:
        swb.os.remove.assert_any_call(path)


def test_purge_empty_dirs():
    '''should purge empty timestamped directories'''
    config = get_test_config()
    config.set('paths', 'local_backup', '~/Backups/%Y/%m/%d/mysite.sql.bz2')
    swb.back_up(config)
    for path in mocks.mock_backups[:-3]:
        swb.os.rmdir.assert_any_call(path)


@mocks.patch('src.local.back_up')
def test_main(mock_back_up):
    '''should call back_up() when config path is passed to main()'''
    config = get_test_config()
    swb.sys.argv = [swb.__file__, TEST_CONFIG_PATH]
    swb.main()
    swb.back_up.assert_any_call(config, stdout=None, stderr=None)
