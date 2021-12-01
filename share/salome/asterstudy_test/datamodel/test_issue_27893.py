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

"""Automatic tests for gettype cache (issue27893)."""


import os
import unittest

from asterstudy.datamodel import ConversionLevel, History, Validity, comm2study
from asterstudy.datamodel.catalogs import CATA
from hamcrest import *


def test_27893():
    """Test for issue27893"""
    history = History()
    case = history.current_case
    stage = case.create_stage('test_27893')

    dsm = CATA.package("DataStructure")
    dyna = stage.add_command("DYNA_VIBRA", "resharm")
    assert_that(dyna.gettype(), equal_to(dsm.harm_gene))

    output = stage.add_command('IMPR_RESU')
    avail = output.groupby(dsm.resultat_sdaster)
    assert_that(avail, has_length(0))

    dyna.init({"TYPE_CALCUL": "TRAN",
               "BASE_CALCUL": "PHYS"})
    assert_that(dyna.gettype(), equal_to(dsm.dyna_trans))

    output = stage.add_command('IMPR_RESU')
    avail = output.groupby(dsm.resultat_sdaster)
    assert_that(avail, has_length(1))


def test_27895():
    """Test for issue27895"""
    history = History()
    case = history.current_case
    stage = case.create_stage('test_27893')

    commfile = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'export', 'CalcIFS.comm')
    with open(commfile) as file:
        text = file.read()
    strict = ConversionLevel.Any
    comm2study(text, stage, strict)

    km_asse = stage["km_asse"]
    modes = stage["modes"]
    assert_that(km_asse.check(), equal_to(Validity.Nothing))
    assert_that(modes.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    stage["m_asse"].delete()
    assert_that(km_asse.check(), equal_to(Validity.Dependency))
    assert_that(modes.check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    k_asse = stage["k_asse"]
    new_mass = stage.add_command("ASSE_MATRICE", "new_mass")
    new_mass.init({"MATR_ELEM": stage["m_elem"], "NUME_DDL": stage["numedd"]})

    km_asse.init({"COMB_R": ({"MATR_ASSE": k_asse, "COEF_R": 1.0},
                             {"MATR_ASSE": new_mass, "COEF_R": 1.0})})
    assert_that(km_asse.check(), equal_to(Validity.Nothing))

    modes.init({"MATR_RIGI": k_asse, "MATR_MASS": new_mass})

    assert_that(history.has_path(new_mass.uid, modes.uid), equal_to(True))
    assert_that(history.has_path(k_asse.uid, modes.uid), equal_to(True))
    assert_that(modes.depends_on(new_mass), equal_to(True))
    assert_that(modes.depends_on(k_asse), equal_to(True))

    assert_that(modes.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    ids = stage.dataset.get_ids()
    assert_that(ids.index(modes.uid), greater_than(ids.index(new_mass.uid)))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
