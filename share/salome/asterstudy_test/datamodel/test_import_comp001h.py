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

"""Automatic tests for export feature."""


import unittest
from hamcrest import *

from asterstudy.common import ConversionError
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.history import History

from testutils.tools import check_export, check_import

#------------------------------------------------------------------------------
def test_command_dependencies():
    """Test for comp001h.comm: command dependencies"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    command = stage.add_command('DEBUT')

    factor = command['CODE']
    factor['NIV_PUB_WEB'] = 'INTERNET'

    command['IGNORE_ALARM'] = 'ELEMENTS3_11'

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_MATERIAU', '_41')

    factor = command['ECRO_PUIS']
    factor['A_PUIS'] = 0.1
    factor['N_PUIS'] = 10.0
    factor['SY'] = 200000000.0

    factor = command['ELAS']
    factor['ALPHA'] = 1.18e-05
    factor['E'] = 2e+11
    factor['NU'] = 0.3

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_MATERIAU', '_1672')

    factor = command['ECRO_PUIS']
    factor['A_PUIS'] = 0.1
    factor['N_PUIS'] = 10.0
    factor['SY'] = 200.0

    factor = command['ELAS']
    factor['ALPHA'] = 1.18e-05
    factor['E'] = 200000.0
    factor['NU'] = 0.3

    #--------------------------------------------------------------------------
    command = stage.add_command('TEST_COMPOR', 'tabresu')

    factor = command['COMPORTEMENT']
    factor['ITER_INTE_MAXI'] = 50
    factor['RELATION'] = 'VMIS_ISOT_PUIS'
    factor['RESI_INTE_RELA'] = 1e-06

    command['OPTION'] = 'MECA'

    assert('LIST_MATER' in command.rkeys())
    factor = command['LIST_MATER']

    command['LIST_MATER'] = [stage['_41'], stage['_1672']]

    assert(stage['tabresu'].depends_on(stage['_1672']))

    assert(stage['tabresu'].depends_on(stage['_1672']))

    assert(stage['_41'] in command['LIST_MATER'].value)

    command['LIST_NPAS'] = [1, 1, 1, 1, 1, 5, 25]

    command['NEWTON']['REAC_ITER'] = 1

    command['POISSON'] = 0.3

    command['VARI_TEST'] = ('V1', 'VMIS', 'TRACE')

    command['YOUNG'] = 200000.0

    #--------------------------------------------------------------------------
    command = stage.add_command('FIN')

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      IGNORE_ALARM='ELEMENTS3_11')

_41 = DEFI_MATERIAU(ECRO_PUIS=_F(A_PUIS=0.1,
                                 N_PUIS=10.0,
                                 SY=200000000.0),
                    ELAS=_F(ALPHA=1.18e-05,
                            E=200000000000.0,
                            NU=0.3))

_1672 = DEFI_MATERIAU(ECRO_PUIS=_F(A_PUIS=0.1,
                                   N_PUIS=10.0,
                                   SY=200.0),
                      ELAS=_F(ALPHA=1.18e-05,
                              E=200000.0,
                              NU=0.3))

tabresu = TEST_COMPOR(COMPORTEMENT=_F(ITER_INTE_MAXI=50,
                                      RELATION='VMIS_ISOT_PUIS',
                                      RESI_INTE_RELA=1e-06),
                      LIST_MATER=[_41, _1672],
                      LIST_NPAS=[1, 1, 1, 1, 1, 5, 25],
                      NEWTON=_F(REAC_ITER=1),
                      OPTION='MECA',
                      POISSON=0.3,
                      VARI_TEST=('V1', 'VMIS', 'TRACE'),
                      YOUNG=200000.0)

FIN()
"""
    assert(check_export(stage, text))

    #--------------------------------------------------------------------------
    command = stage['tabresu']

    simple = command['LIST_MATER']

    assert(stage['tabresu'].depends_on(stage['_1672']))

    simple.value = [stage['_41']]

    assert(stage['tabresu'].depends_on(stage['_1672']) == False)

    simple.value = [stage['_41'], stage['_1672']]

    assert(stage['tabresu'].depends_on(stage['_1672']))

    assert(stage['_41'] in simple.value)

    assert(stage['_41'] in command['LIST_MATER'].value)

    assert(stage['tabresu'].depends_on(stage['_41']))

    assert(check_export(stage, text))

    #--------------------------------------------------------------------------
    assert(check_import(text))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_implicit_command_names():
    """Test for comp001h.comm: implicit command names"""
    #--------------------------------------------------------------------------
    text = \
"""
# def des materiaux
ACIER = [None]*2

DEBUT()

ACIER[0] = DEFI_MATERIAU(
    ECRO_PUIS=_F(A_PUIS=0.1,
                 N_PUIS=10.0,
                 SY=200000000.0, ),
    ELAS=_F(ALPHA=1.18e-05,
            E=2e+11,
            NU=0.3, ), )

ACIER[1] = DEFI_MATERIAU(
    ECRO_PUIS=_F(A_PUIS=0.1, N_PUIS=10.0, SY=200.0),
    ELAS=_F(ALPHA=1.18e-05, E=200000.0, NU=0.3)
)

FIN()
"""
    #--------------------------------------------------------------------------
    from asterstudy.datamodel.history import History
    history = History()

    case = history.current_case
    stage = case.create_stage(':memory:')

    assert_that(calling(comm2study).with_args(text, stage, True),
                raises(ConversionError, "NotImplementedError.*List of"))
    # the stage must not have been changed
    assert_that(stage, has_length(0))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
