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

"""Miscellaneous test cases"""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.command import CO
from asterstudy.datamodel.comm2study import comm2study

from testutils.tools import check_export, print_stage

#------------------------------------------------------------------------------
def test_co_del_reset():
    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE()

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    # check command deletion
    assert_that(stage, has_length(2))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    cmd = stage["model"]
    assert_that(cmd["MAILLAGE"].value, is_not(none()))
    assert_that(cmd["MAILLAGE"].value, equal_to(stage["mesh"]))

    del stage[0]

    assert_that(stage, has_length(1))

    # affe_modele dependencies are broken but syntax stay ok
    affe_modele = stage[0]
    assert_that(affe_modele.check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    # check that MAILLAGE has not been reset
    cmd = stage["model"]
    assert_that(cmd["MAILLAGE"].value.name, "mesh")

#------------------------------------------------------------------------------
def test_co_del_reuse():
    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE()

mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_3D=_F(GROUP_MA='group')
)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    # check command deletion
    assert_that(stage, has_length(3))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    mesh0 = stage[0]
    mesh1 = stage["mesh"]
    cmd = stage["model"]
    assert_that(cmd["MAILLAGE"], is_not(none()))
    assert_that(cmd["MAILLAGE"], equal_to(mesh1))
    assert_that(mesh0, is_not(equal_to(mesh1)))

    del stage[1]

    assert_that(stage, has_length(2))
    assert_that(mesh0.check(), equal_to(Validity.Nothing))

    # AFFE_MODELE / MAILLAGE should have been reassigned to the first mesh
    # the command and the stage stay valid.
    affe_modele = stage[1]
    assert_that(affe_modele["MAILLAGE"].value, equal_to(mesh1))
    assert_that(affe_modele.check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

#------------------------------------------------------------------------------
def test_co_del_hidden():
    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE()

MACR_ADAP_MAIL(
    ADAPTATION="RAFFINEMENT_UNIFORME",
    MAILLAGE_N=mesh,
    MAILLAGE_NP1=CO("meshout")
)

mesh2 = DEFI_GROUP(DETR_GROUP_MA=_F(NOM="group"), MAILLAGE=meshout)
"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    # check command deletion
    assert_that(stage, has_length(4))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    del stage[1]

    assert_that(stage, has_length(2))
    assert_that(stage[0].name, equal_to("mesh"))
    assert_that(stage[1].name, equal_to("mesh2"))

    deps = stage[1].parent_nodes
    assert_that(deps, has_item(stage.dataset))
    # FIXME 'meshout' have been deleted, and should not be still referenced.
    # assert_that(deps, has_length(1))

    assert_that(stage[0].check(), equal_to(Validity.Nothing))
    assert_that(stage[1].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

#------------------------------------------------------------------------------
def test_co_del_splitted():
    #--------------------------------------------------------------------------
    text1 = \
"""
mesh = LIRE_MAILLAGE()
"""
    text2 = \
"""
mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_3D=_F(GROUP_MA='group')
)

MACR_ADAP_MAIL(
    ADAPTATION="RAFFINEMENT_UNIFORME",
    MAILLAGE_N=mesh,
    MAILLAGE_NP1=CO("meshout")
)

mesh2 = DEFI_GROUP(DETR_GROUP_MA=_F(NOM="group"), MAILLAGE=meshout)
"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage1 = case.create_stage(":1:")
    comm2study(text1, stage1)

    # check command deletion
    assert_that(stage1, has_length(1))
    assert_that(stage1.check(), equal_to(Validity.Nothing))

    stage2 = case.create_stage(":2:")
    comm2study(text2, stage2)

    assert_that(stage2, has_length(4))
    mesh1 = stage2["mesh"]
    assert_that(stage2.check(), equal_to(Validity.Nothing))

    # remove MODI_MAILLAGE
    del stage2[0]

    assert_that(case.nb_stages, equal_to(2))

    # stage2 syntax stays valid but not its dependencies
    assert_that(stage2, has_length(3))
    macr = stage2[0]
    assert_that(macr["MAILLAGE_N"].value, equal_to(mesh1))
    assert_that(stage2.check(), equal_to(Validity.Dependency))


def test_hidden_27000():
    text = \
"""
mesh = LIRE_MAILLAGE()

MACR_ADAP_MAIL(
    ADAPTATION="RAFFINEMENT_UNIFORME",
    MAILLAGE_N=mesh,
    MAILLAGE_NP1=CO("meshout")
)

mesh2 = DEFI_GROUP(DETR_GROUP_MA=_F(NOM="group"), MAILLAGE=meshout)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    assert_that(stage, has_length(4))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    macr = stage[1]
    meshout = stage['meshout']
    mesh2 = stage['mesh2']
    assert_that(mesh2.depends_on(meshout))

    # simulate 'Edit command', 'Ok'
    storage = macr.storage
    macr.init(storage)

    assert_that(stage, has_length(4))
    assert_that(mesh2.depends_on(meshout))


def test_hidden_27000_2():
    text = \
"""
mesh = LIRE_MAILLAGE()

MACR_ADAP_MAIL(
    ADAPTATION="RAFFINEMENT_UNIFORME",
    MAILLAGE_N=mesh,
    MAILLAGE_NP1=CO("meshout")
)

mesh2 = DEFI_GROUP(DETR_GROUP_MA=_F(NOM="group"), MAILLAGE=meshout)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    assert_that(stage, has_length(4))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    macr = stage[1]
    meshout = stage[2]
    mesh2 = stage[3]
    assert_that(meshout.depends_on(macr))
    assert_that(meshout.name, equal_to('meshout'))
    assert_that(mesh2.depends_on(meshout))
    names = [i.name for i in stage.sorted_commands if i.name != "_"]
    assert_that(names, contains('mesh', 'meshout', 'mesh2'))

    # simulate 'Edit command', rename 'meshout' to 'meshadap', 'Ok'
    storage = macr.storage
    storage['MAILLAGE_NP1'] = CO('meshadap')
    macr.init(storage)

    assert_that(stage, has_length(4))
    assert_that(meshout.depends_on(macr))
    assert_that(meshout.name, equal_to('meshadap'))
    assert_that(mesh2.depends_on(meshout))
    names = [i.name for i in stage.sorted_commands if i.name != "_"]
    assert_that(names, contains('mesh', 'meshadap', 'mesh2'))

    # simulate 'Edit command', rename 'meshadap' to 'meshout', 'Ok'
    storage = macr.storage
    storage['MAILLAGE_NP1'] = CO('meshout')
    macr.init(storage)

    assert_that(stage, has_length(4))
    assert_that(meshout.depends_on(macr))
    assert_that(meshout.name, equal_to('meshout'))
    assert_that(mesh2.depends_on(meshout))
    names = [i.name for i in stage.sorted_commands if i.name != "_"]
    assert_that(names, contains('mesh', 'meshout', 'mesh2'))


def test_26992_hidden_duplicated():
    text = \
"""
mesh = LIRE_MAILLAGE()

MACR_ADAP_MAIL(
    ADAPTATION="RAFFINEMENT_UNIFORME",
    MAILLAGE_N=mesh,
    MAILLAGE_NP1=CO("meshout")
)

meshout = DEFI_GROUP(DETR_GROUP_MA=_F(NOM="group"), MAILLAGE=meshout)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    assert_that(stage, has_length(4))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    # simulate run 1
    run_case = history.create_run_case([0])
    stage = run_case[0]
    assert_that(stage, has_length(4))
    names = [i.name for i in stage.sorted_commands if i.name != "_"]
    assert_that(names, contains('mesh', 'meshout', 'meshout'))

    # simulate run 2
    run_case = history.create_run_case([0])
    stage = run_case[0]
    assert_that(stage, has_length(4))
    names = [i.name for i in stage.sorted_commands if i.name != "_"]
    assert_that(names, contains('mesh', 'meshout', 'meshout'))

    # simulate 'Edit command', rename 'meshout' to 'meshadap', 'Ok'
    macr = stage[1]
    meshout = stage[2]
    mesh2 = stage[3]
    storage = macr.storage
    storage['MAILLAGE_NP1'] = CO('meshadap')
    macr.init(storage)

    assert_that(stage, has_length(4))
    assert_that(meshout.depends_on(macr))
    assert_that(meshout.name, equal_to('meshadap'))
    assert_that(mesh2.depends_on(meshout))
    # it requires to edit the command...
    mesh2.submit()
    names = [i.name for i in stage.sorted_commands if i.name != "_"]
    assert_that(names, contains('mesh', 'meshadap', 'meshadap'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
