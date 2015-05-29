#!/usr/bin/env python3

import configparser
import os
import shlex
import sys
import nose.tools as nose
import src.local as swb
from unittest.mock import ANY, mock_open, NonCallableMagicMock, patch
from fixtures.local import before_all, before_each, after_each, mock_backups


TEST_CONFIG_PATH = 'tests/files/config.ini'
TEST_BACKUP_PATH = '~/Backups/mysite.sql.bz2'
TEST_BACKUP_PATH_TIMESTAMPED = '~/Backups/%Y/%m/%d/mysite.sql.bz2'


@nose.nottest
def get_test_config():
    config = configparser.RawConfigParser()
    config.read(TEST_CONFIG_PATH)
    return config


def test_config_parser():
    '''should parse configuration file correctly'''
    config = swb.parse_config(TEST_CONFIG_PATH)
    nose.assert_is_instance(config, configparser.RawConfigParser)


@nose.with_setup(before_each, after_each)
def test_create_remote_backup():
    '''should create remote backup via SSH'''
    config = get_test_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'back-up',
        '~/\'public_html/mysite\'',
        'bzip2',
        '~/\'backups/mysite.sql.bz2\''],
        stdin=ANY, stdout=None, stderr=None)


@nose.with_setup(before_each, after_each)
def test_download_remote_backup():
    '''should download remote backup via SCP'''
    config = get_test_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'scp', '-P 2222', 'myname@mysite.com:~/\'backups/mysite.sql.bz2\'',
        os.path.expanduser(TEST_BACKUP_PATH)],
        stdout=None, stderr=None)


@nose.with_setup(before_each, after_each)
def test_create_dir_structure():
    '''should create intermediate directories'''
    config = get_test_config()
    swb.back_up(config)
    swb.os.makedirs.assert_called_with(
        os.path.expanduser(os.path.dirname(TEST_BACKUP_PATH)))


@nose.with_setup(before_each, after_each)
def test_create_dir_structure_silent_fail():
    '''should fail silently if intermediate directories already exist'''
    config = get_test_config()
    with patch('src.local.os.makedirs', side_effect=OSError):
        swb.back_up(config)
        swb.os.makedirs.assert_called_with(
            os.path.expanduser(os.path.dirname(TEST_BACKUP_PATH)))


@nose.with_setup(before_each, after_each)
def test_purge_remote_backup():
    '''should purge remote backup after download'''
    config = get_test_config()
    swb.back_up(config)
    swb.subprocess.Popen.assert_any_call([
        'ssh', '-p 2222', 'myname@mysite.com', 'python3', '-', 'purge-backup',
        '~/\'backups/mysite.sql.bz2\''],
        stdin=ANY, stdout=None, stderr=None)


@nose.with_setup(before_each, after_each)
def test_purge_oldest_backups():
    '''should purge oldest local backups after download'''
    config = get_test_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    swb.back_up(config)
    for path in mock_backups[:-3]:
        swb.os.remove.assert_any_call(path)


@nose.with_setup(before_each, after_each)
def test_null_max_local_backups():
    '''should keep all backups if max_local_backups is not set'''
    config = get_test_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    config.remove_option('backup', 'max_local_backups')
    swb.back_up(config)
    nose.assert_equal(swb.os.remove.call_count, 0)


@nose.with_setup(before_each, after_each)
def test_purge_empty_dirs():
    '''should purge empty timestamped directories'''
    config = get_test_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    swb.back_up(config)
    for path in mock_backups[:-3]:
        swb.os.rmdir.assert_any_call(path)


@nose.with_setup(before_each, after_each)
def test_keep_nonempty_dirs():
    '''should not purge nonempty timestamped directories'''
    config = get_test_config()
    config.set('paths', 'local_backup', TEST_BACKUP_PATH_TIMESTAMPED)
    with patch('src.local.os.rmdir', side_effect=OSError):
        swb.back_up(config)
        for path in mock_backups[:-3]:
            swb.os.rmdir.assert_any_call(path)


@nose.with_setup(before_each, after_each)
def test_main_back_up():
    '''should call back_up() when config path is passed to main()'''
    config = get_test_config()
    args = [swb.__file__, TEST_CONFIG_PATH]
    with patch('src.local.sys.argv', args, create=True):
        with patch('src.local.back_up'):
            swb.main()
            swb.back_up.assert_called_with(config, stdout=None, stderr=None)


@nose.with_setup(before_each, after_each)
def test_missing_shlex_quote():
    '''should use pipes.quote() if shlex.quote() is missing (<3.3)'''
    with patch('src.local.shlex'):
        del swb.shlex.quote
        config = get_test_config()
        swb.back_up(config)
        swb.subprocess.Popen.assert_any_call(
            # Only check if path is quoted (ignore preceding arguments)
            ([ANY] * 6) + ['~/\'backups/mysite.sql.bz2\''],
            stdin=ANY, stdout=None, stderr=None)
        swb.shlex.quote = shlex.quote


@nose.with_setup(before_each, after_each)
def test_ssh_error():
    '''should exit if SSH process returns non-zero exit code'''
    config = get_test_config()
    swb.subprocess.Popen.return_value.returncode = 3
    with patch('src.local.sys.exit'):
        swb.back_up(config)
        swb.sys.exit.assert_called_with(3)


@nose.with_setup(before_each, after_each)
def test_quiet_mode():
    '''should silence SSH output in quiet mode'''
    config = get_test_config()
    args = [swb.__file__, '-q', TEST_CONFIG_PATH]
    with patch('src.local.sys.argv', args, create=True):
        file_obj = mock_open()
        devnull = file_obj()
        with patch('src.local.open', file_obj, create=True):
            swb.main()
            file_obj.assert_any_call(os.devnull, 'w')
            swb.subprocess.Popen.assert_any_call(ANY, stdout=devnull,
                                                 stderr=devnull)


@nose.with_setup(before_each, after_each)
def test_main_restore():
    '''should call restore() when config path is passed to main()'''
    config = get_test_config()
    args = [swb.__file__, TEST_CONFIG_PATH, '-r', TEST_BACKUP_PATH]
    with patch('src.local.sys.argv', args, create=True):
        with patch('src.local.restore'):
            swb.main()
            swb.input.assert_called_with(ANY)
            swb.restore.assert_called_with(config, TEST_BACKUP_PATH,
                                           stdout=None, stderr=None)


@nose.with_setup(before_each, after_each)
def test_force_mode():
    '''should bypass restore confirmation in force mode'''
    config = get_test_config()
    args = [swb.__file__, '-f', TEST_CONFIG_PATH, '-r', TEST_BACKUP_PATH]
    with patch('src.local.sys.argv', args, create=True):
        with patch('src.local.restore'):
            swb.main()
            nose.assert_equal(swb.input.call_count, 0)
            swb.restore.assert_called_with(config, TEST_BACKUP_PATH,
                                           stdout=None, stderr=None)


@nose.with_setup(before_each, after_each)
def test_restore_confirm_cancel():
    '''should exit script when user cancels restore confirmation'''
    config = get_test_config()
    args = [swb.__file__, TEST_CONFIG_PATH, '-r', TEST_BACKUP_PATH]
    with patch('src.local.sys.argv', args, create=True):
        with patch('src.local.input') as mock_input:
            responses = ['n', 'N', ' n ', '']
            for response in responses:
                mock_input.return_value = response
                with nose.assert_raises(Exception):
                    swb.main()


@nose.with_setup(before_each, after_each)
def test_upload_local_backup():
    '''should upload local backup to remote for restoration'''
    config = get_test_config()
    swb.restore(config, TEST_BACKUP_PATH, stdout=None, stderr=None)
    swb.subprocess.Popen.assert_any_call([
        'scp', '-P 2222', TEST_BACKUP_PATH,
        'myname@mysite.com:~/\'backups/mysite.sql.bz2\''],
        stdout=None, stderr=None)


@nose.with_setup(before_each, after_each)
def test_process_wait():
    '''should wait for each SSH process to finish'''
    config = get_test_config()
    swb.back_up(config)
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 3)
    swb.subprocess.Popen.return_value.wait.call_count = 0
    swb.restore(config, TEST_BACKUP_PATH, stdout=None, stderr=None)
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 2)


before_all()
