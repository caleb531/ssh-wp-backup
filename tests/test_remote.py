#!/usr/bin/env python3

import os
import os.path
import subprocess
import nose.tools as nose
import swb.remote as swb
from mock import call, Mock, patch


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
def test_get_mysqldump(popen):
    """should retrieve correct mysqldump subprocess object"""
    mysqldump = swb.get_mysqldump(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword')
    popen.assert_called_once_with([
        'mysqldump', 'mydb', '-h', 'myhost', '-u', 'myname', '-pmypassword',
        '--add-drop-table'], stdout=subprocess.PIPE)
    nose.assert_equal(mysqldump, popen.return_value)


@patch('builtins.open')
def test_dump_compressed_db(builtin_open):
    """should dump compressed database to designated location on remote"""
    manager = Mock()
    with patch('subprocess.Popen', manager.popen):
        with patch('swb.remote.get_mysqldump', manager.get_mysqldump):
            swb.dump_compressed_db(
                db_name='mydb', db_host='myhost',
                db_user='myname', db_password='mypassword',
                backup_compressor='bzip2 -v', backup_path='a/b c/d')
            manager.get_mysqldump.assert_called_once_with(
                'mydb', 'myhost', 'myname', 'mypassword',)
            builtin_open.assert_called_once_with('a/b c/d', 'w')
            manager.popen.assert_called_once_with(
                ['bzip2', '-v'],
                stdin=manager.get_mysqldump.return_value.stdout,
                stdout=builtin_open.return_value.__enter__())
            nose.assert_equal(
                manager.mock_calls[2],
                call.get_mysqldump().wait())
            nose.assert_equal(
                manager.mock_calls[3],
                call.popen().wait())


@patch('swb.remote.get_mysqldump', return_value=Mock(communicate=Mock(
       return_value=[b'db output', b'db error'])))
def test_get_uncompressed_db(get_mysqldump):
    """should return uncompressed database to designated location on remote"""
    db_contents = swb.get_uncompressed_db(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword')
    nose.assert_equal(db_contents, b'db output')
    nose.assert_list_equal(get_mysqldump.return_value.mock_calls, [
        call.communicate(), call.wait()])


@patch('os.path.getsize', return_value=20480)
def test_verify_backup_integrity_valid(getsize):
    """should validate a given valid backup file"""
    swb.verify_backup_integrity('a/b c/d')
    getsize.assert_called_once_with('a/b c/d')


@patch('os.path.getsize', return_value=20)
def test_verify_backup_integrity_invalid(getsize):
    """should invalidate a given corrupted backup file"""
    with nose.assert_raises(OSError):
        swb.verify_backup_integrity('a/b c/d')


@patch('os.remove')
def test_purge_downloaded_backup(remove):
    """should purge the downloaded backup file by removing it"""
    swb.purge_downloaded_backup('a/b c/d')
    remove.assert_called_once_with('a/b c/d')
