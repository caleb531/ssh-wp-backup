#!/usr/bin/env python3

import glob
import src.local as swb
import fixtures.shared as shared
from unittest.mock import Mock


mock_backups = [
    '~/Backups/2011/02/03/mysite.sql.bz2',
    '~/Backups/2012/03/04/mysite.sql.bz2',
    '~/Backups/2013/04/05/mysite.sql.bz2',
    '~/Backups/2014/05/06/mysite.sql.bz2',
    '~/Backups/2015/06/07/mysite.sql.bz2'
]


def before_all():
    shared.before_all(swb)
    swb.glob.iglob = Mock(return_value=mock_backups)
    swb.os.stat = lambda path: Mock(st_mtime=mock_backups.index(path))
    swb.input = Mock()


def before_each():
    shared.before_each(swb)


def after_each():
    shared.after_each(swb)
    swb.input.reset_mock()
