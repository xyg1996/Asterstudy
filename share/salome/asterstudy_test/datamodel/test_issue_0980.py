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

"""Miscellaneous test cases"""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

#------------------------------------------------------------------------------
def test_case_1_unique_names():
    #--------------------------------------------------------------------------
    text = \
"""
m1 = LIRE_MAILLAGE()

m2 = MODI_MAILLAGE(MAILLAGE=m1, ORIE_PEAU_2D=_F(GROUP_MA='A'))

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='C_PLAN', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=m2
)"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    assert_that(stage, has_length(3))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    command = stage[2]
    assert_that(command.check(), equal_to(Validity.Nothing))

    del stage[1]

    assert_that(stage, has_length(2))
    assert_that(stage[0].check(), equal_to(Validity.Nothing))
    assert_that(command.check(), is_not(equal_to(Validity.Nothing)))
    assert_that(stage[1].check(), is_not(equal_to(Validity.Nothing)))

    #--------------------------------------------------------------------------
    pass


#------------------------------------------------------------------------------
def test_case_2_unique_names():
    #--------------------------------------------------------------------------
    text = \
"""
m1 = LIRE_MAILLAGE()

m2 = MODI_MAILLAGE(MAILLAGE=m1, ORIE_PEAU_2D=_F(GROUP_MA='A'))

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='C_PLAN', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=m2
)
"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    assert_that(stage, has_length(3))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    command = stage[2]
    assert_that(command.check(), equal_to(Validity.Nothing))

    del stage[0]

    assert_that(stage, has_length(2))
    assert_that(stage[0].check(), is_not(equal_to(Validity.Nothing)))
    assert_that(stage[1].check(), is_not(equal_to(Validity.Nothing)))
    assert_that(command.check(), is_not(equal_to(Validity.Nothing)))

    #--------------------------------------------------------------------------
    pass


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
