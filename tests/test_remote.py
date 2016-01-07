#!/usr/bin/env python3

import nose.tools as nose
import swb.remote as swb
from mock import patch
from tests.fixtures.remote import set_up, tear_down


@nose.with_setup(set_up, tear_down)
@patch('swb.remote.back_up')
@patch('sys.argv', [swb.__file__, 'back-up', 'a', 'b', 'c'])
def test_route_back_up(back_up):
    """should call back_up() with args if respective action is passed"""
    swb.main()
    back_up.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
@patch('swb.remote.restore')
@patch('sys.argv', [swb.__file__, 'restore', 'a', 'b', 'c'])
def test_route_restore(restore):
    """should call restore() with args if respective action is passed"""
    swb.main()
    restore.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
@patch('swb.remote.purge_downloaded_backup')
@patch('sys.argv', [swb.__file__, 'purge-backup', 'a', 'b', 'c'])
def test_route_purge_backup(purge):
    """should call purge_backup() with args if respective action is passed"""
    swb.main()
    purge.assert_called_once_with('a', 'b', 'c')


@nose.with_setup(set_up, tear_down)
def test_purge_downloaded_backup():
    """should purge remote backup after download"""
    swb.purge_downloaded_backup('abc')
    swb.os.remove.assert_called_once_with('abc')
