#!/usr/bin/env python3

import src.remote as swb
import fixtures.shared as shared
from unittest.mock import Mock, NonCallableMagicMock


def before_all():
    shared.before_all(swb)
    swb.os.path.getsize = Mock(return_value=54321)


def before_each():
    shared.before_each(swb)


def after_each():
    shared.after_each(swb)
