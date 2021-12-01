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

"""Automatic tests for issue with adjacency matrix."""


import unittest

from hamcrest import *
from asterstudy.datamodel.history import History

def test():
    "Test that the adjacency matrix keeps transitive closure"
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':1:')

    # create 2 commands dependent on one another
    model = stage('AFFE_MODELE', 'model')
    fieldmat = stage('AFFE_MATERIAU', 'fieldmat')
    fieldmat['MODELE'] = model

    # add a mesh command on top of the first one
    mesh = stage('LIRE_MAILLAGE', 'mesh')
    model['MAILLAGE'] = mesh

    # assert that transitive closure was kept during process
    assert_that(model.depends_on(mesh), equal_to(True))
    assert_that(fieldmat.depends_on(model), equal_to(True))

    # Here is the crucial test of transitivity
    assert_that(fieldmat.depends_on(mesh), equal_to(True))

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
