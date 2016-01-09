#!/usr/bin/env python3

import os
import os.path
import subprocess
import nose.tools as nose
import swb.remote as swb
from mock import patch


WP_PATH = 'tests/files/mysite'
with open(os.path.join(WP_PATH, 'wp-config.php'), 'r') as wp_config:
    WP_CONFIG_CONTENTS = wp_config.read()


def test_read_wp_config():
    """should correctly read contents of site's wp-config.php"""
    actual_contents = swb.read_wp_config(WP_PATH)
    nose.assert_equal(actual_contents, WP_CONFIG_CONTENTS)


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


@patch('swb.remote.read_wp_config', return_value=WP_CONFIG_CONTENTS)
def test_get_db_info(read_wp_config):
    """should parsedatabase info from wp-config.php"""
    db_info = swb.get_db_info(WP_PATH)
    nose.assert_equal(db_info['name'], 'mydb')
    nose.assert_equal(db_info['user'], 'myname')
    nose.assert_equal(db_info['password'], 'MyPassw0rd!')
    nose.assert_equal(db_info['host'], 'myhost')
    nose.assert_equal(db_info['host'], 'myhost')
    nose.assert_equal(db_info['charset'], 'utf8')
    nose.assert_equal(db_info['collate'], '')


@patch('subprocess.Popen')
@patch('builtins.open')
def test_dump_compressed_db(builtin_open, popen):
    """should dump compressed database to designated location on remote"""
    swb.dump_compressed_db(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword',
        backup_compressor='bzip2 -v', backup_path='a/b c/d')
    popen.assert_any_call([
        'mysqldump', 'mydb', '-h', 'myhost', '-u', 'myname', '-pmypassword',
        '--add-drop-table'], stdout=subprocess.PIPE)
    builtin_open.assert_called_once_with('a/b c/d', 'w')
    popen.assert_any_call(
        ['bzip2', '-v'],
        stdin=popen.return_value.stdout,
        stdout=builtin_open.return_value.__enter__())
    nose.assert_equal(popen.return_value.wait.call_count, 2)


@patch('os.path.getsize', return_value=20480)
def test_verify_backup_integrity_valid(getsize):
    """should validate a given valid backup file"""
    swb.verify_backup_integrity('a/b c/d')
    getsize.assert_called_once_with('a/b c/d')


@patch('os.path.getsize', return_value=20)
@patch('os.remove')
def test_verify_backup_integrity_invalid(remove, getsize):
    """should invalidate a given corrupted backup file"""
    with nose.assert_raises(OSError):
        swb.verify_backup_integrity('a/b c/d')
    remove.assert_called_once_with('a/b c/d')


@patch('os.remove')
def test_purge_downloaded_backup(remove):
    """should purge the downloaded backup file by removing it"""
    swb.purge_downloaded_backup('a/b c/d')
    remove.assert_called_once_with('a/b c/d')


@patch('swb.remote.verify_backup_integrity')
@patch('swb.remote.dump_compressed_db')
@patch('swb.remote.get_db_info', return_value={
    'name': 'mydb',
    'host': 'myhost',
    'user': 'myname',
    'password': 'mypassword'
})
@patch('swb.remote.create_dir_structure')
def test_back_up_db(create_dir_structure, get_db_info,
                    dump_compressed_db, verify_backup_integrity):
    """should perform a WordPress database backup"""
    swb.back_up(
        wordpress_path='path/to/my site',
        backup_compressor='bzip2 -v',
        backup_path='path/to/my backup.sql.bz2')
    create_dir_structure.assert_called_once_with(
        'path/to/my backup.sql.bz2')
    dump_compressed_db.assert_called_once_with(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword',
        backup_path='path/to/my backup.sql.bz2',
        backup_compressor='bzip2 -v')
    verify_backup_integrity.assert_called_once_with(
        'path/to/my backup.sql.bz2')


@patch('subprocess.Popen', spec=subprocess.Popen)
def test_decompress_backup(popen):
    """should decompress the given backup file using the given decompressor"""
    swb.decompress_backup(
        backup_path='path/to/my backup.sql.bz2',
        backup_decompressor='bzip2 -d')
    popen.assert_called_once_with(
        ['bzip2', '-d', 'path/to/my backup.sql.bz2'])
    popen.return_value.wait.assert_called_once_with()


@patch('subprocess.Popen', spec=subprocess.Popen)
@patch('builtins.open')
def test_replace_db(builtin_open, popen):
    """should replace the MySQL database when restoring from backup"""
    swb.replace_db(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword',
        db_path='path/to/my backup.sql')
    builtin_open.assert_called_once_with(
        'path/to/my backup.sql', 'r')
    popen.assert_called_once_with(
        ['mysql', 'mydb', '-h', 'myhost', '-u', 'myname', '-pmypassword'],
        stdin=builtin_open.return_value.__enter__())
    popen.return_value.wait.assert_called_once_with()


@patch('os.remove')
def test_purge_restored_backup(remove):
    """should purge restored backup and database file after restore"""
    swb.purge_restored_backup(
        backup_path='path/to/my backup.sql.bz2',
        db_path='path/to/my backup.sql')
    remove.assert_any_call('path/to/my backup.sql')
    remove.assert_any_call('path/to/my backup.sql.bz2')


@patch('os.remove', side_effect=OSError)
def test_purge_restored_backup_silent_fail(remove):
    """should silently fail if restored database/backup file does not exist"""
    swb.purge_restored_backup(
        backup_path='path/to/my backup.sql.bz2',
        db_path='path/to/my backup.sql')
    nose.assert_equal(remove.call_count, 2)


@patch('swb.remote.verify_backup_integrity')
@patch('swb.remote.replace_db')
@patch('swb.remote.purge_restored_backup')
@patch('swb.remote.get_db_info', return_value={
    'name': 'mydb',
    'host': 'myhost',
    'user': 'myname',
    'password': 'mypassword'
})
@patch('swb.remote.decompress_backup')
def test_restore(decompress_backup, get_db_info, purge_restored_backup,
                 replace_db, verify_backup_integrity):
    """should run restore procedure"""
    swb.restore(
        wordpress_path='~/path/to/my site',
        backup_path='~/path/to/my site.sql.bz2',
        backup_decompressor='bzip2 -d')
    decompress_backup.assert_called_once_with(
        backup_path=os.path.expanduser('~/path/to/my site.sql.bz2'),
        backup_decompressor='bzip2 -d')
    replace_db.assert_called_once_with(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword',
        db_path=os.path.expanduser('~/path/to/my site.sql'))
    purge_restored_backup.assert_called_once_with(
        backup_path=os.path.expanduser('~/path/to/my site.sql.bz2'),
        db_path=os.path.expanduser('~/path/to/my site.sql'))


@patch('swb.remote.back_up')
@patch('sys.argv', [swb.__file__, 'back-up', 'a', 'b', 'c', 'd'])
@patch('builtins.print')
def test_main_back_up(builtin_print, back_up):
    """should run backup procedure by default when remote script is run"""
    swb.main()
    back_up.assert_called_once_with('a', 'b', 'c', 'd')


@patch('swb.remote.restore')
@patch('sys.argv', [swb.__file__, 'restore', 'a', 'b', 'c', 'd'])
@patch('builtins.print')
def test_main_restore(builtin_print, restore):
    """should run restore procedure when remote script is run"""
    swb.main()
    restore.assert_called_once_with('a', 'b', 'c', 'd')


@patch('swb.remote.purge_downloaded_backup')
@patch('sys.argv', [swb.__file__, 'purge-backup', 'a', 'b', 'c', 'd'])
@patch('builtins.print')
def test_main_purge_downloaded(builtin_print, purge_downloaded_backup):
    """should run purge procedure when remote script is run"""
    swb.main()
    purge_downloaded_backup.assert_called_once_with('a', 'b', 'c', 'd')
