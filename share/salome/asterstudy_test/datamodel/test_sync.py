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

"""Automatic tests for trees synchronization."""


import unittest

from asterstudy.datamodel.abstract_data_model import AbstractDataModel, Node
from asterstudy.datamodel.sync import synchronize


class TestObj:
    """Test object for synchronization"""

    def __init__(self, node_id, name):
        self._id = node_id
        self._name = name
        self._children = []

    def _dump(self, indent=''):
        text = "\n" + indent + self._name
        for child in self._children:
            text += child._dump(indent + '  ')
        return text


class TestTreeData:
    """Test tree data for synchronization"""

    def __init__(self):
        self._operations = []

    def clear(self):
        """Clear the tree data"""
        self._operations = []

    def is_equal(self, src, dst):
        """Check if two items are equivalent"""
        if dst is None:
            return src is None
        else:
            return src._id == dst._id

    def update_item(self, src, dst):
        """Update destination item from source"""
        dst._name = src._name

    def get_src_children(self, src):
        """Get children items for a source item"""
        model = src._model
        return [model.get_node(i) for i in src._children]

    def get_dst_children(self, dst):
        """Get children items for a destination item"""
        return dst._children

    def create_item(self, src):
        """Create a destination item on source"""
        item = TestObj(src._id, src._name)
        oper = 'New item: %i %s' % (src._id, src._name)
        self._operations.append(oper)
        return item

    def replace_dst_children(self, dst, new_children):
        """Replace children in the destination item"""
        dst._children = new_children


class TestSync(unittest.TestCase):
    """Automatic tests for synchronization"""

    def test_sync(self):
        """Test for synchronization"""
        model1 = AbstractDataModel()
        root1 = Node('root')
        folder1 = Node('f1')
        folder2 = Node('f2')
        file1 = Node('file1')
        file2 = Node('file2')
        file3 = Node('file3')
        model1.add(root1, None)
        model1.add(folder1, root1)
        model1.add(folder2, root1)
        model1.add(file1, folder1)
        model1.add(file2, folder1)
        model1.add(file3, folder2)

        treedata = TestTreeData()
        root2 = synchronize(root1, None, treedata)
        self.assertEqual(root2._dump(), """
root
  f1
    file1
    file2
  f2
    file3""")
        self.assertEqual(len(treedata._operations), 6)  # 6 new items appear

        treedata.clear()
        self.assertEqual(len(treedata._operations), 0)
        root3 = synchronize(root1, root2, treedata)
        self.assertEqual(root2, root3)
        self.assertEqual(len(treedata._operations), 0)  # No new items

        model1.add(Node('file4'), folder1)
        folder1._children = [4, 7, 5]
        root3 = synchronize(root1, root2, treedata)
        self.assertEqual(root2, root3)
        self.assertEqual(len(treedata._operations), 1)
        self.assertEqual(treedata._operations[0], 'New item: 7 file4')
        self.assertEqual(root2._dump(), """
root
  f1
    file1
    file4
    file2
  f2
    file3""")


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
