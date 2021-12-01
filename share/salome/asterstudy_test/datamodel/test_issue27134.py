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

"""Automatic tests for issue with variables."""


import unittest

from hamcrest import *  # pragma pylint: disable=unused-import
from asterstudy.datamodel.history import History

def test():
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':1:')

    mesh = stage('LIRE_MAILLAGE', 'mesh')
    fieldmat = stage('AFFE_MATERIAU', 'fieldmat')
    mater = stage('DEFI_MATERIAU', 'mater')

    fieldmat['AFFE']['TOUT'] = 'OUI'
    fieldmat['AFFE']['MATER'] = mater
    fieldmat.check()

    assert_that(mater, is_in(fieldmat.parent_nodes))

    rc1 = history.create_run_case()
    rc2 = history.create_run_case()

    # this checks that child_nodes property is specialized for DataSet
    new_fieldmat = rc2[0]['fieldmat']
    assert_that(mater, is_not(is_in(new_fieldmat.parent_nodes)))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
