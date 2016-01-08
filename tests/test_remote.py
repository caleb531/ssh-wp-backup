#!/usr/bin/env python3

import io
import os
import os.path
import subprocess
import tarfile
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


@patch('subprocess.Popen', spec=subprocess.Popen)
def test_get_mysqldump(popen):
    """should retrieve correct mysqldump subprocess object"""
    mysqldump = swb.get_mysqldump(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword')
    popen.assert_called_once_with([
        'mysqldump', 'mydb', '-h', 'myhost', '-u', 'myname', '-pmypassword',
        '--add-drop-table'], stdout=subprocess.PIPE)
    nose.assert_equal(mysqldump, popen.return_value)
    popen.return_value.wait.assert_not_called()


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


@patch('subprocess.Popen', spec=subprocess.Popen)
@patch('builtins.open')
def test_compress_tar(builtin_open, popen):
    """should write a compressed tar file with the given contents"""
    tar_out = io.BytesIO()
    tar_out.write(b'tar contents')
    swb.compress_tar(tar_out, 'a/b c/d', 'bzip2 -v')
    popen.assert_called_once_with(
        ['bzip2', '-v'],
        stdin=subprocess.PIPE,
        stdout=builtin_open.return_value.__enter__())
    nose.assert_list_equal(popen.return_value.mock_calls, [
        call.communicate(input=b'tar contents'), call.wait()])


@patch('tarfile.TarInfo', spec=tarfile.TarInfo)
def test_add_db_to_tar(tarinfo):
    """should add database contents to tar file under the given name"""
    tar_file = Mock(spec=tarfile.TarFile)
    swb.add_db_to_tar(tar_file, 'mysite.sql', b'db contents')
    nose.assert_equal(tarinfo.return_value.size, 11)
    nose.assert_equal(tar_file.addfile.call_count, 1)
    nose.assert_equal(
        tar_file.addfile.call_args_list[0][0][0], tarinfo.return_value)
    nose.assert_equal(
        tar_file.addfile.call_args_list[0][0][1].getvalue(), b'db contents')


@patch('swb.remote.compress_tar')
@patch('swb.remote.add_db_to_tar')
@patch('tarfile.open', spec=tarfile.TarFile)
@patch('io.BytesIO', spec=io.BytesIO)
def test_create_full_backup(bytesio, tarfile_open,
                            add_db_to_tar, compress_tar):
    """should create compressed full backup"""
    swb.create_full_backup(
        wordpress_path='path/to/my site',
        db_contents=b'db contents',
        backup_path='my backup.tar.bz2',
        backup_compressor='bzip2 -v')
    tar_file_obj = tarfile.open.return_value.__enter__()
    tarfile.open.assert_called_once_with(
        fileobj=bytesio.return_value, mode='w')
    tar_file_obj.add.assert_called_once_with(
        'path/to/my site', arcname='my site')
    add_db_to_tar.assert_called_once_with(
        tar_file_obj, 'my site.sql', b'db contents')


@patch('swb.remote.verify_backup_integrity')
@patch('swb.remote.get_uncompressed_db', return_value=b'db contents')
@patch('swb.remote.get_db_info', return_value={
    'name': 'mydb',
    'host': 'myhost',
    'user': 'myname',
    'password': 'mypassword'
})
@patch('swb.remote.create_full_backup')
@patch('swb.remote.create_dir_structure')
def test_back_up_full(create_dir_structure, create_full_backup,
                      get_db_info, get_uncompressed_db,
                      verify_backup_integrity):
    """should perform a full backup"""
    swb.back_up(
        wordpress_path='path/to/my site',
        backup_compressor='bzip2 -v',
        backup_path='path/to/my backup.tar.bz2',
        full_backup='True')
    create_dir_structure.assert_called_once_with(
        'path/to/my backup.tar.bz2')
    get_uncompressed_db.assert_called_once_with(
        db_name='mydb', db_host='myhost',
        db_user='myname', db_password='mypassword')
    create_full_backup.assert_called_once_with(
        wordpress_path='path/to/my site',
        db_contents=b'db contents',
        backup_path='path/to/my backup.tar.bz2',
        backup_compressor='bzip2 -v')
    verify_backup_integrity.assert_called_once_with(
        'path/to/my backup.tar.bz2')


@patch('swb.remote.verify_backup_integrity')
@patch('swb.remote.dump_compressed_db')
@patch('swb.remote.get_db_info', return_value={
    'name': 'mydb',
    'host': 'myhost',
    'user': 'myname',
    'password': 'mypassword'
})
@patch('swb.remote.create_full_backup')
@patch('swb.remote.create_dir_structure')
def test_back_up_db(create_dir_structure, create_full_backup,
                    get_db_info, dump_compressed_db,
                    verify_backup_integrity):
    """should perform a full backup"""
    swb.back_up(
        wordpress_path='path/to/my site',
        backup_compressor='bzip2 -v',
        backup_path='path/to/my backup.sql.bz2',
        full_backup='False')
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
