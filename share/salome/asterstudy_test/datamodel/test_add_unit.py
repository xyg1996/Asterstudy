# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 EDF R&D
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

"""Automatic tests for unit management during import."""


import unittest

from asterstudy.datamodel.catalogs import CATA
from asterstudy.datamodel.comm2study import add_unit_default_value
from hamcrest import *


def test_unit():
    cata = CATA.get_catalog('LIRE_MAILLAGE')
    keywords = dict()
    add_unit_default_value(cata, keywords)
    assert_that(keywords, has_key('UNITE'))

    cata = CATA.get_catalog('IMPR_TABLE')
    dsm = CATA.package("DataStructure")

    # default FORMAT (='ASTER') uses by default UNITE=8
    table = dsm.table_sdaster()
    keywords = dict(TABLE=table)
    add_unit_default_value(cata, keywords)
    assert_that(keywords, has_key('UNITE'))

    # with FORMAT='XMGRACE', default value is 29
    table = dsm.table_sdaster()
    keywords = dict(TABLE=table, FORMAT='XMGRACE')
    add_unit_default_value(cata, keywords)
    assert_that(keywords, has_key('UNITE'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
