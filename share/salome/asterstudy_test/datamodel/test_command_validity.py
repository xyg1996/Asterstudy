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

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History

from asterstudy.datamodel.comm2study import comm2study


#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q)

MODELUPG = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPQ = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPL = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UP', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MATMUPG = CALC_MATR_ELEM(
    CHAM_MATER=CHMAT_Q, MODELE=MODELUPG, OPTION='MASS_MECA'
)

FIN()
"""
    comm2study(text, stage)

    assert_that(stage, has_length(9))

    #--------------------------------------------------------------------------
    command = stage['CHMAT_Q']
    assert_that(command.check(), equal_to(Validity.Nothing))

    storage = command.storage

    command.init({})
    assert_that(command.check(), equal_to(Validity.Syntaxic))

    command.init(storage)
    assert_that(command.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    pass


def test_repair():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q)
"""
    comm2study(text, stage)

    stage.use_text_mode()
    # does nothing in text mode
    assert_that(case.repair(), equal_to(Validity.Nothing))

    stage.use_graphical_mode()
    del stage['MAIL_Q']

    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    # create the "same" command (same names and returned types)
    newmesh = stage('LIRE_MAILLAGE', 'MAIL_Q')

    # the dependencies must be broken
    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    # will be repaired using newmesh
    assert_that(case.repair(), equal_to(Validity.Nothing))


def test_repair_detr():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q)
"""
    comm2study(text, stage)

    stage.use_text_mode()
    # does nothing in text mode
    assert_that(case.repair(), equal_to(Validity.Nothing))

    stage.use_graphical_mode()
    del stage['MAIL_Q']

    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    # create the "same" command (same names and returned types)
    newmesh = stage('LIRE_MAILLAGE', 'MAIL_Q')

    # the dependencies must be broken
    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    detr = stage('DETRUIRE')
    assert_that(detr.check(), equal_to(Validity.Syntaxic))
    assert_that(case.repair(), equal_to(Validity.Syntaxic))

    detr["CONCEPT"]["NOM"] = newmesh
    assert_that(detr.check(), equal_to(Validity.Nothing))

    # can not be repair using newmesh because it is removed
    # FIXME but currently DETRUIRE is added after the other commands...
    assert_that(case.repair(), equal_to(Validity.Nothing))


def test_validity_with_detruire():
    """Test for validity with DETRUIRE command"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
mesh = LIRE_MAILLAGE()

mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_2D=_F(GROUP_MA='groupname')
)

DETRUIRE(CONCEPT=_F(NOM=mesh))

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""
    comm2study(text, stage)

    assert_that(stage['model'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))


def test_validity_with_detruire2():
    """Test for validity with DETRUIRE command (2)"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    cmd = stage.add_command('DETRUIRE')
    assert_that(cmd.check(), equal_to(Validity.Syntaxic))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))


def test_validity_with_detruire3():
    """Test for validity with DETRUIRE command (3)"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
mesh = LIRE_MAILLAGE()

DETRUIRE(CONCEPT=_F(NOM=mesh))

mesh = LIRE_MAILLAGE()
"""
    comm2study(text, stage)

    assert_that(stage.check(), equal_to(Validity.Nothing))


def test_validity_with_detruire4():
    """Test for validity with DETRUIRE command (4)"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
mesh = LIRE_MAILLAGE()

mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_2D=_F(GROUP_MA='groupname')
)

DETRUIRE(OBJET=())

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""
    comm2study(text, stage)

    assert_that(stage.check(), equal_to(Validity.Nothing))


def test_26506():
    """Test for DEFI_FONCTION/ABSCISSE"""
    # issue26506 / ticket1280
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    cmd = stage.add_command('DEFI_FONCTION')
    cmd.init({'NOM_PARA':'INST', 'VALE':(0, 20, 10, 70)})
    cmd.init({'NOM_PARA':'INST', 'ABSCISSE':(0, 10), 'ORDONNEE':(20, 70)})


def test_26764():
    """Test for rules under conditional blocks"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    text = \
"""
MA = LIRE_MAILLAGE(FORMAT='MED', UNITE=20)

MO = AFFE_MODELE(
    AFFE=_F(MODELISATION='DKT', PHENOMENE='MECANIQUE', TOUT='OUI'), MAILLAGE=MA
)

bet = DEFI_MATERIAU(ELAS=_F(E=35000000000.0, NU=0.2, RHO=2500.0))

MAT = AFFE_MATERIAU(AFFE=_F(MATER=bet, TOUT='OUI'), MODELE=MO)

CL = AFFE_CHAR_MECA(
    DDL_IMPO=_F(DX=0.0, DY=0.0, DZ=0.0, GROUP_MA='fix'), MODELE=MO
)

resu = MECA_STATIQUE(
    CHAM_MATER=MAT,
    EXCIT=(_F(CHARGE=CL)),
    INST=0.0,
    MODELE=MO
)

fer = CREA_CHAMP(
    NOM_CHAM='FERRAILLAGE',
    OPERATION='EXTR',
    RESULTAT=resu,
    TYPE_CHAM='ELEM_FER2_R'
)

ferNeut = CREA_CHAMP(
    ASSE=_F(
        CHAM_GD=fer,
        NOM_CMP=('DNSXI', 'DNSYI', 'DNSXS', 'DNSYS'),
        NOM_CMP_RESU=('X1', 'X2', 'X3', 'X4'),
        TOUT='OUI'
    ),
    OPERATION='ASSE',
    TYPE_CHAM='ELEM_NEUT_R'
)
"""
    comm2study(text, stage)

    assert_that(stage['fer'].check(), equal_to(Validity.Nothing))
    assert_that(calling(stage['ferNeut'].check).with_args(safe=False),
                raises(ValueError, "Exactly.*MAILLAGE.*MODELE"))
    assert_that(stage['ferNeut'].check(), equal_to(Validity.Syntaxic))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))

    stage['ferNeut']['MAILLAGE'] = stage['MA']
    assert_that(stage['ferNeut']._check_validity, equal_to(True))
    assert_that(stage['ferNeut'].check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))


def test_rules():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    form = stage('FORMULE')
    form['NOM_PARA'] = 'INST'
    assert_that(calling(form.check).with_args(safe=False),
                raises(ValueError, "Exactly one.*VALE.*VALE_C"))
    assert_that(form.check(), equal_to(Validity.Syntaxic))


def test_27007():
    """Test for DETRUIRE"""
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

DETRUIRE(CONCEPT=_F(NOM=(mesh, )))

mesh = LIRE_MAILLAGE(UNITE=20)

DETRUIRE(CONCEPT=_F(NOM=(mesh, )))

mesh = LIRE_MAILLAGE(UNITE=20)

DETRUIRE(CONCEPT=_F(NOM=(mesh, )))
"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm2study(text, stage)

    cmds = [i.title for i in stage.sorted_commands]
    assert_that(cmds, contains('LIRE_MAILLAGE', 'DETRUIRE',
                               'LIRE_MAILLAGE', 'DETRUIRE',
                               'LIRE_MAILLAGE', 'DETRUIRE'))


def test_28054():
#tab = POST_ELEM(TRAV_EXT=_F())
    text = \
"""
res = MACR_ELEM_STAT(RIGI_MECA=_F())
"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm2study(text, stage)

    cmd = stage.sorted_commands[0]
    assert_that(cmd.check(), equal_to(Validity.Nothing))
    assert_that(cmd.title, equal_to('MACR_ELEM_STAT'))
    assert_that(cmd.storage, contains('RIGI_MECA'))
    assert_that(cmd.storage['RIGI_MECA'], empty())

    cmd.init({'RIGI_MECA': {}})
    assert_that(cmd.check(), equal_to(Validity.Nothing))
    assert_that(cmd.check(safe=False), equal_to(Validity.Nothing))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
