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

"""Automatic tests for utilities."""


import os
import os.path as osp
import unittest

from asterstudy.common import to_unicode
from asterstudy.common.execution import remove_mpi_prefix
from asterstudy.common.decoder import (ConvergenceDecoder, Decoder,
                                       DynaVibraTimeDecoder, NLTimeDecoder)
from hamcrest import *


def test_time_step_decoder():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'ssnv128a.output')
    with open(output) as fmess:
        text = fmess.read()

    decoder = NLTimeDecoder
    datas = decoder.decode(text)
    # no completion values in this file
    assert_that(datas.keys(), contains("time"))
    data = datas["time"]
    assert_that(data.x, has_length(10))
    assert_that(data.y, has_length(10))
    assert_that(data.title, equal_to("Time"))
    assert_that(data.xlabel, none())
    assert_that(data.ylabel, none())


def test_dyna_vibra_decoder():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'sdll135a.output')
    with open(output) as fmess:
        text = fmess.read()

    decoder = DynaVibraTimeDecoder
    datas = decoder.decode(text)
    assert_that(datas.keys(),
                contains("completion", "time"))
    data = datas["time"]
    assert_that(data.x, has_length(42))
    assert_that(data.y, has_length(42))
    assert_that(max(data.x), equal_to(41))
    assert_that(max(data.y), equal_to(3.2e-4))
    assert_that(data.title, equal_to("Time (100%)"))
    assert_that(data.xlabel, none())
    assert_that(data.ylabel, none())


def test_converg_decoder():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'hsnv125c.output')
    with open(output) as fmess:
        text = fmess.read()
    text = remove_mpi_prefix(to_unicode(text))

    decoder = ConvergenceDecoder
    datas = decoder.decode(text)
    assert_that(datas.keys(),
                contains_inanyorder("iteration", "resi_glob_maxi",
                                    "resi_glob_rela",
                                    "suivi_1", "suivi_2"))
    data = datas["iteration"]
    assert_that(data.x, has_length(1904))
    assert_that(data.y, has_length(1904))
    assert_that(max(data.y), equal_to(4))
    assert_that(data.title, equal_to("Iterations"))
    assert_that(data.xlabel, none())
    assert_that(data.ylabel, none())

    data = datas["resi_glob_maxi"]
    assert_that(data.y, has_length(1904))
    assert_that(max(data.y), equal_to(4.54521E+01))


def test_decoder():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'hsnv125c.output')
    with open(output) as fmess:
        text = fmess.read()

    datas = Decoder.decode(text)
    assert_that(datas.keys(),
                contains_inanyorder("time", "iteration", "resi_glob_rela",
                         "resi_glob_maxi", "suivi_1", "suivi_2"))
    assert_that(datas["time"].y, has_length(622))
    assert_that(datas["iteration"].y, has_length(1904))


def test_reg():
    text = \
"""
[ 35%] Instant calculé : 7.00000e-05, dernier instant archivé : 7.00000e-05, au numéro d'ordre :   700
"""
    from asterstudy.common.decoder import REGFLOAT
    mat = REGFLOAT.search("7.00000e-05")
    assert_that(mat.group('value'), equal_to("7.00000e-05"))

    mat = DynaVibraTimeDecoder._expr.search(text)
    assert_that(mat.group('time'), equal_to("7.00000e-05"))
    assert_that(mat.group('completion'), equal_to("35"))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
