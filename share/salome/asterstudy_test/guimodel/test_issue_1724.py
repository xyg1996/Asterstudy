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

"""Automatic tests for the issue 1724 (Force re-check of study validity)."""


import unittest

import testutils.gui_utils
from asterstudy.datamodel import History, Validity
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.gui import HistoryProxy
from asterstudy.gui.datasettings import (create_data_settings_model,
                                         get_object_info)
from common_test_gui import HistoryHolder
from hamcrest import *

# snippet based on contents of "data/export/forma02b.comm"
stage1_text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),DEBUG=_F(SDVERI='OUI'))

MAIL=LIRE_MAILLAGE(FORMAT='MED',);

MODELE=AFFE_MODELE(MAILLAGE=MAIL,
                   AFFE=_F(TOUT='OUI',
                           PHENOMENE='MECANIQUE',
                           MODELISATION='3D',),);

FIN();
"""


# snippet based on contents of "data/export/forma02b.com1"
stage2_text = \
"""
POURSUITE(CODE='OUI');

FYC=AFFE_CHAR_MECA(MODELE=MODELE,
                   FORCE_FACE=_F(GROUP_MA='EFOND',
                                 FY=1.0,),);

FIN();
"""


def test_duplicate_delete():
    """Test for detection of naming conflicts"""

    history = History()
    case = history.current_case

    stage1 = case.create_stage('Stage1')
    comm2study(stage1_text, stage1)

    stage2 = case.create_stage('Stage2')
    comm2study(stage2_text, stage2)

    cmodel = create_data_settings_model(HistoryHolder(history))
    cmodel.update()

    # check that both stages and the command "FYC" are valid
    assert_that(stage1.check(), equal_to(Validity.Nothing))
    assert_that(stage2.check(), equal_to(Validity.Nothing))
    assert_that(stage2["FYC"].check(), equal_to(Validity.Nothing))

    nb_commands_before_duplicate = len(stage1.commands)

    # duplicate the command "MAIL" of the stage "Stage1"
    command = stage1["MAIL"]
    content = str(command)
    duplicated_command = stage1.paste(content)[0]

    # check that new command is added to the "Stage1"
    nb_commands_after_duplicate = len(stage1.commands)
    assert_that(nb_commands_after_duplicate,
                equal_to(nb_commands_before_duplicate + 1))

    # Naming conflict in "Stage1"
    assert_that(stage1.check(), equal_to(Validity.Naming))
    # check that validity of the "Stage2" is still valid
    # it references the first command, not the copy
    assert_that(stage2.check(), equal_to(Validity.Nothing))

    # delete the result of the duplication
    duplicated_command.delete(user_deletion=True)

    # check that the command is removed from the "Stage1"
    nb_commands_after_delete = len(stage1.commands)
    assert_that(nb_commands_after_delete,
                equal_to(nb_commands_after_duplicate - 1))

    # check that validity of the "Stage2" and command "FYC" is still Ok
    assert_that(stage2.check(), equal_to(Validity.Nothing))
    assert_that(stage2["FYC"].check(), equal_to(Validity.Nothing))

    # force re-check of the command "FYC"
    stage2["FYC"].reset_validity()
    assert_that(stage2["FYC"].check(), equal_to(Validity.Nothing))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
