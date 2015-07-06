#!/usr/bin/env python

import os.path
import nose.tools as nose
import pep8
import radon.complexity as radon


def test_pep8():
    '''all Python files should comply with PEP 8'''
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


def test_complexity():
    '''all Python functions should have a low cyclomatic complexity score'''
    for subdir_path, subdir_names, file_names in os.walk('.'):
        if '.git' in subdir_names:
            subdir_names.remove('.git')
        for file_name in file_names:
            file_path = os.path.join(subdir_path, file_name)
            file_ext = os.path.splitext(file_name)[1]
            if file_ext == '.py':
                with open(file_path, 'r') as file:
                    blocks = radon.cc_visit(file.read())
                    for block in blocks:
                        complexity = block.complexity
                        test_doc = '{} ({}) should have a low complexity score'
                        test_complexity.__doc__ = test_doc.format(
                            block.name, file_path)
                        fail_msg = '{} ({}) has a complexity of {}'.format(
                            block.name, file_path, complexity)
                        yield nose.assert_less_equal, complexity, 10, fail_msg
