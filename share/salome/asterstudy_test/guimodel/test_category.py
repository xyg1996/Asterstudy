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

"""Automatic tests for Category class."""


import unittest

from asterstudy.datamodel.abstract_data_model import Node
from asterstudy.datamodel.history import History
from asterstudy.gui.datasettings.category import Category


class TestCategory(unittest.TestCase):
    """Implementation of the automatic tests for Category class."""

    def test_default_category(self):
        """Test for default category"""

        category = Category(0, 'test', None, None)

        self.assertEqual(0, category.uid)
        self.assertEqual('test', category.name)
        self.assertEqual(None, category.stage)
        self.assertEqual(None, category.model)
        self.assertEqual([], category.children)
        self.assertEqual([], category.child_nodes)

        category2 = Category(1, 'other', None, None)
        self.assertFalse(category == category2)

    def test_model_category(self):
        """Test for category with assigned stage"""

        history = History()
        stage = history.current_case.create_stage("Stage")
        cmd1 = stage.add_command('DEFI_MATERIAU')
        cmd2 = stage.add_command('DEFI_MATERIAU')

        category = Category(0, 'test', stage.uid, history)
        category.add_child(cmd1)
        category.add_child(cmd2)

        self.assertEqual([cmd1.uid, cmd2.uid], category.children)
        self.assertEqual([cmd1, cmd2], category.child_nodes)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
