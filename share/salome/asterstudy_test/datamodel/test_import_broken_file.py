# -*- coding: utf-8 -*-

# Copyright 2016-2018 EDF R&D
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


import os.path as osp
import unittest

from asterstudy.common.conversion import IncludeProvider
from asterstudy.datamodel import History
from asterstudy.datamodel.general import ConversionLevel

from hamcrest import *
from testutils import tempdir

def check_strict_mode(tmpdir, provider):
    history = History()
    text = \
"""
table = LIRE_TABLE(UNITE=1)
LIRE_TABLE(UNITE=2)
"""
    file_name = osp.join(tmpdir, 'test.comm')
    with open(file_name, 'w') as f:
        f.write(text)
    force_text = False
    stage = history.current_case.import_stage(file_name,
                                              strict=ConversionLevel.Syntaxic,
                                              force_text=False,
                                              provider=provider)
    assert_that(stage.is_text_mode(), equal_to(True))

@tempdir
def test_strict_mode_with_provider(tmpdir):
    """Check import invalid COMM file, with IncludeProvider provider"""
    check_strict_mode(tmpdir, IncludeProvider("", None))

@tempdir
def test_strict_mode_without_provider(tmpdir):
    """Check import invalid COMM file, with None provider"""
    check_strict_mode(tmpdir, None)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
