#!/usr/bin/env python3

import os
import os.path
import shutil
import subprocess
import tempfile
import swb.remote as swb
from mock import Mock, mock_open, patch


TEMP_DIR = os.path.join(tempfile.gettempdir(), 'swb-remote')
WP_PATH = 'tests/files/mysite'
BACKUP_COMPRESSOR = 'bzip2 -v'
BACKUP_DECOMPRESSOR = 'bzip2 -d'


def run_back_up(backup_path, full_backup,
                wp_path=WP_PATH, backup_compressor=BACKUP_COMPRESSOR):
    swb.back_up(wp_path, backup_compressor, backup_path, full_backup)


def run_restore(backup_path, full_backup,
                wp_path=WP_PATH, backup_decompressor=BACKUP_DECOMPRESSOR):
    swb.restore(wp_path, backup_path, backup_decompressor)


WP_CONFIG_PATH = 'tests/files/mysite/wp-config.php'
with open(WP_CONFIG_PATH, 'r') as wp_config:
    WP_CONFIG_CONTENTS = wp_config.read()


patch_makedirs = patch('os.makedirs')
patch_remove = patch('os.remove')
patch_rmdir = patch('os.rmdir')
patch_getsize = patch('os.path.getsize', return_value=54321)
mock_communicate = Mock(return_value=[b'db contents', b'no errors'])
patch_popen = patch('subprocess.Popen',
                    return_value=Mock(
                        returncode=0, communicate=mock_communicate))
patch_open = None


def set_up():
    global patch_open
    try:
        os.makedirs(TEMP_DIR)
    except OSError:
        pass
    patch_makedirs.start()
    patch_remove.start()
    patch_rmdir.start()
    patch_getsize.start()
    patch_popen.start()
    patch_open = patch('swb.remote.open',
                       mock_open(read_data=WP_CONFIG_CONTENTS), create=True)
    patch_open.start()


def tear_down():
    global patch_open
    patch_makedirs.stop()
    patch_remove.stop()
    patch_rmdir.stop()
    patch_getsize.stop()
    subprocess.Popen.reset_mock()
    patch_popen.stop()
    patch_open.stop()
    try:
        shutil.rmtree(TEMP_DIR)
    except OSError:
        pass
