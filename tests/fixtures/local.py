#!/usr/bin/env python3

import os
import src.local
from unittest.mock import Mock, patch


mock_backups = [
    '~/Backups/2011/02/03/mysite.sql.bz2',
    '~/Backups/2012/03/04/mysite.sql.bz2',
    '~/Backups/2013/04/05/mysite.sql.bz2',
    '~/Backups/2014/05/06/mysite.sql.bz2',
    '~/Backups/2015/06/07/mysite.sql.bz2'
]


def mock_stat(path):
    if path in mock_backups:
        return Mock(st_mtime=mock_backups.index(path))


patch_makedirs = patch('os.makedirs')
patch_remove = patch('os.remove')
patch_rmdir = patch('os.rmdir')
patch_stat = patch('os.stat', mock_stat)
patch_iglob = patch('glob.iglob',
                    return_value=mock_backups)
patch_input = patch('src.local.input', create=True)
patch_popen = patch('subprocess.Popen',
                    return_value=Mock(returncode=0))


def set_up():
    patch_makedirs.start()
    patch_remove.start()
    patch_rmdir.start()
    patch_stat.start()
    patch_iglob.start()
    patch_input.start()
    patch_popen.start()


def tear_down():
    patch_makedirs.stop()
    patch_remove.stop()
    patch_rmdir.stop()
    patch_stat.stop()
    patch_iglob.stop()
    patch_input.stop()
    src.local.subprocess.Popen.reset_mock()
    patch_popen.stop()
