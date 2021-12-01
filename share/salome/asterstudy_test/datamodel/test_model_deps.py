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

from asterstudy.datamodel.history import History
from asterstudy.datamodel.abstract_data_model import add_parent, remove_parent


def test():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    debut = stage('DEBUT')
    mesh = stage('LIRE_MAILLAGE')
    model = stage('AFFE_MODELE')
    mat = stage('DEFI_MATERIAU')
    matfield = stage('AFFE_MATERIAU')

    deps = history._deps[3:, 3:]
    assert_that(min(deps[0]), equal_to(1))
    assert_that(max(deps[0]), equal_to(1))
    for i in range(1, 5):
        assert_that(deps[i, i], equal_to(1))
        assert_that(sum(deps[i]), equal_to(1))

    add_parent(model, mesh)
    add_parent(matfield, mat)
    add_parent(matfield, model)
    deps = history._deps[3:, 3:]
    assert_that((deps == ((1, 1, 1, 1, 1),
                          (0, 1, 1, 0, 1),
                          (0, 0, 1, 0, 1),
                          (0, 0, 0, 1, 1),
                          (0, 0, 0, 0, 1))).all(), equal_to(True))
    assert_that(matfield.depends_on(mesh), equal_to(True))

    remove_parent(matfield, model)
    assert_that((deps == ((1, 1, 1, 1, 1),
                          (0, 1, 1, 0, 0),
                          (0, 0, 1, 0, 0),
                          (0, 0, 0, 1, 1),
                          (0, 0, 0, 0, 1))).all(), equal_to(True))
    assert_that(matfield.depends_on(mesh), equal_to(False))

    return history


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

    # history = test()
    # deps = history._deps[3:, 3:]
    # print deps
