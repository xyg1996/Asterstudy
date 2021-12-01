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

from asterstudy.datamodel.history import History
from testutils import attr
from testutils.tools import check_export, check_import, check_translation


#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    command = stage.add_command('CREA_TABLE', 'tab1')

    sequence = command['LISTE']
    sequence['PARA'] = 'DOMMAGE'
    sequence['LISTE_R'] = [0., 1.]

    #--------------------------------------------------------------------------
    command = stage.add_command('TEST_TABLE')

    command['REFERENCE'] = 'ANALYTIQUE'
    command['VALE_REFE'] = 5.E-06

    command['PRECISION'] = 1.E-05
    command['VALE_CALC'] = 5.E-06
    command['NOM_PARA'] = 'DOMMAGE'
    command['TABLE'] = stage['tab1']

    sequence = command['FILTRE']
    sequence['NOM_PARA'] = 'CYCLE'

    sequence['VALE_I'] = 1
    assert('VALE_I' in sequence.rkeys())

    simple = sequence['VALE_I']
    assert(simple.value == 1)

    assert(sequence['VALE_I'] == 1)

    #--------------------------------------------------------------------------
    text = \
"""
tab1 = CREA_TABLE(LISTE=_F(LISTE_R=[0.0, 1.0],
                           PARA='DOMMAGE'))

TEST_TABLE(FILTRE=_F(NOM_PARA='CYCLE',
                     VALE_I=1),
           NOM_PARA='DOMMAGE',
           PRECISION=1e-05,
           REFERENCE='ANALYTIQUE',
           TABLE=tab1,
           VALE_CALC=5e-06,
           VALE_REFE=5e-06)
"""
    #--------------------------------------------------------------------------
    assert(check_export(stage, text))

    #--------------------------------------------------------------------------
    import pickle
    blob = pickle.dumps(history)
    history2 = pickle.loads(blob)

    case = history2.current_case
    stage2 = case[':memory:']

    #--------------------------------------------------------------------------
    assert(check_export(stage2, text))

    assert(check_import(text))

    assert(check_translation(stage, text))

    #--------------------------------------------------------------------------
    pass


#------------------------------------------------------------------------------
def test_empty_factor():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage("Stage")

    command = stage('DEBUT')

    # the factor keyword exists but is empty
    err = command['ERREUR']

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(ERREUR=_F())
"""

    assert(check_export(stage, text))

    #--------------------------------------------------------------------------
    pass


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
