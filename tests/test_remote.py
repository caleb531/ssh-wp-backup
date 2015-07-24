#!/usr/bin/env python3

import os
import subprocess
import nose.tools as nose
import swb.remote as swb
from mock import ANY, patch
from tests.fixtures.remote import set_up, tear_down


WP_PATH = '~/mysite'
BACKUP_COMPRESSOR = 'bzip2 -v'
BACKUP_DECOMPRESSOR = 'bzip2 -d'
BACKUP_PATH = '~/backups/mysite.sql.bz2'
DB_PATH = BACKUP_PATH.replace('.bz2', '')


def run_back_up():
    swb.back_up(WP_PATH, BACKUP_COMPRESSOR, BACKUP_PATH)


def run_restore():
    swb.restore(WP_PATH, BACKUP_PATH, BACKUP_DECOMPRESSOR)


@nose.with_setup(set_up, tear_down)
@patch('swb.remote.back_up')
@patch('sys.argv', [swb.__file__, 'back-up', 'a', 'b', 'c'])
def test_route_back_up(back_up):
    '''should call back_up() with args if respective action is passed'''
    swb.main()
    back_up.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
@patch('swb.remote.restore')
@patch('sys.argv', [swb.__file__, 'restore', 'a', 'b', 'c'])
def test_route_restore(restore):
    '''should call restore() with args if respective action is passed'''
    swb.main()
    restore.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
@patch('swb.remote.purge_downloaded_backup')
@patch('sys.argv', [swb.__file__, 'purge-backup', 'a', 'b', 'c'])
def test_route_purge_backup(purge):
    '''should call purge_backup() with args if respective action is passed'''
    swb.main()
    purge.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
def test_create_dir_structure():
    '''should create intermediate directories'''
    run_back_up()
    swb.os.makedirs.assert_called_with(os.path.expanduser('~/backups'))


@nose.with_setup(set_up, tear_down)
@patch('os.makedirs', side_effect=OSError)
def test_create_dir_structure_silent_fail(makedirs):
    '''should fail silently if intermediate directories already exist'''
    run_back_up()
    makedirs.assert_called_with(os.path.expanduser('~/backups'))


@nose.with_setup(set_up, tear_down)
def test_dump_db():
    '''should dump database to stdout'''
    run_back_up()
    swb.subprocess.Popen.assert_any_call([
        'mysqldump', 'mydb', '-h', 'myhost', '-u', 'myname',
        '-pmypassword', '--add-drop-table'], stdout=subprocess.PIPE)


@nose.with_setup(set_up, tear_down)
def test_compress_db():
    '''should compress dumped database'''
    run_back_up()
    swb.subprocess.Popen.assert_any_call(['bzip2', '-v'],
                                         stdin=ANY, stdout=ANY)


@nose.with_setup(set_up, tear_down)
@patch('os.path.getsize', return_value=20)
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
@patch('os.remove', side_effect=OSError)
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
