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

"""Automatic tests for commands."""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.command import Comment
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from testutils.tools import check_export


#------------------------------------------------------------------------------
def test_activate_and_deactivate_command():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)

MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)

MATER = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                   SY=3.0),
                      ELAS=_F(E=30000.0,
                              NU=0.2,
                              RHO=2764.0))

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER,
                                TOUT='OUI'),
                        MAILLAGE=MAIL_Q)

MATMUPG = CALC_MATR_ELEM(CHAM_MATER=CHMAT_Q,
                         MODELE=MODELUPG,
                         OPTION='MASS_MECA')
"""
    comm2study(text, stage)
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(stage["MAIL_Q"].active, equal_to(True))

    #------------------------------------------------------------------------------
    stage["MAIL_Q"].active = False
    assert_that(stage["MAIL_Q"].check(), equal_to(Validity.Ok))
    assert_that(stage["MODELUPG"].check(), equal_to(Validity.Dependency))
    assert_that(stage["MATMUPG"].check(), equal_to(Validity.Dependency))

    stage["MAIL_Q"].active = True
    assert_that(stage["MAIL_Q"].check(), equal_to(Validity.Ok))
    assert_that(stage["MODELUPG"].check(), equal_to(Validity.Ok))
    assert_that(stage["MATMUPG"].check(), equal_to(Validity.Ok))

    #------------------------------------------------------------------------------
    stage["MATER"].active = False
    assert_that(stage["MATER"].check(), equal_to(Validity.Ok))
    assert_that(stage["CHMAT_Q"].check(), equal_to(Validity.Dependency))
    assert_that(stage["MATMUPG"].check(), equal_to(Validity.Dependency))

    stage["MATER"].active = True
    assert_that(stage["MATER"].check(), equal_to(Validity.Ok))
    assert_that(stage["CHMAT_Q"].check(), equal_to(Validity.Ok))
    assert_that(stage["MATMUPG"].check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_import_deactivated_command():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
#comment: MAIL_Q = LIRE_MAILLAGE(UNITE=22)

_DISABLE_COMMANDS(globals())
MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
_ENABLE_COMMANDS(globals())
"""
    comm2study(text, stage)
    assert_that(stage["MAIL_Q"].active, equal_to(False))
    assert_that(stage["MODELUPG"].active, equal_to(False))
    assert_that(stage["MODELUPG"].check(), equal_to(Validity.Ok))
    assert_that(stage, has_length(2))

    #------------------------------------------------------------------------------
    stage["MODELUPG"].active = True
    assert_that(stage["MODELUPG"].check(), equal_to(Validity.Dependency))

    #------------------------------------------------------------------------------
    stage["MAIL_Q"].active = True
    assert_that(stage["MODELUPG"].check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_export_deactivated_command():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)

MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text, stage)
    assert_that(stage["MAIL_Q"].active, equal_to(True))
    assert_that(stage["MODELUPG"].active, equal_to(True))

    #------------------------------------------------------------------------------
    stage["MODELUPG"].active = False

    text2 = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)

#comment: MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
#comment:                                PHENOMENE='MECANIQUE',
#comment:                                TOUT='OUI'),
#comment:                        MAILLAGE=MAIL_Q)
"""
    assert(check_export(stage, text2, validity=False, sort=False))

    #------------------------------------------------------------------------------
    stage["MAIL_Q"].active = False

    text3 = \
"""
#comment: MAIL_Q = LIRE_MAILLAGE(UNITE=22)

#comment: MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
#comment:                                PHENOMENE='MECANIQUE',
#comment:                                TOUT='OUI'),
#comment:                        MAILLAGE=MAIL_Q)
"""
    assert(check_export(stage, text3, validity=False, sort=False))

    #------------------------------------------------------------------------------
    stage["MODELUPG"].active = True

    text4 = \
"""
#comment: MAIL_Q = LIRE_MAILLAGE(UNITE=22)

MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    assert(check_export(stage, text4, validity=False, sort=False))

#------------------------------------------------------------------------------
def test_command_comment():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
# comment
#comment: MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text, stage)

    #------------------------------------------------------------------------------
    comment = stage[0]
    assert_that(isinstance(comment, Comment), equal_to(True))

    #------------------------------------------------------------------------------
    command = stage["MAIL_Q"]
    assert_that(comment.active, equal_to(False))
    assert_that(command.active, equal_to(False))
    assert_that(command.comment.active, equal_to(False))

    #------------------------------------------------------------------------------
    command.active = True
    assert_that(comment.active, equal_to(True))
    assert_that(command.active, equal_to(True))
    assert_that(command.comment.active, equal_to(True))

    #------------------------------------------------------------------------------
    command.active = False
    assert(check_export(stage, text, validity=False, sort=False))

#------------------------------------------------------------------------------
def test_variable():
    history = History()
    case = history.current_case

   #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
_DISABLE_COMMANDS(globals())
a = 2
b = a * 3
_ENABLE_COMMANDS(globals())
"""
    comm2study(text, stage)
    assert_that(stage["a"].active, equal_to(False))
    assert_that(stage["b"].active, equal_to(False))

    text1 = \
"""
#comment: a = 2

#comment: b = a * 3
"""
    assert(check_export(stage, text1, validity=False, sort=False))

    #------------------------------------------------------------------------------
    stage["b"].active = True
    assert_that(stage["a"].check(), equal_to(Validity.Ok))
    assert_that(stage["b"].check(), equal_to(Validity.Dependency))

    text2 = \
"""
#comment: a = 2

b = a * 3
"""
    assert(check_export(stage, text2, validity=False, sort=False))

    #------------------------------------------------------------------------------
    stage["a"].active = True
    assert_that(stage["a"].check(), equal_to(Validity.Ok))
    assert_that(stage["b"].check(), equal_to(Validity.Ok))

    text3 = \
"""
a = 2

b = a * 3
"""
    assert(check_export(stage, text3, validity=False, sort=False))

#------------------------------------------------------------------------------
def test_naming_conficts():
    history = History()
    case = history.current_case

   #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
_DISABLE_COMMANDS(globals())
a = 2
a = a * 3
_ENABLE_COMMANDS(globals())
"""
    comm2study(text, stage)
    assert_that(stage[0].check(), equal_to(Validity.Ok))
    assert_that(stage[1].check(), equal_to(Validity.Ok))
    assert_that(stage.check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_syntaxic_errors():
    history = History()
    case = history.current_case

   #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    stage.add_command('ASSE_MAILLAGE', 'MAIL_Q')

    assert_that(stage["MAIL_Q"].active, equal_to(True))
    assert_that(stage['MAIL_Q'].check(), equal_to(Validity.Syntaxic))

    stage["MAIL_Q"].active = False
    assert_that(stage['MAIL_Q'].check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_issue_1792():
    history = History()
    case = history.current_case

   #------------------------------------------------------------------------------
    stage = case.create_stage('forma01a')
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

MAIL = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

MAIL = MODI_MAILLAGE(reuse=MAIL,
                     MAILLAGE=MAIL,
                     ORIE_PEAU_2D=_F(GROUP_MA='haut'))

MODE = AFFE_MODELE(AFFE=_F(MODELISATION='C_PLAN',
                           PHENOMENE='MECANIQUE',
                           TOUT='OUI'),
                   MAILLAGE=MAIL)

MA = DEFI_MATERIAU(ELAS=_F(E=200000.0,
                           NU=0.3))

MATE = AFFE_MATERIAU(AFFE=_F(MATER=MA,
                             TOUT='OUI'),
                     MAILLAGE=MAIL)

CHAR = AFFE_CHAR_MECA(DDL_IMPO=(_F(DY=0.0,
                                   GROUP_MA='bas'),
                                _F(DX=0.0,
                                   GROUP_MA='gauche')),
                      MODELE=MODE,
                      PRES_REP=_F(GROUP_MA='haut',
                                  PRES=-100.0))

RESU = MECA_STATIQUE(CHAM_MATER=MATE,
                     EXCIT=_F(CHARGE=CHAR),
                     MODELE=MODE)

RESU = CALC_CHAMP(reuse=RESU,
                  CONTRAINTE='SIGM_ELNO',
                  CRITERES=('SIEQ_ELNO', 'SIEQ_ELGA'),
                  RESULTAT=RESU)

RESU = CALC_CHAMP(reuse=RESU,
                  CONTRAINTE='SIGM_NOEU',
                  CRITERES='SIEQ_NOEU',
                  RESULTAT=RESU)

IMPR_RESU(FORMAT='MED',
          RESU=_F(MAILLAGE=MAIL,
                  NOM_CHAM=('DEPL', 'SIGM_NOEU', 'SIEQ_NOEU', 'SIEQ_ELGA'),
                  RESULTAT=RESU),
          UNITE=80)
"""
    comm2study(text, stage)

    #------------------------------------------------------------------------------
    assert_that(stage.handle2info, has_length(2))

    assert_that(20, is_in(stage.handle2info))
    stage.handle2info[20].filename = '20'

    assert_that(80, is_in(stage.handle2info))
    stage.handle2info[80].filename = '80'

    assert_that(stage.check(), equal_to(Validity.Ok))

    #------------------------------------------------------------------------------
    stage.use_text_mode()
    assert_that(stage.is_text_mode(), equal_to(True))
    assert_that(stage.handle2info[80].filename, equal_to('80'))

    stage.use_graphical_mode()
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage.handle2info[80].filename, equal_to('80'))

    #------------------------------------------------------------------------------
    stage[-2].active = False
    assert_that(stage.check(), equal_to(Validity.Dependency))

    RESU = stage[-3]
    stage[-1].init({'RESU': {'RESULTAT': RESU}, 'UNITE': {80: '80'}, 'FORMAT': u'MED'})
    assert_that(stage.check(), equal_to(Validity.Ok))

    #------------------------------------------------------------------------------
    stage.use_text_mode()
    assert_that(stage.is_text_mode(), equal_to(True))
    assert_that(stage.handle2info[80].filename, equal_to('80'))

    stage.use_graphical_mode()
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage.handle2info[80].filename, equal_to('80'))

#------------------------------------------------------------------------------
def test_datafiles():
    history = History()
    case = history.current_case

   #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text, stage)
    assert_that(stage.handle2info, has_length(1))

   #------------------------------------------------------------------------------
    stage["MAIL_Q"].active = False
    assert_that(stage.handle2info, has_length(0))

   #------------------------------------------------------------------------------
    stage["MAIL_Q"].active = True
    assert_that(stage.handle2info, has_length(1))

#------------------------------------------------------------------------------
def test_macro():
    history = History()
    case = history.current_case

   #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
MAIL = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

MODELE = AFFE_MODELE(AFFE=_F(MODELISATION='3D',
                             PHENOMENE='MECANIQUE',
                             TOUT='OUI'),
                     MAILLAGE=MAIL)

MAT = DEFI_MATERIAU(ELAS=_F(E=2.04e+11,
                            NU=0.3,
                            RHO=7800.0))

CHMAT = AFFE_MATERIAU(AFFE=_F(MATER=MAT,
                              TOUT='OUI'),
                      MAILLAGE=MAIL)

BLOCAGE = AFFE_CHAR_MECA(DDL_IMPO=_F(DX=0.0,
                                     DY=0.0,
                                     DZ=0.0,
                                     GROUP_MA='BASE'),
                         MODELE=MODELE)

ASSEMBLAGE(CHAM_MATER=CHMAT,
           CHARGE=BLOCAGE,
           MATR_ASSE=(_F(MATRICE=CO('RIGIDITE'),
                         OPTION='RIGI_MECA'),
                      _F(MATRICE=CO('MASSE'),
                         OPTION='MASS_MECA')),
           MODELE=MODELE,
           NUME_DDL=CO('NUMEDDL'))

MODES = CALC_MODES(CALC_FREQ=_F(NMAX_FREQ=10),
                   MATR_MASS=MASSE,
                   MATR_RIGI=RIGIDITE,
                   OPTION='PLUS_PETITE')
"""
    comm2study(text, stage)

   #------------------------------------------------------------------------------
    macro = stage[5]
    assert_that(macro.title, equal_to("ASSEMBLAGE"))
    assert_that('RIGIDITE', is_in(stage))
    assert_that('MASSE', is_in(stage))

    assert_that(stage['MODES'].check(), equal_to(Validity.Ok))

   #------------------------------------------------------------------------------
    macro.active = False
    assert_that(stage["MASSE"].active, equal_to(False))
    assert_that(stage["RIGIDITE"].active, equal_to(False))
    assert_that(stage['MODES'].check(), equal_to(Validity.Dependency))

   #------------------------------------------------------------------------------
    text2 = \
"""
MAIL = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

MODELE = AFFE_MODELE(AFFE=_F(MODELISATION='3D',
                             PHENOMENE='MECANIQUE',
                             TOUT='OUI'),
                     MAILLAGE=MAIL)

MAT = DEFI_MATERIAU(ELAS=_F(E=204000000000.0,
                            NU=0.3,
                            RHO=7800.0))

CHMAT = AFFE_MATERIAU(AFFE=_F(MATER=MAT,
                              TOUT='OUI'),
                      MAILLAGE=MAIL)

BLOCAGE = AFFE_CHAR_MECA(DDL_IMPO=_F(DX=0.0,
                                     DY=0.0,
                                     DZ=0.0,
                                     GROUP_MA='BASE'),
                         MODELE=MODELE)

#comment: ASSEMBLAGE(CHAM_MATER=CHMAT,
#comment:            CHARGE=BLOCAGE,
#comment:            MATR_ASSE=(_F(MATRICE=CO('RIGIDITE'),
#comment:                          OPTION='RIGI_MECA'),
#comment:                       _F(MATRICE=CO('MASSE'),
#comment:                          OPTION='MASS_MECA')),
#comment:            MODELE=MODELE,
#comment:            NUME_DDL=CO('NUMEDDL'))

MODES = CALC_MODES(CALC_FREQ=_F(NMAX_FREQ=10),
                   MATR_MASS=MASSE,
                   MATR_RIGI=RIGIDITE,
                   OPTION='PLUS_PETITE')
"""
    assert(check_export(stage, text2, validity=False, sort=False))

   #------------------------------------------------------------------------------
    macro.active = True
    assert_that(stage["MASSE"].active, equal_to(True))
    assert_that(stage["RIGIDITE"].active, equal_to(True))
    assert_that(stage['MODES'].check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_groupby():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)

MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text, stage)
    assert_that(stage["MAIL_Q"].active, equal_to(True))
    assert_that(stage["MAIL_Q"].check(), equal_to(Validity.Ok))
    assert_that(stage["MODELUPG"].check(), equal_to(Validity.Ok))

    astype = stage['MAIL_Q'].gettype()
    assert_that(stage['MAIL_Q'], is_in(stage["MODELUPG"].groupby(astype)))

    #------------------------------------------------------------------------------
    stage["MAIL_Q"].active = False
    assert_that(stage["MAIL_Q"].check(), equal_to(Validity.Ok))
    assert_that(stage["MODELUPG"].check(), equal_to(Validity.Dependency))

    assert_that(stage['MAIL_Q'], is_not(is_in(stage["MODELUPG"].groupby(astype))))

#------------------------------------------------------------------------------
def test_run():
    history = History()
    cc = history.current_case

    #------------------------------------------------------------------------------
    stage = cc.create_stage()
    stage('LIRE_MAILLAGE', 'm').init({'UNITE':20}).active = False
    assert_that(cc[0]['m'].active, equal_to(False))

    #------------------------------------------------------------------------------
    rc1 = history.create_run_case().run()
    assert_that(cc[0]['m'].active, equal_to(False))
    assert_that(rc1[0]['m'].active, equal_to(False))

    #------------------------------------------------------------------------------
    rc2 = history.create_run_case().run()
    assert_that(cc[0]['m'].active, equal_to(False))
    assert_that(rc1[0]['m'].active, equal_to(False))
    assert_that(rc2[0]['m'].active, equal_to(False))

#------------------------------------------------------------------------------
def test_reload_comment():
    history = History()
    case = history.current_case

    stage = case.create_stage('1')
    text = \
"""
mesh = LIRE_MAILLAGE()

#comment: mesh = MODI_MAILLAGE(MAILLAGE=mesh, ECHELLE=1.)

model = AFFE_MODELE(AFFE=_F(MODELISATION='3D',
                            PHENOMENE='MECANIQUE',
                            TOUT='OUI'),
                    MAILLAGE=mesh)
"""
    comm2study(text, stage)
    assert_that(stage.commands, has_length(3))
    mesh, modi, model = stage.commands

    assert_that(mesh.check(), equal_to(Validity.Ok))
    assert_that(modi.check(), equal_to(Validity.Ok))
    assert_that(model.check(), equal_to(Validity.Ok))
    assert_that(stage.check(), equal_to(Validity.Ok))

    assert_that(modi.depends_on(mesh), equal_to(True))
    assert_that(model.depends_on(mesh), equal_to(True))
    assert_that(model.depends_on(modi), equal_to(False))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
