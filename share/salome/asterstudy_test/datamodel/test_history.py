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

"""Implementation of the automatic tests for history."""


import os.path as osp
import unittest
from hamcrest import *

from testutils import attr, tempdir

from asterstudy.common import CatalogError, CFG, StudyDirectoryError

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.case import Case
from asterstudy.datamodel.catalogs import CATA

class TestHistory(unittest.TestCase):
    """Implementation of the automatic tests for history"""

    def setUp(self):
        CATA.read_catalogs()

    def test_create(self):
        """Test for basic creation"""
        history = History()
        self.assertEqual(True, history.current_case != None)
        case = history.current_case
        self.assertEqual(history, case.model)
        self.assertEqual([], case.stages)

        stage = case.create_stage('Stage_1')
        self.assertEqual([stage], case.stages)
        self.assertEqual(history, stage.model)

        cmd = stage('RECU_FONCTION')

        kwd2 = cmd['TABLE']
        self.assertEqual(kwd2, cmd['TABLE'])

        cmd2 = stage('LIRE_TABLE')
        kwd2.value = cmd2
        self.assertEqual(kwd2.value, cmd2)

        self.assertEqual(2, len(stage))
        self.assertEqual(history.has_path(stage.uid, cmd.uid), True)
        self.assertEqual(history.has_path(cmd.uid, cmd2.uid), False)
        self.assertEqual(history.has_path(cmd2.uid, cmd.uid), True)

        history.get_node(cmd2.uid).delete()
        self.assertEqual(1, len(stage))

        hfolder = '/tmp/history_data'
        history.folder = hfolder
        self.assertEqual(history.folder, hfolder)

    def test_command_catalog(self):
        """Test for catalog of the existing command"""
        history = History()
        stage = history.current_case.create_stage('Stage_1')
        cmd = stage.add_command('AFFE_MODELE')
        cata = cmd.cata
        # pragma pylint: disable=no-member
        self.assertEqual(cata.name, 'AFFE_MODELE')
        self.assertEqual(len(cata.rules), 1)
        self.assertIn('AFFE', cata.keywords)
        self.assertEqual(cata.rules[0].__class__.__name__, 'AtLeastOne')
        self.assertEqual(cata.docstring,
                         "Définir le phénomène physique modélisé et le " + \
                         "type d'éléments finis sur le maillage")
        self.assertEqual(cata.udocstring,
                         "Définir le phénomène physique modélisé et le "
                         "type d'éléments finis sur le maillage")

    def test_catalog_new_command(self):
        """Test for catalog of a new command"""
        cata = CATA.get_catalog('AFFE_MODELE')
        self.assertEqual(cata.name, 'AFFE_MODELE')
        self.assertEqual(len(cata.rules), 1)
        self.assertIn('AFFE', cata.keywords)
        self.assertEqual(cata.rules[0].__class__.__name__, 'AtLeastOne')
        self.assertEqual(cata.docstring,
                         "Définir le phénomène physique modélisé et le " + \
                         "type d'éléments finis sur le maillage")
        self.assertEqual(cata.udocstring,
                         "Définir le phénomène physique modélisé et le "
                         "type d'éléments finis sur le maillage")

    def test_stage_get_commands(self):
        """Test for the method getCommands of the stage"""
        history = History()
        stage = history.current_case.create_stage('Stage_1')
        cmd = stage.add_command('DEFI_MATERIAU')
        self.assertEqual([cmd], stage.commands)

    def test_command_get_parameters(self):
        """Test for the method getParameters of the command"""
        history = History()
        stage = history.current_case.create_stage('Stage_1')
        cmd = stage.add_command('DEFI_MATERIAU')

        param1 = cmd['ELAS']
        self.assertIn('ELAS', cmd.keys())

        param2 = cmd['ELAS_FO']
        self.assertIn('ELAS_FO', cmd.keys())
        self.assertIn('ELAS', cmd.keys())


def test_history_call():
    """Test for __call__ method of History"""
    history = History()

    case = history.current_case
    assert_that(history(case.uid), equal_to(case))

def test_compare():
    """Test for histories comparison"""
    history = History()

    history2 = History()
    history2.create_case('XXX')
    assert_that(calling(history.__mul__).with_args(history2), raises(AssertionError))

    history3 = History()
    history3.current_case.create_stage()
    assert_that(calling(history.__mul__).with_args(history3), raises(AssertionError))

    history4 = History()
    history4.current_case.create_stage()
    history4.create_case('XXX')
    assert_that(calling(history4.__mul__).with_args(history2), raises(AssertionError))

def test_cases():
    """Test for cases management"""
    history = History()
    case1 = history.current_case
    assert_that(history.nb_cases, equal_to(1))
    assert_that(history.cases, equal_to([case1]))
    assert_that(history.run_cases, equal_to([]))
    assert_that(history.current_case.name, equal_to("CurrentCase"))
    case2 = history.create_case()
    assert_that(history.nb_cases, equal_to(2))
    assert_that(history.cases, equal_to([case1, case2]))
    assert_that(history.run_cases, equal_to([case1]))
    assert_that(history.current_case, equal_to(case2))
    assert_that(history.current_case.name, equal_to("Case_1"))
    case3 = history.create_case("aaa", True)
    assert_that(history.nb_cases, equal_to(2))
    assert_that(history.cases, equal_to([case1, case3]))
    assert_that(history.run_cases, equal_to([case1]))
    assert_that(history.current_case, equal_to(case3))
    assert_that(history.current_case.name, equal_to("CurrentCase"))
    case4 = Case("bbb")
    history.add_case(case4)
    assert_that(history.nb_cases, equal_to(3))
    assert_that(history.cases, equal_to([case1, case3, case4]))
    assert_that(history.run_cases, equal_to([case1, case3]))
    assert_that(history.current_case, equal_to(case4))
    assert_that(history.current_case.name, equal_to("bbb"))
    case5 = Case("ccc")
    history.insert_case(case5, True)
    assert_that(history.nb_cases, equal_to(3))
    assert_that(history.cases, equal_to([case1, case3, case5]))
    assert_that(history.run_cases, equal_to([case1, case3]))
    assert_that(history.current_case, equal_to(case5))
    assert_that(history.current_case.name, equal_to("ccc"))
    case6 = Case("ddd")
    history.insert_case(case6, index=0)
    assert_that(history.nb_cases, equal_to(4))
    assert_that(history.cases, equal_to([case6, case1, case3, case5]))
    assert_that(history.run_cases, equal_to([case6, case1, case3]))
    assert_that(history.current_case, equal_to(case5))
    assert_that(history.current_case.name, equal_to("ccc"))
    case7 = Case("eee")
    history.insert_case(case7, replace=True, index=1)
    assert_that(history.nb_cases, equal_to(4))
    assert_that(history.cases, equal_to([case6, case7, case3, case5]))
    assert_that(history.run_cases, equal_to([case6, case7, case3]))
    assert_that(history.current_case, equal_to(case5))
    assert_that(history.current_case.name, equal_to("ccc"))

    # copy now preserves the current case
    case8 = history.current_case.copy("fff")
    assert_that(history.nb_cases, equal_to(5))
    assert_that(history.cases, equal_to([case6, case7, case3, case8, case5]))
    assert_that(history.run_cases, equal_to([case6, case7, case3, case8]))
    assert_that(history.current_case, equal_to(case5))
    assert_that(history.current_case.name, equal_to("ccc"))

def test_replace_current_case():
    """Test for current case replacement"""
    history = History()
    history.current_case.create_stage()
    assert_that(history.nb_cases, equal_to(1))
    history.create_case(replace=True)
    assert_that(history.nb_cases, equal_to(1))
    history.create_case(replace=False)
    assert_that(history.nb_cases, equal_to(2))

@tempdir
def test_folders(tempdir):
    history = History()
    case = history.current_case
    stage = case.create_stage('ss')

    remote_name = 'REMOTE'

    assert_that(history.folder, none())
    assert_that(history.remote_folder, equal_to(''))
    assert_that(case.folder, equal_to(''))
    assert_that(case.remote_folder, equal_to(''))
    assert_that(stage.folder, equal_to('Result-' + stage.name))
    assert_that(stage.remote_folder, equal_to('Result-' + stage.name))

    stage.set_remote(remote_name)
    assert_that(history.remote_folder, equal_to(''))

    history.folder = tempdir
    assert_that(history.folder, equal_to(tempdir))
    assert_that(history.remote_folder, equal_to(osp.join(remote_name, osp.basename(tempdir))))
    assert_that(case.folder, equal_to(osp.join(tempdir, case.name)))
    assert_that(case.remote_folder, equal_to(osp.join(remote_name, osp.basename(tempdir), case.name)))
    assert_that(stage.folder, equal_to(osp.join(tempdir, case.name, 'Result-' + stage.name)))
    assert_that(stage.remote_folder, equal_to(osp.join(remote_name, osp.basename(tempdir), case.name, 'Result-' + stage.name)))

    assert_that(calling(stage.set_remote).with_args('XXX'), raises(StudyDirectoryError))

    stage.set_remote(None) # does nothing
    assert_that(history.folder, equal_to(tempdir))
    assert_that(history.remote_folder, equal_to(osp.join(remote_name, osp.basename(tempdir))))
    assert_that(case.folder, equal_to(osp.join(tempdir, case.name)))
    assert_that(case.remote_folder, equal_to(osp.join(remote_name, osp.basename(tempdir), case.name)))
    assert_that(stage.folder, equal_to(osp.join(tempdir, case.name, 'Result-' + stage.name)))
    assert_that(stage.remote_folder, equal_to(osp.join(remote_name, osp.basename(tempdir), case.name, 'Result-' + stage.name)))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
