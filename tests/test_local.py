#!/usr/bin/env python3

import configparser
# import os
import nose.tools as nose
import swb.local as swb
from mock import patch
# from tests.fixtures.local import set_up, tear_down, mock_backups


def test_parse_config():
    """should correctly parse the supplied configuration file"""
    config_path = 'tests/files/config.ini'
    config = swb.parse_config(config_path)
    expected_config = configparser.RawConfigParser()
    expected_config.read(config_path)
    nose.assert_equal(config, expected_config)


@patch('os.makedirs')
def test_create_dir_structure(makedirs):
    """should create the directory structure for the supplied path"""
    swb.create_dir_structure('a/b c/d')
    makedirs.assert_called_once_with('a/b c')


@patch('os.makedirs', side_effect=OSError)
def test_create_dir_structure_silent_fail(makedirs):
    """should fail silently if directory structure already exists"""
    swb.create_dir_structure('a/b c/d')
    makedirs.assert_called_once_with('a/b c')


def test_unquote_home_dir_path_with_tilde():
    """should unquote the tilde (~) in the supplied quoted path"""
    unquoted_path = swb.unquote_home_dir('\'~/a/b c/d\'')
    nose.assert_equal(unquoted_path, '~/\'a/b c/d\'')


def test_unquote_home_dir_path_without_tilde():
    """should return the supplied quoted path"""
    unquoted_path = swb.unquote_home_dir('\'/a/b c/d\'')
    nose.assert_equal(unquoted_path, '\'/a/b c/d\'')


def test_quote_arg():
    """should correctly quote arguments passed to the shell"""
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')


@patch('swb.local.shlex')
def test_quote_arg_py32(shlex):
    """should correctly quote arguments passed to the shell on Python 3.2"""
    del shlex.quote
    nose.assert_false(hasattr(shlex, 'quote'))
    quoted_arg = swb.quote_arg('a/b c/d')
    nose.assert_equal(quoted_arg, '\'a/b c/d\'')
