# -*- coding: utf-8 -*-

# Copyright 2017 EDF R&D
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

"""
Automatic tests for runners, callable using a `Salome` or `AsRun` runner.
"""


import unittest
import os
import os.path as osp
import shutil
import time
from contextlib import contextmanager
import getpass

from hamcrest import *
from testutils import tempdir

# Necessary for xtest_run_with_smesh_data uniquement
import testutils.gui_utils
import asterstudy.gui.salomegui
from asterstudy.gui.salomegui_utils import publish_meshes

from asterstudy.common import RunnerError, debug_message, ping
from asterstudy.datamodel import CATA
from asterstudy.datamodel.general import FileAttr
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.engine import runner_factory, serverinfos_factory, Engine
from asterstudy.datamodel.engine.salome_runner import has_salome, new_directory
from asterstudy.datamodel.result import StateOptions as SO, Job
from asterstudy.datamodel.usages import load_database

# Due to the configuration at a given time
# The required Aster versions to run the tests may be different
#     between localhost and remote servers.
DEFAULT_LOCAL_VERSION = 'stable'
DEFAULT_REMOTE_VERSION = 'stable-updates'
DEFAULT_REMOTE_ASRUN_VERSION = 'stable-updates'

# Tells which remote salome install to use (runner Salome)
# WARNING: FOR TESTING PURPOSES ONLY, LEAVE EMPTY IN PRODUCTION VERSION !!
REMOTE_APPLI_PATH = osp.join("/projets", "simumeca", "salomemeca",
                             "DEV", "appli_V8_INTEGR")
# For asrun runner, do not provide path to Salome install
REMOTE_ASTER_ROOT = osp.join("/projets", "simumeca")

DEFAULT_PARAMS = {
    'server': 'localhost', 'version': DEFAULT_LOCAL_VERSION,
    'execmode': Job.ExecOptimText, 'mode': Job.InteractiveText,
    'memory': 2048, 'time': '00:05:00'
}
# For asrun, servers must be defined in `~/.astkrc_XXX/config_serveurs`.

# For SALOME, servers must be defined in JobManager.

# The hostname is used to check if one of REMOTE_SERVERS is defined.
REMOTE_SERVERS = ('eole.hpc.edf.fr', 'aster5.hpc.edf.fr', 'eole')

USER = getpass.getuser()

MDELAY = int(os.getenv('ASTERSTUDY_MDELAY', '1'))

class VersionServer:
    """Controller on the settings of the version to use on each server.

    It ensures that we know which version to use on a server.
    It also keep the values in "cache" for each engine type and each server
    (localhost and the remote one).
    """
    class EngineInfos:
        server = None
        version = None
        cached = False

    _cfg = {'AsRun': EngineInfos(), 'Salome': EngineInfos(),
            'Direct': EngineInfos()}

    @classmethod
    def set(cls, engine, server, version):
        """Define the version to use on *server*."""
        cfg = cls._cfg[Engine.name(engine)]
        cfg.server = server
        cfg.version = version

    @classmethod
    def get(cls, engine, server):
        """Return the version to use on *server*."""
        cfg = cls._cfg[Engine.name(engine)]
        if not cfg.cached:
            cls.get_remote_server(engine)
        if server == cfg.server:
            version = cfg.version
        else:
            version = DEFAULT_PARAMS['version']
        return version

    @classmethod
    def get_remote_server(cls, engine):
        """Return an available server, or None."""
        runner = Engine.name(engine)
        cfg = cls._cfg[runner]
        # Run testcases that need a remote connection only if TEST_REMOTE is defined
        if os.getenv("TEST_REMOTE") != "1":
            return None
        if not cfg.cached:
            print("Checking for remote servers for {0} runner..."
                  .format(runner))
            infos = serverinfos_factory(engine)
            found = None
            for server in REMOTE_SERVERS:
                name = infos.server_by_host(server)
                debug_message("search for {0} in servers list, found: {1}"
                              .format(server, name))
                if name is not None:
                    if ping(server, timeout=5):
                        found = name
                        debug_message("remote server used for testcase: {0} ({1})"
                                      .format(name, server))
                        infos.refresh_one(name)
                        lvers = list(infos.server_versions(name).keys())
                        debug_message("available versions: {0}".format(lvers))
                        if runner == "Salome":
                            version = DEFAULT_REMOTE_VERSION
                        if runner == "AsRun":
                            version = DEFAULT_REMOTE_ASRUN_VERSION
                        cls.set(engine, name, version)

                        # adapt applipath to ressource if specified
                        _set_custom_appli_path(runner, infos, server, name)
                        break
                    else:
                        debug_message("server {0} is not responding"
                                      .format(server))
            cfg.cached = True
            print("Server found for {0} runner: {1.server} "
                  "(version '{1.version}')".format(runner, cfg))
        else:
            infos = serverinfos_factory(engine)
            name = infos.server_by_host(cfg.server)
            _set_custom_appli_path(runner, infos, cfg.server, name)
        return cfg.server

def _set_custom_appli_path(runner, infos, server, name):
    if runner == "Salome":
        scfg = infos.server_config(server)
        rc_def = scfg.get('rc_definition', {})
        if REMOTE_APPLI_PATH and hasattr(rc_def, 'applipath'):
            import salome
            rc_manager = salome.lcc.getResourcesManager()
            rc_definition = rc_manager.GetResourceDefinition(str(server))
            # Not sufficient: in ResourcesManager,
            # `GetResourceDefinition` only provides a copy.
            rc_definition.applipath = REMOTE_APPLI_PATH
            rc_manager.RemoveResource(str(server), False, "")
            rc_manager.AddResource(rc_definition, False, "")
            rc_definition = rc_manager.GetResourceDefinition(str(server))
            # Do not forget to put that in def
            scfg['rc_definition'] = rc_definition
    if runner == "AsRun":
        scfg = infos.server_config(name)
        if REMOTE_ASTER_ROOT and "rep_serv" in scfg:
            scfg['rep_serv'] = REMOTE_ASTER_ROOT

# Shortcut
remote_server = VersionServer.get_remote_server


def monitor_refresh(runner, estimated_time):
    """Refresh states up to the estimated end of all the computations"""
    state = SO.Waiting
    delay = estimated_time * MDELAY / 8.
    # in case of server overload, we wait up to 4 x estimated_time
    for i in range(32):
        time.sleep(delay)
        current = runner.current
        if current:
            state = runner.result_state(current)
            debug_message("Refresh", (i + 1) * delay, SO.name(state))
            if runner.is_finished():
                break
        elif runner.__class__.__name__ == "Direct":
            state = SO.Finished
            break
        else:
            debug_message("Refresh", (i + 1) * delay, "nothing to process")
    assert_that(state & SO.Finished)

def _parameters(engine, server=None, failure=False, wrkdir=None):
    params = DEFAULT_PARAMS.copy()
    params['wrkdir'] = wrkdir
    params['folder'] = ('/tmp/{1}_test_{0}_runner'
                        .format(Engine.name(engine), USER))
    if failure:
        params['server'] = 'unknown_server'
    else:
        # adapt parameters for the existing configuration
        infos = serverinfos_factory(engine)
        server = server or DEFAULT_PARAMS['server']
        assert_that(infos.available_servers, has_item(server))
        params['server'] = server
    params['version'] = VersionServer.get(engine, params['server'])
    return params

def _check_jobid(engine, jobid):
    if engine & Engine.AsRun:
        assert_that(jobid, matches_regexp(r'^[0-9]+\-\w+'))
    elif engine & Engine.Salome:
        assert_that(jobid, matches_regexp('^[0-9]+$'))

@contextmanager
def mock_object_creation(inputfile):
    """Context manager to import a MED file as a SMESH object and to clean
    the SALOME study at the end of the test
    """
    import salome
    [mesh_obj] = publish_meshes(inputfile)

    # Now, get its entry
    sobject = salome.ObjectToSObject(mesh_obj.mesh)
    entr = sobject.GetID()
    yield entr
    import salome.kernel.studyedit as sed
    sedit = sed.getStudyEditor()
    sedit.removeItem(sobject, True)
    sm = sedit.findOrCreateComponent("SMESH")
    sedit.removeItem(sm, True)


def xtest_infos(engine, server=DEFAULT_PARAMS['server']):
    """Test for servers informations for SALOME"""
    infos = serverinfos_factory(engine)
    # ensure that server_config refreshes available_servers
    if infos._servers:
        infos._servers = None
        infos.server_config(server)

    assert_that(infos.available_servers, has_item(server))
    if engine & Engine.Salome and server == 'localhost':
        assert_that(calling(infos.refresh_once).with_args('unknown'),
                    raises(ValueError, 'not available'))
        infos.refresh_once('unittest')
        assert_that(server, is_not(is_in(infos._refreshed)))

    infos.refresh_once(server)
    assert_that(server, is_in(infos._refreshed))
    assert_that(infos.server_versions(server),
                has_item(VersionServer.get(engine, server)))
    if server == 'localhost' or engine & Engine.AsRun:
        assert_that(infos.server_modes(server), has_item(Job.InteractiveText))
    else:
        # Batch is imposed on remote servers
        assert_that(infos.server_modes(server), has_item(Job.BatchText))
    assert_that(infos.exec_modes(), has_item(Job.ExecOptimText))

    if engine & Engine.Salome:
        assert_that(infos.server_config(server), has_key('rc_definition'))
        cfg = infos.server_config(server)['rc_definition']
        assert_that(cfg, has_property('working_directory'))
        assert_that(cfg.working_directory, contains_string('/'))

        # check errors
        assert_that(calling(infos.refresh_once).with_args('unavailable'),
                    raises(ValueError, "not available"))


@tempdir
def xtest_init_from_database(tmpdir, engine, server=None):
    """Test for init from a database"""
    # 1. create a database
    rc1 = _setup_run_case(tmpdir, 0, [0])
    expected_results = rc1.results()
    assert_that(expected_results, has_length(1))

    runner = runner_factory(engine, case=rc1, logger=lambda x: None,
                            unittest=True)

    params = _parameters(engine, server,
                         wrkdir=osp.join(tmpdir, 'CreateDataBase'))
    params['compress'] = engine == Engine.AsRun
    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))
    monitor_refresh(runner, estimated_time=5.)
    result = expected_results[0]
    assert_that(runner.result_state(result) & SO.Success)

    # 2. check existing cases
    history = rc1.model
    assert_that(history.cases, has_length(2))
    assert_that(history.cases[0], same_instance(rc1))
    assert_that(result.state & SO.Success)
    dbpath = result.stage.database_path
    suffix = ".gz" if params['compress'] else ""
    assert_that(osp.isfile(osp.join(dbpath, "glob.1" + suffix)))

    # 3a. restart from the database without reading it
    current = load_database(history, dbpath, engine=engine, extract=False)
    # no new runcase
    assert_that(history.cases, has_length(2))

    # 3b. restart from the database
    current = load_database(history, dbpath, engine=engine)
    assert_that(history.cases, has_length(3))

    assert_that(history.cases[0], same_instance(rc1))
    assert_that(history.cases[2], same_instance(current))
    load = current[0].parent_case
    assert_that(history.cases[1], same_instance(load))

    assert_that(rc1.stages, has_length(1))
    assert_that(current.stages, has_length(1))

    # FIXME result is cleared by case.detach
    # because insert_case 'pops' previous case
    # assert_that(result.state & SO.Success)

    # 4. restart using the API
    from asterstudy.api import Calculation
    calc = Calculation(osp.join(tmpdir, "test_api"))
    calc._watcher.set_engine(engine)
    if engine == Engine.AsRun:
        # workaround: as_run uses 'batch_nom' even if 'batch' is 'non'...
        calc.set("mode", "Interactive")

    calc.add_stage_from_database(dbpath)
    assert_that(calc.database_path, none())

    calc.run()

    assert_that(calc.database_path, is_not(none()))
    assert_that(osp.exists(calc.database_path), equal_to(True))

    runner.cleanup()


@tempdir
def xtest_run_with_data(tmpdir, engine, server=None):
    """Test for runner with data files"""
    rc2 = _create_run_case_with_data(tmpdir)

    expected_results = rc2.results()
    assert_that(expected_results, has_length(1))
    result = expected_results[0]

    runner = runner_factory(engine, case=rc2, unittest=True)

    assert_that(runner.is_started(), equal_to(False))
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(runner.result_state(result) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    params['memory'] = DEFAULT_PARAMS['memory'] + 123
    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))
    monitor_refresh(runner, estimated_time=5.)

    assert_that(runner.result_state(result) & SO.Success)
    _check_jobid(engine, result.job.jobid)
    assert_that(result.job.name, equal_to('rc2_s1'))
    assert_that(result.job.server, equal_to(params['server']))
    assert_that(result.job.mode & Job.Interactive)
    assert_that(result.job.get("memory"),
                equal_to(DEFAULT_PARAMS['memory'] + 123))
    assert_that(runner.is_finished(), equal_to(True))
    runner.cleanup()

@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def xtest_run_with_smesh_data(tmpdir, engine, server=None):
    """Test for runner with input meshes from SMESH."""
    inputfile = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'forma13a.20')
    with mock_object_creation(inputfile) as entry:

        # create history
        history = History()
        history.folder = tmpdir
        case = history.current_case
        case.name = 'c2'
        stage = case.create_stage('s1')

        # add mesh file
        unit = 20
        info = stage.handle2info[unit]
        info.filename = str(entry)
        assert_that(stage.handle2file(unit), is_not(None))

        text = \
"""
DEBUT()

mesh = LIRE_MAILLAGE(FORMAT='MED', UNITE={0})

FIN()
""".format(unit)
        comm2study(text, stage)

        # assert exists attribute
        assert_that(info.exists, equal_to(True))

        rc2 = history.create_run_case(name='rc2')

        expected_results = rc2.results()
        assert_that(expected_results, has_length(1))
        result = expected_results[0]

        runner = runner_factory(engine, case=rc2, unittest=True)

        assert_that(runner.is_started(), equal_to(False))
        assert_that(runner.is_finished(), equal_to(False))
        assert_that(runner.result_state(result) & SO.Waiting)

        params = _parameters(engine, server, wrkdir=tmpdir)
        runner.start(params)
        assert_that(runner.is_started(), equal_to(True))
        monitor_refresh(runner, estimated_time=5.)

        assert_that(runner.result_state(result) & SO.Success)
        _check_jobid(engine, result.job.jobid)
        assert_that(result.job.name, equal_to('rc2_s1'))
        assert_that(result.job.server, equal_to(params['server']))
        assert_that(result.job.mode & Job.Interactive)
        assert_that(runner.is_finished(), equal_to(True))
        runner.cleanup()

@tempdir
def xtest_run_with_embfiles(tmpdir, engine, server=None):
    """Test for runner with embedded files"""
    unit_in = 20
    unit_out = 22
    text = \
"""
DEBUT()

mesh = LIRE_MAILLAGE(FORMAT='MED', UNITE={0})

IMPR_RESU(RESU=_F(MAILLAGE=mesh), UNITE={1})

FIN()
""".format(unit_in, unit_out)
    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c2'
    stage = case.create_stage('s1')
    comm2study(text, stage)

    # add a mesh file, declare it as embedded
    info_in = stage.handle2info[unit_in]
    info_in.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                                'data', 'export', 'forma13a.20')
    assert_that(stage.handle2file(unit_in), is_not(None))
    info_in.embedded = True

    # declare output file
    info_out = stage.handle2info[unit_out]
    info_out.filename = stage.ext2emb(osp.join('not_used_dirname', 'mesh.out'))
    info_out.embedded = True
    assert_that(info_out.filename, equal_to(osp.join(history.tmpdir, 'mesh.out')))

    rc2 = history.create_run_case(name='rc2')
    rc2.make_run_dir()

    expected_results = rc2.results()
    assert_that(expected_results, has_length(1))
    result = expected_results[0]

    runner = runner_factory(engine, case=rc2, unittest=True)

    assert_that(runner.is_started(), equal_to(False))
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(runner.result_state(result) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))
    monitor_refresh(runner, estimated_time=5.)

    assert_that(runner.result_state(result) & SO.Success)
    _check_jobid(engine, result.job.jobid)
    assert_that(result.job.name, equal_to('rc2_s1'))
    assert_that(result.job.server, equal_to(params['server']))
    assert_that(result.job.mode & Job.Interactive)
    assert_that(runner.is_finished(), equal_to(True))

    infile = osp.join(osp.join(tmpdir, 'rc2/Embedded'), 'forma13a.20')
    assert_that(osp.isfile(infile), equal_to(True))
    outfile = osp.join(osp.join(tmpdir, 'rc2/Embedded'), 'mesh.out')
    assert_that(osp.isfile(outfile), equal_to(True))
    runner.cleanup()

@tempdir
def xtest_run_with_directory(tmpdir, engine, server=None):
    """Test for runner with directory"""
    text = \
"""
DEBUT()

DEFI_FICHIER(UNITE=20, FICHIER='./REPE_IN/forma13a.20')
DEFI_FICHIER(UNITE=80, TYPE='LIBRE', FICHIER='./REPE_OUT/mesh.out')

mesh = LIRE_MAILLAGE(FORMAT='MED', UNITE=20)

IMPR_RESU(RESU=_F(MAILLAGE=mesh), UNITE=80)

DEFI_FICHIER(ACTION='LIBERER', UNITE=20)
DEFI_FICHIER(ACTION='LIBERER', UNITE=80)

FIN()
"""
    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c2'
    stage = case.create_stage('s1')
    stage.use_text_mode()
    stage.set_text(text)

    # add input dir
    data_dir = osp.join(tmpdir, 'data_dir')
    os.makedirs(data_dir)
    case.in_dir = data_dir
    shutil.copyfile(osp.join(os.getenv('ASTERSTUDYDIR'),
                             'data', 'export', 'forma13a.20'),
                    osp.join(data_dir, 'forma13a.20'))

    # add output dir
    resu_dir = osp.join(tmpdir, 'resu_dir')
    case.out_dir = resu_dir

    rc2 = history.create_run_case(name='rc2')
    rc2.make_run_dir()

    expected_results = rc2.results()
    assert_that(expected_results, has_length(1))
    result = expected_results[0]

    runner = runner_factory(engine, case=rc2, unittest=True)
    assert_that(runner.is_started(), equal_to(False))
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(runner.result_state(result) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))

    monitor_refresh(runner, estimated_time=15.)
    assert_that(runner.result_state(result) & SO.Finished)

    assert_that(runner.result_state(result) & SO.Success)

    outfile = osp.join(osp.join(resu_dir, 'mesh.out'))
    assert_that(osp.isfile(outfile), equal_to(True))
    runner.cleanup()


@tempdir
def xtest_override_output_dir(tmpdir, engine, server=None):
    # check that files are overridden in REPE_OUT destination
    # not applicable with as_run runner
    text = \
"""
DEBUT()

with open('REPE_OUT/a_result', 'w') as fout:
    fout.write('output file')

FIN()
"""
    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c2'
    stage = case.create_stage('s1')
    stage.use_text_mode()
    stage.set_text(text)

    # add output dir
    resu_dir = osp.join(tmpdir, 'resu_dir')
    case.out_dir = resu_dir
    # create an old result to check the overriding
    os.makedirs(resu_dir)
    with open(osp.join(resu_dir, 'a_result'), 'w') as fout:
        fout.write("old")

    rc2 = history.create_run_case(name='rc2')
    rc2.make_run_dir()

    expected_results = rc2.results()
    assert_that(expected_results, has_length(1))
    result = expected_results[0]

    runner = runner_factory(engine, case=rc2, unittest=True)
    assert_that(runner.is_started(), equal_to(False))
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(runner.result_state(result) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))

    monitor_refresh(runner, estimated_time=10.)

    assert_that(runner.result_state(result) & SO.Success)

    outfile = osp.join(osp.join(resu_dir, 'a_result'))
    assert_that(osp.isfile(outfile), equal_to(True))
    assert_that(os.stat(outfile).st_size, greater_than(5))
    runner.cleanup()


@tempdir
def xtest_error_output_dir(tmpdir, engine, server=None):
    # check that files are overridden in REPE_OUT destination
    # not applicable with as_run runner
    text = \
"""
DEBUT()

with open('REPE_OUT/a_result', 'w') as fout:
    fout.write('output file')

FIN()
"""
    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c2'
    stage = case.create_stage('s1')
    stage.use_text_mode()
    stage.set_text(text)

    # add output dir that can not be copied
    if not os.access('/noaccess', os.W_OK):
        resu_dir = osp.join('/noaccess', 'resu_dir')
        case.out_dir = resu_dir
    else:
        return

    rc2 = history.create_run_case(name='rc2')
    rc2.make_run_dir()

    expected_results = rc2.results()
    assert_that(expected_results, has_length(1))
    result = expected_results[0]

    runner = runner_factory(engine, case=rc2, unittest=True)
    assert_that(runner.is_started(), equal_to(False))
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(runner.result_state(result) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))

    monitor_refresh(runner, estimated_time=15.)

    # because of Copy failed
    assert_that(runner.result_state(result) & SO.Error)
    runner.cleanup()


@tempdir
def xtest_run_with_error(tmpdir, engine, server=None):
    """Test for runner with a job that can't be run"""
    umesh = 20
    unotexists = 34

    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c2'
    stage = case.create_stage('s1')
    stage('LIRE_MAILLAGE').init({'UNITE': umesh})
    stage('LIRE_MAILLAGE').init({'UNITE': unotexists})

    # add mesh file
    info20 = stage.handle2info[umesh]
    info20.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                               'data', 'export', 'forma13a.20')
    assert_that(stage.handle2file(umesh), is_not(None))
    assert_that(info20.exists, equal_to(True))
    assert_that(info20.attr, equal_to(FileAttr.In))
    assert_that(info20.isreference, equal_to(False))
    assert_that(info20.first_attr, equal_to(FileAttr.In))

    # test for not existent data that references a mesh object
    info34 = stage.handle2info[unotexists]
    info34.filename = '0:1:8:9'
    info34.attr = FileAttr.In
    assert_that(info34.exists, equal_to(False))
    assert_that(info34.attr, equal_to(FileAttr.In))
    assert_that(info34.isreference, equal_to(True))
    assert_that(info34.first_attr, equal_to(FileAttr.In))

    rc2 = history.create_run_case(name='rc2')

    expected_results = rc2.results()
    assert_that(expected_results, has_length(1))
    result = expected_results[0]

    runner = runner_factory(engine, case=rc2, unittest=True)

    # start with a non-existent file will be cancelled
    params = _parameters(engine, server, wrkdir=tmpdir)
    assert_that(calling(runner.start).with_args(params),
                raises(RunnerError, "mesh object does not exist"))
    assert_that(runner.is_started(), equal_to(True))
    assert_that(runner.is_finished(), equal_to(True))
    assert_that(runner.result_state(result) & SO.Error)

    # check undefined result file
    stage = history.current_case[0]
    del stage.handle2info[unotexists]
    uundef = 81
    info81 = stage.handle2info[uundef]
    info81.attr = FileAttr.Out
    rc3 = history.create_run_case(name='rc3')

    runner = runner_factory(engine, case=rc3, unittest=True)
    assert_that(calling(runner.start).with_args(params), raises(RunnerError))
    runner.cleanup()


@tempdir
def xtest_failure(tmpdir, engine, server=None):
    """Test for runner with failure"""
    nbs = 3
    rc1 = _setup_run_case(tmpdir, [0, 2], reusable_stages=range(nbs), fail=1)
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(engine, case=rc1, unittest=True)
    runner.cleanup()
    assert_that(runner.result_state(expected_results[0]) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=10.)

    assert_that(runner.result_state(expected_results[0]) & SO.Success)
    assert_that(runner.result_state(expected_results[1]) & SO.Error)
    assert_that(runner.result_state(expected_results[2]),
                equal_to(SO.Waiting))

    # to force messages extraction in 'messages()'
    expected_results[0].clear_messages()
    messages = rc1.messages()
    warning = [msg for msg in messages if "SUPERVIS_1" in msg.text]

    # message are duplicated in 13.5.9, fixed from 13.5.11
    assert_that(len(warning), greater_than_or_equal_to(1))
    assert_that(len(warning), less_than_or_equal_to(2))
    runner.cleanup()


@tempdir
def xtest_success_with_results(tmpdir, engine, server=None):
    # Test for runner with success, same result file used by the both stages
    nbs = 2
    rc1 = _setup_run_case(tmpdir, [0, 1])

    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))
    res0, res1 = expected_results

    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.result_state(res0) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)

    monitor_refresh(runner, estimated_time=10.)

    assert_that(runner.result_state(res0) & SO.Success)
    assert_that(runner.result_state(res1) & SO.Success)
    runner.cleanup()


@tempdir
def xtest_success(tmpdir, engine, server=None):
    """Test for runner with success"""
    nbs = 2
    rc1 = _setup_run_case(tmpdir, [0, 1], reusable_stages=range(2))

    # add a result file that can not be copied
    unit = 88
    if not os.access('/noaccess', os.W_OK):
        info88 = rc1[-1].handle2info[unit]
        info88.filename = osp.join('/noaccess/can_not_write')
        info88.attr = FileAttr.Out

    st = rc1[-1]
    out = st('IMPR_FONCTION')
    out['COURBE']['FONCTION'] = st['N4']
    out['UNITE'] = unit

    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))
    res0, res1 = expected_results

    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.result_state(res0) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=10.)

    assert_that(runner.result_state(res0) & SO.Success)
    if engine & Engine.Salome or server is None or server == "localhost":
        assert_that(runner.result_state(res1) & SO.Error)
    # fixit: asrun does not capture copyfile errors on servers
    elif engine & Engine.AsRun:
        assert_that(runner.result_state(res1) & SO.Success)
    runner.cleanup()

    assert_that(osp.exists(osp.join(tmpdir, 'a_result_dir', 'a_result_file')))
    assert_that(osp.exists(osp.join(rc1['s1'].folder, 'a_result_file')),
                equal_to(False))
    assert_that(osp.exists(osp.join(rc1['s2'].folder, 'a_result_file')),
                equal_to(False))

    # restart the same RunCase does nothing because seen as already finished
    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.is_finished())
    runner.start(params)
    runner.cleanup()

    # restart the "same" RunCase (same=that wants to use the same directory)
    # doesn't start because results directory exists.
    res0.state = SO.Waiting
    res1.state = SO.Waiting
    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(calling(runner.start).with_args(params),
                raises(RunnerError, "results already exist"))
    assert_that(runner.is_finished())
    runner.cleanup()

    # check for job description
    job = res0.job
    assert_that(job.description, empty())
    assert_that(job.full_description, contains_string("Start time"))
    assert_that(job.full_description,
                matches_regexp("Server name.*{0}".format(params['server'])))
    assert_that(job.full_description,
                matches_regexp("Version.*{0}".format(params['version'])))
    assert_that(job.full_description,
                matches_regexp("Memory limit.*{0}".format(params['memory'])))
    assert_that(job.full_description,
                matches_regexp("Time limit.*{0}".format(params['time'])))
    assert_that(job.full_description,
                matches_regexp("Number of nodes.*{0}".format(0)))
    assert_that(job.full_description,
                matches_regexp("Number of processors.*{0}".format(0)))
    assert_that(job.full_description,
                matches_regexp("Number of threads.*{0}".format(0)))


def _run_and_test(engine, server, rc1, tmpdir, rfolder=""):
    """Utility for xtest_remote, runs and test a runcase with 2 stages."""
    expected_results = rc1.results()
    assert_that(expected_results, has_length(2))
    res0, res1 = expected_results

    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.result_state(res1) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)

    # refresh is automatically done by the dashboard, here must be forced
    runner._infos.refresh_one(server)
    servcfg = runner._infos.server_config(server)

    remote_folder = new_directory(servcfg) if not rfolder else rfolder
    params['remote_folder'] = remote_folder
    runner.start(params)

    monitor_refresh(runner, estimated_time=10.)
    assert_that(runner.result_state(res0) & SO.Success)
    assert_that(runner.result_state(res1) & SO.Success)

    runner.cleanup()
    return runner, remote_folder

@tempdir
def xtest_remote(tmpdir, engine, server):
    """Test for runner with remote database left on server"""
    # Meant for remote servers only
    from asterstudy.datamodel.engine.engine_utils import remote_exec
    rc1 = _setup_run_case(tmpdir, [0, 1], reusable_stages=range(2))

    runner, remote_folder = _run_and_test(engine, server, rc1, tmpdir)

    # databases should be left on server, not copied locally
    assert_that(osp.isdir(rc1[0].database_path), equal_to(False))
    assert_that(osp.isdir(rc1[1].database_path), equal_to(False))

    # ---- Get host and user
    user = runner._infos.server_username(server)
    user = user if user else getpass.getuser()
    host = runner._infos.server_hostname(server)

    # ---- Test remote directory existence
    exists = "if [ -d {} ]; then echo True; else echo False; fi;".format(rc1[0].database_path)
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("True"))

    exists = "if [ -d {} ]; then echo True; else echo False; fi;".format(rc1[1].database_path)
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("True"))

    # Check that we can start a new remote execution from there
    hist = rc1.model
    rc2 = hist.create_run_case(exec_stages=1, reusable_stages=1, name='rc2')

    runner = _run_and_test(engine, server, rc2, tmpdir, remote_folder)

@tempdir
def xtest_remote_out_file(tmpdir, engine, server):
    """Test for runner with an out file left on server"""
    # Meant for remote servers only

    # Create run case
    nbs = 2
    rc1 = _setup_run_case(tmpdir, [0, 1], reusable_stages=range(2))

    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))
    res0, res1 = expected_results

    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.result_state(res0) & SO.Waiting)

    # Change out file to leave it on server

    # ---- Get host and user
    user = runner._infos.server_username(server)
    user = user if user else getpass.getuser()
    host = runner._infos.server_hostname(server)

    # ---- Set path on remote file system, clean if necessary
    relpath = ("/tmp/{0}_my_tmp_astudy_test/tmp-asterstudy-test-out-file"
               .format(USER))

    from asterstudy.datamodel.engine.engine_utils import remote_exec
    command = "if [ -f {0} ]; then rm {0}; fi;".format(relpath)
    remote_exec(user, host, command)

    exists = "if [ -f {} ]; then echo True; else echo False; fi;".format(relpath)
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("False"))

    # ---- Modify out file to provide remote url
    rc1[0].handle2info[44].filename = "sftp://" + user + "@" + host + relpath
    assert_that(rc1[0].handle2info[44].isremote, equal_to(True))

    params = _parameters(engine, server, wrkdir=tmpdir)

    # refresh is automatically done by the dashboard, here must be forced
    runner._infos.refresh_one(server)
    runner.start(params)
    monitor_refresh(runner, estimated_time=10.)

    assert_that(runner.result_state(res0) & SO.Success)
    assert_that(runner.result_state(res1) & SO.Success)
    runner.cleanup()

    # This time the out file should be created
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("True"))

@tempdir
def xtest_remote_in_file(tmpdir, engine, server):
    """Test for runner with an in file left on server"""
    # Meant for remote servers only

    # Create run case
    rc2 = _create_run_case_with_data(tmpdir)

    # Proceed as in `xtest_run_with_data`
    expected_results = rc2.results()
    assert_that(expected_results, has_length(1))
    result = expected_results[0]

    runner = runner_factory(engine, case=rc2, unittest=True)

    assert_that(runner.is_started(), equal_to(False))
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(runner.result_state(result) & SO.Waiting)

    # Modify in file to provide it straight on server

    # ---- retrieve original path
    info = rc2[0].handle2info[20]
    fname = info.filename

    # ---- Get host and user
    user = runner._infos.server_username(server)
    user = user if user else getpass.getuser()
    host = runner._infos.server_hostname(server)

    # ---- Set path on remote file system, clean if necessary (from `xtest_remote_out_file`)
    relpath = "/tmp/{0}_tmp-asterstudy-test-in-file".format(USER)

    from asterstudy.datamodel.engine.engine_utils import remote_exec
    command = "if [ -f {0} ]; then rm {0}; fi;".format(relpath)
    remote_exec(user, host, command)

    exists = "if [ -f {} ]; then echo True; else echo False; fi;".format(relpath)
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("False"))

    # ---- Modify in file to provide remote url (also from `xtest_remote_out_file`)
    theurl = "sftp://" + user + "@" + host + relpath
    info.filename = theurl

    # ---- Copy file on remote location
    dest = user + "@" + host + ":" + relpath
    command = "scp {0} {1}".format(fname, dest)
    remote_exec("", "localhost", command)

    # ---- Check file existence
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("True"))

    # Run with success
    params = _parameters(engine, server, wrkdir=tmpdir)
    params['memory'] = DEFAULT_PARAMS['memory'] + 123
    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))
    monitor_refresh(runner, estimated_time=5.)

    assert_that(runner.result_state(result) & SO.Success)
    runner.cleanup()

@tempdir
def xtest_several_stages(tmpdir, engine, server=None):
    """Test for runner with several stages and embedded files"""
    history = _setup_history(tmpdir)

    # start the first run case
    rc1 = history.create_run_case(exec_stages=0, name='rc1')
    rc1.make_run_dir()
    assert_that(rc1[0].is_intermediate(), equal_to(False))
    assert_that(rc1[0].is_without_db(), equal_to(False))

    expected_results = rc1.results()
    assert_that(expected_results, has_length(1))
    res0 = expected_results[0]

    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.result_state(res0) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=10.)

    assert_that(runner.result_state(res0) & SO.Success)
    runner.cleanup()

    # now start the second run case
    rc2 = history.create_run_case(exec_stages=1, name='rc2')
    rc2.make_run_dir()
    assert_that(rc2[1].is_intermediate(), equal_to(False))
    assert_that(rc2[1].is_without_db(), equal_to(False))

    expected_results = rc2.results()
    assert_that(expected_results, has_length(2))
    res1 = expected_results[1]

    #
    runner = runner_factory(engine, case=rc2, unittest=True)
    assert_that(runner.result_state(res1) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=10.)

    assert_that(runner.result_state(res1) & SO.Success)
    runner.cleanup()

    # start the third run case, with stages 3 and 4
    rc3 = history.create_run_case(exec_stages=[2, 3], reusable_stages=[2, 3],
                                  name='rc3')
    rc3.make_run_dir()
    assert_that(rc3[2].is_intermediate(), equal_to(False))
    assert_that(rc3[2].is_without_db(), equal_to(False))
    assert_that(rc3[3].is_intermediate(), equal_to(False))
    assert_that(rc3[3].is_without_db(), equal_to(False))

    expected_results = rc3.results()
    assert_that(expected_results, has_length(4))
    res2 = expected_results[2]
    res3 = expected_results[3]

    #
    runner = runner_factory(engine, case=rc3, unittest=True)
    assert_that(runner.result_state(res2) & SO.Waiting)
    assert_that(runner.result_state(res3) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=20.)

    # TODO: take <A>_COPY_DATA into account in the runner?
    #assert_that(runner.result_state(res2) & SO.Success)
    #assert_that(runner.result_state(res3) & SO.Success)

    # check that fileA was correctly moved for both stages
    unit_a = 44
    unit_b = 38
    unit_c = 39

    st3 = rc3[2]
    st4 = rc3[3]

    # the in file is referenced
    testdir = osp.join(tmpdir, rc1.name, 'Embedded')
    testname = osp.join(testdir, 'fileA.44')
    assert_that(st3.handle2info[unit_a].filename, equal_to(testname))
    assert_that(osp.isfile(testname), equal_to(True))

    testdir = osp.join(tmpdir, rc3.name, 'Embedded')
    testname = osp.join(testdir, 'fileA.44')
    assert_that(osp.isfile(testname), equal_to(False))

    # the inout file has been copied
    testdir = osp.join(tmpdir, rc3.name, 'Embedded')
    testname = osp.join(testdir, 'fileB.38')
    assert_that(st3.handle2info[unit_b].filename, equal_to(testname))
    assert_that(osp.isfile(testname), equal_to(True))

    testdir = osp.join(tmpdir, rc2.name, 'Embedded')
    testname = osp.join(testdir, 'fileB.38')
    assert_that(osp.isfile(testname), equal_to(True))

    # out file, not existing previously
    testdir = osp.join(tmpdir, rc3.name, 'Embedded')
    testname = osp.join(testdir, 'fileC.39')
    assert_that(st3.handle2info[unit_c].filename, equal_to(testname))
    assert_that(osp.isfile(testname), equal_to(True))

    # check the paths for stage 4
    #     - the in file is still referenced
    #     - nothing changed for the others
    testdir = osp.join(tmpdir, rc1.name, 'Embedded')
    testname = osp.join(testdir, 'fileA.44')
    assert_that(st4.handle2info[unit_a].filename, equal_to(testname))

    testdir = osp.join(tmpdir, rc3.name, 'Embedded')
    testname = osp.join(testdir, 'fileB.38')
    assert_that(st4.handle2info[unit_b].filename, equal_to(testname))

    testdir = osp.join(tmpdir, rc3.name, 'Embedded')
    testname = osp.join(testdir, 'fileC.39')
    assert_that(st4.handle2info[unit_c].filename, equal_to(testname))

    runner.cleanup()


@tempdir
def xtest_stop(tmpdir, engine, server=None):
    """Test for stop feature of runner"""
    nbs = 2
    rc1 = _setup_run_case(tmpdir, [0, 1], reusable_stages=range(nbs),
                          add="import time ; time.sleep(10)")
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(engine, case=rc1, unittest=True)
    assert_that(runner.result_state(expected_results[0]) & SO.Waiting)

    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    assert_that(runner.result_state(expected_results[0]) & SO.Running)
    runner.stop()
    assert_that(runner.result_state(expected_results[0]) & SO.Error)
    assert_that(runner.result_state(expected_results[1]) & SO.Waiting)
    # stopping again must not fail, just log a message
    runner.stop()
    time.sleep(0.25)
    runner.cleanup()


@tempdir
def xtest_reload(tmpdir, engine, server=None):
    """Test for close/reload of runner"""
    ajsfile = osp.join(tmpdir, 'asterstudy-reload.ajs')

    # use separated namespaces
    nbs = 1
    def step1():
        rc1 = _setup_run_case_for_load(ajsfile, 0)
        expected_results = rc1.results()
        assert_that(expected_results, has_length(nbs))
        # Test for message formatting: no output
        text = rc1.show_message()
        assert_that("Summary", is_not(is_in(text)))
        assert_that("#summary", is_in(text))
        assert_that("#bottom", is_not(is_in(text)))
        assert_that(text.count("<br />"), equal_to(1))

        runner = runner_factory(engine, case=rc1, unittest=True)

        assert_that(runner.result_state(expected_results[0]),
                                        equal_to(SO.Waiting))

        params = _parameters(engine, server, wrkdir=tmpdir)
        runner.start(params)
        assert_that(runner.result_state(expected_results[0]) & SO.Running)
        history = rc1.model
        History.save(history, ajsfile)
        return runner

    def step2():
        debug_message("Begin of step #2")
        history = History.load(ajsfile)
        history.folder = osp.splitext(ajsfile)[0] + '_Files'
        history.check_dir(History.warn)
        assert_that(history.run_cases, has_length(1))

        rc1 = history.run_cases[0]
        # Restart is not supported by Salome runner in interactive mode.
        # As the job always exists in SalomeLauncher, just keep 'jobid'
        for stg in rc1.stages:
            stg.result.job._assigned = True

        waiting = rc1[0].database_path
        debug_message("waiting for", waiting)
        run1 = runner_factory(engine, case=rc1, unittest=True)
        monitor_refresh(run1, 10.)
        assert_that(osp.exists(waiting))

        rc2 = history.create_run_case(exec_stages=1, name='rc2')
        expected_results = rc2.results()
        assert_that(expected_results, has_length(2))

        runner = runner_factory(engine, case=rc2, unittest=True)
        assert_that(runner.result_state(expected_results[1]) & SO.Waiting)
        params = _parameters(engine, server, wrkdir=tmpdir)
        runner.start(params)

        monitor_refresh(runner, estimated_time=5.)
        assert_that(runner.result_state(expected_results[1]) & SO.Success)

        # Test for message formatting: only the second output should be here
        text = rc2.show_message()
        assert_that("Summary", is_in(text))
        assert_that("#summary", is_in(text))
        assert_that(text.count("#bottom"), equal_to(1))
        assert_that(text.count("<br />"), greater_than(100))
        # if message does not exist
        os.remove(osp.join(rc2[1].folder, "message"))
        text = rc2.show_message()
        assert_that("Summary", is_in(text))
        assert_that("#summary", is_in(text))
        assert_that(text.count("#bottom"), equal_to(1))
        assert_that(text.count("<br />"), less_than(20))
        assert_that("job output should be available", is_in(text))
        return runner

    run1 = step1()
    run2 = step2()
    run1.cleanup()
    run2.cleanup()


@tempdir
def xtest_zzzz241a(tmpdir, engine, server=None):
    """Test for runner for zzzz241a + reuse"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zzzz241a.export')

    history = History()
    history.folder = tmpdir
    case, _ = history.import_case(export)
    nbs = len(case)
    rc1 = history.create_run_case(exec_stages=[0, 1], reusable_stages=[0, 1],
                                  name='rc1')
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(engine, case=rc1, unittest=True)
    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=15.)

    assert_that(runner.result_state(expected_results[0]) & SO.Success)
    assert_that(runner.result_state(expected_results[1]) & SO.Success)

    # reuse stage1 and rerun stage2
    rc2 = rc1.model.create_run_case(exec_stages=1, name='rc2')
    results2 = rc2.results()
    assert_that(results2, has_length(nbs))
    res1, res2 = results2
    assert_that(res1, same_instance(expected_results[0]))
    assert_that(res2, is_not(same_instance(expected_results[1])))
    assert_that(runner.result_state(res2) & SO.Waiting)
    runner.cleanup()

    runner = runner_factory(engine, case=rc2, unittest=True)
    runner.start(params)
    monitor_refresh(runner, estimated_time=5.)

    stage0 = expected_results[1].stage
    stage2 = res2.stage
    assert_that(runner.result_state(res2) & SO.Success)
    runner.cleanup()


@tempdir
def xtest_zzzz241a_once(tmpdir, engine, server=None):
    """Test for runner for zzzz241a at once"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zzzz241a.export')

    history = History()
    history.folder = tmpdir
    case, _ = history.import_case(export)
    nbs = len(case)
    rc1 = history.create_run_case(exec_stages=[0, 1], name='rc1')
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(engine, case=rc1, unittest=True)
    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=15.)

    assert_that(runner.result_state(expected_results[0]) & SO.Intermediate)
    assert_that(runner.result_state(expected_results[1]) & SO.Success)
    runner.cleanup()

    text = rc1.show_message()
    assert_that("Execution grouped", is_in(text))


@tempdir
def xtest_25975(tmpdir, engine, server=None):
    """Test for runner for adlv100a"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'adlv100a.export')

    history = History()
    history.folder = tmpdir
    case, _ = history.import_case(export)

    # run 1
    rc1 = history.create_run_case(name='rc1')
    res = rc1.results()
    runner = runner_factory(engine, case=rc1, unittest=True)
    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=15.)
    assert_that(runner.result_state(res[0]) & SO.Success)
    runner.cleanup()

    # run 2
    rc2 = history.create_run_case(name='rc2')
    res = rc2.results()
    runner = runner_factory(engine, case=rc2, unittest=True)
    params = _parameters(engine, server, wrkdir=tmpdir)
    runner.start(params)
    monitor_refresh(runner, estimated_time=15.)
    assert_that(runner.result_state(res[0]) & SO.Success)
    runner.cleanup()

    # Test for message formatting
    text = rc2.show_message(maxlines=10)
    assert_that("Summary", is_in(text))
    assert_that("#bottom", is_in(text))


@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def xtest_27166(tmpdir, engine, server=None):
    """Test for runner with intermediate stages"""
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zoom00.export')

    history = History()
    history.folder = tmpdir
    case, _ = history.import_case(export)

    # use a SMESH object to check that the mesh file is exported into the
    # right direction (of the first *intermediate* stage, not the last executed)
    input_mesh = osp.join(os.getenv('ASTERSTUDYDIR'),
                          'data', 'export', 'zoom00.med')
    with mock_object_creation(input_mesh) as entry:
        info = case[0].handle2info[20]
        info.filename = str(entry)

        # run 1
        rc1 = history.create_run_case([0, 2], [2], 'rc1')
        res = rc1.results()
        runner = runner_factory(engine, case=rc1, unittest=True)
        params = _parameters(engine, server, wrkdir=tmpdir)
        runner.start(params)
        monitor_refresh(runner, estimated_time=15.)
        assert_that(runner.result_state(res[0]) & SO.Intermediate)
        assert_that(runner.result_state(res[0]) & SO.Success)
        assert_that(runner.result_state(res[1]) & SO.Intermediate)
        assert_that(runner.result_state(res[1]) & SO.Success)
        assert_that(runner.result_state(res[2]) & SO.Success)
        runner.cleanup()

        # run 2
        rc2 = history.create_run_case([3, 3], [3], 'rc2')
        res = rc2.results()
        runner = runner_factory(engine, case=rc2, unittest=True)
        params = _parameters(engine, server, wrkdir=tmpdir)
        runner.start(params)
        monitor_refresh(runner, estimated_time=15.)
        assert_that(runner.result_state(res[3]) & SO.Success)
        runner.cleanup()


def xtest_userhost(engine):
    """Test for user/host parameters"""
    import socket
    infos = serverinfos_factory(engine)
    assert_that(infos.server_username("localhost"),
                is_in(['', getpass.getuser()]))
    assert_that(infos.server_hostname('localhost'),
                is_in(['localhost', socket.gethostname()]))


def _setup_run_case_for_load(ajsfile, exec_stages, fail=-1):
    """Wrapper when the accurate directory structure is required."""
    tmpdir = osp.splitext(ajsfile)[0] + '_Files'
    return _setup_run_case(tmpdir, exec_stages, fail=fail)

def _setup_run_case(tmpdir, exec_stages, reusable_stages=None, fail=-1, add=""):
    """Return a new history with a runnable 'current' case."""
    # This serves as run case for most of the tests
    # The same result file is used by stage 1 & 2
    unit = 44
    text1 = \
"""
DEBUT()

{1}

N1=DEFI_NAPPE(NOM_PARA='INST',
              PARA=(111., 222.),
              NOM_PARA_FONC='X',
              DEFI_FONCTION=(_F(VALE=(1.0,3.0,2.0,4.0,),),
                             _F(VALE=(1.0,3.0,2.0,4.0,),),),)


N2=DEFI_NAPPE(NOM_PARA='INST',
              PARA=(111.,222.),
              NOM_PARA_FONC='X',
              DEFI_FONCTION=(_F(VALE=(1.0,4.0,2.0,9.0,),),
                             _F(VALE=(1.0,4.0,2.0,9.0,),),),)

N3=DEFI_NAPPE(NOM_PARA='INST',
              PARA=(111.,222.),
              NOM_PARA_FONC='X',
              DEFI_FONCTION=(_F(VALE=(1.0,8.0,2.0,7.0,),),
                             _F(VALE=(1.0,8.0,2.0,7.0,),),),)

IMPR_FONCTION(COURBE=_F(FONCTION=N1), UNITE={0})

FIN()
""".format(unit, add)
    text2 = \
"""
POURSUITE()

N4=CALC_FONCTION(FRACTILE=_F(FONCTION=(N1,N2,N3),
                             FRACT=1.) )

TEST_FONCTION(VALEUR=_F(VALE_CALC=8.0,
                        VALE_REFE=8.0,
                        VALE_PARA=(222.0, 1.0),
                        REFERENCE='ANALYTIQUE',
                        NOM_PARA=('INST', 'X'),
                        FONCTION=N4,),
              )

IMPR_FONCTION(COURBE=_F(FONCTION=N4), UNITE={0})

FIN()
""".format(unit)
    failure = \
"""
POURSUITE(PAR_LOT='NON')

bad = DEFI_FONCTION(NOM_PARA='unauthorized parameter')

FIN()
"""
    history = History()

    # identical to gui/dashboard.py
    history.folder = tmpdir
    cc = history.current_case
    cc.name = 'c1'
    cc.text2stage(text1 if fail != 0 else failure, 's1')
    cc.text2stage(text2 if fail != 1 else failure, 's2')
    cc.create_stage('s3')
    # add a result file
    for i in [0, 1]:
        info44 = cc[i].handle2info[unit]
        info44.filename = osp.join(tmpdir, 'a_result_dir', 'a_result_file')
        info44.attr = FileAttr.Out
        assert_that(info44.exists, equal_to(False))

    run_case = history.create_run_case(exec_stages=exec_stages,
                                       reusable_stages=reusable_stages,
                                       name='rc1')
    return run_case

def _create_run_case_with_data(tmpdir):
    """Create a run case with some in file"""
    unit = 20
    text = """
DEBUT()

mesh = LIRE_MAILLAGE(FORMAT='MED', UNITE={0})

FIN()
""".format(unit)
    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c2'
    stage = case.create_stage('s1')
    comm2study(text, stage)
    # add mesh file
    info = stage.handle2info[unit]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'export', 'forma13a.20')
    assert_that(stage.handle2file(unit), is_not(None))
    rc2 = history.create_run_case(name='rc2')
    return rc2

def _setup_history(folder):
    """Return a new history with 4 stages and embedded files."""
    # -----------------------------------------------------------------------
    # First stage with an embedded out file A
    unit_a = 44
    text1 = \
"""
DEBUT()

N1=DEFI_NAPPE(NOM_PARA='INST',
              PARA=(111., 222.),
              NOM_PARA_FONC='X',
              DEFI_FONCTION=(_F(VALE=(1.0,3.0,2.0,4.0,),),
                             _F(VALE=(1.0,3.0,2.0,4.0,),),),)


N2=DEFI_NAPPE(NOM_PARA='INST',
              PARA=(111.,222.),
              NOM_PARA_FONC='X',
              DEFI_FONCTION=(_F(VALE=(1.0,4.0,2.0,9.0,),),
                             _F(VALE=(1.0,4.0,2.0,9.0,),),),)

N3=DEFI_NAPPE(NOM_PARA='INST',
              PARA=(111.,222.),
              NOM_PARA_FONC='X',
              DEFI_FONCTION=(_F(VALE=(1.0,8.0,2.0,7.0,),),
                             _F(VALE=(1.0,8.0,2.0,7.0,),),),)

IMPR_FONCTION(COURBE=_F(FONCTION=N1), UNITE={0})

FIN()
""".format(unit_a)

    # -----------------------------------------------------------------------
    # second stage with an embedded in file B
    unit_b = 38
    text2 = \
"""
POURSUITE()

N4=CALC_FONCTION(FRACTILE=_F(FONCTION=(N1,N2,N3),
                             FRACT=1.) )

N5=LIRE_FONCTION(UNITE={0},
                 TYPE='NAPPE',
                 NOM_PARA='INST',
                 INDIC_PARA=[4,1],
                 NOM_PARA_FONC='FREQ',
                 INDIC_ABSCISSE= [2,2],
                 DEFI_FONCTION= (_F(INDIC_RESU = [3,1], ),
                                 _F(INDIC_RESU = [2,3], ),
                                )
                 )

FIN()
""".format(unit_b)

    # -----------------------------------------------------------------------
    # third stage with embedded in, inout and out files A, B, C
    unit_c = 39
    text3 = \
"""
POURSUITE()

N6=LIRE_FONCTION(UNITE={0},
                 NOM_PARA='INST',
                 INDIC_PARA=[1, 1],
                 INDIC_RESU=[1, 2]
                 )

N7=LIRE_FONCTION(UNITE={1},
                 TYPE='NAPPE',
                 NOM_PARA='INST',
                 INDIC_PARA=[4,1],
                 NOM_PARA_FONC='FREQ',
                 INDIC_ABSCISSE= [2,2],
                 DEFI_FONCTION= (_F(INDIC_RESU = [3,1], ),
                                 _F(INDIC_RESU = [2,3], ),
                                )
                 )
IMPR_FONCTION(COURBE=_F(FONCTION=N7), UNITE={1})

IMPR_FONCTION(COURBE=_F(FONCTION=N6), UNITE={2})


FIN()
""".format(unit_a, unit_b, unit_c)

    # -----------------------------------------------------------------------
    # fourth stage with embedded in, inout and out files A, B, C
    text4 = \
"""
POURSUITE()

N8=LIRE_FONCTION(UNITE={0},
                 NOM_PARA='INST',
                 INDIC_PARA=[1, 1],
                 INDIC_RESU=[1, 2]
                 )

N9=LIRE_FONCTION(UNITE={1},
                 TYPE='NAPPE',
                 NOM_PARA='INST',
                 INDIC_PARA=[4,1],
                 NOM_PARA_FONC='FREQ',
                 INDIC_ABSCISSE= [2,2],
                 DEFI_FONCTION= (_F(INDIC_RESU = [3,1], ),
                                 _F(INDIC_RESU = [2,3], ),
                                )
                 )
IMPR_FONCTION(COURBE=_F(FONCTION=N8), UNITE={1})

IMPR_FONCTION(COURBE=_F(FONCTION=N9), UNITE={2})


FIN()
""".format(unit_a, unit_b, unit_c)


    history = History()
    history.folder = folder
    cc = history.current_case
    cc.name = 'c1'
    cc.text2stage(text1, 's1')
    cc.text2stage(text2, 's2')
    cc.text2stage(text3, 's3')
    cc.text2stage(text4, 's4')

    # inout attr is automatically set during import of the texts

    # add the files to handle, first stage
    info = cc[0].handle2info[unit_a]
    info.filename = osp.join(history.tmpdir, 'fileA.44')
    info.embedded = True
    assert_that(info.exists, equal_to(False))

    # add the files to handle, second stage
    info = cc[1].handle2info[unit_b]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                               'data', 'export', 'fileB.38')
    info.embedded = True
    assert_that(info.exists, equal_to(True))

    # add the files to handle, third stage
    info = cc[2].handle2info[unit_a]
    info.filename = osp.join(history.tmpdir, 'fileA.44')
    info.embedded = True

    info = cc[2].handle2info[unit_b]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                               'data', 'export', 'fileB.38')
    info.embedded = True


    info = cc[2].handle2info[unit_c]
    info.filename = osp.join(history.tmpdir, 'fileC.39')
    info.embedded = True

    # add the files to handle, fourth stage
    info = cc[3].handle2info[unit_a]
    info.filename = osp.join(history.tmpdir, 'fileA.44')
    info.embedded = True


    info = cc[3].handle2info[unit_b]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                               'data', 'export', 'fileB.38')
    info.embedded = True


    info = cc[3].handle2info[unit_c]
    info.filename = osp.join(history.tmpdir, 'fileC.39')
    info.embedded = True

    return history
