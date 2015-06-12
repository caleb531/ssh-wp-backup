#!/usr/bin/env python3

import configparser
import os
import shlex
import sys
import nose.tools as nose
import src.local as swb
from unittest.mock import ANY, mock_open, NonCallableMagicMock, patch
from fixtures.local import set_up, tear_down, mock_backups


TEST_CONFIG_PATH = 'tests/files/config.ini'
TEST_BACKUP_PATH = '~/Backups/mysite.sql.bz2'
TEST_BACKUP_PATH_TIMESTAMPED = '~/Backups/%Y/%m/%d/mysite.sql.bz2'


def get_config():
    config = configparser.RawConfigParser()
    config.read(TEST_CONFIG_PATH)
    return config


def test_config_parser():
    '''should parse configuration file correctly'''
    config = swb.parse_config(TEST_CONFIG_PATH)
    nose.assert_is_instance(config, configparser.RawConfigParser)


@nose.with_setup(set_up, tear_down)
def test_create_remote_backup():
    '''should create remote backup via SSH'''
    config = get_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'back-up',
        '~/\'public_html/mysite\'',
        'bzip2',
        '~/\'backups/mysite.sql.bz2\''],
        stdin=ANY, stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
def test_download_remote_backup():
    '''should download remote backup via SCP'''
    config = get_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'scp', '-P 2222', 'myname@mysite.com:~/\'backups/mysite.sql.bz2\'',
        os.path.expanduser(TEST_BACKUP_PATH)],
        stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
def test_create_dir_structure():
    '''should create intermediate directories'''
    config = get_config()
    swb.back_up(config)
    swb.os.makedirs.assert_called_with(
        os.path.expanduser(os.path.dirname(TEST_BACKUP_PATH)))


@nose.with_setup(set_up, tear_down)
@patch('src.local.os.makedirs', side_effect=OSError)
def test_create_dir_structure_silent_fail(makedirs):
    '''should fail silently if intermediate directories already exist'''
    config = get_config()
    swb.back_up(config)
    makedirs.assert_called_with(os.path.expanduser(
        os.path.dirname(TEST_BACKUP_PATH)))


@nose.with_setup(set_up, tear_down)
def test_purge_remote_backup():
    '''should purge remote backup after download'''
    config = get_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'purge-backup',
        '~/\'backups/mysite.sql.bz2\''],
        stdin=ANY, stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
def test_purge_oldest_backups():
    '''should purge oldest local backups after download'''
    config = get_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    swb.back_up(config)
    for path in mock_backups[:-3]:
        swb.os.remove.assert_any_call(path)


@nose.with_setup(set_up, tear_down)
def test_null_max_local_backups():
    '''should keep all backups if max_local_backups is not set'''
    config = get_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    config.remove_option('backup', 'max_local_backups')
    swb.back_up(config)
    nose.assert_equal(swb.os.remove.call_count, 0)


@nose.with_setup(set_up, tear_down)
def test_purge_empty_dirs():
    '''should purge empty timestamped directories'''
    config = get_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    swb.back_up(config)
    for path in mock_backups[:-3]:
        swb.os.rmdir.assert_any_call(path)


@nose.with_setup(set_up, tear_down)
@patch('src.local.os.rmdir', side_effect=OSError)
def test_keep_nonempty_dirs(rmdir):
    '''should not purge nonempty timestamped directories'''
    config = get_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    swb.back_up(config)
    for path in mock_backups[:-3]:
        rmdir.assert_any_call(path)


@nose.with_setup(set_up, tear_down)
@patch('src.local.back_up')
def test_main_back_up(back_up):
    '''should call back_up() when config path is passed to main()'''
    config = get_config()
    args = [swb.__file__, TEST_CONFIG_PATH]
    with patch('src.local.sys.argv', args, create=True):
        swb.main()
        back_up.assert_called_with(config, stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
@patch('src.local.shlex')
def test_missing_shlex_quote(shlex):
    '''should use pipes.quote() if shlex.quote() is missing (<3.3)'''
    del shlex.quote
    config = get_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call(
        # Only check if path is quoted (ignore preceding arguments)
        ([ANY] * 6) + ['~/\'backups/mysite.sql.bz2\''],
        stdin=ANY, stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
@patch('src.local.sys.exit')
def test_ssh_error(exit):
    '''should exit if SSH process returns non-zero exit code'''
    config = get_config()
    swb.subprocess.Popen.return_value.returncode = 3
    swb.back_up(config)
    exit.assert_called_with(3)


@nose.with_setup(set_up, tear_down)
def test_quiet_mode():
    '''should silence SSH output in quiet mode'''
    config = get_config()
    args = [swb.__file__, '-q', TEST_CONFIG_PATH]
    with patch('src.local.sys.argv', args, create=True):
        file_obj = mock_open()
        devnull = file_obj()
        with patch('src.local.open', file_obj, create=True):
            swb.main()
            file_obj.assert_any_call(os.devnull, 'w')
            swb.subprocess.Popen.assert_any_call(ANY, stdout=devnull,
                                                 stderr=devnull)


@nose.with_setup(set_up, tear_down)
@patch('src.local.restore')
def test_main_restore(restore):
    '''should call restore() when config path is passed to main()'''
    config = get_config()
    args = [swb.__file__, TEST_CONFIG_PATH, '-r', TEST_BACKUP_PATH]
    with patch('src.local.sys.argv', args, create=True):
        swb.main()
        swb.input.assert_called_with(ANY)
        restore.assert_called_with(config, TEST_BACKUP_PATH,
                                   stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
@patch('src.local.restore')
def test_force_mode(restore):
    '''should bypass restore confirmation in force mode'''
    config = get_config()
    args = [swb.__file__, '-f', TEST_CONFIG_PATH, '-r', TEST_BACKUP_PATH]
    with patch('src.local.sys.argv', args, create=True):
        swb.main()
        nose.assert_equal(swb.input.call_count, 0)
        restore.assert_called_with(config, TEST_BACKUP_PATH,
                                   stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
@patch('src.local.input')
def test_restore_confirm_cancel(input):
    '''should exit script when user cancels restore confirmation'''
    config = get_config()
    args = [swb.__file__, TEST_CONFIG_PATH, '-r', TEST_BACKUP_PATH]
    with patch('src.local.sys.argv', args, create=True):
        responses = ['n', 'N', ' n ', '']
        for response in responses:
            input.return_value = response
            with nose.assert_raises(Exception):
                swb.main()


@nose.with_setup(set_up, tear_down)
def test_upload_local_backup():
    '''should upload local backup to remote for restoration'''
    config = get_config()
    swb.restore(config, TEST_BACKUP_PATH, stdout=None, stderr=None)
    swb.subprocess.Popen.assert_any_call([
        'scp', '-P 2222', TEST_BACKUP_PATH,
        'myname@mysite.com:~/\'backups/mysite.sql.bz2\''],
        stdout=None, stderr=None)


@nose.with_setup(set_up, tear_down)
def test_process_wait_back_up():
    '''should wait for each process to finish when backing up'''
    config = get_config()
    swb.back_up(config)
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 3)


@nose.with_setup(set_up, tear_down)
def test_process_wait_restore():
    '''should wait for each process to finish when restoring'''
    config = get_config()
    swb.restore(config, TEST_BACKUP_PATH, stdout=None, stderr=None)
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 2)
