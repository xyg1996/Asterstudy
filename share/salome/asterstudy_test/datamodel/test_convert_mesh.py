# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 EDF R&D
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

"""Automatic tests for parametric studies."""


import os
import os.path as osp
import unittest

from asterstudy.datamodel.engine.salome_runner import has_salome
from asterstudy.datamodel.usages import convert_mesh
from hamcrest import *
from testutils import attr


@unittest.skipIf(not has_salome(), "salome is required")
def test_convert():
    filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'sslv159b.mail')
    medfile = convert_mesh(filename, log=lambda *x: None)
    assert_that(osp.isfile(medfile), equal_to(True))
    os.remove(medfile)

    # unknown format
    ret = convert_mesh("unknown.extension", log=lambda *x: None)
    assert_that(ret, none())

    # failure during conversion
    assert_that(calling(convert_mesh).with_args(filename, 'ideas',
                                                log=lambda *x: None),
                raises(RuntimeError, "Error"))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
