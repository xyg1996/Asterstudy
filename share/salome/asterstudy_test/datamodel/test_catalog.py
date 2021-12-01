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

"""Automatic tests for commands catalog."""


from collections import defaultdict
import os
import os.path as osp
import unittest
import re
from hamcrest import *

from asterstudy.common import CFG
from asterstudy.datamodel.aster_syntax import IDS, get_cata_typeid, is_unit_valid
from asterstudy.datamodel.catalogs import CATA

from testutils import attr


def test_import_catalog():
    """Test for import of commands catalog"""
    # check catalogs container
    cata = CATA.get_catalog('LIRE_MAILLAGE')
    assert_that(get_cata_typeid(cata), equal_to(IDS.command))
    assert_that(cata.getCataTypeId(), equal_to(IDS.command))
    assert_that(cata.name, equal_to("LIRE_MAILLAGE"))
    assert_that("maillage", is_in(cata.udocstring))
    assert_that(cata.rules, empty())

def test_keyword_order():
    """Test for order of keywords in catalog"""
    cmd = CATA.get_catalog("DEBUT").keywords
    cataorder = ["PAR_LOT", "IMPR_MACRO", "BASE", "CATALOGUE", "CODE",
                 "ERREUR", "DEBUG", "MESURE_TEMPS", "MEMOIRE", "RESERVE_CPU",
                 "IGNORE_ALARM", "LANG", "INFO"]
    assert_that(list(cmd.keys()), equal_to(cataorder))

    base = cmd['BASE'].keywords
    cataorder = ["FICHIER", "TITRE", "CAS", "NMAX_ENRE", "LONG_ENRE",
                 "LONG_REPE", "TAILLE"]
    assert_that(list(base.keys()), equal_to(cataorder))

    cmd = CATA.get_catalog("DEFI_FONCTION").entities
    cataorder = ['NOM_PARA', 'NOM_RESU', 'VALE', 'ABSCISSE', 'VALE_C',
                 'VALE_PARA', 'b_vale_para', 'b_abscisse', 'NOEUD_PARA',
                 'b_noeud_para', 'INTERPOL', 'PROL_DROITE', 'PROL_GAUCHE',
                 'VERIF', 'INFO', 'TITRE']
    assert_that(list(cmd.keys()), equal_to(cataorder))
    cmd = CATA.get_catalog("DEFI_FONCTION").keywords
    cataorder = ['NOM_PARA', 'NOM_RESU', 'VALE', 'ABSCISSE', 'VALE_C',
                 'VALE_PARA', 'VALE_FONC', 'ORDONNEE', 'NOEUD_PARA',
                 'MAILLAGE', 'VALE_Y', 'INTERPOL', 'PROL_DROITE', 'PROL_GAUCHE',
                 'VERIF', 'INFO', 'TITRE']
    assert_that(list(cmd.keys()), equal_to(cataorder))

def test_catalog_utilities():
    """Test for catalog utilities"""
    from collections import OrderedDict
    utils = CATA.package("SyntaxUtils")
    dtest = OrderedDict([
        ('a', 1), ('b', None), ('c', [3, 4, 5]),
        ('d', {'u': None, 'v': 9}), ('e', object())
    ])

    # test mixedcopy
    dcopy = utils.mixedcopy(dtest)
    assert_that(dtest, has_length(5))
    assert_that(dcopy, has_length(5))
    assert_that(id(dcopy), is_not(equal_to(id(dtest))))
    assert_that(dcopy['b'], none())
    assert_that(id(dcopy['c']), is_not(equal_to(id(dtest['c']))))
    assert_that(dcopy['c'], has_length(3))
    assert_that(id(dcopy['d']), is_not(equal_to(id(dtest['d']))))
    assert_that(dcopy['d'], has_length(2))
    assert_that(id(dcopy['e']), equal_to(id(dtest['e'])))

    # test remove_none
    utils.remove_none(dcopy)
    assert_that(dcopy, has_length(4))
    assert_that(dcopy, is_not(has_item('b')))
    assert_that(dcopy['c'], has_length(3))
    assert_that(dcopy['d'], has_length(1))
    assert_that(dcopy, has_item('e'))

def test_catalog_1():
    """Test for catalog definition"""
    cmd = CATA.get_catalog('DEBUT')
    # with no keywords
    assert_that(cmd.checkMandatory({}, []), none())
    # with default keywords
    keywords = {}
    cmd.addDefaultKeywords(keywords)
    # simple keyword with a default value
    assert_that(keywords.get('INFO'), equal_to(1))
    # simple keyword without any default value with max=1
    assert_that(keywords.get('LANG'), none())
    # simple keyword without any default value with max > 1
    assert_that(keywords.get('IGNORE_ALARM'), none())
    # optional factor keyword
    assert_that(keywords.get('CODE'), none())
    # factor keyword present by default
    assert_that(keywords.get('MEMOIRE'), has_length(2))

    assert_that(cmd.checkMandatory(keywords, []), none())

    CH = CATA.package("SyntaxChecker")
    checker = CH.SyntaxCheckerVisitor()
    cmd.accept(checker, keywords)

def test_catalog_2():
    """Test for catalog definition"""
    cmd = CATA.get_catalog('DEBUT')
    # with an empty keywords, but with missing keywords
    keywords = {'CODE': {}}
    cmd.addDefaultKeywords(keywords)

    # simple keywords with a default value should be added
    assert_that(keywords.get('CODE'), has_length(0))
    assert_that(keywords.get('MEMOIRE'), has_length(2))

    # checkMandatory passes at the command level
    assert_that(cmd.checkMandatory(keywords, []), none())
    # checkMandatory should fail at the factor keyword level
    fact = cmd.definition['CODE']
    assert_that(calling(fact.checkMandatory).with_args(keywords['CODE'], []),
                raises(KeyError, "NIV_PUB_WEB is mandatory"))

    CH = CATA.package("SyntaxChecker")
    checker = CH.SyntaxCheckerVisitor()
    assert_that(calling(cmd.accept).with_args(checker, keywords),
                raises(KeyError))

def test_catalog_3():
    """Test catalog types"""
    assert_that(CATA.baseds, is_not(none()))
    assert_that(CATA.unitds, is_not(none()))

def test_translation():
    """Test for keywords translation"""
    # check for untranslated keywords
    assert_that(CATA.get_translation("DUMMY_CMD"), equal_to("DUMMY_CMD"))
    # check for common keywords (in GLOBAL_DICT)
    assert_that(CATA.get_translation("DUMMY_CMD", "UNITE"),
                equal_to("Filename"))
    # check for translation from catalog
    assert_that(CATA.get_translation("LIRE_MAILLAGE", "UNITE"),
                equal_to("Mesh file location"))
    assert_that(CATA.get_translation("LIRE_MAILLAGE", "ASTER"),
                equal_to("Aster"))

def test_datastructure():
    """Test for DataStructure types"""
    dsm = CATA.package("DataStructure")
    path = osp.join(CFG.installdir, "asterstudy", "code_aster_version",
                    "code_aster", "Cata")
    re_cmt = re.compile("^ *#.*$", re.M)
    text = []
    for root, dirs, files in os.walk(path):
        if osp.basename(root) not in ("Commands", "Commons"):
            continue
        for fname in files:
            if not fname.endswith(".py"):
                continue
            with open(osp.join(root, fname), "rb") as fobj:
                text.append(fobj.read().decode())

    cata = os.linesep.join(text)
    cata = re_cmt.sub("", cata)

    exceptions = ("PythonVariable", )
    types = [obj for obj in dsm.__dict__.values() \
             if type(obj) is type and issubclass(obj, dsm.ASSD)]
    notused = {}
    for typ in types:
        name = typ.__name__
        if name in exceptions:
            continue
        if name not in cata:
            notused[name] = typ

    expected = set(["dyna_gene", "dyna_phys", "fonction_class", "matr_asse_gd"])

    diff = expected.symmetric_difference(notused.keys())
    assert_that(diff, empty())

    def _hassubclass(typ):
        for obj in types:
            if obj is typ or type(obj) is not type:
                continue
            if issubclass(obj, typ):
                return True
        return False

    for typ in notused.values():
        assert_that(_hassubclass(typ), equal_to(True), typ)


def test_unit_validity():
    """Test for unit validity"""
    assert_that(is_unit_valid(-5), equal_to(False))
    assert_that(is_unit_valid(0), equal_to(False))
    assert_that(is_unit_valid(1), equal_to(False))
    assert_that(is_unit_valid(6), equal_to(False))
    assert_that(is_unit_valid(8), equal_to(True))
    assert_that(is_unit_valid(9), equal_to(True))
    assert_that(is_unit_valid(""), equal_to(False))
    assert_that(is_unit_valid(2), equal_to(True))
    assert_that(is_unit_valid(7), equal_to(True))
    assert_that(is_unit_valid("11"), equal_to(True))
    assert_that(is_unit_valid("+13"), equal_to(True))
    assert_that(is_unit_valid("-17"), equal_to(False))
    assert_that(is_unit_valid("none"), equal_to(False))


def test_url():
    """Test for documentations urls"""
    root = CFG.get("General", "doc_base_url")
    assert_that(CATA.get_command_url(u"MODI_MAILLAGE", root),
                equal_to(root + "v14/fr/man_u/u4/u4.23.04.pdf"))
    assert_that(CATA.get_command_url("EXEC_LOGICIEL", root),
                equal_to(root + "v14/fr/man_u/u7/u7.00.01.pdf"))
    # failover url
    assert_that(CATA.get_command_url("?/!§%$£", root),
                equal_to(root + "v14/fr/index.php?man=commande"))


def test_docstring():
    """Test for docstrings"""
    assert_that(CATA.get_command_docstring(u"LIRE_MAILLAGE"),
                equal_to("Crée un maillage par lecture d'un fichier"))


def test_get_types():
    """Test for get_all_types"""
    cmd = CATA.get_catalog('DEBUT')
    res = cmd.get_all_types()
    assert_that(res, has_length(1))
    assert_that(res, contains(None))

    DS = CATA.package("DataStructure")
    cmd = CATA.get_catalog('DEFI_FONCTION')
    res = cmd.get_all_types()
    assert_that(res, has_length(2))
    assert_that(res, contains_inanyorder(DS.fonction_sdaster, DS.fonction_c))

    cmd = CATA.get_catalog('ASSEMBLAGE')
    res = cmd.get_all_types()
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


def test_type2command():
    typ2cmd = CATA.type2command
    # there are 87 different types in v13
    assert_that(typ2cmd, has_length(greater_than(85)))
    assert_that(typ2cmd, has_length(less_than(100)))

    # check some types
    assert_that(typ2cmd, has_item("nappe_sdaster"))
    assert_that(typ2cmd, has_item("modele_sdaster"))
    assert_that(typ2cmd, has_item("fonction_c"))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
