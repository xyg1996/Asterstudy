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

"""Automatic tests for commands."""


import unittest

from hamcrest import *

from asterstudy.common import ConversionError

from asterstudy.datamodel import CATA
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.general import FileAttr
from testutils import attr

#------------------------------------------------------------------------------
def setup():
    history = History()
    stage = history.current_case.create_stage('Stage_1')
    return stage

#------------------------------------------------------------------------------
def test_parameters_creation():
    """Test for parameters creation"""
    stage = setup()

    cmd = stage.add_command('AFFE_MODELE')
    assert_that(cmd.cata.keywords, has_length(7))
    assert_that(cmd.rkeys(), has_length(7))

    affe = cmd['AFFE']
    assert_that(affe.cata.entities, has_length(7))
    assert_that(affe.cata.keywords, has_length(5))
    assert_that(affe.rkeys(), has_length(7))

    assert_that('TOUT', is_in(affe.rkeys()))
    assert_that('GROUP_MA', is_in(affe.rkeys()))
    assert_that('MAILLE', is_in(affe.rkeys()))
    assert_that('PHENOMENE', is_in(affe.rkeys()))
    assert_that('MODELISATION', is_in(affe.rkeys()))

#------------------------------------------------------------------------------
def test_command_rename():
    """Test for command rename"""
    stage = setup()

    cmd = stage('DEFI_MATERIAU')
    assert_that(cmd, is_in(stage))
    assert_that(cmd.name, is_not(equal_to('m')))

    cmd.rename('m')
    assert_that(cmd.name, equal_to('m'))

    # unchanged
    cmd.rename('m')
    assert_that(cmd.name, equal_to('m'))

#------------------------------------------------------------------------------
def test_command_eq_cata():
    """Test for commands equality"""
    stage = setup()

    cmd1 = stage('DEBUT')
    cmd2 = stage('DEBUT')

    assert_that(cmd1 * cmd2, none())

#------------------------------------------------------------------------------
def test_command_ne_cata():
    """Test for two same-named commands non-equality"""
    stage = setup()

    cmd1 = stage('DEBUT', 'm')
    cmd2 = stage('DEFI_MATERIAU', 'm')

    assert_that(calling(cmd1.__mul__).with_args(cmd2), raises(AssertionError))

#------------------------------------------------------------------------------
def test_command_ne_name():
    """Test for commands non-equality"""
    stage = setup()

    cmd1 = stage('DEFI_MATERIAU', 'm1')
    cmd2 = stage('DEFI_MATERIAU', 'm2')

    assert_that(calling(cmd1.__mul__).with_args(cmd2), raises(AssertionError))

#------------------------------------------------------------------------------
def test_invalid_operations():
    """Test for invalid operations"""
    stage = setup()

    cmd1 = stage('DEFI_MATERIAU', 'm')
    cmd2 = stage('DEFI_MATERIAU', 'm')
    cmd3 = stage('DEFI_NAPPE', 'n')

    assert_that(cmd1 * cmd2, none())

    elas = cmd1['ELAS']
    elas['E'] = 1.0
    assert_that(elas['E'], equal_to(1.0))

    cmd2['ELAS']['E'] = 2.0
    assert_that(calling(cmd1.__mul__).with_args(cmd2), raises(AssertionError))

    def set_kw():
        elas['E'] = cmd2

    assert_that(calling(set_kw), raises(TypeError))

    elas_fo = cmd1['ELAS_FO']
    elas_fo['E'] = cmd3

    def del_kw():
        del elas['e']

    assert_that(calling(del_kw), raises(KeyError))

    assert_that(calling(cmd2.__mul__).with_args(None), raises(AssertionError))

#------------------------------------------------------------------------------
def test_command_repr():
    """Test for commands representation"""
    stage = setup()

    stage("LIRE_MAILLAGE", "mesh")
    cmd = stage("AFFE_MODELE", "model")
    cmd["MAILLAGE"] = stage["mesh"]

    repr_text = 'model = AFFE_MODELE(MAILLAGE=mesh)\n'
    assert_that(str(cmd), equal_to(repr_text))

    short_repr = 'model <from AFFE_MODELE>'
    assert_that(cmd.short_repr(), equal_to(short_repr))

    node_repr = "model <5:Command child=[] parent=['DataSet <3:GraphicalDataSet>', 'mesh <4:Command>']>"
    assert_that(cmd.node_repr(), equal_to(node_repr))

    assert_that(repr(cmd), equal_to(node_repr))

#------------------------------------------------------------------------------
def test_command_naming():
    """Test for commands naming"""
    stage = setup()
    case = stage.parent_case

    # test adding notype command with default name
    debut = stage('DEBUT')
    assert_that(debut.name, equal_to('_'))
    assert_that(debut.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # unknown type
    defi = stage('DEFI_FICHIER')
    defi['UNITE'] = 55
    name = case.generate_name(defi)
    assert_that(name, equal_to('_'))

    # test adding typed command with default name
    meshdef = stage.add_command('LIRE_MAILLAGE')
    assert_that(meshdef.name, equal_to('mesh'))
    assert_that(meshdef.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    mesh2 = stage.add_command('LIRE_MAILLAGE')
    assert_that(mesh2.name, equal_to('mesh0'))

    # test renaming with valid name
    meshdef.name = 'good'
    assert_that(meshdef.name, equal_to('good'))
    assert_that(meshdef.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # test adding typed command with valid name
    mesh = stage('LIRE_MAILLAGE', 'Mesh')
    assert_that(mesh.name, equal_to('Mesh'))
    assert_that(mesh.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # test adding typed command with invalid name
    bad = stage('LIRE_MAILLAGE', '?./§')
    assert_that(bad.check(), equal_to(Validity.Naming))
    assert_that(stage.check(), equal_to(Validity.Naming))
    assert_that(case.check(), equal_to(Validity.Naming))
    bad.delete()
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # test adding typed command with long name
    toolong = stage('LIRE_MAILLAGE', 'abcdedfghjkl')
    assert_that(toolong.check(), equal_to(Validity.Naming))
    assert_that(stage.check(), equal_to(Validity.Naming))
    assert_that(case.check(), equal_to(Validity.Naming))
    toolong.delete()
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # the command is valid but not the stage
    badname = stage('LIRE_MAILLAGE', 'Mesh')
    assert_that(badname.name, equal_to('Mesh'))
    assert_that(badname.check(), equal_to(Validity.Naming))
    assert_that(stage.check(), equal_to(Validity.Naming))
    assert_that(case.check(), equal_to(Validity.Naming))
    badname.delete()
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # test command with assigned keywords
    detr = stage('DETRUIRE')
    detr["CONCEPT"]["NOM"] = mesh
    assert_that(detr.name, equal_to('_'))
    assert_that(detr.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # test name reusage
    newmesh = stage('LIRE_MAILLAGE', 'Mesh')
    newmesh.init({})
    newmesh.check()

    assert_that(newmesh.name, equal_to('Mesh'))
    assert_that(newmesh.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # order will be preserved by adding a dependency to DETRUIRE
    assert_that(newmesh.depends_on(detr), equal_to(True))

    # more test name reusage
    reused = stage('MODI_MAILLAGE', 'Mesh')
    reused['MAILLAGE'] = newmesh
    reused['ORIE_PEAU_2D']['GROUP_MA'] = 'edge'
    assert_that(reused.name, equal_to('Mesh'))
    assert_that(reused.check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # test for several stages
    stage2 = case.create_stage('Stage_2')
    model = stage('AFFE_MODELE', 'model')
    model['MAILLAGE'] = stage['Mesh']
    factor = model['AFFE']
    factor['TOUT'] = 'OUI'
    factor['PHENOMENE'] = 'MECANIQUE'
    factor['MODELISATION'] = '3D'
    assert_that(model.check(safe=False), equal_to(Validity.Nothing))
    assert_that(stage2.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    # test that command from first stage is valid but not stage itself
    badname = stage('LIRE_MAILLAGE', 'Mesh')
    assert_that(badname.name, equal_to('Mesh'))
    assert_that(badname.check(), equal_to(Validity.Naming))
    assert_that(stage.check(), equal_to(Validity.Naming))
    assert_that(stage2.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Naming))


def test_expects_result():
    from asterstudy.datamodel.catalogs import CATA
    DS = CATA.package("DataStructure")

    stage = setup()
    case = stage.parent_case
    # operator
    cmd = stage('LIRE_MAILLAGE')
    assert_that(CATA.expects_result(cmd.cata), equal_to(True))
    assert_that(cmd.safe_type(), is_not(is_in([CATA.baseds, None])))
    # macro
    cmd = stage('DEBUT')
    assert_that(CATA.expects_result(cmd.cata), equal_to(False))
    assert_that(cmd.safe_type(), equal_to(None))
    # formule is a special macro
    form = stage('FORMULE')
    assert_that(CATA.expects_result(form.cata), equal_to(True))
    assert_that(form.safe_type(), equal_to(DS.formule))
    assert_that(calling(form.gettype), raises(TypeError))
    # proc
    cmd = stage('FIN')
    assert_that(CATA.expects_result(cmd.cata), equal_to(False))
    assert_that(cmd.safe_type(), equal_to(None))

    # gettype should not raise TypeError in text mode
    stage.use_text_mode()
    assert_that(form.safe_type(), equal_to(DS.formule))
    assert_that(form.gettype(), equal_to(DS.formule))

def test_detruire_deps():
    """Test for automatic dependencies to DETRUIRE"""
    stage = setup()
    case = stage.parent_case

    mesh = stage('LIRE_MAILLAGE', 'Mesh')

    detr = stage('DETRUIRE')
    detr.init({'CONCEPT': {'NOM': mesh}})

    newmesh = stage('LIRE_MAILLAGE', 'Mesh')
    assert_that(newmesh.name, equal_to('Mesh'))
    assert_that(newmesh.check(), equal_to(Validity.Nothing))

    # order will be preserved by adding a dependency to DETRUIRE
    assert_that(newmesh.depends_on(detr), equal_to(True))


#------------------------------------------------------------------------------
def test_unit_keyword():
    """Test for UNITE keywords"""
    #--------------------------------------------------------------------------
    stage = setup()
    case = stage.parent_case

    command = stage('PRE_GMSH')

    #--------------------------------------------------------------------------
    command.init({'UNITE_GMSH': None})
    assert_that(command.storage, has_length(0))

    #--------------------------------------------------------------------------
    unit = command['UNITE_MAILLAGE']

    unit.value = 20

    #--------------------------------------------------------------------------
    unit = command['UNITE_GMSH']

    unit.value = {19: 'gmsh.file'}

    assert_that(unit.value, is_in(stage.handle2info))

    info = stage.handle2info[unit.value]
    assert_that(command, is_in(info))
    assert_that(info.commands, equal_to([command]))

    def _check_get():
        _i = info[1]
    def _check_set():
        info[1] = 100
    def _check_del():
        del info[1]

    assert_that(calling(_check_get), raises(TypeError))
    assert_that(calling(_check_set), raises(TypeError))
    assert_that(calling(_check_del), raises(TypeError))

    attrs = info[command]
    assert_that(attrs, equal_to([FileAttr.In]))

    assert_that(unit.filename, equal_to(info.filename))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_unit2stage_mapping():
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage1 = case.create_stage('Stage_1')

    command1 = stage1('PRE_GMSH')
    unit = command1['UNITE_GMSH']
    unit.value = {19: 'gmsh.file'}

    from asterstudy.datamodel.study2comm import study2comm
    # print study2comm(stage1)

    assert_that(unit.value, is_in(stage1.handle2info))

    info = stage1.handle2info[unit.value]
    assert_that(command1, is_in(info))

    attrs = info[command1]
    assert_that(attrs, equal_to([FileAttr.In]))

    #--------------------------------------------------------------------------
    stage2 = case.create_stage('Stage_2')

    command2 = stage2('PRE_GMSH')

    unit = command2['UNITE_GMSH']
    unit.value = {19: 'gmsh.file'}

    unit = command2['UNITE_MAILLAGE']
    unit.value = {20: 'maillage.file'}

    assert_that(unit.value, is_in(stage2.handle2info))

    info = stage2.handle2info[unit.value]
    assert_that(command2, is_in(info))

    attrs = info[command2]
    assert_that(attrs, equal_to([FileAttr.Out]))

    #--------------------------------------------------------------------------
    stage2('PRE_GMSH')

    stage2.use_text_mode()

    #--------------------------------------------------------------------------
    pass

def test_deletion():
    """Test for deletion of invalid command

    It may occur if a conversion to graphical mode fails. The stage is cleared
    and so each created command, even an invalid one, is deleted.
    It must not fail."""

    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    stage.use_text_mode()
    stage.set_text("""mesh = LIRE_MAILLAGE(UNKNOWN='VALUE')""")

    assert_that(calling(stage.use_graphical_mode), raises(ConversionError))
    assert_that(stage.conversion_report.get_errors(), is_not(equal_to("")))


def test_invalid_unit():
    """Test for initialization of UNITE keyword with invalid value"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    command = stage('LIRE_MAILLAGE')
    assert_that(command.storage, has_length(0))

    command.init({'UNITE': None})
    assert_that(command.storage, has_length(0))

    command.init({'UNITE': {None:''}})
    assert_that(command.storage, has_length(0))

def _mock_old_history():
    history = History()
    history.support._all_types = False
    return history

def test_get_types():
    """Test for get_all_types feature"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    command = stage('DEBUT')
    res = command.get_possible_types()
    assert_that(res, has_length(1))
    assert_that(res, contains(None))

    command = stage('DEFI_FONCTION')
    DS = CATA.package("DataStructure")
    res = command.get_possible_types()
    assert_that(res, has_length(2))
    assert_that(res, contains_inanyorder(DS.fonction_sdaster, DS.fonction_c))

    command = stage('ASSEMBLAGE')
    res = command.get_possible_types()
    assert_that(res, has_length(4))
    assert_that(res[0], has_length(1))
    assert_that(res[0], contains(None))
    assert_that(res[1], has_length(2))
    assert_that(res[1], contains(None, DS.nume_ddl_sdaster))
    assert_that(res[2], has_length(5))
    assert_that(res[2], contains(None, DS.matr_asse_depl_r, DS.matr_asse_pres_c,
                                 DS.matr_asse_temp_r, DS.matr_asse_depl_c))
    assert_that(res[3], has_length(2))
    assert_that(res[3], contains(None, DS.cham_no_sdaster))

    # check failover if called on old catalogs
    hist2 = _mock_old_history()
    case2 = hist2.current_case
    stage2 = case2.create_stage(':memory2:')
    command = stage2('DEFI_FONCTION')
    res = command.get_possible_types()
    assert_that(res, has_length(1))
    assert_that(res, contains(CATA.baseds))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
