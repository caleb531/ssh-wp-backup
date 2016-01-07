#!/usr/bin/env python3

import configparser
import nose.tools as nose
import swb.local as swb
from mock import NonCallableMock, patch
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


def test_quote_arg():
    """should correctly quote arguments passed to the shell"""
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')


@patch('swb.local.shlex')
def test_quote_arg_py32(shlex):
    """should correctly quote arguments passed to the shell on Python 3.2"""
    del shlex.quote
    nose.assert_false(hasattr(shlex, 'quote'))
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')


@patch('subprocess.Popen', return_value=NonCallableMock(returncode=0))
@patch('swb.local.open')
def test_exec_on_remote(local_open, popen):
    """should execute script on remote server"""
    swb.exec_on_remote(
        'myname', 'mysite.com', '2222',
        'back-up', ['~/public_html/mysite', 'bzip2 -v', 'a/b c/d', 'False'],
        stdout=1, stderr=2)
    popen.assert_called_once_with([
        'ssh', '-p 2222', 'myname@mysite.com',
        'python3', '-', 'back-up', '~/\'public_html/mysite\'',
        '\'bzip2 -v\'', '\'a/b c/d\'', 'False'],
        stdin=local_open.return_value.__enter__(), stdout=1, stderr=2)
    popen.return_value.wait.assert_called_once_with()


@patch('subprocess.Popen', return_value=NonCallableMock(returncode=3))
@patch('swb.local.open')
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
        'myname', 'mysite.com', '2222', 'a/b c/d', 'e/f g/h',
        action='download', stdout=1, stderr=2)
    popen.assert_called_once_with(
        ['scp', '-P 2222', 'myname@mysite.com:\'a/b c/d\'', 'e/f g/h'],
        stdout=1, stderr=2)
    popen.return_value.wait.assert_called_once_with()


@patch('subprocess.Popen')
def test_transfer_file_upload(popen):
    """should upload backup to remote server when restoring"""
    swb.transfer_file(
        'myname', 'mysite.com', '2222', 'a/b c/d', 'e/f g/h',
        action='upload', stdout=1, stderr=2)
    popen.assert_called_once_with(
        ['scp', '-P 2222', 'a/b c/d', 'myname@mysite.com:\'e/f g/h\''],
        stdout=1, stderr=2)
    popen.return_value.wait.assert_called_once_with()
