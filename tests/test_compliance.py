#!/usr/bin/env python

import os.path
import nose.tools as nose
import pep8


def test_pep8():
    '''all Python files should comply with PEP 8'''
    print('YDFSDFSFDS')
    for subdir_path, subdir_names, file_names in os.walk('.'):
        if '.git' in subdir_names:
            subdir_names.remove('.git')
        for file_name in file_names:
            file_path = os.path.join(subdir_path, file_name)
            file_ext = os.path.splitext(file_name)[1]
            if file_ext == '.py':
                style_guide = pep8.StyleGuide(quiet=True)
                total_errors = style_guide.input_file(file_path)
                msg = '{} does not comply with PEP 8'.format(file_path)
                yield nose.assert_equal, total_errors, 0, msg
