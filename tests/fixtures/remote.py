#!/usr/bin/env python3

import src.remote as swb
import fixtures.shared as shared
from unittest.mock import Mock, mock_open


TEST_WP_CONFIG_PATH = 'tests/files/wp-config.php'
with open(TEST_WP_CONFIG_PATH) as wp_config:
    TEST_WP_CONFIG_CONTENTS = wp_config.read()


def before_all():
    shared.before_all(swb)
    swb.os.path.getsize = Mock(return_value=54321)


def before_each():
    shared.before_each(swb)
    mock_open_inst = mock_open(read_data=TEST_WP_CONFIG_CONTENTS)
    swb.open = mock_open_inst


def after_each():
    shared.after_each(swb)
    swb.os.path.getsize.reset_mock()
