#!/usr/bin/env python3

import os
import os.path
import subprocess
from unittest.mock import Mock, mock_open, NonCallableMock


def before_all(module):

    module.os = NonCallableMock()
    module.os.devnull = os.devnull
    module.os.makedirs = Mock()
    module.os.remove = Mock()
    module.os.rmdir = Mock()
    module.os.path.basename = os.path.basename
    module.os.path.dirname = os.path.dirname
    module.os.path.expanduser = os.path.expanduser
    module.os.path.join = os.path.join


def before_each(module):
    # reset_mock() doesn't clear return_value or any child attributes
    module.subprocess.Popen = Mock(return_value=Mock(returncode=0))


def after_each(module):
    module.os.makedirs.reset_mock()
    module.os.remove.reset_mock()
    module.os.rmdir.reset_mock()
