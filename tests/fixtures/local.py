#!/usr/bin/env python3

import glob
import os
import os.path
import src.local as swb
import mocks.local as mocks
from unittest.mock import Mock, NonCallableMagicMock


def before_all():

    swb.input = Mock()
    swb.glob.iglob = Mock(return_value=mocks.mock_backups)
    swb.os = NonCallableMagicMock()
    swb.os.devnull = os.devnull
    swb.os.makedirs = Mock()
    swb.os.remove = Mock()
    swb.os.rmdir = Mock()
    swb.os.stat = mocks.mock_os_stat
    swb.os.path.basename = os.path.basename
    swb.os.path.dirname = os.path.dirname
    swb.os.path.expanduser = os.path.expanduser
    swb.subprocess = NonCallableMagicMock()


def before_each():
    pass


def after_each():
    swb.input.reset_mock()
    swb.os.makedirs.reset_mock()
    swb.os.remove.reset_mock()
    swb.os.rmdir.reset_mock()
    # reset_mock() doesn't clear return_value or any child attributes
    swb.subprocess = NonCallableMagicMock()
