#!/usr/bin/env python

import nose.tools as nose
import glob
import json
import pep8


def test_pep8():
    '''all Python files should comply with PEP 8'''
    files = glob.iglob('*/*.py')
    for file in files:
        style_guide = pep8.StyleGuide(quiet=True)
        total_errors = style_guide.input_file(file)
        msg = '{} does not comply with PEP 8'.format(file)
        yield nose.assert_equal, total_errors, 0, msg
