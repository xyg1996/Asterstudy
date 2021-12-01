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

"""Automatic tests for category model."""


import unittest

import testutils.gui_utils
from asterstudy.datamodel.case import Case
from asterstudy.datamodel.catalogs import CATA
from asterstudy.datamodel.history import History
from asterstudy.gui import HistoryProxy, Role
from asterstudy.gui.behavior import behavior
from asterstudy.gui.datasettings import create_data_settings_model
from common_test_gui import HistoryHolder


class HistoryCaseHolder(HistoryProxy):
    """History adapter with Case as a root node."""

    def __init__(self, history):
        self._history = history

    @property
    def root(self):
        return self._history.current_case

    @property
    def case(self):
        return self._history.current_case

class HistoryStageHolder(HistoryProxy):
    """History adapter with Stage as a root node."""

    def __init__(self, history):
        self._history = history

    @property
    def root(self):
        return self._history.current_case.stages[0]

    @property
    def case(self):
        return None

class TestCategoryModel(unittest.TestCase):
    """Implementation of the automatic tests for category model."""

    def setUp(self):
        behavior().show_categories = True

    def check_categories_grouping(self, *args):
        """Helper function to check default categories order."""

        history = History()
        stage = history.current_case.create_stage('Stage')

        categories = {}
        for cmd in args:
            idx = CATA.get_category_index(cmd)
            if idx not in categories:
                categories[idx] = []
            categories[idx].append(stage.add_command(cmd))
        keys = sorted(categories.keys())

        cmodel = create_data_settings_model(HistoryCaseHolder(history))
        cmodel.update()

        children = cmodel.get_stage_children(stage)
        self.assertEqual(len(categories), len(children))

        for i, child in enumerate(children):
            ids = [cmd.uid for cmd in categories[keys[i]]]
            self.assertEqual(child._id, -i - 1)
            self.assertEqual(child._name, CATA.get_categories()[keys[i]])
            self.assertEqual(child._children, ids)

    def test_categories_grouping(self):
        """Test for default categories order"""

        # Here there are two commands in category 1 and one command in
        # category 2; category 1 precedes category 2; there are no
        # dependencies between commands.
        # In the data tree category 1 should always go before category
        # not dependening on the order in which commands are added to
        # the stage.

        # case 1: categories - 1, 1, 2
        self.check_categories_grouping("RECU_FONCTION",
                                       "RECU_FONCTION",
                                       "POST_COQUE")
        # case 2: categories - 1, 2, 1
        self.check_categories_grouping("RECU_FONCTION",
                                       "POST_COQUE",
                                       "RECU_FONCTION")
        # case 2: categories - 2, 1, 1
        self.check_categories_grouping("POST_COQUE",
                                       "RECU_FONCTION",
                                       "RECU_FONCTION")

    def check_categories_dependencies(self, case):
        """Helper function to check categories dependencies."""

        history = History()
        stage = history.current_case.create_stage('Stage')
        cmodel = create_data_settings_model(HistoryCaseHolder(history))

        if case == 1:
            fonc = stage.add_command("RECU_FONCTION")
            tabl = stage.add_command("POST_COQUE")
        else:
            tabl = stage.add_command("POST_COQUE")
            fonc = stage.add_command("RECU_FONCTION")

        # initial sorting order: no dependencies
        # categories follow their order in catalogue
        cmodel.update()
        children = cmodel.get_stage_children(stage)
        self.assertEqual(2, len(children))
        self.assertEqual(-1, children[0]._id)
        self.assertEqual("Output", children[0]._name)
        self.assertEqual([fonc._id], children[0]._children)
        self.assertEqual(-2, children[1]._id)
        self.assertEqual("Other", children[1]._name)
        self.assertEqual([tabl._id], children[1]._children)

        # add dependency
        fonc.init({"TABLE": tabl})
        fonc.check()

        # updated sorting order: take into account dependencies
        # categories are sorted to follow commands dependency order
        cmodel.update()
        children = cmodel.get_stage_children(stage)
        self.assertEqual(2, len(children))
        self.assertEqual(-1, children[0]._id)
        self.assertEqual("Other", children[0]._name)
        self.assertEqual([tabl._id], children[0]._children)
        self.assertEqual(-2, children[1]._id)
        self.assertEqual("Output", children[1]._name)
        self.assertEqual([fonc._id], children[1]._children)

    def test_categories_dependencies(self):
        """Test for categories grouping"""

        # Here command 1 of category 1 depends on command 2 of category
        # 2; category 1 normally precedes category 2.
        # Taking into account commands dependencies, command 2 should be
        # inserted before command 1 and category 2 should be shown
        # before category 1 in the data tree.
        # The behavior does not depend on the order in which comands are
        # added to the stage.

        # case 1: categories - 1, 2
        self.check_categories_dependencies(case=1)

        # case 2: categories - 2, 1
        self.check_categories_dependencies(case=2)

    def check_categories_break(self, case):
        """Helper function to check categories break."""

        history = History()
        stage = history.current_case.create_stage('Stage')
        cmodel = create_data_settings_model(HistoryCaseHolder(history))

        if case == 1:
            fonc1 = stage.add_command("RECU_FONCTION")
            fonc2 = stage.add_command("RECU_FONCTION")
            tabl = stage.add_command("POST_COQUE")
        elif case == 2:
            fonc1 = stage.add_command("RECU_FONCTION")
            tabl = stage.add_command("POST_COQUE")
            fonc2 = stage.add_command("RECU_FONCTION")
        else:
            tabl = stage.add_command("POST_COQUE")
            fonc1 = stage.add_command("RECU_FONCTION")
            fonc2 = stage.add_command("RECU_FONCTION")

        # initial sorting order: no dependencies
        # categories follow their order in catalogue
        cmodel.update()
        children = cmodel.get_stage_children(stage)
        self.assertEqual(2, len(children))
        self.assertEqual(-1, children[0]._id)
        self.assertEqual("Output", children[0]._name)
        self.assertEqual([fonc1._id, fonc2._id], children[0]._children)
        self.assertEqual(-2, children[1]._id)
        self.assertEqual("Other", children[1]._name)
        self.assertEqual([tabl._id], children[1]._children)

        # add dependency
        fonc2.init({"TABLE": tabl})
        fonc2.check()

        # updated sorting order: take into account dependencies
        # categories are sorted to follow commands dependency order
        cmodel.update()
        children = cmodel.get_stage_children(stage)
        self.assertEqual(3, len(children))
        self.assertEqual(-1, children[0]._id)
        self.assertEqual("Output", children[0]._name)
        self.assertEqual([fonc1._id], children[0]._children)
        self.assertEqual(-2, children[1]._id)
        self.assertEqual("Other", children[1]._name)
        self.assertEqual([tabl._id], children[1]._children)
        self.assertEqual(-3, children[2]._id)
        self.assertEqual("Output", children[2]._name)
        self.assertEqual([fonc2._id], children[2]._children)

    def test_categories_break(self):
        """Test for categories grouping with break"""

        # Here command 1 of category 1 depends on command 2 of category
        # 2; category 1 normally precedes category 2.
        # Taking into account commands dependencies, command 2 should be
        # inserted before command 1 and category 2 should be shown
        # before category 1 in the data tree.
        # The behavior does not depend on the order in which comands are
        # added to the stage.

        # case 1: categories - 1, 1, 2
        self.check_categories_break(case=1)

        # case 2: categories - 1, 2, 1
        self.check_categories_break(case=2)

        # case 3: categories - 2, 1, 1
        self.check_categories_break(case=2)

    def test_categories_tree_sync(self):
        """Test for categories tree synchronization"""

        history = History()
        stage = history.current_case.create_stage('Stage')
        cmodel1 = create_data_settings_model(HistoryHolder(history))

        tabl = stage.add_command("POST_COQUE", "tabl")
        fonc1 = stage.add_command("RECU_FONCTION", "fonc1")
        fonc2 = stage.add_command("RECU_FONCTION", "fonc2")
        fonc2.init({"TABLE": tabl})
        fonc2.check()

        cmodel1.update()
        troot = cmodel1.synchronize()
        self._check_categories_tree_sync(troot, history, history.current_case,
                                         stage, tabl, fonc1, fonc2)

        cmodel2 = create_data_settings_model(HistoryCaseHolder(history))
        troot = cmodel2.update_all()
        self._check_categories_tree_sync(troot, history.current_case, stage,
                                         tabl, fonc1, fonc2)

        cmodel3 = create_data_settings_model(HistoryStageHolder(history))
        troot = cmodel3.update_all()
        self._check_categories_tree_sync(troot, stage, tabl,
                                         fonc1, fonc2)

    def _check_categories_tree_sync(self, *params):
        """
        Check for categories tree synchronization

        Arguments:
            params: list of parameters.
        """

        titem = params[0].child(0)
        param_id = 1

        if isinstance(params[param_id], History):
            self.assertEqual('History', titem.text(0))
            titem = titem.child(0)
            param_id += 1
        if isinstance(params[param_id], Case):
            self.assertEqual(titem.text(0), 'CurrentCase')
            titem = titem.child(0)
            param_id += 1

        stage = params[param_id]
        tabl = params[param_id + 1]
        fonc1 = params[param_id + 2]
        fonc2 = params[param_id + 3]

        self.assertEqual('Stage', titem.text(0))
        self.assertEqual(stage._id, titem.data(0, Role.IdRole))
        self.assertEqual(3, titem.childCount())

        self.assertEqual("Output", titem.child(0).text(0))
        self.assertEqual(-1, titem.child(0).data(0, Role.IdRole))
        self.assertEqual(1, titem.child(0).childCount())

        self.assertEqual('fonc1', titem.child(0).child(0).text(0))
        self.assertEqual(fonc1._id, titem.child(0).child(0).data(0, Role.IdRole))
        self.assertEqual(0, titem.child(0).child(0).childCount())

        self.assertEqual("Other", titem.child(1).text(0))
        self.assertEqual(-2, titem.child(1).data(0, Role.IdRole))
        self.assertEqual(1, titem.child(1).childCount())

        self.assertEqual('tabl', titem.child(1).child(0).text(0))
        self.assertEqual(tabl._id, titem.child(1).child(0).data(0, Role.IdRole))
        self.assertEqual(0, titem.child(1).child(0).childCount())

        self.assertEqual("Output", titem.child(2).text(0))
        self.assertEqual(-3, titem.child(2).data(0, Role.IdRole))
        self.assertEqual(1, titem.child(2).childCount())

        self.assertEqual('fonc2', titem.child(2).child(0).text(0))
        self.assertEqual(fonc2._id, titem.child(2).child(0).data(0, Role.IdRole))
        self.assertEqual(0, titem.child(2).child(0).childCount())

    def test_categories_hidden(self):
        """Test for hiding categories"""
        history = History()
        stage = history.current_case.create_stage('Stage')
        cmodel = create_data_settings_model(HistoryCaseHolder(history))
        fonc = stage.add_command("RECU_FONCTION")
        tabl = stage.add_command("POST_COQUE")
        cmodel.update()
        children = cmodel.get_stage_children(stage)
        self.assertEqual(2, len(children))
        self.assertEqual(-1, children[0]._id)
        self.assertEqual("Output", children[0]._name)
        self.assertEqual([fonc._id], children[0]._children)
        self.assertEqual(-2, children[1]._id)
        self.assertEqual("Other", children[1]._name)
        self.assertEqual([tabl._id], children[1]._children)
        behavior().show_categories = False
        cmodel.update()
        children = cmodel.get_stage_children(stage)
        self.assertEqual(2, len(children))
        self.assertEqual(fonc._id, children[0]._id)
        self.assertEqual(tabl._id, children[1]._id)

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
