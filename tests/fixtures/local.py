#!/usr/bin/env python3

import glob
import os.path
import src.local as swb
import mocks.local as mocks
from unittest.mock import Mock, NonCallableMagicMock


def before_all():

    swb.glob.iglob = Mock(return_value=mocks.mock_backups)
    swb.os = NonCallableMagicMock()
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
    swb.os.makedirs.reset_mock()
    swb.os.remove.reset_mock()
    swb.os.rmdir.reset_mock()
    swb.subprocess.reset_mock()
