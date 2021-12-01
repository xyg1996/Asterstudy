# coding=utf-8

# Copyright 2016-2019 EDF R&D
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

"""Automatic tests for CatalogsView class."""

import unittest

from PyQt5 import Qt as Q

from asterstudy.gui.widgets.catalogsview import CatalogsView
from common_test_gui import get_application
from hamcrest import *

def setup():
    """required to create widgets"""
    get_application()

def test():
    view = CatalogsView(None, unittest=True)
    view.restore()
    # needs at least one version to be tested
    nbitems = len(view.items)
    if nbitems < 1:
        return

    data = [item.data() for item in view.items]
    labels = [i[0] for i in data]
    paths = [i[1] for i in data]
    label0 = labels[0]
    path0 = paths[0]

    assert_that(view.checkLabel("new_version", None), equal_to(True))
    assert_that(calling(view.checkLabel).with_args("testing", None),
                raises(ValueError, "reserved"))
    assert_that(calling(view.checkLabel).with_args(label0, None),
                raises(ValueError, "already in use"))
    assert_that(calling(view.checkPath).with_args(path0, None),
                raises(ValueError, "already in use"))
    assert_that(calling(view.checkPath).with_args(path0 + "XXX", None),
                raises(ValueError, "does not exist"))

    # simulate click on X
    view.items[0].deleted.emit()
    assert_that(view.items, has_length(nbitems - 1))

    # add an item with same label
    new_label = label0
    result = view.checkLabel(new_label, None)
    assert_that(result, equal_to(True))

    view._addItem(new_label, '/a/new_path')


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
