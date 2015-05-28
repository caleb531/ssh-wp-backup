#!/usr/bin/env python3

import glob
import os.path
import re
from datetime import datetime
from unittest.mock import MagicMock


# Class for instantiating empty objects on which attributes can be set
class AttrObject(object):
    pass


# Mock the os.stat() function
def mock_os_stat(path):
    date_ymd = re.search('\d+/\d+/\d+', path).group(0)
    stats = AttrObject()
    stats.st_mtime = datetime.strptime(date_ymd, '%Y/%m/%d')
    return stats


mock_backups = [
    '~/Backups/2011/02/03/mysite.sql.bz2',
    '~/Backups/2012/03/04/mysite.sql.bz2',
    '~/Backups/2013/04/05/mysite.sql.bz2',
    '~/Backups/2014/05/06/mysite.sql.bz2',
    '~/Backups/2015/06/07/mysite.sql.bz2'
]


def mock_iglob(path):
    if '*' in path:
        return [os.path.dirname(backup_path) for backup_path in mock_backups]
    else:
        return mock_backups


def mock_module_imports(module):

    module.os = MagicMock()
    module.os.makedirs = MagicMock()
    module.os.remove = MagicMock()
    module.os.rmdir = MagicMock()
    module.os.stat = mock_os_stat
    module.os.path.expanduser = os.path.expanduser
    module.os.path.dirname = os.path.dirname
    module.os.path.basename = os.path.basename
    module.subprocess = MagicMock()
    module.glob.iglob = mock_iglob

    fake_stdout = MagicMock()
    fake_stderr = MagicMock()
