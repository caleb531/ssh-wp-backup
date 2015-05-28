#!/usr/bin/env python3

from unittest.mock import MagicMock


mock_backups = [
    '~/Backups/2011/02/03/mysite.sql.bz2',
    '~/Backups/2012/03/04/mysite.sql.bz2',
    '~/Backups/2013/04/05/mysite.sql.bz2',
    '~/Backups/2014/05/06/mysite.sql.bz2',
    '~/Backups/2015/06/07/mysite.sql.bz2'
]


# Mock the os.stat() function
def mock_os_stat(path):
    return MagicMock(st_mtime=mock_backups.index(path))
