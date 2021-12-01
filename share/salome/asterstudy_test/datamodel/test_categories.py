# -*- coding: utf-8 -*-

# Copyright 2016 EDF R&D
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

"""Automatic tests for categories."""


import unittest
from hamcrest import *

from asterstudy.datamodel.catalogs import CATA

#------------------------------------------------------------------------------
def test_default_categories():
    """Test for categories definition"""
    #--------------------------------------------------------------------------
    # Check number of categories

    # - total (all from dict_categories + Variables, Other, Deprecated, Hidden)
    categories = CATA.get_categories()
    assert_that(categories, has_length(10 + 4))

    # - for the toolbar
    categories = CATA.get_categories("toolbar")
    assert_that(categories, has_length(10))

    # - for the ShowAll dialog
    categories = CATA.get_categories("showall")
    assert_that(categories, has_length(12))

    #--------------------------------------------------------------------------
    # Check categories order
    categories = CATA.get_categories()
    assert_that(categories[1], equal_to('Mesh'))
    assert_that(categories[2], equal_to('Model Definition'))
    assert_that(categories[3], equal_to('Material'))

    #--------------------------------------------------------------------------
    # Check specific category
    cmds = CATA.get_category('Material')
    assert_that(cmds, has_length(9))

    #--------------------------------------------------------------------------
    # Check command's category and sub-category
    assert_that(cmds[0], equal_to('AFFE_MATERIAU'))
    assert_that(CATA.get_command_category(cmds[0]), equal_to('Material'))
    assert_that(CATA.get_command_subcategory(cmds[0]), none())

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
