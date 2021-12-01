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

"""Data Model tests for
Removing DEBUT command makes stage invalide in Dependency terms"""


import unittest

from hamcrest import * # pragma pylint: disable=unused-import
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.comm2study import comm2study

def test():
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE(UNITE=20)

M = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHM = AFFE_MATERIAU(AFFE=_F(MATER=M, TOUT='OUI'), MAILLAGE=MAIL_Q)
"""
    for idx, validity in [(0, Validity.Ok),
                          (1, Validity.Dependency),
                          (2, Validity.Dependency),
                          (3, Validity.Ok)]:
        history = History()
        case = history.current_case
        stage = case.create_stage(':1:')

        comm2study(text, stage)

        assert_that(stage.check(), equal_to(Validity.Ok))

        del stage[idx]

        assert_that(stage.check(), equal_to(validity))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
