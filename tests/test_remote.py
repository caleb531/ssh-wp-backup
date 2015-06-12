#!/usr/bin/env python3

import configparser
import os
import shlex
import subprocess
import sys
import nose.tools as nose
import src.remote as swb
from unittest.mock import ANY, mock_open, NonCallableMagicMock, patch
from fixtures.remote import set_up, tear_down


WP_PATH = '~/mysite'
BACKUP_COMPRESSOR = 'bzip2'
BACKUP_DECOMPRESSOR = '{} -d'.format(BACKUP_COMPRESSOR)
BACKUP_PATH = '~/backups/mysite.sql.bz2'
DB_PATH = BACKUP_PATH.replace('.bz2', '')


def run_back_up(wordpress_path=WP_PATH,
                compressor=BACKUP_COMPRESSOR,
                backup_path=BACKUP_PATH):
    swb.back_up(wordpress_path, compressor, backup_path)


def run_restore(wordpress_path=WP_PATH,
                backup_path=BACKUP_PATH,
                backup_decompressor=BACKUP_DECOMPRESSOR):
    swb.restore(wordpress_path, backup_path, backup_decompressor)


@nose.with_setup(set_up, tear_down)
@patch('src.remote.back_up')
def test_route_back_up(back_up):
    '''should call back_up() with args if respective action is passed'''
    swb.sys.argv = [swb.__file__, 'back-up', 'a', 'b', 'c']
    swb.main()
    back_up.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
@patch('src.remote.restore')
def test_route_restore(restore):
    '''should call restore() with args if respective action is passed'''
    swb.sys.argv = [swb.__file__, 'restore', 'a', 'b', 'c']
    swb.main()
    restore.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
@patch('src.remote.purge_downloaded_backup')
def test_route_purge_backup(purge):
    '''should call purge_backup() with args if respective action is passed'''
    swb.sys.argv = [swb.__file__, 'purge-backup', 'a', 'b', 'c']
    swb.main()
    purge.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
def test_create_dir_structure():
    '''should create intermediate directories'''
    run_back_up()
    swb.os.makedirs.assert_called_with(os.path.expanduser('~/backups'))


@nose.with_setup(set_up, tear_down)
@patch('src.remote.os.makedirs', side_effect=OSError)
def test_create_dir_structure_silent_fail(makedirs):
    '''should fail silently if intermediate directories already exist'''
    run_back_up()
    makedirs.assert_called_with(os.path.expanduser('~/backups'))


@nose.with_setup(set_up, tear_down)
def test_dump_db():
    '''should dump database'''
    run_back_up()
    swb.subprocess.Popen.assert_any_call([
        'mysqldump', 'mydb', '-h', 'myhost', '-u', 'myname',
        '-pmypassword', '--add-drop-table'], stdout=subprocess.PIPE)


@nose.with_setup(set_up, tear_down)
@patch('src.remote.os.path.getsize', return_value=20)
def test_corrupted_backup(getsize):
    '''should raise OSError if backup is corrupted'''
    with nose.assert_raises(OSError):
        run_back_up()


@nose.with_setup(set_up, tear_down)
def test_purge_downloaded_backup():
    '''should purge remote backup after download'''
    swb.purge_downloaded_backup(BACKUP_PATH)
    swb.os.remove.assert_called_once_with(BACKUP_PATH)


@nose.with_setup(set_up, tear_down)
def test_restore_verify():
    '''should verify backup on restore'''
    run_restore()
    swb.os.path.getsize.assert_called_once_with(
        os.path.expanduser(BACKUP_PATH))


@nose.with_setup(set_up, tear_down)
def test_decompress_backup():
    '''should decompress backup on restore'''
    run_restore()
    swb.subprocess.Popen.assert_any_call(['bzip2', '-d', os.path.expanduser(
        BACKUP_PATH)])


@nose.with_setup(set_up, tear_down)
def test_replace_db():
    '''should replace database with decompressed revision'''
    run_restore()
    swb.subprocess.Popen.assert_any_call([
        'mysql', 'mydb', '-h', 'myhost', '-u', 'myname',
        '-pmypassword'], stdin=swb.open())


@nose.with_setup(set_up, tear_down)
def test_purge_restored_backup():
    '''should purge remote backup/database after restore'''
    run_restore()
    swb.os.remove.assert_any_call(os.path.expanduser(BACKUP_PATH))
    swb.os.remove.assert_any_call(os.path.expanduser(DB_PATH))


@nose.with_setup(set_up, tear_down)
@patch('src.remote.os.remove', side_effect=OSError)
def test_purge_restored_backup_silent_fail(remove):
    '''should fail silently if remote files do not exist after restore'''
    run_restore()
    remove.assert_called_once_with(os.path.expanduser(DB_PATH))


@nose.with_setup(set_up, tear_down)
def test_process_wait_back_up():
    '''should wait for each process to finish when backing up'''
    run_back_up()
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 2)


@nose.with_setup(set_up, tear_down)
def test_process_wait_restore():
    '''should wait for each process to finish when restoring'''
    run_restore()
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 2)
