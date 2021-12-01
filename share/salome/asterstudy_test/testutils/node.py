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

"""Utilities for testing nodes of the model."""


def is_not_referenced(node, history):
    """Tests that a node has been removed from the data model

    It no longer has parents.

    It no longer has children.

    It does not reference history, neither is referenced by it.

    No remaining nodes in history point to it.
    """

    # test it no longer has parents
    if node.nb_parents != 0:
        return False

    # test it no longer has children
    if node.nb_children != 0:
        return False

    # test it does not reference history
    if hasattr(node, 'model') and node.model is history:
        return False

    # test it is not referenced by history
    if node.uid in history.nodes:
        return False

    # test there are no remaining nodes in history pointing to it
    for myuid in history.nodes:
        mynode = history.get_node(myuid)
        if mynode.depends_on(node):
            return False
        if node in mynode.child_nodes:
            return False

    # that's all OK
    return True
