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


import unittest

from hamcrest import *

from asterstudy.datamodel import History


def test_variable():
    """Test for copy with variables"""
    history = History()
    case = history.current_case
    case.name = 'c1'
    stage = case.create_stage('s1')

    stage.add_variable('a', '1')

    command = stage('DEFI_MATERIAU', 'mat')
    factor = command['ELAS']
    factor['E'] = stage['a']
    factor['NU'] = 0.2
    factor['RHO'] = 2764.0

    rc = history.create_run_case()
    stage.copy(parent_case=rc)
    # just pass here is a success!
    assert_that(True)


def test_hidden():
    """Test for copy with hidden commands"""
    history = History()
    case = history.current_case
    case.name = 'c1'
    stage = case.create_stage('s1')

    mesh = stage('LIRE_MAILLAGE', 'mesh')

    cmd = stage.add_command('MACR_ADAP_MAIL')
    cmd['ADAPTATION'] = 'RAFFINEMENT_UNIFORME'
    cmd['MAILLAGE_N'] = mesh
    cmd['MAILLAGE_NP1'] = 'mesh_np1'

    assert_that(cmd.list_co, has_length(1))

    rc = history.create_run_case()
    stage.copy(parent_case=rc)
    # just pass here is a success!
    assert_that(True)


def test_hidden_on_deletion():
    """Test for behavior of hidden commands"""
    history = History()
    case = history.current_case
    case.name = 'c1'
    stage = case.create_stage('s1')

    debut = stage('DEBUT')

    mesh = stage('LIRE_MAILLAGE', 'mesh')

    cmd = stage.add_command('MACR_ADAP_MAIL')
    cmd['ADAPTATION'] = 'RAFFINEMENT_UNIFORME'
    cmd['MAILLAGE_N'] = mesh
    cmd['MAILLAGE_NP1'] = 'mesh_np1'

    assert_that(cmd.list_co, has_length(1))
    assert_that(stage, has_length(4))
    assert_that(stage[0].title, equal_to("DEBUT"))
    assert_that(stage[1].title, equal_to("LIRE_MAILLAGE"))
    assert_that(stage[2].title, equal_to("MACR_ADAP_MAIL"))
    assert_that(stage[3].title, equal_to("_RESULT_OF_MACRO"))

    debut.delete()
    assert_that(cmd.list_co, has_length(1))
    assert_that(stage, has_length(3))
    assert_that(stage[0].title, equal_to("LIRE_MAILLAGE"))
    assert_that(stage[1].title, equal_to("MACR_ADAP_MAIL"))
    assert_that(stage[2].title, equal_to("_RESULT_OF_MACRO"))


def test_hidden_on_deletion2():
    """Test for behavior of hidden commands"""
    history = History()
    case = history.current_case
    case.name = 'c1'
    stage = case.create_stage('s1')

    debut = stage('DEBUT')

    mesh = stage('LIRE_MAILLAGE', 'mesh')

    cmd = stage.add_command('MACR_ADAP_MAIL')
    cmd['ADAPTATION'] = 'RAFFINEMENT_UNIFORME'
    cmd['MAILLAGE_N'] = mesh
    cmd['MAILLAGE_NP1'] = 'mesh_np1'

    assert_that(cmd.list_co, has_length(1))
    assert_that(stage, has_length(4))
    assert_that(stage[0].title, equal_to("DEBUT"))
    assert_that(stage[1].title, equal_to("LIRE_MAILLAGE"))
    assert_that(stage[2].title, equal_to("MACR_ADAP_MAIL"))
    assert_that(stage[3].title, equal_to("_RESULT_OF_MACRO"))

    cmd.delete()
    assert_that(cmd.list_co, has_length(1))
    assert_that(stage, has_length(2))
    assert_that(stage[0].title, equal_to("DEBUT"))
    assert_that(stage[1].title, equal_to("LIRE_MAILLAGE"))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
