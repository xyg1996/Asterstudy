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

"""Implementation of the automatic tests for history."""


import os
import re
import unittest
from tempfile import mkstemp

from asterstudy.common import ConversionError, VersionError
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.dataset import DataSet
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.history import History
from asterstudy.datamodel.serializer import JSONSerializer
from hamcrest import *
from testutils import attr, tempdir


#------------------------------------------------------------------------------
def test_save_ast():
    #--------------------------------------------------------------------------
    history = History()
    stage = history.current_case.create_stage('Stage_1')
    cmd = stage.add_command('DEFI_MATERIAU')
    param1 = cmd['ELAS']['NU']
    param1.value = 1000

    #--------------------------------------------------------------------------
    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ast')[1]

    History.save(history, an_outfile)
    history2 = History.load(an_outfile)

    os.remove(an_outfile)

    assert_that(history * history2, none())


def test_save_json():
    history = History()
    stage = history.current_case.create_stage('Stage_1')
    cmd = stage.add_command('DEFI_MATERIAU')
    param1 = cmd['ELAS']['NU']
    param1.value = 1000

    job = stage.result.job
    job.set('partition', 'par')
    job.set('queue', 'xyz123')

    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]

    History.save(history, an_outfile)
    history2 = History.load(an_outfile, strict=ConversionLevel.NoFail)
    assert_that(history * history2, none())

    with open(an_outfile) as ajs:
        jstext = ajs.read()
    # check backward compatibility: state replaced by resstate
    jstext = jstext.replace('"resstate": 1', '"state": "Waiting"')
    assert_that(jstext, contains_string("Waiting"))

    with open(an_outfile, 'w') as ajs:
        ajs.write(jstext)

    history3 = History.load(an_outfile, strict=ConversionLevel.NoFail)
    assert_that(history * history3, none())

    os.remove(an_outfile)


def test_save_file_descriptors():
    #--------------------------------------------------------------------------
    an_infile = os.path.join(os.getenv('ASTERSTUDYDIR'), 'data',
                             'persistence', 'rccm01b.file_descriptors.ajs')

    history = History.load(an_infile)

    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]

    History.save(history, an_outfile)

    history2 = History.load(an_outfile)

    os.remove(an_outfile)

    assert_that(history * history2, none())


def test_save_run_cases():
    an_infile = os.path.join(os.getenv('ASTERSTUDYDIR'), 'data',
                             'persistence', 'rccm01b.run_cases.ajs')

    history = History.load(an_infile)

    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]

    History.save(history, an_outfile)

    history2 = History.load(an_outfile)

    os.remove(an_outfile)

    assert_that(history * history2, none())

    # 5 stages: the first 4 in graphical mode, the 5th is in text mode
    case = history.current_case
    for i, stage in enumerate(case):
        assert_that(stage.is_graphical_mode(), equal_to(i != 4))

    # no stages shared with the current case, so all are in text mode
    for runc in history.run_cases:
        for i, stage in enumerate(runc):
            assert_that(stage.is_text_mode(),
                        equal_to(True))
            assert_that(stage.saving_mode == DataSet.graphicalMode,
                        equal_to(i != 4))

    runc = history.run_cases[1]
    assert_that(runc.name, equal_to('Case_2'))
    runc.restore_stages_mode()
    for i, stage in enumerate(runc):
        assert_that(stage.is_graphical_mode(), equal_to(i != 4))

    # first 3 stages are shared by Case_1 and Case_2
    runc = history.run_cases[0]
    assert_that(runc.name, equal_to('Case_1'))
    for i, stage in enumerate(runc):
        assert_that(stage.is_graphical_mode(), equal_to(i < 3))


def test_save_graphically_enabled_stages():
    an_infile = os.path.join(os.getenv('ASTERSTUDYDIR'), 'data',
                             'persistence', 'tst_save_open.ajs')

    history = History.load(an_infile, strict=ConversionLevel.NoFail)

    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]

    History.save(history, an_outfile)

    history2 = History.load(an_outfile, strict=ConversionLevel.NoFail)

    os.remove(an_outfile)

    assert_that(history * history2, none())


def test_error_at_restore():
    an_infile = os.path.join(os.getenv('ASTERSTUDYDIR'), 'data',
                             'persistence', 'invalid_command.ajs')
    with open(an_infile) as file:
        jstext = file.read()

    jsversion = re.sub('"versionMajor": [0-9]+', '"versionMajor": 1', jstext)
    jssyntax = jstext.replace("LIRE_MAILLAGE()",
                              "LIRE_MAILLAGE(UNKNOWN=1)")

    mod_infile = mkstemp(prefix='invalid' + '-', suffix='.ajs')[1]

    # error: version number changed => VersionError
    with open(mod_infile, "w") as jsfile:
        jsfile.write(jsversion)

    assert_that(calling(History.load).with_args(mod_infile),
                raises(VersionError))

    # without strict "Restore"
    serializer = JSONSerializer(strict=ConversionLevel.Syntaxic)
    history = serializer.load(mod_infile)
    stage = history.current_case[0]

    assert_that(stage.dataset.is_graphical_mode(), equal_to(True))

    # error: invalid syntax => ConversionError
    with open(mod_infile, "w") as jsfile:
        jsfile.write(jstext.replace("LIRE_MAILLAGE(UNITE=20)",
                                    "LIRE_MAILLAGE(UNKNOWN=1)"))

    assert_that(calling(History.load).with_args(mod_infile),
                raises(ConversionError))

    # check failover to text mode of JSONSerializer
    serializer = JSONSerializer(strict=ConversionLevel.NoFail)
    history = serializer.load(mod_infile)
    stage = history.current_case[0]

    assert_that(stage.dataset.is_text_mode(), equal_to(True))

    os.remove(mod_infile)


@tempdir
def test_27704(tmpdir):
    filename = os.path.join(os.getenv('ASTERSTUDYDIR'), 'data', 'performance',
                            "study_anais.ajs")
    history = History.load(filename, strict=ConversionLevel.Syntaxic)

    assert_that(history.cases, has_length(85))
    stages = set()
    for case in history.cases:
        stages.update(case.stages)
    assert_that(stages, has_length(145))

    history.folder = tmpdir + '/xxx_Files'
    history.check_dir(History.clean)

    assert_that(history.run_cases, has_length(0))
    assert_that(history.cases, has_length(1))


@tempdir
def test_save_text_stage(tmpdir):
    history = History()
    case = history.current_case
    # see test_issue_27948
    stage0 = case.create_stage(':init:')
    text0 = """tab0 = CREA_TABLE(LISTE=_F(PARA='X', LISTE_R=[0., 1.]))"""
    comm2study(text0, stage0)

    stage1 = case.create_stage(':text:')
    stage1.use_text_mode()
    # 'tab1' is defined in the text stage and 'tab0' is deleted
    stage1.update_commands([('tab1', 'CREA_TABLE', 'table_sdaster'), ])
    stage1.delete_commands(['tab0', ])

    stage2 = case.create_stage(':graph:')
    stage2.use_text_mode()
    stage2.set_text("""IMPR_TABLE(TABLE=tab1)""")
    stage2.use_graphical_mode()

    an_outfile = os.path.join(tmpdir, 'test_save_text_stage.ajs')

    History.save(history, an_outfile)
    history2 = History.load(an_outfile, strict=ConversionLevel.NoFail)
    assert_that(history * history2, none())


def test_result_job():
    an_infile = os.path.join(os.getenv('ASTERSTUDYDIR'), 'data',
                             'persistence', 'result_job.ajs')

    history = History.load(an_infile)

    rc0, rc1 = history.run_cases
    assert_that(rc0.results(), has_length(1))
    assert_that(rc1.results(), has_length(2))

    jd00 = rc0.results()[0].job.asdict()
    jd10 = rc1.results()[0].job.asdict()
    jd11 = rc1.results()[1].job.asdict()

    # only the values saved in '.ajs'
    expected = ('description', 'time', 'server', 'version', 'mode', 'memory',
                'folder', 'jobid', 'name')
    assert_that(jd00.keys(), contains_inanyorder(*expected))

    assert_that(jd10.keys(), empty())

    assert_that(jd11.keys(), contains_inanyorder(*expected))

    # comparison (even if job are not compared)
    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]

    History.save(history, an_outfile)

    history2 = History.load(an_outfile)

    os.remove(an_outfile)

    assert_that(history * history2, none())


def test_recover_28495():
    data = os.path.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'data_forma02b.ajs')
    # in_dir does not exist: must not fail
    history = History.load(data)

    case = history.current_case
    assert_that(case, has_length(2))
    assert_that(case[0].is_graphical_mode(), equal_to(True))
    assert_that(case[1].is_graphical_mode(), equal_to(True))

    ajs = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]
    with open(data, "r") as src:
        text = src.read()
        text = text.replace('''"in_dir": "/tmp/path/to/repe/in"''',
                            '''"in_dir": "{0}", "out_dir": "{0}"'''
                            .format(os.getcwd()))
    with open(ajs, "w") as dst:
        dst.write(text)

    # out_dir is the same than in_dir: must not fail
    history = History.load(ajs)
    case = history.current_case
    assert_that(case.in_dir, equal_to(os.getcwd()))
    assert_that(case.out_dir, none())


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
