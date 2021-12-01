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


import os
import unittest

from hamcrest import *
from testutils import attr
from asterstudy.common import CFG

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.study2comm import study2comm

from testutils.tools import check_export, check_import, check_translation


def test():
    """Test for szlz108b.comm"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    command = stage.add_command('DEBUT')

    command['CODE']['NIV_PUB_WEB'] = 'INTERNET'
    command['DEBUG']['SDVERI'] = 'OUI'

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_FONCTION', 'TAUN1')

    command['NOM_PARA'] = 'INST'
    command['VALE'] = (0.0, 1.0, 1.0, 1.0, 2.0, 1.0, 3.0, 1)

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_FONCTION', 'F_EPS')

    command['NOM_PARA'] = 'SIGM'
    command['PROL_DROITE'] = 'LINEAIRE'
    command['PROL_GAUCHE'] = 'LINEAIRE'
    command['VALE'] = (0.0, 0.0, 1000.0, 10.0)
    command['TITRE'] = 'FONCTION DE TAHERI'

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_NAPPE', 'F_EPSMAX')

    command['NOM_PARA'] = 'X'
    command['PROL_DROITE'] = 'LINEAIRE'
    command['PROL_GAUCHE'] = 'LINEAIRE'
    command['PARA'] = (0.5, 1.0)

    command['NOM_PARA_FONC'] = 'EPSI'

    sequence = command['DEFI_FONCTION']

    factor = sequence.append()
    factor['PROL_DROITE'] = 'LINEAIRE'
    factor['PROL_GAUCHE'] = 'LINEAIRE'
    factor['VALE'] = (0.0, 25.0, 10.0, 525.0)

    factor = sequence.append()
    factor['PROL_DROITE'] = 'LINEAIRE'
    factor['PROL_GAUCHE'] = 'LINEAIRE'
    factor['VALE'] = (0.0, 50.0, 10.0, 550.0)

    command['TITRE'] = 'NAPPE DE TAHERI'

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_FONCTION', 'F_MANSON')

    command['NOM_PARA'] = 'EPSI'
    command['PROL_DROITE'] = 'LINEAIRE'
    command['PROL_GAUCHE'] = 'LINEAIRE'
    command['VALE'] = (0.0, 200000.0, 2.0, 0.0)
    command['TITRE'] = 'FONCTION DE MANSON_COFFIN'

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_FONCTION', 'F_WOHLER')

    command['NOM_PARA'] = 'SIGM'
    command['PROL_DROITE'] = 'LINEAIRE'
    command['PROL_GAUCHE'] = 'LINEAIRE'
    command['VALE'] = (0.0, 200000.0, 200.0, 0.0)
    command['TITRE'] = 'FONCTION DE WOHLER'

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_MATERIAU', 'MAT0')

    factor = command['FATIGUE']
    factor['WOHLER'] = stage['F_WOHLER']
    factor['MANSON_COFFIN'] = stage['F_MANSON']

    #--------------------------------------------------------------------------
    command = stage.add_command('POST_FATIGUE', 'TAB_1')

    command['CHARGEMENT'] = 'UNIAXIAL'
    command['HISTOIRE']['EPSI'] = stage['TAUN1']
    command['COMPTAGE'] = 'RAINFLOW'
    command['DOMMAGE'] = 'TAHERI_MANSON'
    command['TAHERI_FONC'] = stage['F_EPS']
    command['TAHERI_NAPPE'] = stage['F_EPSMAX']
    command['MATER'] = stage['MAT0']
    command['CUMUL'] = 'LINEAIRE'
    command['INFO'] = 2

    #--------------------------------------------------------------------------
    command = stage.add_command('TEST_TABLE')

    command['REFERENCE'] = 'ANALYTIQUE'
    command['VALE_REFE'] = 5.E-06

    command['PRECISION'] = 1.E-05
    command['VALE_CALC'] = 5.E-06
    command['NOM_PARA'] = 'DOMMAGE'
    command['TABLE'] = stage['TAB_1']

    sequence = command['FILTRE']
    sequence['NOM_PARA'] = 'CYCLE'

    sequence['VALE_I'] = 1
    assert('VALE_I' in sequence.rkeys())

    simple = sequence['VALE_I']
    assert(simple.value == 1)

    assert(sequence['VALE_I'] == 1)

    #--------------------------------------------------------------------------
    command = stage.add_command('FIN')

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

TAUN1 = DEFI_FONCTION(NOM_PARA='INST',
                      VALE=(0.0, 1.0, 1.0, 1.0, 2.0, 1.0, 3.0, 1))

F_EPS = DEFI_FONCTION(NOM_PARA='SIGM',
                      PROL_DROITE='LINEAIRE',
                      PROL_GAUCHE='LINEAIRE',
                      TITRE='FONCTION DE TAHERI',
                      VALE=(0.0, 0.0, 1000.0, 10.0))

F_EPSMAX = DEFI_NAPPE(DEFI_FONCTION=(_F(PROL_DROITE='LINEAIRE',
                                        PROL_GAUCHE='LINEAIRE',
                                        VALE=(0.0, 25.0, 10.0, 525.0)),
                                     _F(PROL_DROITE='LINEAIRE',
                                        PROL_GAUCHE='LINEAIRE',
                                        VALE=(0.0, 50.0, 10.0, 550.0))),
                      NOM_PARA='X',
                      NOM_PARA_FONC='EPSI',
                      PARA=(0.5, 1.0),
                      PROL_DROITE='LINEAIRE',
                      PROL_GAUCHE='LINEAIRE',
                      TITRE='NAPPE DE TAHERI')

F_MANSON = DEFI_FONCTION(NOM_PARA='EPSI',
                         PROL_DROITE='LINEAIRE',
                         PROL_GAUCHE='LINEAIRE',
                         TITRE='FONCTION DE MANSON_COFFIN',
                         VALE=(0.0, 200000.0, 2.0, 0.0))

F_WOHLER = DEFI_FONCTION(NOM_PARA='SIGM',
                         PROL_DROITE='LINEAIRE',
                         PROL_GAUCHE='LINEAIRE',
                         TITRE='FONCTION DE WOHLER',
                         VALE=(0.0, 200000.0, 200.0, 0.0))

MAT0 = DEFI_MATERIAU(FATIGUE=_F(MANSON_COFFIN=F_MANSON,
                                WOHLER=F_WOHLER))

TAB_1 = POST_FATIGUE(CHARGEMENT='UNIAXIAL',
                     COMPTAGE='RAINFLOW',
                     CUMUL='LINEAIRE',
                     DOMMAGE='TAHERI_MANSON',
                     HISTOIRE=_F(EPSI=TAUN1),
                     INFO=2,
                     MATER=MAT0,
                     TAHERI_FONC=F_EPS,
                     TAHERI_NAPPE=F_EPSMAX)

TEST_TABLE(FILTRE=_F(NOM_PARA='CYCLE',
                     VALE_I=1),
           NOM_PARA='DOMMAGE',
           PRECISION=1e-05,
           REFERENCE='ANALYTIQUE',
           TABLE=TAB_1,
           VALE_CALC=5e-06,
           VALE_REFE=5e-06)

FIN()
"""
    #--------------------------------------------------------------------------
    import pickle
    blob = pickle.dumps(history)
    history2 = pickle.loads(blob)

    case = history2.current_case
    stage2 = case[':memory:']

    #--------------------------------------------------------------------------
    assert(check_export(stage2, text, sort=False))

    assert(check_import(text))

    assert(check_translation(stage, text))

    #--------------------------------------------------------------------------
    pass


def test_szlz108b():
    """Test for import/export szlz108b"""
    comm = os.path.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'comm2study', 'szlz108b.comm')

    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    with open(comm) as file:
        text = file.read()
    comm2study(text, stage)

    func = stage['F_MANSON']
    mat0 = stage['MAT0']
    model = stage._model
    assert_that(model.has_path(func.uid, mat0.uid))
    assert_that(mat0.depends_on(func))
    assert_that(mat0, greater_than(func))

    # check commands by creation order
    refs = ['TAUN1', 'F_EPS', 'F_EPSMAX', 'F_MANSON', 'F_WOHLER', 'MAT0',
    'TAB_1', 'TAB_2', 'TAB_3', 'TAB_4', 'TAB_5']
    cmds = stage.commands
    names = [i.name for i in cmds if i.name != "_"]
    assert_that(names, contains(*refs))

    # as the text was valid, order could only change because of categories
    cmds = stage.sorted_commands
    _check_order(cmds)

    names = [i.name for i in cmds if i.name != "_"]
    assert_that(names, contains(*refs))

    text2 = study2comm(stage)

    case2 = history.create_case("Case 2")
    stage2 = case2.create_stage(":2:")
    comm2study(text2, stage2)
    assert_that(stage2.check(), equal_to(Validity.Nothing))

def _check_order(commands):
    # names = ["{0.name}:{0.uid}".format(i) for i in commands]
    # print "DEBUG: commands", names
    nbc = len(commands)
    for i in range(nbc):
        for j in range(i + 1, nbc):
            # _debug_cmp(commands[i], commands[j])
            assert_that(commands[i], less_than_or_equal_to(commands[j]))

def _debug_cmp(cmd1, cmd2):
    print("DEBUG: compare", cmd1, cmd1.categ, cmd2, cmd2.categ)

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
