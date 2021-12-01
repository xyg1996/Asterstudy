# coding=utf-8

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

"""Automatic tests for the issue 1648 (Manage naming conflicts)."""


import unittest

import testutils.gui_utils
from asterstudy.datamodel import History, Validity
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.gui import HistoryProxy
from asterstudy.gui.datasettings import (create_data_settings_model,
                                         get_object_info)
from asterstudy.gui.datasettings.model import NameConflictVisitor
from common_test_gui import HistoryHolder
from hamcrest import *

stage1_text = \
"""
DEBUT();

var1 = 1;
var2 = 2;
var1 = 3;

FIN();
"""


# snippet based on contents of "data/comm2study/zzzz289a.comm"
# (with command "CHMAT_L" renamed to "CHMAT_Q")
stage2_text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET',),DEBUG=_F(SDVERI='OUI'))

MAIL_Q=LIRE_MAILLAGE(FORMAT="ASTER",);

MAIL_L=CREA_MAILLAGE(MAILLAGE=MAIL_Q,
                     QUAD_LINE=_F(TOUT='OUI',),);

MATER=DEFI_MATERIAU(ELAS=_F(E=30000.0,
                            NU=0.2,
                            RHO=2764.0,),
                    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                 SY=3.0,),);

CHMAT_Q=AFFE_MATERIAU(MAILLAGE=MAIL_Q,
                      AFFE=_F(TOUT='OUI',
                              MATER=MATER,),);

CHMAT_Q=AFFE_MATERIAU(MAILLAGE=MAIL_L,
                      AFFE=_F(TOUT='OUI',
                              MATER=MATER,),);

MODELUPG=AFFE_MODELE(MAILLAGE=MAIL_Q,
                     AFFE=_F(TOUT='OUI',
                             PHENOMENE='MECANIQUE',
                             MODELISATION='3D_INCO_UPG',),);

MODELUPQ=AFFE_MODELE(MAILLAGE=MAIL_Q,
                     AFFE=_F(TOUT='OUI',
                             PHENOMENE='MECANIQUE',
                             MODELISATION='3D_INCO_UP',),);

MATMUPG=CALC_MATR_ELEM(OPTION='MASS_MECA',
                       MODELE=MODELUPG,
                       CHAM_MATER=CHMAT_Q,);

MATMUPQ=CALC_MATR_ELEM(OPTION='MASS_MECA',
                       MODELE=MODELUPQ,
                       CHAM_MATER=CHMAT_Q,);

FIN();
"""


def test_naming_conflict_visitor():
    """Test for NameConflictVisitor"""
    history = History()
    case = history.current_case

    stage1 = case.create_stage('Stage1')
    comm2study(stage1_text, stage1)

    stage2 = case.create_stage('Stage2')
    comm2study(stage2_text, stage2)

    visitor = NameConflictVisitor()
    stage1.accept(visitor)
    assert_that(visitor.names, equal_to(["var1"]))

    visitor = NameConflictVisitor()
    stage2.accept(visitor)
    assert_that(visitor.names, equal_to(["CHMAT_Q"]))

    visitor = NameConflictVisitor()
    case.accept(visitor)
    assert_that(visitor.names, equal_to(["var1", "CHMAT_Q"]))


def test_naming_conflicts():
    """Test for detection of naming conflicts"""

    history = History()
    case = history.current_case

    stage1 = case.create_stage('Stage1')
    comm2study(stage1_text, stage1)

    stage2 = case.create_stage('Stage2')
    comm2study(stage2_text, stage2)

    cmodel = create_data_settings_model(HistoryHolder(history))
    cmodel.update()

    assert_that(case.check(), equal_to(Validity.Naming))
    assert_that(stage1.check(), equal_to(Validity.Naming))
    assert_that(stage2.check(), equal_to(Validity.Naming))

    invalid_commands = [
        1,  # first "var1" in "Stage1"
        3,  # second "var1" in "Stage1"
        9,  # first "CHMAT_Q" in "Stage2"
        10, # second "CHMAT_Q" in "Stage2"
    ]

    for index, command in enumerate(stage1.commands + stage2.commands):
        expected_validity = Validity.Naming if index in invalid_commands \
            else Validity.Nothing
        assert_that(command.check(), equal_to(expected_validity))

    stage1_expected = "Naming conflict (var1)"
    stage2_expected = "Naming conflict (CHMAT_Q)"
    case_expected = "Naming conflict (var1, CHMAT_Q)"

    assert_that(stage1_expected in get_object_info(stage1), equal_to(True))
    assert_that(stage2_expected in get_object_info(stage2), equal_to(True))
    assert_that(case_expected in get_object_info(case), equal_to(True))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
