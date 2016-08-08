#!/usr/bin/env python3

import configparser
import os
import os.path
import subprocess
import nose.tools as nose
import swb.local as swb
from time import strftime
from mock import ANY, call, patch


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


@patch('swb.local.unquote_home_dir', side_effect=lambda x: x)
def test_quote_arg_str(unquote_home_dir):
    """should correctly quote arguments passed to the shell"""
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')
    unquote_home_dir.assert_called_once_with('\'a/b c/d\'')


@patch('swb.local.unquote_home_dir', side_effect=lambda x: x)
@patch('swb.local.shlex')
def test_quote_arg_py32(shlex, unquote_home_dir):
    """should correctly quote arguments passed to the shell on Python 3.2"""
    del shlex.quote
    nose.assert_false(hasattr(shlex, 'quote'))
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')
    unquote_home_dir.assert_called_once_with('\'a/b c/d\'')


@patch('subprocess.Popen', spec=subprocess.Popen)
@patch('builtins.open')
def test_exec_on_remote(builtin_open, popen):
    """should execute script on remote server"""
    popen.return_value.returncode = 0
    swb.exec_on_remote(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        action='back-up',
        action_args=['~/public_html/mysite', 'bzip2 -v', 'a/b c/d'],
        stdout=1, stderr=2)
    popen.assert_called_once_with([
        'ssh', '-p 2222', 'myname@mysite.com',
        'python3', '-', 'back-up', '~/\'public_html/mysite\'',
        '\'bzip2 -v\'', '\'a/b c/d\''],
        stdin=builtin_open.return_value.__enter__(), stdout=1, stderr=2)
    popen.return_value.wait.assert_called_once_with()


@patch('sys.exit')
@patch('subprocess.Popen', spec=subprocess.Popen)
@patch('builtins.open')
def test_exec_on_remote_nonzero_return(builtin_open, popen, exit):
    """should exit script if nonzero status code is returned"""
    popen.return_value.returncode = 3
    swb.exec_on_remote(
        ssh_user='a', ssh_hostname='b.com', ssh_port='2222',
        action='c', action_args=['d', 'e', 'f', 'g'],
        stdout=1, stderr=2)
    exit.assert_called_once_with(3)


@patch('subprocess.Popen', spec=subprocess.Popen)
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


@patch('subprocess.Popen', spec=subprocess.Popen)
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
        backup_compressor='bzip2 -v',
        stdout=1, stderr=2)
    exec_on_remote.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        action='back-up', action_args=['a/b c/d', 'bzip2 -v', 'e/f g/h'],
        stdout=1, stderr=2)


@patch('swb.local.transfer_file')
def test_download_remote_backup(transfer_file):
    """should download remote backup after creation"""
    swb.download_remote_backup(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        remote_backup_path='a/b c/d', local_backup_path='e/f g/h',
        stdout=1, stderr=2)
    transfer_file.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        src_path='a/b c/d', dest_path='e/f g/h',
        action='download', stdout=1, stderr=2)


@patch('swb.local.transfer_file')
def test_upload_local_backup(transfer_file):
    """should upload local backup when restoring"""
    swb.upload_local_backup(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        remote_backup_path='a/b c/d', local_backup_path='e/f g/h',
        stdout=1, stderr=2)
    transfer_file.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        src_path='e/f g/h', dest_path='a/b c/d',
        action='upload', stdout=1, stderr=2)


@patch('swb.local.exec_on_remote')
def test_restore_remote_backup(exec_on_remote):
    """should restore remote backup after upload"""
    swb.restore_remote_backup(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        wordpress_path='a/b c/d', remote_backup_path='e/f g/h',
        backup_decompressor='bzip2 -v',
        stdout=1, stderr=2)
    exec_on_remote.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        action='restore',
        action_args=['a/b c/d', 'e/f g/h', 'bzip2 -v'],
        stdout=1, stderr=2)


@patch('swb.local.exec_on_remote')
def test_purge_remote_backup(exec_on_remote):
    """should purge remote backup after download"""
    swb.purge_remote_backup(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        remote_backup_path='a/b c/d', stdout=1, stderr=2)
    exec_on_remote.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        action='purge-backup', action_args=['a/b c/d'],
        stdout=1, stderr=2)


def test_get_last_modified_time():
    """should retrieve correct last modified time of the supplied path"""
    nose.assert_equal(
        swb.get_last_modified_time('swb/local.py'),
        os.stat('swb/local.py').st_mtime)


@patch('os.rmdir')
@patch('glob.iglob', side_effect=[
    ['/a/b/2011/02/03', '/a/b/2011/02/04'],
    ['/a/b/2011/02'],
    ['/a/b/2010', '/a/b/2011'],
    ['/a/b'],
    ['/a']
])
def test_purge_empty_dirs(iglob, rmdir):
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


@patch('os.rmdir', side_effect=OSError)
@patch('glob.iglob', side_effect=[
    ['/a/b/2011/02/03', '/a/b/2011/02/04'],
    ['/a/b/2011/02'],
    ['/a/b/2010', '/a/b/2011'],
    ['/a/b'],
    ['/a']
])
def test_purge_empty_dirs_silent_fail(iglob, rmdir):
    """should ignore non-empty directories when purging empty directories"""
    swb.purge_empty_dirs('/a/b/*/*/*/c')
    nose.assert_equal(iglob.call_count, 3)
    nose.assert_equal(rmdir.call_count, 5)


@patch('swb.local.get_last_modified_time', side_effect=[5, 3, 6, 2, 4])
@patch('swb.local.purge_empty_dirs')
@patch('os.remove')
@patch('glob.iglob', return_value=[
    'a/2015/02/03/b',
    'a/2013/04/05/b',
    'a/2016/01/02/b',
    'a/2012/05/06/b',
    'a/2014/03/04/b'
])
def test_purge_oldest_backups(iglob, remove, purge_empty_dirs,
                              get_last_modified_time):
    """should purge oldest local backups"""
    swb.purge_oldest_backups('a/%y/%m/%d/b', max_local_backups=3)
    nose.assert_equal(remove.call_args_list, [
        call('a/2012/05/06/b'),
        call('a/2013/04/05/b')
    ])
    purge_empty_dirs.assert_called_once_with('a/*/*/*/b')


@patch('swb.local.purge_remote_backup')
@patch('swb.local.purge_oldest_backups')
@patch('swb.local.download_remote_backup')
@patch('swb.local.create_remote_backup')
@patch('swb.local.create_dir_structure')
def test_back_up(create_dir_structure, create_remote_backup,
                 download_remote_backup, purge_oldest_backups,
                 purge_remote_backup):
    """should run correct backup procedure"""
    config = configparser.RawConfigParser()
    config.read('tests/files/config.ini')
    swb.back_up(config, stdout=1, stderr=2)
    expanded_local_backup_path = os.path.expanduser(strftime(
        '~/Backups/%y/%m/%d/mysite.sql.bz2'))
    expanded_remote_backup_path = strftime('~/backups/%y/%m/%d/mysite.sql.bz2')
    create_remote_backup.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        wordpress_path='~/public_html/mysite',
        remote_backup_path=expanded_remote_backup_path,
        backup_compressor='bzip2 -v',
        stdout=1, stderr=2)
    create_dir_structure.assert_called_once_with(
        local_backup_path=expanded_local_backup_path)
    download_remote_backup.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        remote_backup_path=expanded_remote_backup_path,
        local_backup_path=expanded_local_backup_path,
        stdout=1, stderr=2)
    purge_remote_backup.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        remote_backup_path=expanded_remote_backup_path,
        stdout=1, stderr=2)


@patch('swb.local.purge_remote_backup')
@patch('swb.local.purge_oldest_backups')
@patch('swb.local.download_remote_backup')
@patch('swb.local.create_remote_backup')
@patch('swb.local.create_dir_structure')
def test_back_up_purge_oldest(create_dir_structure, create_remote_backup,
                              download_remote_backup, purge_oldest_backups,
                              purge_remote_backup):
    """should purge oldest backups if max_local_backups option is set"""
    config = configparser.RawConfigParser()
    config.read('tests/files/config.ini')
    config.set('backup', 'max_local_backups', 3)
    swb.back_up(config)
    purge_oldest_backups.assert_called_once_with(
        local_backup_path=os.path.expanduser(
            '~/Backups/%y/%m/%d/mysite.sql.bz2'),
        max_local_backups=3)


@patch('swb.local.upload_local_backup')
@patch('swb.local.restore_remote_backup')
def test_restore(restore_remote_backup, upload_local_backup):
    """should run correct restore procedure"""
    config = configparser.RawConfigParser()
    config.read('tests/files/config.ini')
    swb.restore(
        config, local_backup_path='a/b/c.tar.bz2',
        stdout=1, stderr=2)
    expanded_remote_backup_path = strftime(
        config.get('paths', 'remote_backup'))
    upload_local_backup.assert_called_once_with(
        ssh_user='myname', ssh_hostname='mysite.com', ssh_port='2222',
        local_backup_path='a/b/c.tar.bz2',
        remote_backup_path=expanded_remote_backup_path,
        stdout=1, stderr=2)


@patch('swb.local.parse_config')
@patch('swb.local.back_up')
@patch('sys.argv', [swb.__file__, 'tests/files/config.ini'])
def test_main_back_up(back_up, parse_config):
    """should run backup procedure by default when utility is run"""
    swb.main()
    back_up.assert_called_once_with(
        parse_config.return_value, stdout=None, stderr=None)


@patch('swb.local.parse_config')
@patch('swb.local.back_up')
@patch('sys.argv', [swb.__file__, '-q', 'tests/files/config.ini'])
@patch('builtins.open')
def test_main_quiet(builtin_open, back_up, parse_config):
    """should silence stdout/stderr when utility is run in quiet mode"""
    swb.main()
    devnull = builtin_open.return_value.__enter__()
    back_up.assert_called_once_with(
        parse_config.return_value,
        stdout=devnull, stderr=devnull)


@patch('swb.local.restore')
@patch('swb.local.parse_config')
@patch('sys.argv', [swb.__file__, 'tests/files/config.ini', '-r', 'a.tar.bz2'])
@patch('builtins.print')
@patch('builtins.input', return_value='y')
def test_main_restore(builtin_input, builtin_print, parse_config, restore):
    """should run restore procedure when -r/--restore is passed to utility"""
    swb.main()
    builtin_input.assert_called_once_with(ANY)
    restore.assert_called_once_with(
        parse_config.return_value, local_backup_path='a.tar.bz2',
        stdout=None, stderr=None)


@patch('swb.local.restore')
@patch('swb.local.parse_config')
@patch('sys.argv', [swb.__file__, 'tests/files/config.ini', '-r', 'a.tar.bz2'])
@patch('builtins.print')
@patch('builtins.input', return_value='n')
def test_main_restore_cancel(builtin_input, builtin_print,
                             parse_config, restore):
    """should cancel restore procedure when user cancels confirmation"""
    with nose.assert_raises(Exception):
        swb.main()
    restore.assert_not_called()


@patch('swb.local.restore')
@patch('swb.local.parse_config')
@patch('sys.argv', [
    swb.__file__, 'tests/files/config.ini',
    '-fr', 'a.tar.bz2'])
@patch('builtins.print')
@patch('builtins.input', return_value='y')
def test_main_restore_force(builtin_input, builtin_print,
                            parse_config, restore):
    """should force restore procedure when -fr is passed to utility"""
    swb.main()
    builtin_input.assert_not_called()
    restore.assert_called_once_with(
        parse_config.return_value, local_backup_path='a.tar.bz2',
        stdout=None, stderr=None)
