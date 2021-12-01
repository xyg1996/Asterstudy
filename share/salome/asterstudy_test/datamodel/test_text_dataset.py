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

"""Automatic tests for TextDataSet class."""


import unittest

from asterstudy.datamodel.history import History
from asterstudy.datamodel.dataset import TextDataSet


class TestTextDataSet(unittest.TestCase):
    """Test case for TextDataSet class."""

    def test_set_text(self):
        """Test for adding text content to stage"""

        # Create history and stage in text mode.
        history = History()
        case = history.current_case
        stage = case.create_stage('Stage_1')
        stage.use_text_mode()

        # check if there is a single child of type TextDataSet
        children = stage.child_nodes
        self.assertEqual(len(children), 1)
        self.assertTrue(isinstance(children[0], TextDataSet))

        test_text = "Test text"
        children[0].text = test_text

        self.assertTrue(stage in children[0].parent_nodes)
        self.assertEqual(children[0].text, test_text)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
