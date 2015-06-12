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


original_stat = os.stat


def mock_stat(path):
    if path in mock_backups:
        return Mock(st_mtime=mock_backups.index(path))
    else:
        return original_stat(path)


patch_makedirs = patch('src.local.os.makedirs').start()
patch_remove = patch('src.local.os.remove')
patch_rmdir = patch('src.local.os.rmdir')
patch_stat = patch('src.local.os.stat', new=mock_stat)
patch_iglob = patch('src.local.glob.iglob', return_value=mock_backups)
src.local.input = input
patch_input = patch('src.local.input')
patch_popen = patch('src.local.subprocess.Popen',
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
