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

"""Automatic tests for export feature."""


import unittest
from hamcrest import *

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.study2code import study2code
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.history import History

from testutils.tools import check_export, check_import
from testutils.tools import check_text_eq

#------------------------------------------------------------------------------
def test_1():
    """Test for command introspection"""
    #--------------------------------------------------------------------------
    text1 = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

MAYA = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

MODELE = AFFE_MODELE(AFFE=(_F(GROUP_MA='EFLUIDE',
                              MODELISATION='2D_FLUIDE',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA=('EFS_P_IN', 'EFS_PIST', 'EFS_P_OU'),
                              MODELISATION='2D_FLUI_STRU',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA=('E_PISTON', 'E_P_IN', 'ES_P_IN', 'E_P_OU'),
                              MODELISATION='D_PLAN',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA='AMORPONC',
                              MODELISATION='2D_DIS_T',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA=('MASSPONC', ),
                              MODELISATION='2D_DIS_T',
                              PHENOMENE='MECANIQUE')),
                     INFO=2,
                     MAILLAGE=MAYA)

FIN()
"""
    #--------------------------------------------------------------------------
    history1 = History()
    case1 = history1.current_case
    stage1 = case1.create_stage(':memory:')

    comm2study(text1, stage1)

    #--------------------------------------------------------------------------
    text2 = study2code(stage1, 'stage2')

    history2 = History()
    case2 = history2.current_case
    stage2 = case2.create_stage(':memory-2:')
    exec(text2)

    assert(check_export(stage2, text1))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_2():
    """Test (2) for command introspection"""
    #--------------------------------------------------------------------------
    text1 = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      IGNORE_ALARM='ELEMENTS3_11')

_41 = DEFI_MATERIAU(ECRO_PUIS=_F(A_PUIS=0.1,
                                 N_PUIS=10.0,
                                 SY=200000000.0),
                    ELAS=_F(ALPHA=1.18e-05,
                            E=200000000000.0,
                            NU=0.3))

_1672 = DEFI_MATERIAU(ECRO_PUIS=_F(A_PUIS=0.1,
                                   N_PUIS=10.0,
                                   SY=200.0),
                      ELAS=_F(ALPHA=1.18e-05,
                              E=200000.0,
                              NU=0.3))

tabresu = TEST_COMPOR(COMPORTEMENT=_F(ITER_INTE_MAXI=50,
                                      RELATION='VMIS_ISOT_PUIS',
                                      RESI_INTE_RELA=1e-06),
                      LIST_MATER=[_41, _1672],
                      LIST_NPAS=[1, 1, 1, 1, 1, 5, 25],
                      NEWTON=_F(REAC_ITER=1),
                      OPTION='MECA',
                      POISSON=0.3,
                      VARI_TEST=('V1', 'VMIS', 'TRACE'),
                      YOUNG=200000.0)

FIN()
"""
    #--------------------------------------------------------------------------
    history1 = History()
    case1 = history1.current_case
    stage1 = case1.create_stage(':memory:')

    comm2study(text1, stage1)

    #--------------------------------------------------------------------------
    text2 = study2code(stage1, 'stage2')

    history2 = History()
    case2 = history2.current_case
    stage2 = case2.create_stage(':memory-2:')
    exec(text2)

    assert(check_export(stage2, text1))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_python_like_command_name_resolution():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':0:')

    #--------------------------------------------------------------------------
    command = stage('DEBUT')

    factor = command['CODE']
    factor['NIV_PUB_WEB'] = 'INTERNET'

    factor = command['DEBUG']
    factor['SDVERI'] = 'OUI'

    command = stage("LIRE_MAILLAGE", "mesh")
    command['UNITE'] = 20

    command = stage('DEFI_MATERIAU', 'mat')

    factor = command['ECRO_LINE']
    factor['D_SIGM_EPSI'] = -1950.0
    factor['SY'] = 3.0

    factor = command['ELAS']
    factor['E'] = 30000.0
    factor['NU'] = 0.2
    factor['RHO'] = 2764.0

    command = stage('AFFE_MATERIAU', 'fieldmat')

    factor = command['AFFE']
    factor['MATER'] = stage['mat':command]
    factor['TOUT'] = 'OUI'

    command['MAILLAGE'] = stage['mesh']

    command = stage('AFFE_MODELE', 'model')

    factor = command['AFFE']
    factor['PHENOMENE'] = 'MECANIQUE'
    factor['MODELISATION'] = 'AXIS_INCO_UPG'
    factor['TOUT'] = 'OUI'

    command['MAILLAGE'] = stage['mesh']

    command = stage('CALC_MATR_ELEM', 'matr')
    command['OPTION'] = 'MASS_MECA'
    command['CHAM_MATER'] = stage['fieldmat':command]
    command['MODELE'] = stage['model']

    stage('FIN')

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

mesh = LIRE_MAILLAGE(UNITE=20)

model = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                            PHENOMENE='MECANIQUE',
                            TOUT='OUI'),
                    MAILLAGE=mesh)

mat = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                 SY=3.0),
                    ELAS=_F(E=30000.0,
                            NU=0.2,
                            RHO=2764.0))

fieldmat = AFFE_MATERIAU(AFFE=_F(MATER=mat,
                                 TOUT='OUI'),
                         MAILLAGE=mesh)

matr = CALC_MATR_ELEM(CHAM_MATER=fieldmat,
                      MODELE=model,
                      OPTION='MASS_MECA')

FIN()
"""
    #--------------------------------------------------------------------------
    assert(check_export(stage, text, sort=True))

    assert(check_import(text, sort=True))

    #--------------------------------------------------------------------------
    history2 = History()
    case2 = history2.current_case
    stage2 = case2.create_stage(':2:')
    comm2study(text, stage2)

    #--------------------------------------------------------------------------
    text2 = study2code(stage, 'stage3')
    history3 = History()
    case3 = history3.current_case
    stage3 = case3.create_stage(':3:')
    exec(text2)

    assert(check_export(stage3, text, sort=True))

    #--------------------------------------------------------------------------
    pass

def test_factor_storage_type():
    """Test for unique factor keyword as tuple, list"""
    #--------------------------------------------------------------------------
    text_tuple = \
"""
DEBUT(CODE=( _F(NIV_PUB_WEB='INTERNET'),))

FIN()
"""
    text_list = \
"""
DEBUT(CODE=[ _F(NIV_PUB_WEB='INTERNET'), ])

FIN()
"""
    expected_text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'))

FIN()
"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm2study(text_tuple, stage)

    debut = stage.sorted_commands[0]
    code = debut['CODE']
    assert(not code.undefined())

    text2 = study2code(stage, 'stage2')
    stage2 = case.create_stage(':memory-2:')
    exec(text2)

    assert(check_export(stage2, expected_text))

    #--------------------------------------------------------------------------
    stage = case.create_stage(':memory:')

    comm2study(text_list, stage)

    debut = stage.sorted_commands[0]
    code = debut['CODE']
    assert(not code.undefined())

    text2 = study2code(stage, 'stage2')
    stage2 = case.create_stage(':memory-2:')
    exec(text2)

    assert(check_export(stage2, expected_text))


#------------------------------------------------------------------------------
def test_command_type_lookup():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage1 = case.create_stage(':1:')
    text1 = \
"""
table = POST_COQUE(UNITE=1)
recu1 = RECU_FONCTION(TABLE=table)
"""
    comm2study(text1, stage1)
    assert_that(stage1, has_length(2))
    assert_that(stage1, contains(stage1['table'], stage1['recu1']))

    #--------------------------------------------------------------------------
    stage2 = case.create_stage(':2:')
    text2 = \
"""
table2 = POST_COQUE(UNITE=2)
table3 = POST_COQUE(UNITE=3)
recu2 = RECU_FONCTION(TABLE=table2, FILTRE=_F(NOM_PARA="X"))
"""
    comm2study(text2, stage2)
    assert_that(stage2, has_length(3))
    assert_that(stage2, contains(stage2['table2'], stage2['table3'], stage2['recu2']))

    #--------------------------------------------------------------------------
    command = stage2['recu2']
    assert_that(command.stage, equal_to(stage2))

    fact = command['FILTRE']
    astype = fact.gettype('NOM_PARA')
    assert_that(astype, equal_to('TXM'))

    astype = stage2['recu2']['TABLE'].gettype()
    assert_that(astype, not_none())

    commands = stage2['recu2'].groupby(astype)
    assert_that(commands, contains(stage2['table3'], stage2['table2'], stage2['table']))

    # only one function (recu1) could be used by table2
    astype = stage2['recu2'].gettype()
    commands = stage2['table2'].groupby(astype)
    assert_that(commands, contains(stage1['recu1']))


def test_co():
    """Test for secondary result in macro-command"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    mesh = stage("LIRE_MAILLAGE", "mesh")
    mesh['UNITE'] = 20

    command = stage('MACR_ADAP_MAIL', '_')
    command['ADAPTATION'] = 'RAFFINEMENT_UNIFORME'
    command['MAILLAGE_N'] = stage['mesh':command]
    assert_that(len(stage), equal_to(2))

    command['MAILLAGE_NP1'] = 'meshout'
    assert_that(len(stage), equal_to(3))

    decls = command.list_co
    assert_that(len(decls), equal_to(1))
    assert_that(decls[0].name, equal_to('meshout'))

    command = stage('DEFI_GROUP', 'mesh2')
    command['MAILLAGE'] = stage['meshout']
    fact = command['DETR_GROUP_MA']
    fact['NOM'] = 'group'

    # check "if command" for a Command
    assert_that(stage['mesh'])
    # check "if command" for a Hidden
    assert_that(stage['meshout'])
    # check "if keyword" for a CO
    assert_that(stage['meshout']['DECL'])

    # check typing of CO results
    from asterstudy.datamodel.catalogs import CATA
    dsm = CATA.package("DataStructure")
    assert_that(stage['mesh'].gettype(), equal_to(dsm.maillage_sdaster))
    assert_that(stage['meshout'].gettype(), equal_to(dsm.maillage_sdaster))

    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

MACR_ADAP_MAIL(ADAPTATION='RAFFINEMENT_UNIFORME',
               MAILLAGE_N=mesh,
               MAILLAGE_NP1=CO('meshout'))

mesh2 = DEFI_GROUP(DETR_GROUP_MA=_F(NOM='group'),
                   MAILLAGE=meshout)
"""
    #--------------------------------------------------------------------------
    assert(check_export(stage, text))

    assert(check_import(text))

    #--------------------------------------------------------------------------
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    stage2 = case.create_stage(':2:')
    comm2study(text, stage2)
    assert_that(stage2.check(), equal_to(Validity.Naming))
    assert_that(case.check(), equal_to(Validity.Naming))

    #--------------------------------------------------------------------------
    text2 = study2code(stage, 'stage3')
    history3 = History()
    case3 = history3.current_case
    stage3 = case3.create_stage(':3:')
    exec(text2)

    assert(check_export(stage3, text))
    assert_that(stage3.check(), equal_to(Validity.Nothing))
    assert_that(case3.check(), equal_to(Validity.Nothing))


def test_block_crea_champ():
    """Test for block and empty keyword"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    mesh = stage("LIRE_MAILLAGE", "mesh")
    mesh['UNITE'] = 20

    geom = stage("CREA_CHAMP", "geom")
    geom["TYPE_CHAM"] = "NOEU_GEOM_R"
    geom["OPERATION"] = "EXTR"
    geom["MAILLAGE"] = mesh
    # FIXME: NOM_CHAM is not available in the GUI
    geom["NOM_CHAM"] = "GEOMETRIE"

    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

geom = CREA_CHAMP(MAILLAGE=mesh,
                  NOM_CHAM='GEOMETRIE',
                  OPERATION='EXTR',
                  TYPE_CHAM='NOEU_GEOM_R')
"""
    assert(check_export(stage, text))
    assert(check_import(text))


def test_crea_champ_order():
    """Test for block and empty keyword"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    mesh = stage("LIRE_MAILLAGE", "mesh")
    mesh['UNITE'] = 20

    geom = stage("CREA_CHAMP", "geom")
    geom["TYPE_CHAM"] = "NOEU_GEOM_R"
    geom["OPERATION"] = "EXTR"
    geom["MAILLAGE"] = mesh

    tab = stage("CREA_TABLE", "tab")
    fact = tab["LISTE"]
    fact["LISTE_R"] = (0., 1.)
    fact["PARA"] = "INST"

    # FIXME: as 'tab' has been created after 'geom', it isn't available
    # as a choice for TABLE in the GUI.
    geom["TABLE"] = tab

    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

tab = CREA_TABLE(LISTE=_F(LISTE_R=(0.0, 1.0),
                          PARA='INST'))

geom = CREA_CHAMP(MAILLAGE=mesh,
                  OPERATION='EXTR',
                  TABLE=tab,
                  TYPE_CHAM='NOEU_GEOM_R')
"""
    assert(check_export(stage, text, sort=True))
    assert(check_import(text, sort=True))


def test_command_reordering():
    """Test for command reordering"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    mesh = stage("LIRE_MAILLAGE", "mesh")

    model = stage("AFFE_MODELE", "model")
    factor = model["AFFE"]
    factor['PHENOMENE'] = 'MECANIQUE'
    factor['MODELISATION'] = 'AXIS_INCO_UPG'
    factor['TOUT'] = 'OUI'
    model['MAILLAGE'] = mesh

    changed = stage("MODI_MAILLAGE", "mesh")
    changed["MAILLAGE"] = mesh
    changed["ORIE_PEAU_2D"]["GROUP_MA"] = "groupname"
    # should be this update automatic?
    # if not MODI_MAILLAGE must be placed after AFFE_MODELE for clarity.
    model['MAILLAGE'] = changed

    #--------------------------------------------------------------------------
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(stage.commands, contains(mesh, model, changed))

    assert_that(changed, greater_than(mesh))
    assert_that(changed, less_than(model))

    assert_that(stage.sorted_commands, contains(mesh, changed, model))

    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE()

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_2D=_F(GROUP_MA='groupname'))

model = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                            PHENOMENE='MECANIQUE',
                            TOUT='OUI'),
                    MAILLAGE=mesh)
"""

    assert(check_export(stage, text, sort=True))


def test_command_ordering():
    """Test for command ordering (1)"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    tabl = stage("POST_COQUE") # Other: last
    form = stage("FORMULE") # Functions and Lists: 3
    mesh = stage("LIRE_MAILLAGE") # Mesh: 0
    lstr = stage("DEFI_LIST_REEL") # Functions and Lists: 3
    recu = stage("RECU_FONCTION") # Post Processing: 8
    mate = stage("DEFI_MATERIAU") # Material: 2

    # no dependencies, the commands are sorted first by category, then by uid
    commands = stage.sorted_commands
    assert_that(commands, contains(mesh, mate, form, lstr, recu, tabl))

    # add dependencies
    recu.init({'TABLE': tabl})
    sorted_cmds = stage.sorted_commands
    assert_that(sorted_cmds, contains(mesh, mate, form, lstr, tabl, recu))

    mate.init({'TRACTION': {'SIGM': recu}})
    sorted_cmds = stage.sorted_commands
    assert_that(sorted_cmds, contains(mesh, form, lstr, tabl, recu, mate))
    form.init({})
    lstr.init({})
    sorted_cmds = stage.sorted_commands
    assert_that(sorted_cmds, contains(mesh, form, lstr, tabl, recu, mate))

    from asterstudy.datamodel.abstract_data_model import compare_deps
    assert_that(compare_deps(tabl, tabl), equal_to(0))
    assert_that(compare_deps(tabl, form), equal_to(0))
    assert_that(compare_deps(tabl, mesh), equal_to(0))
    assert_that(compare_deps(tabl, lstr), equal_to(0))
    assert_that(compare_deps(tabl, recu), equal_to(-1))
    assert_that(compare_deps(tabl, mate), equal_to(-1))

    assert_that(compare_deps(mate, tabl), equal_to(1))
    assert_that(compare_deps(mate, form), equal_to(0))
    assert_that(compare_deps(mate, mesh), equal_to(0))
    assert_that(compare_deps(mate, lstr), equal_to(0))
    assert_that(compare_deps(mate, recu), equal_to(1))
    assert_that(compare_deps(mate, mate), equal_to(0))

    assert_that(compare_deps(recu, tabl), equal_to(1))
    assert_that(compare_deps(recu, form), equal_to(0))
    assert_that(compare_deps(recu, mesh), equal_to(0))
    assert_that(compare_deps(recu, lstr), equal_to(0))
    assert_that(compare_deps(recu, recu), equal_to(0))
    assert_that(compare_deps(recu, mate), equal_to(-1))


def test_command_ordering2():
    """Test for command ordering (2)"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    tabl = stage("RECU_FONCTION") # Post processing: 7
    form = stage("POST_COQUE") # Other: last
    mesh = stage("RECU_FONCTION") # Post processing: 7

    commands = stage.sorted_commands
    assert_that(commands, contains(tabl, mesh, form))


def test_command_ordering3():
    """Test for command ordering (3)"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    tabl = stage("RECU_FONCTION") # Post processing: 7
    form = stage("POST_COQUE") # Other: last

    tabl.init({"TABLE": form})
    tabl.check()

    commands = stage.sorted_commands
    assert_that(commands, contains(form, tabl))


def test_variable_ordering():
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    text = \
"""
vitesse = 1.e-5

t_0 = 5.e-2 / (8.0 * vitesse)

c1 = DEFI_CONSTANTE(VALE=t_0)
"""
    comm2study(text, stage)

    commands = stage.sorted_commands
    assert_that(commands, has_length(3))
    names = ["{0.name}:{0.uid}".format(i) for i in commands]
    assert_that(names, contains("vitesse:4", "t_0:5", "c1:6"))

    # if dependency between vitesse and t_0 is not added, vitesse will be
    # at last position
    sorted_cmds = stage.sorted_commands
    names = ["{0.name}:{0.uid}".format(i) for i in sorted_cmds]
    assert_that(names, contains("vitesse:4", "t_0:5", "c1:6"))


def test_keywords_filtering():
    """Test for keywords filtering"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
mesh = LIRE_MAILLAGE()

mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_2D=_F(GROUP_MA='groupname')
)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""

    comm2study(text, stage)

    mesh = stage[0]
    kwds = stage[1].keywords_equal_to(mesh)
    assert_that(kwds, has_length(1))
    assert_that(kwds[0].name, equal_to('MAILLAGE'))
    assert_that(kwds[0].value, equal_to(mesh))

    kwds = stage[2].keywords_equal_to(mesh)
    assert_that(kwds, has_length(0))


#------------------------------------------------------------------------------
def test_export_none():
    """Test for export command with None values"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
func = DEFI_FONCTION(NOM_PARA='INST',
                     VALE=(0.0, 0.0, 1.0, 1.0))
"""

    func = stage('DEFI_FONCTION', 'func')
    func['VALE'] = (0., 0., 1., 1.)
    func['NOM_PARA'] = 'INST'

    assert(check_export(stage, text))

    # None values must not be exported
    func['NOM_RESU'] = None

    assert(check_export(stage, text))


def test_comment_deps():
    """Test for dependencies to comments"""
    text = \
"""
# read the mesh
mesh = LIRE_MAILLAGE(UNITE=20)
"""
    code = \
"""
command = stage2('_CONVERT_COMMENT')
command['EXPR'] = 'read the mesh'

previous = command
command = stage2('LIRE_MAILLAGE', 'mesh')
command['UNITE'] = 20
stage2.add_dependency(command, previous)
stage2.reorder()
"""

    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm2study(text, stage)

    text2 = study2code(stage, 'stage2')
    assert_that(check_text_eq(text2, code))


def test_variable_deps():
    """Test for dependencies between of variables"""
    text = \
"""
a = 1
b = a * 2
"""
    code = \
"""
command = stage2('_CONVERT_VARIABLE', 'a')
command['EXPR'] = '1'
command.update(expression='1')

command = stage2('_CONVERT_VARIABLE', 'b')
command['EXPR'] = 'a * 2'
stage2.add_dependency(command, stage2['a'])
command.update(expression='a * 2')
stage2.reorder()
"""

    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm2study(text, stage)

    text2 = study2code(stage, 'stage2')
    assert_that(check_text_eq(text2, code))

    stage2 = case.create_stage(':from_code:')
    exec(code)
    lvar = [cmd.name for cmd in stage2.commands]
    assert_that(lvar, has_length(2))
    assert_that(lvar, contains('a', 'b'))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
