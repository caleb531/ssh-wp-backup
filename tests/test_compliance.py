# #!/usr/bin/env python
#
# import glob
# import itertools
# import nose.tools as nose
# import pep8
# import radon.complexity as radon
#
#
# def test_pep8():
#     file_paths = glob.iglob('*/*.py')
#     for file_path in file_paths:
#         style_guide = pep8.StyleGuide(quiet=True)
#         total_errors = style_guide.input_file(file_path)
#         test_pep8.__doc__ = '{} should comply with PEP 8'.format(file_path)
#         fail_msg = '{} does not comply with PEP 8'.format(file_path)
#         yield nose.assert_equal, total_errors, 0, fail_msg
#
#
# def test_complexity():
#     file_paths = itertools.chain(glob.iglob('*/*.py'), glob.iglob('*/*/*.py'))
#     for file_path in file_paths:
#         with open(file_path, 'r') as file:
#             blocks = radon.cc_visit(file.read())
#         for block in blocks:
#             test_doc = '{} ({}) should have a low cyclomatic complexity score'
#             test_complexity.__doc__ = test_doc.format(
#                 block.name, file_path)
#             fail_msg = '{} ({}) has a cyclomatic complexity of {}'.format(
#                 block.name, file_path, block.complexity)
#             yield nose.assert_less_equal, block.complexity, 10, fail_msg
