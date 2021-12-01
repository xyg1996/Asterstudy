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
'Edition panel: management of Python variables (CCTP 2.3.2)' functionality"""


import unittest

from hamcrest import * # pragma pylint: disable=unused-import

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.command import Command
from asterstudy.datamodel.comm2study import comm2study

#------------------------------------------------------------------------------
def test_filterby():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('a', '1').evaluation, equal_to(1))

    assert_that(Command.filterby(stage, 'I'), contains(stage['a']))
    assert_that(Command.filterby(stage, 'R'), contains(stage['a']))
    assert_that(Command.filterby(stage, 'TXM'), empty())

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('b', '"xxx"').evaluation, equal_to("xxx"))

    assert_that(Command.filterby(stage, 'I'), contains(stage['a']))
    assert_that(Command.filterby(stage, 'R'), contains(stage['a']))
    assert_that(Command.filterby(stage, 'TXM'), contains(stage['b']))

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('c', '1.0').evaluation, equal_to(1))

    assert_that(Command.filterby(stage, 'I'), contains(stage['c'], stage['a']))
    assert_that(Command.filterby(stage, 'R'), contains(stage['c'], stage['a']))
    assert_that(Command.filterby(stage, 'TXM'), contains(stage['b']))

    #--------------------------------------------------------------------------
    stage.add_command('LIRE_MAILLAGE', 'm')

    astype = stage['m']['INFO'].gettype()
    assert_that(stage['m'].groupby(astype), has_item(stage['a']))
    stage['m']['INFO'] = stage['a']

    #--------------------------------------------------------------------------
    astype = stage['m']['FORMAT'].gettype()
    assert_that(stage['m'].groupby(astype), has_item(stage['b']))
    stage['m']['FORMAT'] = stage['b']

    #--------------------------------------------------------------------------
    stage.add_variable('d', '@$%')
    assert_that(stage['d'].gettype(), none())

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_no_type():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
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
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    astype = stage['CHM']['AFFE'].gettype('MATER')
    assert_that(stage['CHM'].groupby(astype), contains(stage['M']))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_validity():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('a', '1').evaluation, equal_to(1))
    assert_that(stage['a'].check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('b', '"xxx"').evaluation, equal_to("xxx"))
    assert_that(stage['a'].check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    stage.add_command('LIRE_MAILLAGE', 'm')
    stage['m']['INFO'] = stage['a']
    assert_that(stage['m'].check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    stage['a'].update('3.3')
    assert_that(stage['a'].evaluation, equal_to(3.3))
    assert_that(stage['a'].check(), equal_to(Validity.Ok))
    assert_that(stage['m'].check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    stage['a'].update('"aaa"')
    assert_that(stage['a'].evaluation, equal_to("aaa"))
    assert_that(stage['a'].check(), equal_to(Validity.Ok))
    assert_that(stage['m'].check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    stage['a'].update('1')
    assert_that(stage['a'].evaluation, equal_to(1))
    assert_that(stage['a'].check(), equal_to(Validity.Ok))
    assert_that(stage['m'].check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    astype = stage['m']['FORMAT'].gettype()
    assert_that(stage['m'].groupby(astype), has_item(stage['b']))
    stage['m']['FORMAT'] = stage['b']
    assert_that(stage['m'].check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    stage['b'].update('"MED"')
    assert_that(stage['b'].evaluation, equal_to("MED"))
    assert_that(stage['b'].check(), equal_to(Validity.Ok))
    assert_that(stage['m'].check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
