# -*- coding: utf-8 -*-

# Copyright 2016 - 2017 EDF R&D
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


import os
import os.path as osp
import unittest

from hamcrest import *
from testutils import attr

from asterstudy.common import CFG
from asterstudy.datamodel import CATA, History
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import ConversionLevel, Validity
from asterstudy.datamodel.study2comm import study2comm


def test():
    """Test for export with default keywords"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    # from test/squish/suite_acceptance_lot1_lot2/tst_commands_creation/ref/
    comm = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'data', 'export', 'beforeList_r.comm')
    with open(comm, "rb") as file:
        text = file.read()
    strict = ConversionLevel.Any
    comm2study(text, stage, strict)

    assert_that(stage.check(), equal_to(Validity.Nothing))

    out1 = study2comm(stage)
    assert_that(out1, contains_string('Cont_mast'))
    assert_that(out1, is_not(contains_string('ADAPTATION')))
    assert_that(out1, is_not(contains_string('CONTACT_INIT')))

    zone = stage['Cont1']['ZONE']
    # user dict
    assert_that(zone._storage, has_key('GROUP_MA_ESCL'))
    assert_that(zone._storage, has_key('GROUP_MA_MAIT'))
    assert_that(zone._storage, has_length(2))

    checker = CATA.package('Syntax').SyntaxCheckerVisitor()
    zone.cata.accept(checker, zone._storage)

    assert_that(zone._storage, has_key('GROUP_MA_ESCL'))
    assert_that(zone._storage, has_key('GROUP_MA_MAIT'))
    assert_that(zone._storage, has_length(2))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
