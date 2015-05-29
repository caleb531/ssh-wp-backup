#!/usr/bin/env python3

import configparser
import os
import shlex
import sys
import nose.tools as nose
import mocks.remote as mocks
import src.remote as swb
from unittest.mock import ANY, mock_open, NonCallableMagicMock, patch
from fixtures.remote import before_all, before_each, after_each


def test_route_back_up():
    '''should call back_up() with args if respective action is passed'''
    with patch('src.remote.back_up'):
        swb.sys.argv = [swb.__file__, 'back-up', 'a', 'b', 'c']
        swb.main()
        swb.back_up.assert_called_once_with('a', 'b', 'c')


def test_route_restore():
    '''should call restore() with args if respective action is passed'''
    with patch('src.remote.restore'):
        swb.sys.argv = [swb.__file__, 'restore', 'a', 'b', 'c']
        swb.main()
        swb.restore.assert_called_once_with('a', 'b', 'c')


def test_route_purge_backup():
    '''should call purge_backup() with args if respective action is passed'''
    with patch('src.remote.purge_downloaded_backup'):
        swb.sys.argv = [swb.__file__, 'purge-backup', 'a', 'b', 'c']
        swb.main()
        swb.purge_downloaded_backup.assert_called_once_with('a', 'b', 'c')


before_all()
