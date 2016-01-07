#!/usr/bin/env python3

import os
import os.path
import subprocess
import nose.tools as nose
import swb.remote as swb
from mock import ANY, patch
from tests.fixtures.remote import run_back_up, run_restore
from tests.fixtures.remote import set_up, tear_down


BACKUP_PATH = '~/backups/mysite.sql.bz2'
FULL_BACKUP = 'False'


@nose.with_setup(set_up, tear_down)
def test_create_dir_structure():
    """should create intermediate directories"""
    run_back_up(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    swb.os.makedirs.assert_called_with(
        os.path.expanduser(os.path.dirname(BACKUP_PATH)))


@nose.with_setup(set_up, tear_down)
@patch('os.makedirs', side_effect=OSError)
def test_create_dir_structure_silent_fail(makedirs):
    """should fail silently if intermediate directories already exist"""
    run_back_up(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    makedirs.assert_called_with(
        os.path.expanduser(os.path.dirname(BACKUP_PATH)))


@nose.with_setup(set_up, tear_down)
def test_dump_db():
    """should dump database to stdout"""
    run_back_up(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    swb.subprocess.Popen.assert_any_call([
        'mysqldump', 'mydb', '-h', 'myhost', '-u', 'myname',
        '-pmypassword', '--add-drop-table'], stdout=subprocess.PIPE)


@nose.with_setup(set_up, tear_down)
def test_compress_db():
    """should compress dumped database"""
    run_back_up(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    swb.subprocess.Popen.assert_any_call(['bzip2', '-v'],
                                         stdin=ANY, stdout=ANY)


@nose.with_setup(set_up, tear_down)
@patch('os.path.getsize', return_value=20)
def test_corrupted_backup(getsize):
    """should raise OSError if backup is corrupted"""
    with nose.assert_raises(OSError):
        run_back_up(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)


@nose.with_setup(set_up, tear_down)
def test_restore_verify():
    """should verify backup on restore"""
    run_restore(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    swb.os.path.getsize.assert_called_once_with(
        os.path.expanduser(BACKUP_PATH))


@nose.with_setup(set_up, tear_down)
def test_decompress_backup():
    """should decompress backup on restore"""
    run_restore(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    swb.subprocess.Popen.assert_any_call(['bzip2', '-d', os.path.expanduser(
        BACKUP_PATH)])


@nose.with_setup(set_up, tear_down)
def test_replace_db():
    """should replace database with decompressed revision"""
    run_restore(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    swb.subprocess.Popen.assert_any_call([
        'mysql', 'mydb', '-h', 'myhost', '-u', 'myname',
        '-pmypassword'], stdin=swb.open())


@nose.with_setup(set_up, tear_down)
def test_purge_restored_backup():
    """should purge remote backup/database after restore"""
    run_restore(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    swb.os.remove.assert_any_call(os.path.expanduser(BACKUP_PATH))
    swb.os.remove.assert_any_call(os.path.expanduser(
        os.path.splitext(BACKUP_PATH)[0]))


@nose.with_setup(set_up, tear_down)
@patch('os.remove', side_effect=OSError)
def test_purge_restored_backup_silent_fail(remove):
    """should fail silently if remote files do not exist after restore"""
    run_restore(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    remove.assert_called_once_with(os.path.expanduser(
        os.path.splitext(BACKUP_PATH)[0]))


@nose.with_setup(set_up, tear_down)
def test_process_wait_back_up():
    """should wait for each process to finish when backing up"""
    run_back_up(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 2)


@nose.with_setup(set_up, tear_down)
def test_process_wait_restore():
    """should wait for each process to finish when restoring"""
    run_restore(backup_path=BACKUP_PATH, full_backup=FULL_BACKUP)
    nose.assert_equal(swb.subprocess.Popen.return_value.wait.call_count, 2)
