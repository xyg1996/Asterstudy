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

"""Automatic tests for Feature #1153 -
Edition panel: management of macro keywords (CCTP 2.3.3)
implementation"""


import unittest
from hamcrest import *

from asterstudy.datamodel.catalogs import CATA
from asterstudy.datamodel.history import History
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.command import CO, Hidden

#------------------------------------------------------------------------------
def test_initialization_via_dictionary():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')

    mesh = stage("LIRE_MAILLAGE", "mesh")
    mesh['UNITE'] = 20

    #--------------------------------------------------------------------------
    stage('MACR_ADAP_MAIL')
    assert_that(stage, has_length(2))

    stage[1]['ADAPTATION'] = 'RAFFINEMENT_UNIFORME'
    stage[1]['MAILLAGE_N'] = stage['mesh']

    stage[1]['MAILLAGE_NP1'] = 'meshout'
    assert_that('meshout', is_in(stage))
    assert_that(stage, has_length(3))

    decls = stage[1].list_co
    assert_that(decls, has_length(1))
    assert_that(decls[0].name, equal_to('meshout'))
    assert_that('DECL', is_in(stage['meshout'].keys()))

    assert_that(stage['meshout'].check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    dsm = CATA.package("DataStructure")
    assert_that(stage['mesh'].gettype(), equal_to(dsm.maillage_sdaster))
    assert_that(stage['meshout'].gettype(), equal_to(dsm.maillage_sdaster))

    stage('DEFI_GROUP', 'mesh2')
    assert_that(stage, has_length(4))

    stage[3]['MAILLAGE'] = stage['meshout']
    fact = stage[3]['DETR_GROUP_MA']
    fact['NOM'] = 'group'

    #--------------------------------------------------------------------------
    stage('MACR_ADAP_MAIL')
    assert_that(stage, has_length(5))

    stage[4].init({'MAILLAGE_N': mesh,
                   'ADAPTATION': 'RAFFINEMENT_UNIFORME',
                   'MAILLAGE_NP1': CO('meshout')})
    assert_that(stage[4].check(), equal_to(Validity.Ok))
    assert_that(stage, has_length(6))

    assert_that(stage[5], instance_of(Hidden))
    assert_that(stage[5].name, equal_to('meshout'))

    assert_that(stage[1] * stage[4], none())

    #--------------------------------------------------------------------------
    stage[4].init({'MAILLAGE_N': mesh,
                   'ADAPTATION': 'RAFFINEMENT_UNIFORME'})
    assert_that(stage, has_length(5))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_delete_parent_macro_command():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')

    mesh = stage("LIRE_MAILLAGE", "mesh")
    mesh['UNITE'] = 20

    #--------------------------------------------------------------------------
    stage('MACR_ADAP_MAIL')
    assert_that(stage, has_length(2))

    stage[1]['ADAPTATION'] = 'RAFFINEMENT_UNIFORME'
    stage[1]['MAILLAGE_N'] = stage['mesh']

    stage[1]['MAILLAGE_NP1'] = 'meshout'
    assert_that('meshout', is_in(stage))
    assert_that(stage, has_length(3))

    del stage[1]

    assert_that(stage, has_length(1))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_initialization_via_text():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')

    snippet = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

MACR_ADAP_MAIL = MACR_ADAP_MAIL(
    ADAPTATION='RAFFINEMENT_UNIFORME',
    MAILLAGE_N=mesh,
    MAILLAGE_NP1=CO('meshout')
)

mesh2 = DEFI_GROUP(DETR_GROUP_MA=_F(NOM=('group', )), MAILLAGE=meshout)
"""
    stage.paste(snippet)
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
