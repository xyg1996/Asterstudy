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

"""Automatic tests for Case class."""


import os
import os.path as osp
import unittest

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.command import Comment
from asterstudy.datamodel.engine.engine_utils import has_asrun
from asterstudy.datamodel.general import ConversionLevel, FileAttr, Validity
from asterstudy.datamodel.history import History
from hamcrest import *
from testutils import tempdir


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def test_import_case():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    casefile = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'export', 'forma13a.export')
    casedir = os.path.abspath(os.path.dirname(casefile))

    with open(casefile) as desc:
        for line in desc.readlines():
            if not line.startswith('F'):
                continue

            _, ext, name, _, unit = line.split()

            filename = os.path.join(casedir, name)
            assert_that(os.path.isfile(filename), equal_to(True))

            if ext == 'comm':
                stage = case.create_stage(':memory:')
                with open(filename) as file:
                    comm2study(file.read(), stage)

                assert_that(stage.is_graphical_mode(), equal_to(True))
                continue

            unite = stage.file2unit(filename)
            assert_that(unite, is_not(is_in(stage.handle2info)))

            stage.handle2info[int(unit)].filename = filename
            pass

    command = stage['MAY_POM']
    unit = command['UNITE']

    from asterstudy.datamodel.command import Unit
    assert_that(unit, instance_of(Unit))

    assert_that(unit.value, is_in(stage.handle2info))

    info = stage.handle2info[unit.value]
    assert_that(command, is_in(info))

    attrs = info[command]
    assert_that([FileAttr.In], equal_to(attrs))

    assert_that(unit.filename, equal_to(info.filename))

    # check assignment
    unit.filename = "forma13a.20"
    assert_that(unit.filename, equal_to("forma13a.20"))
    assert_that(unit.filename, equal_to(info.filename))

    assert_that(case.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    pass

def test_file2unit():
    """Test for automatic assignment of unit numbers"""

    # creating a stage creates a file descriptors
    history = History()
    file_descriptors = history.current_case.create_stage(':a:')
    #file_descriptors = Mixing()

    # forbidden units: 0, 1, 6
    assert_that(file_descriptors.file2unit("bad0", udefault=0), equal_to(2))
    assert_that(file_descriptors.file2unit("bad1", udefault=1), equal_to(2))
    assert_that(file_descriptors.file2unit("bad6", udefault=6), equal_to(7))

    assert_that(file_descriptors.file2unit("file0", udefault=19), equal_to(19))

    assert_that(file_descriptors.file2unit("file0", umin=19), equal_to(19))

    assert_that(calling(file_descriptors.file2unit).with_args("file0", umax=0),
                raises(ValueError))

    unit0 = 1
    info = file_descriptors.handle2info[unit0]
    info.filename = "file0"
    info.attr = FileAttr.In
    info.embedded = True
    assert_that(file_descriptors.file2unit("file0"), equal_to(unit0))

    assert_that(file_descriptors.file2unit("file1"), is_not(equal_to(unit0)))

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def test_rccm01b():
    """Test for import with POURSUITE usage"""
    history = History()
    case = history.current_case

    casedir = osp.abspath(osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'export'))

    def _files(ext):
        return osp.join(casedir, 'rccm01b.' + ext)

    stage = case.create_stage('rccm01b.comm')
    with open(_files('comm')) as file:
        comm2study(file.read(), stage, ConversionLevel.Syntaxic)
    assert_that(stage.is_graphical_mode(), equal_to(True))

    stage = case.create_stage('rccm01b.com0')
    with open(_files('com0')) as file:
        comm2study(file.read(), stage, ConversionLevel.Syntaxic)
    assert_that(stage.is_graphical_mode(), equal_to(True))

    stage = case.create_stage('rccm01b.com1')
    with open(_files('com1')) as file:
        comm2study(file.read(), stage, ConversionLevel.Syntaxic)
    assert_that(stage.is_graphical_mode(), equal_to(True))

    stage = case.create_stage('rccm01b.com2')
    with open(_files('com2')) as file:
        comm2study(file.read(), stage, ConversionLevel.Syntaxic)
    assert_that(stage.is_graphical_mode(), equal_to(True))

    stage = case.create_stage('rccm01b.com3')
    with open(_files('com3')) as file:
        comm2study(file.read(), stage, ConversionLevel.Syntaxic)
    assert_that(stage.is_graphical_mode(), equal_to(True))

    pers = osp.abspath(osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'persistence'))
    if os.getenv("BUILD_AJS"):
        History.save(history, osp.join(pers, "rccm01b.test.ajs"))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_rccm01b_from_export():
    """Test for import rccm01b from its export file"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'rccm01b.export')

    nbs = 5
    history = History()
    case, params = history.import_case(export)
    assert_that(case, has_length(nbs))
    assert_that('memory', is_in(params))
    assert_that(params['memory'], equal_to(256))
    assert_that('server', not_(is_in(params)))
    last = case[nbs - 1]
    assert_that(last.is_graphical_mode())

    # check stage names and ordering by extension
    assert_that([stage.name for stage in case],
                contains('rccm01b', 'rccm01b_1', 'rccm01b_2', 'rccm01b_3',
                         'rccm01b_4'))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_zzzz241a_from_export():
    """Test for import zzzz241a from its export file"""
    import tempfile
    from asrun import create_profil
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zzzz241a.export')
    prof = create_profil(export)
    prof.absolutize_filename(export)
    content = prof.get_content()
    export_test = tempfile.mkstemp(prefix='asterstudy-export-')[1]

    history = History()
    changed = prof.copy()
    changed.add_entry('a_result', result=True, type='nom')
    changed.WriteExportTo(export_test)

    nbs = 2
    case, _ = history.import_case(export_test)
    assert_that(case, has_length(nbs))

    keys0 = case[0].handle2info.keys()
    assert_that(keys0, contains_inanyorder(11, 'a_result'))
    keys1 = case[1].handle2info.keys()
    assert_that(keys1, contains_inanyorder(11, 'a_result'))

    assert_that([stage.name for stage in case],
                contains('zzzz241a', 'zzzz241a_1'))

    # check for directory
    changed = prof.copy()
    changed.add_entry('/tmp', isrep=True, data=True)
    changed.add_entry('/home', isrep=True, result=True)
    changed.WriteExportTo(export_test)
    case, _ = history.import_case(export_test)
    assert_that(case.in_dir, equal_to('/tmp'))
    assert_that(case.out_dir, equal_to('/home'))
    os.remove(export_test)

    # check for expected errors
    try:
        changed = prof.copy()
        changed.add_entry('xxx.gz', data=True, compr=True)
        changed.WriteExportTo(export_test)

        assert_that(calling(history.import_case).with_args(export_test),
                    raises(TypeError, "not yet supported"))
    finally:
        os.remove(export_test)


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_import_from_astk():
    """Test for import from a astk file"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zzzz241a.astk')

    nbs = 2
    history = History()
    case, _ = history.import_case(export)
    assert_that(case, has_length(nbs))
    assert_that(case[0].is_text_mode(), equal_to(True))
    assert_that(case[1].is_text_mode(), equal_to(True))

    # check stage names and ordering by extension
    assert_that([stage.name for stage in case],
                contains('zzzz241a', 'zzzz241a_1'))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_order():
    """Test for import rccm01b from its export file"""
    history = History()
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'nothing.export')
    case, _ = history.import_case(export)
    assert_that(case, has_length(2))
    # check stage names and ordering by extension
    assert_that([stage.name for stage in case], contains('s1', 's2'))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_import_unknown_type():
    """Test for error checking during import"""
    history = History()
    assert_that(calling(history.import_case).with_args(__file__),
                raises(TypeError, "unknown file type"))


def test_export_failed():
    """Test export with invalid Python statement"""
    text = \
"""
DEBUT()

if:
mesh = LIRE_MAILLAGE(FORMAT='MED', UNITE={0})

FIN()
"""
    import tempfile
    history = History()
    case = history.current_case
    stage = case.create_stage('s1')
    stage.use_text_mode()
    stage.set_text(text)
    export_test = tempfile.mkstemp(prefix='asterstudy-export-')[1]
    stage.export(export_test)

    # check that text with syntax error can be extracted
    text2 = stage.get_text(pretty_text=True)
    assert_that(text2, contains_string("if:"))
    assert_that(text2, equal_to(text))

    os.remove(export_test)


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_export_testcase():
    """Test for export a case to make a testcase"""
    import re
    import shutil
    import tempfile
    text = \
"""
mesh1 = LIRE_MAILLAGE(UNITE=20)

mesh2 = LIRE_MAILLAGE(UNITE=22)

model = AFFE_MODELE(AFFE=_F(MODELISATION='3D',
                            PHENOMENE='MECANIQUE',
                            TOUT='OUI'),
                    MAILLAGE=mesh1)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage('s1')
    stage.use_text_mode()
    stage.set_text(text)
    stage.use_graphical_mode()

    case.in_dir = osp.join('/tmp')

    info = stage.handle2info[20]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                             'data', 'export', 'adlv100a.mmed')
    info.attr = FileAttr.In
    info = stage.handle2info[22]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                             'data', 'export', 'rccm01b.mmed')
    info.attr = FileAttr.In
    info = stage.handle2info[88]
    info.filename = '/tmp/a result_file.resu'
    info.attr = FileAttr.Out

    destdir = tempfile.mkdtemp(prefix='asterstudy-export-')
    test_name = "abcd001a"
    export_name = osp.join(destdir, test_name + ".export")

    # ensure export does not fail with invalid value
    case[-1].result.job.set('time', 'a bad value')

    case.export(export_name, testcase=True)

    # check files
    exts = (".export", ".comm", ".mmed", "_1.mmed")
    files = [osp.join(destdir, test_name + i) for i in exts]

    for i in files:
        assert_that(osp.isfile(i), equal_to(True))

    with open(files[0]) as fobj:
        content = fobj.read()

    assert_that(content, matches_regexp("F +comm +abcd001a.comm +D +1"))
    assert_that(content, matches_regexp("F +libr +abcd001a.mmed +D +20"))
    assert_that(content, matches_regexp("F +libr +abcd001a_1.mmed +D +22"))
    assert_that(content, matches_regexp("R +repe +tmp +D +0"))
    assert_that(content, is_not(matches_regexp("abcd001a.resu.+88")))

    assert_that(content, matches_regexp("P +testlist +verification +sequential"))
    assert_that(content, matches_regexp("P +memory_limit"))
    assert_that(content, matches_regexp("P +time_limit"))
    assert_that(content, matches_regexp("P +mpi_nbnoeud"))
    assert_that(content, matches_regexp("P +mpi_nbcpu"))
    assert_that(content, matches_regexp("P +ncpus"))

    with open(files[1]) as fobj:
        comm_text = fobj.read()

    # remove identifiers for comparison
    reid = re.compile(r" *identifier *= *[0-9]+ *,? *\n?", re.M)
    comm_text = reid.sub("", comm_text)

    assert_that(comm_text, contains_string(text))
    assert_that(comm_text, contains_string('DEBUT()'))
    assert_that(comm_text, contains_string('FIN()'))

    shutil.rmtree(destdir)


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_forma02b_from_export():
    """Test for import forma02b from its export file"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'forma02b.export')

    nbs = 2
    history = History()
    case, _ = history.import_case(export)
    assert_that(case, has_length(nbs))

    assert_that([stage.name for stage in case],
                contains('forma02b', 'forma02b_1'))
    # check that the second stage can be deleted, see #26991.
    case[1].delete()
    assert_that(case, has_length(1))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_zoom():
    """Test for import of 'zoom' file"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zoom00.export')

    nbs = 4
    history = History()
    case, _ = history.import_case(export)
    assert_that(case, has_length(nbs))

    keys0 = case[0].handle2info.keys()
    assert_that(keys0, contains(20))
    info = case[0].handle2info[20]
    assert_that(osp.basename(info.filename), equal_to("zoom00.med"))

    keys1 = case[1].handle2info.keys()
    assert_that(keys1, empty())

    keys2 = case[2].handle2info.keys()
    assert_that(keys2, empty())

    keys3 = case[3].handle2info.keys()
    assert_that(keys3, contains(80))
    info = case[3].handle2info[80]
    assert_that(osp.basename(info.filename), equal_to("zoom80.txt"))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_sdlx101a_from_export():
    """Test for import sdlx101a from its export file"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'sdlx', 'sdlx101a.export')

    history = History()
    case, _ = history.import_case(export)

    expected = [
        # stage name, graphical, number of commands
        ('sdlx101a', True, 2),
        ('sdlx101a_1', True, 2),
        ('sdlx101a_2', True, 5),
        ('sdlx101a_3', True, 1),
        ('sdlx101a_4', True, 17),
        ('sdlx101a_5', True, 1),
        ('sdlx101a_6', True, 1),
        ('sdlx101a_7', True, 1),
        ('sdlx101a_8', True, 1),
        ('sdlx101a_9', True, 1),
        ('sdlx101a_10', True, 2),
        ('sdlx101a_11', True, 10),
        ('sdlx101a_12', True, 5),
        ('sdlx101a_13', True, 16),
        ('sdlx101a_14', True, 33),
    ]
    nbs = len(expected)
    ic = 0
    for stage, (name, graph, nbcmd) in zip(case.stages, expected):
        ic += 1
        assert_that(stage.name, equal_to(name))
        assert_that(stage.is_graphical_mode(), equal_to(graph))
        cmds = [i for i in stage if not isinstance(i, Comment)]
        assert_that(cmds, has_length(nbcmd))

    assert_that(case, has_length(nbs))
    last = case[nbs - 1]
    assert_that(last.is_graphical_mode())


@unittest.skipIf(not has_asrun(), "asrun is required")
@tempdir
def test_exportOT(tmpdir):
    # ensure that outputs are not set as data when there are several stages
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'exportOT.export')
    export = export.replace('output_file R', '{0}/output_file R'.format(tmpdir))

    nbs = 2
    history = History()
    history.folder = tmpdir
    case, _ = history.import_case(export, force_text=True)
    assert_that(case, has_length(nbs))
    st1, st2 = case.stages

    unit = 20
    assert_that(unit, is_in(st1.handle2info.keys()))
    assert_that(unit, is_in(st2.handle2info.keys()))
    assert_that(st1.handle2info[unit].attr, equal_to(FileAttr.In))
    assert_that(st2.handle2info[unit].attr, equal_to(FileAttr.In))

    unit = 10
    assert_that(unit, is_in(st1.handle2info.keys()))
    assert_that(unit, is_in(st2.handle2info.keys()))
    assert_that(st1.handle2info[unit].attr, equal_to(FileAttr.Out))
    assert_that(st2.handle2info[unit].attr, equal_to(FileAttr.Out))

    # check that several files with type 'nom' are correctly supported
    assert_that(st1.handle2info,
                contains_inanyorder(10, 20, 'filename1', 'filename2'))
    assert_that(st2.handle2info,
                contains_inanyorder(10, 20, 'filename1', 'filename2'))
    info1 = st1.handle2info['filename1']
    info2 = st1.handle2info['filename2']
    assert_that(info1.attr & (FileAttr.In | FileAttr.Named))
    assert_that(info2.attr & (FileAttr.In | FileAttr.Named))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
