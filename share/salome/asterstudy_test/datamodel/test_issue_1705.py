# -*- coding: utf-8 -*-

# Copyright 2016-2018 EDF R&D
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License Version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, you may download a copy of license
# from https://www.gnu.org/licenses/gpl-3.0.


import unittest
from itertools import chain

from hamcrest import *

from asterstudy.common import is_valid_group_name

def test_of_input_data():
    """Test for mesh group name validity check"""
    assert_that(is_valid_group_name(None), equal_to(False))
    assert_that(is_valid_group_name(''), equal_to(False))
    assert_that(is_valid_group_name('aaa bbb'), equal_to(False))
    for i in range(1, 25):
        assert_that(is_valid_group_name('a'*i), equal_to(True))
    for i in range(25, 100):
        assert_that(is_valid_group_name('a'*i), equal_to(False))
    assert_that(is_valid_group_name('a'*25), equal_to(False))
    invalid_codes = chain(range(32, 48), range(58, 65), range(91, 97), range(123, 127))
    invalid_codes = [chr(i) for i in invalid_codes]
    invalid_codes.remove('+')
    invalid_codes.remove('-')
    invalid_codes.remove('.')
    invalid_codes.remove('_')
    for i in invalid_codes:
        assert_that(is_valid_group_name(i), equal_to(False))

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
