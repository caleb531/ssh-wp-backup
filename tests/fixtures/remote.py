#!/usr/bin/env python3

import src.remote
from unittest.mock import Mock, mock_open, patch


WP_CONFIG_PATH = 'tests/files/wp-config.php'
with open(WP_CONFIG_PATH) as wp_config:
    WP_CONFIG_CONTENTS = wp_config.read()


patch_makedirs = patch('src.remote.os.makedirs')
patch_remove = patch('src.remote.os.remove')
patch_rmdir = patch('src.remote.os.rmdir')
patch_getsize = patch('src.remote.os.path.getsize', return_value=54321)
patch_popen = patch('src.remote.subprocess.Popen',
                    return_value=Mock(returncode=0))


def set_up():
    global patch_open
    patch_makedirs.start()
    patch_remove.start()
    patch_rmdir.start()
    patch_getsize.start()
    patch_popen.start()
    patch_open = patch('src.remote.open',
                       mock_open(read_data=WP_CONFIG_CONTENTS), create=True)
    patch_open.start()


def tear_down():
    patch_makedirs.stop()
    patch_remove.stop()
    patch_rmdir.stop()
    patch_getsize.stop()
    src.local.subprocess.Popen.reset_mock()
    patch_popen.stop()
    patch_open.stop()
