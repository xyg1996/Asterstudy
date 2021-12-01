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

"""Automatic tests for nodes."""


import unittest

from asterstudy.datamodel.abstract_data_model import AbstractDataModel, Node
from hamcrest import *
from testutils.node import is_not_referenced


# pragma pylint: disable=protected-access
class TestNode(unittest.TestCase):
    """Automatic tests for nodes"""

    def check_equal(self, node1, node2, result):
        """Auxiliary method: compare two nodes."""
        self.assertEqual(node1 == node2, result)
        self.assertEqual(node1 != node2, not result)
        self.assertEqual(node2 == node1, result)
        self.assertEqual(node2 != node1, not result)

    def test_attrs(self):
        """Test for node attributes"""
        node = Node('test')
        self.assertEqual(node.uid, -1)
        self.assertEqual(node.name, 'test')
        self.assertEqual(node.model, None)
        self.assertEqual(node.parent_nodes, [])
        self.assertEqual(node.children, [])

        with self.assertRaises(AttributeError):
            node.uid = 0

        with self.assertRaises(AttributeError):
            node.new_attr = False

    def test_name(self):
        """Test for name attribute"""
        node = Node()
        self.assertEqual(node.name, '')

        node.name = 'test'
        self.assertEqual(node.name, 'test')

    def test_parent(self):
        """Test for parent attribute"""
        node1 = Node('test')
        node2 = Node('')

        self.assertEqual(node1.parent_nodes, [])
        self.assertEqual(node1.has_parents(), False)

        node1.add_parent(None)
        self.assertEqual(node1.parent_nodes, [])
        self.assertEqual(node1.has_parents(), False)

        node1.add_parent(node2)
        self.assertEqual(node1.parent_nodes, [node2])
        self.assertEqual(node1.has_parents(), True)

        node1.add_parent(node2)
        self.assertEqual(node1.parent_nodes, [node2])
        self.assertEqual(node1.has_parents(), True)

        node1.remove_parent(None)
        self.assertEqual(node1.parent_nodes, [node2])
        self.assertEqual(node1.has_parents(), True)

        node1.remove_parent(node2)
        self.assertEqual(node1.parent_nodes, [])
        self.assertEqual(node1.has_parents(), False)

        node1.remove_parent(node2)
        self.assertEqual(node1.parent_nodes, [])
        self.assertEqual(node1.has_parents(), False)

    def test_repr(self):
        """Test for node's representation"""
        node1 = Node('test1')
        self.assertFalse(node1.has_parents())
        self.assertEqual(node1.shortrepr(), "test1 <-1:Node>")
        self.assertEqual(repr(node1), "test1 <-1:Node child=[] parent=[]>")

        node2 = Node('test2')
        node1.add_parent(node2)
        self.assertTrue(node1.has_parents())
        self.assertEqual(node1.shortrepr(),
                         "test1 <-1:Node>")
        self.assertEqual(repr(node1),
                         "test1 <-1:Node child=[] parent=['test2 <-1:Node>']>")

    def test_equality(self):
        """Test for node equality method"""
        # check that two default nodes are equal
        node1 = Node()
        node2 = Node()
        self.check_equal(node1, node2, True)

        # check equality in regard of name attribute
        node1 = Node()
        node2 = Node()
        node1.name = "a"
        self.check_equal(node1, node2, False)
        node2.name = "b"
        self.check_equal(node1, node2, False)
        node2.name = node1.name
        self.check_equal(node1, node2, True)

        # check equality in regard of uid attribute
        node1 = Node()
        node2 = Node()
        node1._id = 100
        self.check_equal(node1, node2, False)
        node2._id = 200
        self.check_equal(node1, node2, False)
        node2._id = node1._id
        self.check_equal(node1, node2, True)

        # check equality in regard of model attribute
        node1 = Node()
        node2 = Node()
        node1._model = AbstractDataModel()
        self.check_equal(node1, node2, False)
        node2._model = AbstractDataModel()
        self.check_equal(node1, node2, False)
        node2._model = node1._model
        self.check_equal(node1, node2, True)

        # check equality in regard of parent attribute
        node1 = Node()
        node2 = Node()
        node3 = Node()

        node1.add_parent(node3)
        self.check_equal(node1, node2, False)

        node2.add_parent(node3)
        self.check_equal(node1, node2, True)

        node1.add_parent(node2)
        node1.remove_parent(node3)
        self.check_equal(node1, node2, False)

        # check equality in regard of chidren attribute
        node1 = Node()
        node2 = Node()
        node3 = Node()

        node1._children.append(node3)
        self.check_equal(node1, node2, False)

        node2._children.append(node3)
        self.check_equal(node1, node2, True)

        node1._children.append(node2)
        node1._children.remove(node3)
        self.check_equal(node1, node2, False)

        # check non-equality when comparing with other types
        node = Node()
        self.check_equal(node, 1, False)
        self.check_equal(node, 2.3, False)
        self.check_equal(node, "123", False)
        self.check_equal(node, object(), False)

    def test_len(self):
        node1 = Node()
        assert_that(node1, has_length(0))

        node2 = Node()
        node1._children.append(node2)
        assert_that(node1, has_length(1))

    def test_mul(self):
        model = AbstractDataModel()
        node1 = model.add(Node())
        node2 = model.add(Node())
        assert_that(node1 * node2, none())

        node3 = model.add(Node())
        node1.add_child(node3)
        assert_that(calling(node1.__mul__).with_args(node2), raises(AssertionError))

        node2.add_child(node1)
        assert_that(calling(node1.__mul__).with_args(node2), raises(AssertionError))

    def test_add_remove_child(self):
        model = AbstractDataModel()
        node1 = model.add(Node())
        node2 = model.add(Node())

        assert_that(node1.add_child(node2), equal_to(True))
        assert_that(node2.uid, is_in(node1))

        assert_that(node1.add_child(node2), equal_to(False))
        assert_that(node2, is_in(node1))

        assert_that(node1.remove_child(node2), equal_to(True))
        assert_that(node2, is_not(is_in(node1)))

        assert_that(node1.remove_child(node2), equal_to(False))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
