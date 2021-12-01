# coding=utf-8

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

"""Unittests that **MUST** not be run with concurrency."""
# 'code_aster' package is global and must not be changed by a new History.


import os
import os.path as osp
import unittest
from contextlib import contextmanager
from tempfile import mkstemp

from asterstudy.common import CFG, CatalogError, ConversionError, VersionError
from asterstudy.common.decoder import Decoder
from asterstudy.datamodel.case import Case
from asterstudy.datamodel.catalogs import CATA
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.history import History
from hamcrest import *
from testutils import attr


@attr(skip_on_install=CFG.is_installed)
@unittest.skipIf(CFG.is_installed, "can't be run on install")
def test_history_catalog():
    """Test for catalog's version for History"""
    history = History()
    assert_that(history.version, equal_to("stable"))
    # versions equal to the last read
    assert_that(history.version, equal_to(CATA.version))
    assert_that(history.version_number, equal_to(CATA.version_number))
    lib_aster = CFG.get('Versions', "stable")
    expected = osp.normpath(osp.join(lib_aster, '..', '..',
                                     'share', 'aster', 'tests'))
    assert_that(history.tests_path, equal_to(expected))
    # version_number is a tuple of 3 integers
    assert_that(type(history.version_number), equal_to(tuple))
    assert_that(history.version_number, has_length(3))
    assert_that(type(history.version_number[0]), equal_to(int))
    assert_that(type(history.version_number[1]), equal_to(int))
    assert_that(type(history.version_number[2]), equal_to(int))

    assert_that(history.support.command_ids, equal_to(True))
    assert_that(history.support.parametric, equal_to(True))
    assert_that(history.support.all_types, equal_to(True))
    assert_that(history.support.formula_deps, equal_to(True))

    # unregister attached catalog
    History.reset_catalog()

    history2 = History("fake")
    assert_that(history2.version, equal_to("fake"))
    # versions equal to the last read
    assert_that(history2.version, equal_to(CATA.version))
    assert_that(history2.version_number, equal_to(CATA.version_number))

    assert_that(calling(History).with_args("aaa"),
                raises(CatalogError))

    # unregister attached catalog
    History.reset_catalog()

    history4 = History("stable")
    assert_that(history4.version, equal_to("stable"))
    # versions equal to the last read
    assert_that(history4.version, equal_to(CATA.version))
    assert_that(history4.version_number, equal_to(CATA.version_number))


def test_history_load():
    """Test for loading history with failovers"""
    # myfunc = DEFI_FONCTION(NOM_PARA='ABSC', VALE=(0.0, 0.0, 1.0, 10.0))
    # IMPR_FONCTION(COURBE=_F(FONCTION=myfunc), FORMAT='TABLEAU', UNITE=10)
    infile = osp.join(os.getenv('ASTERSTUDYDIR'), 'data',
                      'export', 'fixable_command.ajs')

    # Reproduce what does `Study._load_ajs()`
    args = {}
    # version error
    History.reset_catalog()
    assert_that(calling(History.load).with_args(infile, **args),
                raises(CatalogError))

    # try with default version
    args['aster_version'] = CFG.default_version
    # versions numbers mismatch
    History.reset_catalog()
    assert_that(calling(History.load).with_args(infile, **args),
                raises(VersionError, "study was created using"))

    # try without the Restore flag
    args['strict'] = ConversionLevel.Syntaxic
    # just works: 1 stage, 2 commands
    History.reset_catalog()
    hist1 = History.load(infile, **args)
    assert_that(hist1.current_case, has_length(1))
    assert_that(hist1.current_case[0], has_length(2))

    # but if there was a syntaxic error in the second command
    with open(infile) as inajs:
        jstext = inajs.read().replace("COURBE", "REPETABLE")
        jstext = jstext.replace("myfunc =", "DEBUT()\\n\\nmyfunc =")

    fname = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]
    with open(fname, 'w') as ajs:
        ajs.write(jstext)

    # ConversionError
    History.reset_catalog()
    assert_that(calling(History.load).with_args(fname, **args),
                raises(ConversionError, "COURBE.*mandatory"))

    # allow partial conversion
    args['strict'] = ConversionLevel.Partial
    # should work: 2 stages, first in graphical mode, second in text mode
    History.reset_catalog()
    hist2 = History.load(fname, **args)
    assert_that(hist2.nb_cases, equal_to(1))
    case = hist2.current_case
    assert_that(case, has_length(2))
    assert_that(case[0].is_graphical_mode(), equal_to(True))
    assert_that(case[1].is_graphical_mode(), equal_to(False))

    # TODO last command not completed? to be removed?
    # + adding NotImplementedError add an offset: +1 to next eoi?
    assert_that(case[0], has_length(2))

    # force to load without error in text mode
    args['strict'] = ConversionLevel.NoGraphical
    # should work: only one stage in text mode
    History.reset_catalog()
    hist3 = History.load(fname, **args)
    assert_that(hist3.nb_cases, equal_to(1))
    case = hist3.current_case
    assert_that(case, has_length(1))
    assert_that(case[0].is_text_mode(), equal_to(True))

    os.remove(fname)


def test_generated_names():
    """Test for different naming systems"""
    history = History()
    case = history.current_case

    class TestCommand:
        safe_type = lambda x: "fake"
        title = "COMMAND"

    cmd = TestCommand()

    assert_that(case.naming_system, equal_to(Case.autoNaming))
    assert_that(case.generate_name(cmd), equal_to("unnamed"))
    for i in range(1000):
        idx = str(i)
        size = 8 - len(idx)
        assert_that(case.generate_name(cmd), equal_to("unnamed"[:size] + idx))

    assert_that(case.generate_name(cmd), equal_to("unnamed_XXX"))

    case.use_basic_naming()
    assert_that(case.generate_name(cmd), equal_to("COMMAND"))

    # naming system is shared by all cases
    other = history.create_case()
    assert_that(other.naming_system, equal_to(Case.basicNaming))
    assert_that(other.generate_name(cmd), equal_to("COMMAND"))
    assert_that(other.generate_name(cmd), equal_to("COMMAND"))

    other.use_default_naming()
    assert_that(other.naming_system, equal_to(Case.autoNaming))

    assert_that(other.generate_name(cmd), equal_to("unnamed"))
    assert_that(other.generate_name(cmd), equal_to("unnamed0"))

    import os
    os.environ["ASTERSTUDY_NAMING"] = "basic"

    assert_that(other.naming_system, equal_to(Case.autoNaming))
    another = history.create_case()
    assert_that(another.naming_system, equal_to(Case.basicNaming))

    # restore default naming for following tests
    del os.environ["ASTERSTUDY_NAMING"]
    another.use_default_naming()


def test_gui():
    # just to avoid an empty report when checking 'gui' package only
    import asterstudy.gui


def test_decoder_failover():
    @contextmanager
    def using_wrong_decoder():
        """Define a unusable decoder."""
        orig = Decoder.SubDecoders
        try:
            Decoder.SubDecoders = (object, )
            # 'object' has no attribute 'decode'!
            yield Decoder
        finally:
            Decoder.SubDecoders = orig

    # ensure that a wrong decoder do not make fail extraction
    with using_wrong_decoder() as decoder:
        data = decoder.decode("a sample text")
    assert_that(data, empty())


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
