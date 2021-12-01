# coding=utf-8

# Copyright 2016 - 2019 EDF R&D
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

"""Automatic tests for calculation wizards."""


import os
import os.path as osp
import unittest
from collections import OrderedDict

from PyQt5 import Qt as Q

import testutils.gui_utils
from asterstudy.api import Calculation
from asterstudy.assistant import Runner, from_config, generate_wizard_from_file
from asterstudy.datamodel import FileAttr
from asterstudy.datamodel.result import StateOptions
from common_test_gui import get_application
from hamcrest import *
from testutils import tempdir
from testutils.assist import check_runner

_multiprocess_can_split_ = True


def setup():
    get_application()


def from_files(directory, stage_suffix=''):
    path = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'resources', 'assistants', directory)
    with open(osp.join(path, 'declaration.json')) as dfile:
        declaration = dfile.read()
    wizpy = osp.join(path, 'wizard.py')
    if osp.isfile(wizpy):
        with open(wizpy) as wfile:
            wizard = wfile.read()
    else:
        wizard = generate_wizard_from_file(osp.join(path, 'declaration.json'))
    with open(osp.join(path, 'template.comm')) as tfile:
        template = tfile.read()
    return declaration, wizard, template


def data(filename):
    return osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'assistant', filename)


@tempdir
def test_gc(tmpdir):
    value = {
        'INTRO': '',
        'INPUTPOU': {20: data("forma43a.20.med")},
        'GROUP_BEAM': 'POUTRE',
        'INPUTSEC': {22: data("forma43a.22.med")},
        'CBETON': "C30/37",
        'SIGY_ACIER': 400.e6,
        'VALE_TRIPLET': (-0.056, -0.206, 0.032,
                         0.056, -0.206, 0.032,
                         -0.08, 0.218, 0.008,
                         0.08, 0.218, 0.008),
        'OUTPUTFIBSEC': {80: osp.join(tmpdir, 'sect.med')},
        'OUTPUTREPLOC': {81: osp.join(tmpdir, 'coord.med')},
        'OUTPUTFIBPOS': {82: osp.join(tmpdir, 'posit.med')},
        'BC': [OrderedDict(GROUP_NO='A', DX=0, DY=0, DZ=0, DRX=0, DRY=0),
               OrderedDict(GROUP_NO='B', DY=0)],
        'LOAD': [OrderedDict(GROUP_NO='C', DY=-0.01)],
        'TIME': [OrderedDict(JUSQU_A=0.1, NOMBRE=2, COEF=0.1),
                 OrderedDict(JUSQU_A=3.2, NOMBRE=20, COEF=3.2)],
        'SUBD': 'YES_SUBD',
        'SUBD_PAS1': 10,
        'SUBD_NIVEAU1': 10,
        'OUTPUT': {90: osp.join(tmpdir, 'resu.med')},
    }
    # --- special `wizard.value()` method
    intervalle = tuple(list(value['TIME']))
    value['INSTFIN'] = intervalle[-1]['JUSQU_A']
    value['FOMULT'] = [0., 0.]
    for time in intervalle:
        value['FOMULT'].extend([time['JUSQU_A'], time['COEF']])
        del time['COEF']
    value['INTERVALLE'] = tuple(intervalle)
    # --- end of `wizard.value()` method

    _, wiz, templ = from_files('tpgeniecivil')
    runner = check_runner(wiz, templ, value)

    calc = Calculation(tmpdir)
    calc.add_stage_from_string(runner.stage_data)
    calc.add_file(data("forma43a.20.med"), 20, FileAttr.In)
    calc.add_file(data("forma43a.22.med"), 22, FileAttr.In)
    calc.use_interactive()
    calc.run()
    assert_that(calc.state & StateOptions.Success)


@tempdir
def test_thermic(tmpdir):
    value = {
        'INTRO': '',
        'INPUT': {20: data('forma01a.20.med')},
        'MODELISATION': 'PLAN',
        'LAMBDA': 0.54,
        'BC': OrderedDict(GROUP_MA='bas', TEMP=20.0),
        'COND_STREAM': 'YES_STREAM',
        'FLUX_REP1': OrderedDict(GROUP_MA='haut', FLUN=50.0),
        'COND_SOURCE': 'NO_SOURCE',
        'OUTPUT': {80: osp.join(tmpdir, 'resu.med')}
    }
    _, wiz, templ = from_files('thermic')
    runner = check_runner(wiz, templ, value)

    calc = Calculation(tmpdir)
    calc.add_stage_from_string(runner.stage_data)
    calc.add_file(data("forma01a.20.med"), 20, FileAttr.In)
    calc.use_interactive()
    calc.run()
    assert_that(calc.state & StateOptions.Success)


@tempdir
def test_elastic(tmpdir):
    value = {
        'INTRO': '',
        'INPUT': {20: data('forma01a.20.med')},
        'MODELISATION': 'C_PLAN',
        'E': 2.1e11,
        'NU': 0.3,
        'BC': [OrderedDict(GROUP_MA='bas', DY=0.0),
               OrderedDict(GROUP_MA='gauche', DX=0.0)],
        'LOAD': OrderedDict(GROUP_MA='haut', PRES=-100),
        'OUTPUT': {80: osp.join(tmpdir, 'resu.med')}
    }
    _, wiz, templ = from_files('elastic')
    runner = check_runner(wiz, templ, value)

    calc = Calculation(tmpdir)
    calc.add_stage_from_string(runner.stage_data)
    calc.add_file(data("forma01a.20.med"), 20, FileAttr.In)
    calc.use_interactive()
    calc.run()
    assert_that(calc.state & StateOptions.Success)


@tempdir
def test_thermomeca(tmpdir):
    value = {
        'INTRO': '',
        'INPUT': {20: data('forma01a.20.med')},
        'MODELISATIONTH': 'PLAN',
        'LAMBDA': 0.54,
        'E': 210000000000.0,
        'NU': 0.3,
        'ALPHA': 0.54,
        'RHO_CP': 0.0,
        'BCTH': OrderedDict(GROUP_MA='bas', TEMP=20.0),
        'COND_STREAM': 'NO_STREAM',
        'COND_SOURCE': 'NO_SOURCE',
        'INIT': 0.0,
        'VALE': (5, 10, 15),
        'MODELISATIONMECA': 'C_PLAN',
        'BC_MECH': [OrderedDict(GROUP_MA='bas', DY=0.0),
                    OrderedDict(GROUP_MA='gauche', DX=0.0)],
        'LOAD': OrderedDict(GROUP_MA='haut', PRES=-100),
        'OUTPUT': {80: osp.join(tmpdir, 'resu.med')}
    }
    _, wiz, templ = from_files('thermomeca')
    runner = check_runner(wiz, templ, value)

    calc = Calculation(tmpdir)
    calc.add_stage_from_string(runner.stage_data)
    calc.add_file(data("forma01a.20.med"), 20, FileAttr.In)
    calc.use_interactive()
    calc.run()
    assert_that(calc.state & StateOptions.Success)


@tempdir
def test_modal(tmpdir):
    value = {
        'INTRO': '',
        'INPUT': {20: data('forma01a.20.med')},
        'MODELISATION': 'C_PLAN',
        'E': 210000000000.0,
        'RHO': 7800.0,
        'NU': 0.3,
        'BC': [OrderedDict(GROUP_MA='bas', DY=0.0),
               OrderedDict(GROUP_MA='gauche', DX=0.0)],
        'MODES': 'PETITE',
        'FREQ_PETITE_NMAX': 5,
        'OUTPUT': {80: osp.join(tmpdir, 'resu.med')}
    }
    _, wiz, templ = from_files('modal')
    runner = check_runner(wiz, templ, value)

    calc = Calculation(tmpdir)
    calc.add_stage_from_string(runner.stage_data)
    calc.add_file(data("forma01a.20.med"), 20, FileAttr.In)
    calc.use_interactive()
    calc.run()
    assert_that(calc.state & StateOptions.Success)


@tempdir
def test_fracture(tmpdir):
    value = {
        'INTRO': '',
        'INPUT': {20: data('sslv322a.20.med')},
        'MODELISATION': '3DNOSYM',
        'FISS3DNOSYM': OrderedDict(GROUP_MA='FONDFISS'),
        'LEV_INF3D': OrderedDict(GROUP_MA='FACE2'),
        'LEV_SUP3D': OrderedDict(GROUP_MA='FACE1'),
        'RINF': 0.016,
        'RSUP': 0.032,
        'E': 210000000000.0,
        'NU': 0.3,
        'BC': OrderedDict(GROUP_MA='bas', DX=0.0, DY=0.0, DZ=0.0),
        'LOAD': OrderedDict(GROUP_MA=('FACE1', 'FACE2', 'inter'), PRES=1000000.0),
        'OUTPUTRES': {80: osp.join(tmpdir, 'resu.med')},
        'OUTPUTG': {81: osp.join(tmpdir, 'tabl.txt')},
        'POSTK': 'YES_POSTK',
        'ABSC_CURV_MAXI': 0.1,
        'OUTPUTPOSTK': {83: osp.join(tmpdir, 'postk.txt')}
    }
    _, wiz, templ = from_files('fracture')
    runner = check_runner(wiz, templ, value)

    calc = Calculation(tmpdir)
    calc.add_stage_from_string(runner.stage_data)
    calc.add_file(data("sslv322a.20.med"), 20, FileAttr.In)
    calc.use_interactive()
    calc.run()
    assert_that(calc.state & StateOptions.Success)

@tempdir
def test_contact(tmpdir):
    value = {
        'INTRO': '',
        'INPUT': {20: data('ssnp170a.20.med')},
        'MODELISATION': 'D_PLAN',
        'E': 2000.0,
        'NU': 0.3,
        'BC': [OrderedDict(GROUP_MA='Sym', DX=0.0),
               OrderedDict(GROUP_MA='Group_3', DY=0.0),],
        'LOAD': [OrderedDict(GROUP_MA='Group_4', PRES=25.0)],
        'CONTACT': 'LAC',
        'ZONES': [OrderedDict(GROUP_MA_MAIT='Group_2',
                              GROUP_MA_ESCL='Group_1'),],
    }
    # --- special `wizard.value()` method
    groups = []
    slave_zones = []
    zones = []
    for zone in value['ZONES']:
        zone.update(dict(ALGO_CONT=value['CONTACT']))
        zones.append(zone)
        slave_zones.append(zone['GROUP_MA_ESCL'])
        groups.append(zone['GROUP_MA_MAIT'])
    value['ZONES'] = tuple(zones)
    value['SLAVE_ZONES'] = tuple(set(slave_zones)) # groups must not repeat!
    groups.extend(slave_zones)
    for load in value['LOAD']:
        groups.append(load['GROUP_MA'])
    value['ORIE_GROUPS'] = tuple(set(groups))
    # --- end of `wizard.value()` method

    _, wiz, templ = from_files('contact')
    runner = check_runner(wiz, templ, value)

    calc = Calculation(tmpdir)
    calc.add_stage_from_string(runner.stage_data)
    calc.add_file(data("ssnp170a.20.med"), 20, FileAttr.In)
    calc.use_interactive()
    calc.run()
    assert_that(calc.state & StateOptions.Success)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
