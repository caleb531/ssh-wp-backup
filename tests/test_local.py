#!/usr/bin/env python3

import configparser
import os
import nose.tools as nose
import swb.local as swb
from mock import call, NonCallableMock, patch
# from tests.fixtures.local import set_up, tear_down, mock_backups


def test_parse_config():
    """should correctly parse the supplied configuration file"""
    config_path = 'tests/files/config.ini'
    config = swb.parse_config(config_path)
    expected_config = configparser.RawConfigParser()
    expected_config.read(config_path)
    nose.assert_equal(config, expected_config)


@patch('os.makedirs')
def test_create_dir_structure(makedirs):
    """should create the directory structure for the supplied path"""
    swb.create_dir_structure('a/b c/d')
    makedirs.assert_called_once_with('a/b c')


@patch('os.makedirs', side_effect=OSError)
def test_create_dir_structure_silent_fail(makedirs):
    """should fail silently if directory structure already exists"""
    swb.create_dir_structure('a/b c/d')
    makedirs.assert_called_once_with('a/b c')


def test_unquote_home_dir_path_with_tilde():
    """should unquote the tilde (~) in the supplied quoted path"""
    unquoted_path = swb.unquote_home_dir('\'~/a/b c/d\'')
    nose.assert_equal(unquoted_path, '~/\'a/b c/d\'')


def test_unquote_home_dir_path_without_tilde():
    """should return the supplied quoted path"""
    unquoted_path = swb.unquote_home_dir('\'/a/b c/d\'')
    nose.assert_equal(unquoted_path, '\'/a/b c/d\'')


@patch('swb.local.unquote_home_dir', side_effect=lambda x: x)
def test_quote_arg(unquote_home_dir):
    """should correctly quote arguments passed to the shell"""
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')
    unquote_home_dir.assert_called_once_with('\'a/b c/d\'')


@patch('swb.local.shlex')
def test_quote_arg_py32(shlex):
    """should correctly quote arguments passed to the shell on Python 3.2"""
    del shlex.quote
    nose.assert_false(hasattr(shlex, 'quote'))
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')


@patch('subprocess.Popen', return_value=NonCallableMock(returncode=0))
@patch('builtins.open')
def test_exec_on_remote(local_open, popen):
    """should execute script on remote server"""
    swb.exec_on_remote(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        action='back-up',
        action_args=['~/public_html/mysite', 'bzip2 -v', 'a/b c/d', 'False'],
        stdout=1, stderr=2)
    popen.assert_called_once_with([
        'ssh', '-p 2222', 'myname@mysite.com',
        'python3', '-', 'back-up', '~/\'public_html/mysite\'',
        '\'bzip2 -v\'', '\'a/b c/d\'', 'False'],
        stdin=local_open.return_value.__enter__(), stdout=1, stderr=2)
    popen.return_value.wait.assert_called_once_with()


@patch('subprocess.Popen', return_value=NonCallableMock(returncode=3))
@patch('builtins.open')
@patch('sys.exit')
def test_exec_on_remote_nonzero_return(exit, local_open, popen):
    """should exit script if nonzero status code is returned"""
    swb.exec_on_remote(
        'a', 'b.com', '2222', 'c', ['d', 'e', 'f', 'g'], stdout=1, stderr=2)
    exit.assert_called_once_with(3)


@patch('subprocess.Popen')
def test_transfer_file_download(popen):
    """should download backup from remote server when backing up"""
    swb.transfer_file(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        src_path='a/b c/d', dest_path='e/f g/h',
        action='download', stdout=1, stderr=2)
    popen.assert_called_once_with(
        ['scp', '-P 2222', 'myname@mysite.com:\'a/b c/d\'', 'e/f g/h'],
        stdout=1, stderr=2)
    popen.return_value.wait.assert_called_once_with()


@patch('subprocess.Popen')
def test_transfer_file_upload(popen):
    """should upload backup to remote server when restoring"""
    swb.transfer_file(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        src_path='a/b c/d', dest_path='e/f g/h',
        action='upload', stdout=1, stderr=2)
    popen.assert_called_once_with(
        ['scp', '-P 2222', 'a/b c/d', 'myname@mysite.com:\'e/f g/h\''],
        stdout=1, stderr=2)
    popen.return_value.wait.assert_called_once_with()


@patch('swb.local.exec_on_remote')
def test_create_remote_backup(exec_on_remote):
    """should execute remote script when creating remote backup"""
    swb.create_remote_backup(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        wordpress_path='a/b c/d', remote_backup_path='e/f g/h',
        backup_compressor='bzip2 -v', full_backup=False,
        stdout=1, stderr=2)
    exec_on_remote.assert_called_once_with(
        'myname', 'mysite.com', '2222', 'back-up',
        ['a/b c/d', 'bzip2 -v', 'e/f g/h', False],
        stdout=1, stderr=2)


@patch('swb.local.transfer_file')
def test_download_remote_backup(transfer_file):
    """should download remote backup after creation"""
    swb.download_remote_backup(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        remote_backup_path='a/b c/d', local_backup_path='e/f g/h',
        stdout=1, stderr=2)
    transfer_file.assert_called_once_with(
        'myname', 'mysite.com', '2222',
        'a/b c/d', 'e/f g/h', 'download',
        stdout=1, stderr=2)


@patch('swb.local.exec_on_remote')
def test_purge_remote_backup(exec_on_remote):
    """should purge remote backup after download"""
    swb.purge_remote_backup(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        remote_backup_path='a/b c/d', stdout=1, stderr=2)
    exec_on_remote.assert_called_once_with(
        'myname', 'mysite.com', '2222', 'purge-backup', ['a/b c/d'],
        stdout=1, stderr=2)


def test_get_last_modified_time():
    """should retrieve correct last modified time of the supplied path"""
    nose.assert_equal(
        swb.get_last_modified_time('swb/local.py'),
        os.stat('swb/local.py').st_mtime)


@patch('glob.iglob', side_effect=[
    ['/a/b/2011/02/03', '/a/b/2011/02/04'],
    ['/a/b/2011/02'],
    ['/a/b/2010', '/a/b/2011'],
    ['/a/b'],
    ['/a']
])
@patch('os.rmdir')
def test_purge_empty_dirs(rmdir, iglob):
    """should purge empty timestamped directories"""
    swb.purge_empty_dirs('/a/b/*/*/*/c')
    nose.assert_equal(iglob.call_count, 3)
    nose.assert_equal(iglob.call_args_list, [
        call('/a/b/*/*/*'),
        call('/a/b/*/*'),
        call('/a/b/*')
    ])
    nose.assert_equal(rmdir.call_args_list, [
        call('/a/b/2011/02/03'),
        call('/a/b/2011/02/04'),
        call('/a/b/2011/02'),
        call('/a/b/2010'),
        call('/a/b/2011')
    ])


@patch('glob.iglob', side_effect=[
    ['/a/b/2011/02/03', '/a/b/2011/02/04'],
    ['/a/b/2011/02'],
    ['/a/b/2010', '/a/b/2011'],
    ['/a/b'],
    ['/a']
])
@patch('os.rmdir', side_effect=OSError)
def test_purge_empty_dirs_silent_fail(rmdir, iglob):
    """should ignore non-empty directories when purging empty directories"""
    swb.purge_empty_dirs('/a/b/*/*/*/c')
    nose.assert_equal(iglob.call_count, 3)
    nose.assert_equal(rmdir.call_count, 5)
