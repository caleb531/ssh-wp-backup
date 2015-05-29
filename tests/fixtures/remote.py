#!/usr/bin/env python3

import os
import src.remote as swb
import mocks.remote as mocks
from unittest.mock import Mock, NonCallableMagicMock


def before_all():

    swb.os = NonCallableMagicMock()
    swb.os.makedirs = Mock()
    swb.os.remove = Mock()
    swb.subprocess = NonCallableMagicMock()


def before_each():
    pass


def after_each():
    swb.os.makedirs.reset_mock()
    swb.os.remove.reset_mock()
    swb.subprocess = NonCallableMagicMock()
