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

"""Automatic tests for the issue 1672 (Show validity report for stage)."""


import unittest

from PyQt5 import Qt as Q

import testutils.gui_utils
from asterstudy.datamodel import History, Validity
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.gui import HistoryProxy, Role
from asterstudy.gui.datasettings import create_data_settings_model
from asterstudy.gui.validityreport import ValidityReportDialog
from common_test_gui import HistoryHolder, get_application
from hamcrest import *


# (with command "CHMAT_L" renamed to "CHMAT_Q" and intentional
# misprint in definition of "MODELUPG")
stage_text = \
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

MODELUPG=AFFE_MODELE(X=MAIL_Q,
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

def setup():
    """required to create widgets"""
    get_application()

def test_naming_conflicts():
    """Test for validity report dialog"""

    class MockStudy:
        def __init__(self, h):
            self.history = h

    class MockGui:
        def __init__(self, h):
            self._study = MockStudy(h)
        def study(self):
            return self._study

    history = History()
    gui = MockGui(history)
    case = history.current_case

    stage = case.create_stage('Stage')
    comm2study(stage_text, stage)

    cmodel = create_data_settings_model(HistoryHolder(history))
    cmodel.update()

    dialog = ValidityReportDialog(gui, stage)

    table = dialog._table

    rowCount = table.rowCount()
    columnCount = table.columnCount()

    assert_that(rowCount, equal_to(11))
    assert_that(columnCount, equal_to(5))

    invalid_commands = {
        3: ("MODELUPG", [1]),   # Syntax problem
        6: ("CHMAT_Q", [3]),    # Naming conflict
        7: ("CHMAT_Q", [3]),    # Naming conflict
        8: ("MATMUPG", [1]),    # Syntax problem
    }

    for row in range(rowCount):
        assert_that(table.isRowHidden(row), equal_to(False))

        expected_error_columns = []
        if row in invalid_commands:
            command_name = table.item(row, 0).text()
            command_name_expected = invalid_commands[row][0]
            assert_that(command_name_expected in command_name, equal_to(True))

            expected_error_columns = invalid_commands[row][1]

        for column in range(0, columnCount):
            validity = table.item(row, column).data(Role.ValidityRole)
            is_error = validity is not None and not table.item(row, column).data(Role.ValidityRole)
            is_error_expected = column in expected_error_columns
            assert_that(is_error, equal_to(is_error_expected))

    dialog.showValidCommands(False)

    for row in range(rowCount):
        if row in invalid_commands:
            assert_that(table.isRowHidden(row), equal_to(False))
        else:
            assert_that(table.isRowHidden(row), equal_to(True))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
