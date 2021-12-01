# coding=utf-8

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

"""Test for issue27760"""


import unittest

from asterstudy.datamodel import History, comm2study
from hamcrest import *


def test():
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

mater = DEFI_MATERIAU(ELAS=_F(E=2.1e9, NU=0.3))

fieldmat = AFFE_MATERIAU(AFFE=_F(MATER=(mater, ), TOUT='OUI'), MAILLAGE=mesh)
"""
    history = History()
    stage = history.current_case.create_stage("orig")
    comm2study(text, stage)

    mater = stage['mater']
    fieldmat = stage['fieldmat']
    assert_that(mater, is_in(fieldmat.parent_nodes))

    # done by Case.copy_shared_stages_from()
    stage.copy(history.current_case)
    stage = history.current_case[0]

    mater = stage['mater']
    fieldmat = stage['fieldmat']
    assert_that(mater, is_in(fieldmat.parent_nodes))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
