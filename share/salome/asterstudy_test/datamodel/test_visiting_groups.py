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
from testutils import attr

from asterstudy.common import MeshGroupType
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.command.helper import (avail_groups_in_cmd,
                                                 avail_groups,
                                                 avail_groups_in_storage,
                                                 tout_usage,
                                                 tout_usage_in_cmd)
from asterstudy.datamodel.history import History
from asterstudy.datamodel.visit_study import GroupFilterVisitor

ELEMTYPE = MeshGroupType.GElement
NODETYPE = MeshGroupType.GNode
#------------------------------------------------------------------------------

def _test_setup():
    hist = History()
    cc = hist.current_case
    st = cc.create_stage('s1')
    text = """
MAIL=LIRE_MAILLAGE(FORMAT='MED',);

MATER=DEFI_MATERIAU(THER=_F(LAMBDA=54.6,
                        RHO_CP=3710000.0,),);

MODTH=AFFE_MODELE(MAILLAGE=MAIL,
              AFFE=_F(GROUP_MA=('VOLUME','BORD'),
                      PHENOMENE='THERMIQUE',
                      MODELISATION='3D',),);

CHMATER=AFFE_MATERIAU(MAILLAGE=MAIL,
                  AFFE=_F(GROUP_MA='VOLUME',
                          MATER=MATER,),);

CHARTH=AFFE_CHAR_THER(MODELE=MODTH,
                    TEMP_IMPO=(_F(GROUP_MA='SURFINT',
                                 TEMP=0.0,),
                               _F(GROUP_MA=('SURFEXT','BORD'),
                                 TEMP=1.0,),),
                    );
CHART =AFFE_CHAR_THER(MODELE=MODTH,
                  TEMP_IMPO=_F(GROUP_MA='GROUP1',
                               TEMP=0.0,),
                  LIAISON_UNIF=_F(GROUP_MA='GROUP2'),
                  );

CHARG =AFFE_CHAR_THER(MODELE=MODTH,
                  LIAISON_GROUP=_F(GROUP_MA_1='GROUP1',
                                   COEF_MULT_1=1.0,
                                   GROUP_MA_2='GROUP2',
                                   COEF_MULT_2=1.0,
                                   COEF_IMPO=0.0),
                  );
LINST=DEFI_LIST_REEL(VALE=(0,5,10,),);

F_MULT=DEFI_FONCTION(NOM_PARA='INST',VALE=(0,1,10,1,),);

TEMPE=THER_LINEAIRE(MODELE=MODTH,
                CHAM_MATER=CHMATER,
                EXCIT=_F(CHARGE=CHARTH,
                         FONC_MULT=F_MULT,),
                INCREMENT=_F(LIST_INST=LINST,),
                ETAT_INIT=_F(VALE=20,),);

MECA=LIRE_RESU(FORMAT='MED', UNITE=81, TYPE_RESU='EVOL_NOLI');

CHAMNO = CALC_PRESSION(MAILLAGE=MAIL,
                  RESULTAT=MECA,
                  GROUP_MA=('GROUP1', 'GROUP2'),
                  INST=10,
                  GEOMETRIE='INITIALE');

CHAMN  = CALC_PRESSION(MAILLAGE=MAIL,
                  RESULTAT=MECA,
                  GROUP_MA='GROUP',
                  INST=10,
                  GEOMETRIE='INITIALE');
"""
    comm2study(text, st)
    return st

def _test_setup_macro(dupl_co):
    # Inspired from fdlv102a and fdlv106a
    hist = History()
    cc = hist.current_case
    st = cc.create_stage('s1')
    text1 = """
MAIL=LIRE_MAILLAGE(FORMAT='MED',);

CHAMNO=CREA_CHAMP(TYPE_CHAM='NOEU_DEPL_R',
                  OPERATION='AFFE', PROL_ZERO='OUI',
                  MAILLAGE=MAIL,
                  AFFE=(
                  _F(TOUT='OUI',
                     NOM_CMP=('DX','DY','DZ',),
                     VALE=(0.,0.,0.,)
                     ),)
                  );

MACRO_MATR_AJOU(MAILLAGE=MAIL,
                GROUP_MA_FLUIDE='FLUIDE',
                GROUP_MA_INTERF='INTERFAC',
                MODELISATION='3D',
                FLUIDE=_F(RHO=1000.0,
                          TOUT='OUI'),
                DDL_IMPO=(_F(GROUP_NO='TEMPIMPO',
                             PRES_FLUIDE=0.0,),
                          _F(GROUP_NO='NOSORT',
                             PRES_SORTIE=0.0,),),
                ECOULEMENT=_F(GROUP_MA_1='ENTREE',
                              GROUP_MA_2='SORTIE',
                              VNOR_1=-4.0,
                              VNOR_2=4.0,),
                DEPL_IMPO=CHAMNO,
                MATR_MASS_AJOU=CO('MASSAJ'),
                MATR_RIGI_AJOU=CO('RIGIAJ'),
                MATR_AMOR_AJOU=CO('AMORAJ'),
                SOLVEUR=_F(METHODE='GCPC',),
                INFO=2,);

"""
    if dupl_co:
        text2 = """
MASTOT2=COMB_MATR_ASSE( COMB_R= (_F( MATR_ASSE = MASSAJ,
                                    COEF_R = 1.),
                                 _F( MATR_ASSE = RIGIAJ,
                                    COEF_R = 1.),
                                    ))
"""
    else:
        text2 = """
MASTOT2=COMB_MATR_ASSE( COMB_R= _F( MATR_ASSE = MASSAJ,
                                    COEF_R = 1.))
"""
    text = text1 + text2
    comm2study(text, st)
    return st

def _test_setup_tout():
    # Inspired from fdlv102a and fdlv106a
    hist = History()
    cc = hist.current_case
    st = cc.create_stage('s1')
    text = """
MAIL=LIRE_MAILLAGE(FORMAT='MED',);

MATER=DEFI_MATERIAU(THER=_F(LAMBDA=54.6,
                        RHO_CP=3710000.0,),);

MODTH=AFFE_MODELE(MAILLAGE=MAIL,
              AFFE=_F(TOUT='OUI',
                      PHENOMENE='THERMIQUE',
                      MODELISATION='3D',),);

CHMATER=AFFE_MATERIAU(MAILLAGE=MAIL,
                  AFFE=_F(TOUT='OUI',
                          MATER=MATER,),);

CHARTH=AFFE_CHAR_THER(MODELE=MODTH,
                    TEMP_IMPO=(_F(GROUP_MA='SURFINT',
                                 TEMP=0.0,),
                               _F(GROUP_MA=('SURFEXT','BORD'),
                                 TEMP=1.0,),),
                    );
LINST=DEFI_LIST_REEL(VALE=(0,5,10,),);

F_MULT=DEFI_FONCTION(NOM_PARA='INST',VALE=(0,1,10,1,),);

TEMPE=THER_LINEAIRE(MODELE=MODTH,
                CHAM_MATER=CHMATER,
                EXCIT=_F(CHARGE=CHARTH,
                         FONC_MULT=F_MULT,),
                INCREMENT=_F(LIST_INST=LINST,),
                ETAT_INIT=_F(VALE=20,),);
    """
    comm2study(text, st)
    return st

def _test_setup_comportement(is_tout):
    # Inspired from ssnp170k
    hist = History()
    cc = hist.current_case
    st = cc.create_stage('s1')
    text1 = """
lisi=DEFI_LIST_REEL(DEBUT=0,
                    INTERVALLE=_F(JUSQU_A=1,
                                  PAS=1,),);
LINST=DEFI_LIST_INST(DEFI_LIST=_F(LIST_INST=lisi,),);

RAMPE=DEFI_FONCTION(NOM_PARA='INST',VALE=(0,0,1,1),);

Mail=LIRE_MAILLAGE(UNITE=20,
                   FORMAT='MED',);

mat1=DEFI_MATERIAU(ELAS=_F(E=2000,
                           NU=0.3,),);

MODI=AFFE_MODELE(MAILLAGE=Mail,
                    AFFE=_F(TOUT='OUI',
                         PHENOMENE='MECANIQUE',
                         MODELISATION='3D',),);

AFFE=AFFE_MATERIAU(MAILLAGE=Mail,
                   MODELE=MODI,
                   AFFE=_F(TOUT='OUI',
                           MATER=mat1,),);

CHAR2= AFFE_CHAR_MECA(MODELE=MODI,
                             PRES_REP=_F(GROUP_MA='Group_4',
                             PRES=25,), );
"""
    if is_tout:
        text2 = """

RES=STAT_NON_LINE(MODELE=MODI,
                  CHAM_MATER=AFFE,
                  EXCIT=_F(CHARGE=CHAR2,
                           FONC_MULT=RAMPE,
                          ),
                  NEWTON=_F(MATRICE='TANGENTE',
                            REAC_ITER=1,),
                  COMPORTEMENT=_F(RELATION='ELAS',
                                  DEFORMATION='PETIT',
                                  TOUT='OUI',),
                  INCREMENT=_F(LIST_INST=LINST,),
                  CONVERGENCE=_F(RESI_GLOB_RELA=1.E-6,
                                 ITER_GLOB_MAXI=50,));
"""

    else:
        text2 = """

RES=STAT_NON_LINE(MODELE=MODI,
                  CHAM_MATER=AFFE,
                  EXCIT=_F(CHARGE=CHAR2,
                           FONC_MULT=RAMPE,
                          ),
                  NEWTON=_F(MATRICE='TANGENTE',
                            REAC_ITER=1,),
                  COMPORTEMENT=_F(RELATION='ELAS',
                                  DEFORMATION='PETIT',
                                  GROUP_MA='AGROUP',),
                  INCREMENT=_F(LIST_INST=LINST,),
                  CONVERGENCE=_F(RESI_GLOB_RELA=1.E-6,
                                 ITER_GLOB_MAXI=50,));
"""
    text = text1 + text2
    comm2study(text, st)
    return st

def _test_setup_calc_modes():
    # Inspired from forma02b
    hist = History()
    cc = hist.current_case
    st = cc.create_stage('s1')
    text = """
MAIL=LIRE_MAILLAGE(FORMAT='MED',);

MODELE=AFFE_MODELE(MAILLAGE=MAIL,
                   AFFE=_F(TOUT='OUI',
                           PHENOMENE='MECANIQUE',
                           MODELISATION='3D',),);

MAT=DEFI_MATERIAU(ELAS=_F(E=204000000000.0,
                          NU=0.3,
                          RHO=7800.0,),);

CHMAT=AFFE_MATERIAU(MAILLAGE=MAIL,
                    AFFE=_F(GROUP_MA='AGROUP',
                            MATER=MAT,),);

BLOCAGE=AFFE_CHAR_MECA(MODELE=MODELE,
                       DDL_IMPO=_F(GROUP_MA='BASE',
                                   DX=0.0,
                                   DY=0.0,
                                   DZ=0.0,),);

ASSEMBLAGE(MODELE=MODELE,
                CHAM_MATER=CHMAT,
                CHARGE=BLOCAGE,
                NUME_DDL=CO('NUMEDDL'),
                MATR_ASSE=(_F(MATRICE=CO('RIGIDITE'),
                              OPTION='RIGI_MECA',),
                           _F(MATRICE=CO('MASSE'),
                              OPTION='MASS_MECA',),),);

MODES=CALC_MODES(MATR_RIGI=RIGIDITE,
                 OPTION='PLUS_PETITE',
                 CALC_FREQ=_F(NMAX_FREQ=10,
                              ),
                 MATR_MASS=MASSE,
                 )
"""
    comm2study(text, st)
    return st

def _test_setup_issue_28896():
    # Inspired from forma02b
    hist = History()
    cc = hist.current_case
    st = cc.create_stage('s1')
    text = """
MAIL=LIRE_MAILLAGE(FORMAT='MED',);

MODELE=AFFE_MODELE(MAILLAGE=MAIL,
                   AFFE=_F(TOUT='OUI',
                           PHENOMENE='MECANIQUE',
                           MODELISATION='3D',),);

MAT=DEFI_MATERIAU(ELAS=_F(E=204000000000.0,
                          NU=0.3,
                          RHO=7800.0,),);

CHMAT=AFFE_MATERIAU(MAILLAGE=MAIL,
                    AFFE=_F(GROUP_MA='AGROUP',
                            MATER=MAT,),);

BLOCAGE=AFFE_CHAR_MECA(MODELE=MODELE,
                       DDL_IMPO=_F(GROUP_MA='BASE',
                                   DX=0.0,
                                   DY=0.0,
                                   DZ=0.0,),);

ASSEMBLAGE(MODELE=MODELE,
                CHAM_MATER=CHMAT,
                CHARGE=BLOCAGE,
                NUME_DDL=CO('NUMEDDL'),
                MATR_ASSE=(_F(MATRICE=CO('RIGIDITE'),
                              OPTION='RIGI_MECA',),
                           _F(MATRICE=CO('MASSE'),
                              OPTION='MASS_MECA',),),);

MODES=CALC_MODES(MATR_RIGI=RIGIDITE,
                 OPTION='PLUS_PETITE',
                 CALC_FREQ=_F(NMAX_FREQ=10,
                              ),
                 MATR_MASS=MASSE,
                 )
PROJ_BASE(BASE=MODES, 
          MATR_ASSE_GENE=(_F(MATRICE=CO('MASPRO'), 
                             MATR_ASSE=MASSE), 
                          _F(MATRICE=CO('RIPRO'), 
                             MATR_ASSE=RIGIDITE)), 
          ) 
DTM = DYNA_VIBRA(BASE_CALCUL='GENE', 
                 INCREMENT=_F(INST_FIN=1.0, 
                              PAS=1.0), 
                 MATR_MASS=MASPRO, 
                 MATR_RIGI=RIPRO, 
                 SCHEMA_TEMPS=_F(SCHEMA='DIFF_CENTRE'), 
                 TYPE_CALCUL='TRAN')
"""
    comm2study(text, st)
    return st

def test_group_visitor_command():
    st = _test_setup()

    # Test command visitor on first level GROUP_MA
    cmd = st['CHAMN']
    res = avail_groups_in_cmd(cmd)
    assert_that(res, equal_to({".CALC_PRESSION.GROUP_MA": (ELEMTYPE,
                                                           ["GROUP"],
                                                           {"MAILLAGE": st["MAIL"],
                                                            "RESULTAT": st["MECA"],
                                                            "INST": 10,
                                                            "GEOMETRIE": "INITIALE"})}))

    # Test command visitor on first level list of GROUP_MA
    cmd = st['CHAMNO']
    res = avail_groups_in_cmd(cmd)
    assert_that(res, equal_to({".CALC_PRESSION.GROUP_MA": (ELEMTYPE,
                                                           ["GROUP1", "GROUP2"],
                                                           {"MAILLAGE": st["MAIL"],
                                                            "RESULTAT": st["MECA"],
                                                            "INST": 10,
                                                            "GEOMETRIE": "INITIALE"})}))
    # Test command visitor in single factor for a GROUP_MA
    cmd = st['CHMATER']
    res = avail_groups_in_cmd(cmd)
    assert_that(res, equal_to({".AFFE_MATERIAU.AFFE.GROUP_MA": (ELEMTYPE,
                                                                ["VOLUME"],
                                                                {"MATER": st["MATER"]})}))

    # Test command visitor in single factor for a list of GROUP_MA
    cmd = st['MODTH']
    res = avail_groups_in_cmd(cmd)
    assert_that(res, equal_to({".AFFE_MODELE.AFFE.GROUP_MA": (ELEMTYPE,
                                                              ["VOLUME", "BORD"],
                                                              {"PHENOMENE": 'THERMIQUE',
                                                               "MODELISATION": '3D'})}))

    # Test command visitor in factor list for a GROUP_MA and a list of GROUP_MA
    cmd = st['CHARTH']
    res = avail_groups_in_cmd(cmd)
    assert_that(res, equal_to({".AFFE_CHAR_THER.TEMP_IMPO.0.GROUP_MA": (ELEMTYPE,
                                                                        ["SURFINT"],
                                                                        {"TEMP": 0.0}),
                               ".AFFE_CHAR_THER.TEMP_IMPO.1.GROUP_MA": (ELEMTYPE,
                                                                        ["SURFEXT", "BORD"],
                                                                        {"TEMP": 1.0})}))

    # Test command visitor in command with several factors
    cmd = st['CHART']
    res = avail_groups_in_cmd(cmd)
    assert_that(res, equal_to({".AFFE_CHAR_THER.TEMP_IMPO.GROUP_MA": (ELEMTYPE,
                                                                      ["GROUP1"],
                                                                      {"TEMP": 0.0}),
                               ".AFFE_CHAR_THER.LIAISON_UNIF.GROUP_MA": (ELEMTYPE,
                                                                         ["GROUP2"],
                                                                         {})}))

    # Test command visitor in command with GROUP_MA_1 and 2 in the same factor
    cmd = st['CHARG']
    res = avail_groups_in_cmd(cmd)

    # TODO: COEF_MULT_2 should no longer appear in the first case,
    #       neither should COEF_MULT_1 in the second one.
    assert_that(res, equal_to({".AFFE_CHAR_THER.LIAISON_GROUP.GROUP_MA_1": (ELEMTYPE,
                                                                            ["GROUP1"],
                                                                            {"COEF_MULT_1": 1.0,
                                                                             "COEF_MULT_2": 1.0,
                                                                             "COEF_IMPO": 0.0}),
                               ".AFFE_CHAR_THER.LIAISON_GROUP.GROUP_MA_2": (ELEMTYPE,
                                                                            ["GROUP2"],
                                                                            {"COEF_MULT_1": 1.0,
                                                                             "COEF_MULT_2": 1.0,
                                                                             "COEF_IMPO": 0.0})}))

def test_group_visitor_stage():
    st = _test_setup()
    # test usage of GROUP1
    res = st.group_usage('GROUP1')
    assert_that(set(res), equal_to({".AFFE_CHAR_THER.LIAISON_GROUP.GROUP_MA_1",
                                    ".AFFE_CHAR_THER.TEMP_IMPO.GROUP_MA",
                                    ".CALC_PRESSION.GROUP_MA"}))

    # test usage of BORD
    res = st.group_usage('BORD')
    assert_that(set(res), equal_to({".AFFE_MODELE.AFFE.GROUP_MA", ".AFFE_CHAR_THER.TEMP_IMPO.1.GROUP_MA"}))

    # test usage of GROUP
    res = st.group_usage('GROUP')
    assert_that(res, equal_to([".CALC_PRESSION.GROUP_MA"]))

    assert_that(GroupFilterVisitor._is_group('blabla'), equal_to(False))

def test_groups_in_analysis():
    """Test retrieving used groups at level <= 1 for an analysis"""
    st = _test_setup()

    # Test command visitor on first level GROUP_MA
    cmd = st['TEMPE']
    res = avail_groups(cmd.storage, "THER_LINEAIRE")
    assert_that(res, equal_to({".AFFE_CHAR_THER.TEMP_IMPO.0.GROUP_MA": (ELEMTYPE,
                                                                        ["SURFINT"],
                                                                        {"TEMP": 0.0}),
                               ".AFFE_CHAR_THER.TEMP_IMPO.1.GROUP_MA": (ELEMTYPE,
                                                                        ["SURFEXT", "BORD"],
                                                                        {"TEMP": 1.0}),
                               ".AFFE_MATERIAU.AFFE.GROUP_MA": (ELEMTYPE,
                                                                ["VOLUME"],
                                                                {"MATER": st["MATER"]}),
                               ".AFFE_MODELE.AFFE.GROUP_MA": (ELEMTYPE,
                                                              ["VOLUME", "BORD"],
                                                              {"PHENOMENE": 'THERMIQUE',
                                                               "MODELISATION": '3D'})}))


def test_duplicated_paths():
    h = History()
    st = h.current_case.create_stage()
    ch1 = st.add_command('AFFE_CHAR_THER', 'ch1')
    ch1.init(dict(TEMP_IMPO=(dict(GROUP_MA='SURFINT'), dict(GROUP_MA=('SURFEXT', 'BORD')))))
    ch2 = st.add_command('AFFE_CHAR_THER', 'ch2')
    ch2.init(dict(TEMP_IMPO=(dict(GROUP_MA='GROUP1'), dict(GROUP_MA='GROUP2'))))
    tempe = st.add_command('THER_LINEAIRE', 'tempe')
    tempe.init(dict(EXCIT=(dict(CHARGE=ch1),dict(CHARGE=ch2))))
    groups_dict = avail_groups(tempe.storage_nocopy, "THER_LINEAIRE")
    assert_that(groups_dict, has_length(4))

def test_3_duplicated_paths():
    h = History()
    st = h.current_case.create_stage()
    ch1 = st.add_command('AFFE_CHAR_THER', 'ch1')
    ch1.init(dict(TEMP_IMPO=(dict(GROUP_MA='SURFINT'), dict(GROUP_MA=('SURFEXT', 'BORD')))))
    ch2 = st.add_command('AFFE_CHAR_THER', 'ch2')
    ch2.init(dict(TEMP_IMPO=(dict(GROUP_MA='GROUP1'), dict(GROUP_MA='GROUP2'))))
    ch3 = st.add_command('AFFE_CHAR_THER', 'ch3')
    ch3.init(dict(TEMP_IMPO=(dict(GROUP_MA='GROUP3'), dict(GROUP_MA='GROUP4'))))
    tempe = st.add_command('THER_LINEAIRE', 'tempe')
    tempe.init(dict(EXCIT=(dict(CHARGE=ch1),dict(CHARGE=ch2),dict(CHARGE=ch3))))
    groups_dict = avail_groups(tempe.storage_nocopy, "THER_LINEAIRE")
    assert_that(groups_dict, has_length(6))
    assert_that(".AFFE_CHAR_THER.0.TEMP_IMPO.0.GROUP_MA", is_in(groups_dict))
    assert_that(".AFFE_CHAR_THER.1.TEMP_IMPO.0.GROUP_MA", is_in(groups_dict))
    assert_that(".AFFE_CHAR_THER.2.TEMP_IMPO.0.GROUP_MA", is_in(groups_dict))
    assert_that(".AFFE_CHAR_THER.TEMP_IMPO.0.GROUP_MA", is_not(is_in(groups_dict)))

def test_group_search_storage():
    """Test search group for not yet commited dictionary"""

    # Strictly identical to `test_group_visitor_command`, except that we search from
    # dictionary instead of constituted *Command* object.
    st = _test_setup()

    # Test command visitor on first level GROUP_MA
    stg = st['CHAMN'].storage_nocopy
    res = avail_groups_in_storage(stg, "CALC_PRESSION")
    assert_that(res, equal_to({".CALC_PRESSION.GROUP_MA": (ELEMTYPE,
                                                           ["GROUP"],
                                                           {"MAILLAGE": st["MAIL"],
                                                            "RESULTAT": st["MECA"],
                                                            "INST": 10,
                                                            "GEOMETRIE": "INITIALE"})}))

    # Test command visitor on first level list of GROUP_MA
    stg = st['CHAMNO'].storage_nocopy
    res = avail_groups_in_storage(stg, "CALC_PRESSION")
    assert_that(res, equal_to({".CALC_PRESSION.GROUP_MA": (ELEMTYPE,
                                                           ["GROUP1", "GROUP2"],
                                                           {"MAILLAGE": st["MAIL"],
                                                            "RESULTAT": st["MECA"],
                                                            "INST": 10,
                                                            "GEOMETRIE": "INITIALE"})}))

    # Test command visitor in single factor for a GROUP_MA
    stg = st['CHMATER'].storage_nocopy
    res = avail_groups_in_storage(stg, "AFFE_MATERIAU")
    assert_that(res, equal_to({".AFFE_MATERIAU.AFFE.GROUP_MA": (ELEMTYPE,
                                                                ["VOLUME"],
                                                                {"MATER": st["MATER"]})}))

    # Test command visitor in single factor for a list of GROUP_MA
    stg = st['MODTH'].storage_nocopy
    res = avail_groups_in_storage(stg, "AFFE_MODELE")
    assert_that(res, equal_to({".AFFE_MODELE.AFFE.GROUP_MA": (ELEMTYPE,
                                                              ["VOLUME", "BORD"],
                                                              {"PHENOMENE": 'THERMIQUE',
                                                               "MODELISATION": '3D'})}))

    # Test command visitor in factor list for a GROUP_MA and a list of GROUP_MA
    stg = st['CHARTH'].storage_nocopy
    res = avail_groups_in_storage(stg, "AFFE_CHAR_THER")
    assert_that(res, equal_to({".AFFE_CHAR_THER.TEMP_IMPO.0.GROUP_MA": (ELEMTYPE,
                                                                        ["SURFINT"],
                                                                        {"TEMP": 0.0}),
                               ".AFFE_CHAR_THER.TEMP_IMPO.1.GROUP_MA": (ELEMTYPE,
                                                                        ["SURFEXT", "BORD"],
                                                                        {"TEMP": 1.0})}))

    # Test command visitor in command with several factors
    stg = st['CHART'].storage_nocopy
    res = avail_groups_in_storage(stg, "AFFE_CHAR_THER")
    assert_that(res, equal_to({".AFFE_CHAR_THER.TEMP_IMPO.GROUP_MA": (ELEMTYPE,
                                                                      ["GROUP1"],
                                                                      {"TEMP": 0.0}),
                               ".AFFE_CHAR_THER.LIAISON_UNIF.GROUP_MA": (ELEMTYPE,
                                                                         ["GROUP2"],
                                                                         {})}))

    # Test command visitor in command with GROUP_MA_1 and 2 in the same factor
    # TODO: COEF_MULT_2 should no longer appear in the first case,
    #       neither should COEF_MULT_1 in the second one.
    stg = st['CHARG'].storage_nocopy
    res = avail_groups_in_storage(stg, "AFFE_CHAR_THER")
    assert_that(res, equal_to({".AFFE_CHAR_THER.LIAISON_GROUP.GROUP_MA_1": (ELEMTYPE,
                                                                            ["GROUP1"],
                                                                            {"COEF_MULT_1": 1.0,
                                                                             "COEF_MULT_2": 1.0,
                                                                             "COEF_IMPO": 0.0}),
                               ".AFFE_CHAR_THER.LIAISON_GROUP.GROUP_MA_2": (ELEMTYPE,
                                                                            ["GROUP2"],
                                                                            {"COEF_MULT_1": 1.0,
                                                                             "COEF_MULT_2": 1.0,
                                                                             "COEF_IMPO": 0.0})}))

def test_group_search_hidden():
    """Test avail groups with a macro"""
    _test_group_search_hidden(False)

def _test_group_search_hidden(dupl_co):
    st = _test_setup_macro(dupl_co)

    # Test command visitor on first level GROUP_MA
    # For first level keywords: display only input *Simple* values
    #    (i.e. output CO Simple objs are discarded, Factor objs discarded as well)
    cmd = st['MASTOT2']
    res = avail_groups(cmd.storage, "COMB_MATR_ASSE")
    assert_that(res, equal_to({".MACRO_MATR_AJOU.GROUP_MA_FLUIDE": (ELEMTYPE,
                                                                    ["FLUIDE"],
                                                                    {"MODELISATION": "3D",
                                                                     "MAILLAGE": st["MAIL"],
                                                                     "DEPL_IMPO": st["CHAMNO"],
                                                                     "INFO": 2}),
                               ".MACRO_MATR_AJOU.GROUP_MA_INTERF": (ELEMTYPE,
                                                                    ["INTERFAC"],
                                                                    {"MODELISATION": "3D",
                                                                     "MAILLAGE": st["MAIL"],
                                                                     "DEPL_IMPO": st["CHAMNO"],
                                                                     "INFO": 2}
                                                                    ),
                               ".MACRO_MATR_AJOU.DDL_IMPO.0.GROUP_NO": (NODETYPE,
                                                                        ["TEMPIMPO"],
                                                                        {"PRES_FLUIDE": 0.0}),
                               ".MACRO_MATR_AJOU.DDL_IMPO.1.GROUP_NO": (NODETYPE,
                                                                        ["NOSORT"],
                                                                        {"PRES_SORTIE": 0.0}),
                               ".MACRO_MATR_AJOU.ECOULEMENT.GROUP_MA_1": (ELEMTYPE,
                                                                          ["ENTREE"],
                                                                          {"VNOR_1": -4.0,
                                                                           "VNOR_2": 4.0}),
                               ".MACRO_MATR_AJOU.ECOULEMENT.GROUP_MA_2": (ELEMTYPE,
                                                                          ["SORTIE"],
                                                                          {"VNOR_1": -4.0,
                                                                           "VNOR_2": 4.0}),}))

def test_search_tout_hidden():
    """Search use of TOUT='OUI' through macro"""
    # First with no duplicated concept
    st = _test_setup_macro(False)
    cmd = st['MASTOT2']
    res = tout_usage(cmd.storage, "COMB_MATR_ASSE")
    assert_that(res, equal_to({'.MACRO_MATR_AJOU.FLUIDE.TOUT': {'RHO': 1000.0}}))

    # Then with duplicated concept
    st = _test_setup_macro(True)
    cmd = st['MASTOT2']
    res = tout_usage(cmd.storage, "COMB_MATR_ASSE")
    assert_that(res, equal_to({'.MACRO_MATR_AJOU.FLUIDE.TOUT': {'RHO': 1000.0}}))


def test_search_duplicated_hidden():
    """Search with macro that outputs two concepts used"""
    # Results should be displayed only one
    _test_group_search_hidden(True)

def test_search_tout():
    """Test searching TOUT='OUI' in command"""
    st =  _test_setup_tout()

    # Test command visitor in single factor for a GROUP_MA
    cmd = st['CHMATER']
    res = tout_usage_in_cmd(cmd)
    assert_that(res, equal_to({".AFFE_MATERIAU.AFFE.TOUT": {"MATER": st["MATER"]}}))

    # Test command visitor in single factor for a list of GROUP_MA
    cmd = st['MODTH']
    res = tout_usage_in_cmd(cmd)
    assert_that(res, equal_to({".AFFE_MODELE.AFFE.TOUT": {"PHENOMENE": 'THERMIQUE',
                                                          "MODELISATION": '3D'}}))

    # Test tout_usage
    cmd = st['TEMPE']
    res = tout_usage(cmd.storage, "THER_LINEAIRE")
    assert_that(res, equal_to({".AFFE_MATERIAU.AFFE.TOUT": {"MATER": st["MATER"]},
                               ".AFFE_MODELE.AFFE.TOUT": {"PHENOMENE": 'THERMIQUE',
                                                          "MODELISATION": '3D'}}))

def test_groups_in_analysis_level_0():
    """Test that `avail_groups` also takes level 0 group usage"""
    # Example with comportement
    st = _test_setup_comportement(False)
    cmd = st['RES']
    res = avail_groups(cmd.storage, "STAT_NON_LINE")
    assert_that(".STAT_NON_LINE.COMPORTEMENT.GROUP_MA", is_in(res.keys()))
    assert_that(res[".STAT_NON_LINE.COMPORTEMENT.GROUP_MA"], equal_to((ELEMTYPE,
                                                                       ["AGROUP"],
                                                                       {"RELATION": "ELAS",
                                                                       "DEFORMATION": "PETIT"})))

def test_tout_in_analysis_level_0():
    """Test that `tout_usage` also takes level 0 group usage"""
    # Example with comportement
    st = _test_setup_comportement(True)
    cmd = st['RES']
    res = tout_usage(cmd.storage, "STAT_NON_LINE")
    assert_that(".STAT_NON_LINE.COMPORTEMENT.TOUT", is_in(res.keys()))
    assert_that(res[".STAT_NON_LINE.COMPORTEMENT.TOUT"], equal_to({"RELATION": "ELAS",
                                                                   "DEFORMATION": "PETIT"}))

def test_groups_one_level_more():
    """Test `avail_groups` for special commands requiring to go up one level more"""
    st = _test_setup_calc_modes()

    # Check that testing CALC_MODES would yield the same level 1 results as ASSEMBLAGE
    cmd = st['MODES']
    res = avail_groups(cmd.storage, "CALC_MODES")
    assert_that(res, equal_to({".AFFE_CHAR_MECA.DDL_IMPO.GROUP_MA": (ELEMTYPE,
                                                                     ['BASE'],
                                                                     {'DX': 0.0, 'DY': 0.0, 'DZ': 0.0}),
                               ".AFFE_MATERIAU.AFFE.GROUP_MA": (ELEMTYPE,
                                                                ['AGROUP'],
                                                                {"MATER": st['MAT']})}))
    res = tout_usage(cmd.storage, "CALC_MODES")
    assert_that(res, equal_to({".AFFE_MODELE.AFFE.TOUT": {"PHENOMENE": 'MECANIQUE',
                                                          "MODELISATION": '3D'}}))


def test_cover():
    # because the failure can not be reproduced with CALC_MODES...
    from asterstudy.datamodel.visit_study import filter_groups
    assert_that(filter_groups("DEBUT.TOUT"), equal_to(False))

def test_issue_28896():
    """Recursive test `avail_groups` for special commands requiring additional levels"""
    st = _test_setup_issue_28896()
    # Check that testing CALC_MODES would yield the same level 1 results as ASSEMBLAGE
    cmd = st['DTM']
    res = avail_groups(cmd.storage, "DYNA_VIBRA")
    assert_that(res, equal_to({".AFFE_CHAR_MECA.DDL_IMPO.GROUP_MA": (ELEMTYPE,
                                                                     ['BASE'],
                                                                     {'DX': 0.0, 'DY': 0.0, 'DZ': 0.0}),
                               ".AFFE_MATERIAU.AFFE.GROUP_MA": (ELEMTYPE,
                                                                ['AGROUP'],
                                                                {"MATER": st['MAT']})}))
    res = tout_usage(cmd.storage, "CALC_MODES")
    assert_that(res, equal_to({".AFFE_MODELE.AFFE.TOUT": {"PHENOMENE": 'MECANIQUE',
                                                          "MODELISATION": '3D'}}))



if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
