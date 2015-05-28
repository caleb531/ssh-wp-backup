#!/usr/bin/env python3

import glob
import os.path
from unittest.mock import ANY, MagicMock, patch


# Class for instantiating empty objects on which attributes can be set
class AttrObject(object):
    pass


mock_backups = [
    '~/Backups/2011/02/03/mysite.sql.bz2',
    '~/Backups/2012/03/04/mysite.sql.bz2',
    '~/Backups/2013/04/05/mysite.sql.bz2',
    '~/Backups/2014/05/06/mysite.sql.bz2',
    '~/Backups/2015/06/07/mysite.sql.bz2'
]


# Mock the os.stat() function
def mock_os_stat(path):
    stats = AttrObject()
    stats.st_mtime = mock_backups.index(path)
    return stats


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
    module.glob.iglob = MagicMock(return_value=mock_backups)

    fake_stdout = MagicMock()
    fake_stderr = MagicMock()
