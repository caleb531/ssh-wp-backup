#!/usr/bin/env python3

import glob
import os.path
from unittest.mock import MagicMock
import src.local as swb
import mocks.local as mocks


def before_all():

    swb.glob.iglob = MagicMock(return_value=mocks.mock_backups)
    swb.os = MagicMock()
    swb.os.makedirs = MagicMock()
    swb.os.remove = MagicMock()
    swb.os.rmdir = MagicMock()
    swb.os.stat = mocks.mock_os_stat
    swb.os.path.basename = os.path.basename
    swb.os.path.dirname = os.path.dirname
    swb.os.path.expanduser = os.path.expanduser
    swb.subprocess = MagicMock()


def before_each():
    pass


def after_each():
    swb.os.makedirs.reset_mock()
    swb.os.remove.reset_mock()
    swb.os.rmdir.reset_mock()
    swb.subprocess.reset_mock()
