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

"""Automatic tests for calculation assistant (issue 1720)."""


import os
import os.path as osp
import unittest

from PyQt5 import Qt as Q

import testutils.gui_utils
from asterstudy.assistant import (Runner, from_config,
                                  generate_wizard_from_file,
                                  generate_wizard_from_string)
from common_test_gui import get_application
from hamcrest import *
from testutils import tempdir

_multiprocess_can_split_ = True

def setup():
    get_application()

#------------------------------------------------------------------------------
def from_files(directory, stage_suffix=''):
    path = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'assistant', directory)
    with open(os.path.join(path, 'declaration.json')) as dfile:
        declaration = dfile.read()
    with open(os.path.join(path, 'wizard.py')) as wfile:
        wizard = wfile.read()
    with open(os.path.join(path, 'template.comm')) as tfile:
        template = tfile.read()
    with open(os.path.join(path, 'stage{suffix}.comm').format(suffix=stage_suffix)) as sfile:
        stage = sfile.read()
    return declaration, wizard, template, stage

#------------------------------------------------------------------------------
def use_case_01():
    # ----------------------------------
    # Assistant "data/assistant/simple1"
    # ----------------------------------
    return from_files('simple1')

#------------------------------------------------------------------------------
def use_case_02():
    # ----------------------------------
    # Assistant "data/assistant/simple2"
    # ----------------------------------
    return from_files('simple2')

#------------------------------------------------------------------------------
def use_case_03():
    # ----------------------------------
    # Assistant "data/assistant/simple3"
    # ----------------------------------
    return from_files('simple3')

#------------------------------------------------------------------------------
def use_case_04():
    # ----------------------------------
    # Assistant "data/assistant/simple4"
    # ----------------------------------
    return from_files('simple4')

#------------------------------------------------------------------------------
def use_case_05(case):
    # ----------------------------------
    # Assistant "data/assistant/simple5"
    # ----------------------------------
    return from_files('simple5', stage_suffix='_{}'.format(case))

#------------------------------------------------------------------------------
def test_generator_invalid_format():
    """Check generator: invalid format"""
    declaration = """
{
  "title": "Test calculation assistant",
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), raises(ValueError))

#------------------------------------------------------------------------------
def test_generator_old_format_01():
    """Check generator: old format (version unknown)"""
    declaration = """
{
  "title": "Test calculation assistant"
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), raises(ImportError))

#------------------------------------------------------------------------------
def test_generator_old_format_02():
    """Check generator: old format (version < 2.0)"""
    declaration = """
{
  "title": "Test calculation assistant",
  "format": "1.1"
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), raises(ImportError))

#------------------------------------------------------------------------------
def test_generator_duplicated_param():
    """Check generator: duplicated parameter"""
    declaration = """
{
  "title": "Test calculation assistant",
  "format": "2.0",
  "pages": [
    {
      "title": "Page 1",
      "parameters": [
        {
          "name": "PARAM1",
          "typ": "int"
        }
      ]
    },
    {
      "title": "Page 2",
      "parameters": [
        {
          "name": "PARAM1",
          "typ": "int"
        }
      ]
    }
  ]
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), raises(ImportError))

#------------------------------------------------------------------------------
def test_generator_unnamed_param():
    """Check generator: unnamed parameter"""
    declaration = """
{
  "title": "Test calculation assistant",
  "format": "2.0",
  "pages": [
    {
      "title": "Page 1",
      "parameters": [
        {
          "typ": "int"
        }
      ]
    }
  ]
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), raises(ImportError))

#------------------------------------------------------------------------------
def test_generator_bad_type():
    """Check generator: unsupported parameter type"""
    declaration = """
{
  "title": "Test calculation assistant",
  "format": "2.0",
  "pages": [
    {
      "title": "Page 1",
      "parameters": [
        {
          "name": "PARAM1",
          "typ": "unsupported"
        }
      ]
    }
  ]
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), raises(ImportError))

#------------------------------------------------------------------------------
def test_generator_empty_type():
    """Check generator: empty type"""
    declaration = """
{
  "title": "Test calculation assistant",
  "format": "2.0",
  "pages": [
    {
      "title": "Page 1",
      "parameters": [
        {
          "name": "PARAM1"
        }
      ]
    }
  ]
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), not_(raises(ImportError)))

#------------------------------------------------------------------------------
def test_generator_table_bad_column():
    """Check generator: empty type"""
    declaration = """
{
  "title": "Test calculation assistant",
  "format": "2.0",
  "pages": [
    {
      "title": "Page 1",
      "parameters": [
        {
          "name": "PARAM1",
          "typ": "table",
          "columns": [
            {
              "typ": "int"
            }
          ]
        }
      ]
    }
  ]
}
"""
    assert_that(calling(generate_wizard_from_string).with_args(declaration), raises(ImportError))

#------------------------------------------------------------------------------
def check_generator(declaration, wizard):
    output = generate_wizard_from_string(declaration)
    assert_that(output, equal_to(wizard))

#------------------------------------------------------------------------------
def test_generator_case_01():
    """Check generator: use case 01"""
    declaration, wizard, _, _ = use_case_01()
    check_generator(declaration, wizard)

#------------------------------------------------------------------------------
def test_generator_case_02():
    """Check generator: use case 02"""
    declaration, wizard, _, _ = use_case_02()
    check_generator(declaration, wizard)

#------------------------------------------------------------------------------
def test_generator_case_03():
    """Check generator: use case 03"""
    declaration, wizard, _, _ = use_case_03()
    check_generator(declaration, wizard)

#------------------------------------------------------------------------------
def test_generator_case_04():
    """Check generator: use case 04"""
    declaration, wizard, _, _ = use_case_04()
    check_generator(declaration, wizard)

#------------------------------------------------------------------------------
def test_generator_case_05():
    """Check generator: use case 05"""
    declaration, wizard, _, _ = use_case_05(1)
    check_generator(declaration, wizard)

#------------------------------------------------------------------------------
def test_generator_from_file_case_01():
    """Check generator: generate_wizard_from_file(): use case 01"""
    directory = 'simple1'
    path = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'assistant', directory)
    description_file = os.path.join(path, 'declaration.json')
    with open(os.path.join(path, 'wizard.py')) as wfile:
        wizard = wfile.read()
    assert_that(generate_wizard_from_file(description_file), equal_to(wizard))

#------------------------------------------------------------------------------
def test_runner_null_wizard_data():
    """Check runner: null wizard data"""
    runner = Runner(None)
    assert_that(calling(runner.runWizard), raises(ValueError))

#------------------------------------------------------------------------------
def check_runner(wizard, template, stage, case=None):
    runner = Runner(None)
    runner.wizard_data = wizard
    runner.template_data = template
    runner.createWizard()
    from asterstudy.assistant.widgets import TableWidget, Choices

    for widget in runner.wizard.widgets:
        if isinstance(widget, TableWidget):
            widget._addRow() # table shouldn't be empty
        if isinstance(widget, Choices) and case is not None:
            choices = list(widget.choices.keys())
            choices[case-1].setChecked(True)

    def _mock_function(cls, int):
        return True

    runner.wizard.__class__.hasVisitedPage = classmethod(_mock_function)

    uids = runner.wizard.pageIds()
    for uid in uids:
        runner.wizard.page(uid).validatePage()

    runner._wizardFinished(1) # Q.QDialog.Accepted
    assert_that(runner.stage_data, equal_to(stage))

#------------------------------------------------------------------------------
def test_runner_case_01():
    """Check runner: use case 01"""
    _, wizard, template, stage = use_case_01()
    check_runner(wizard, template, stage)

#------------------------------------------------------------------------------
def test_runner_case_02():
    """Check runner: use case 02"""
    _, wizard, template, stage = use_case_02()
    check_runner(wizard, template, stage)

#------------------------------------------------------------------------------
def test_runner_case_03():
    """Check runner: use case 03"""
    _, wizard, template, stage = use_case_03()
    check_runner(wizard, template, stage)

#------------------------------------------------------------------------------
def test_runner_case_04():
    """Check runner: use case 04"""
    _, wizard, template, stage = use_case_04()
    check_runner(wizard, template, stage)

#------------------------------------------------------------------------------
def test_runner_case_05_01():
    """Check runner: use case 05, choice 1"""
    _, wizard, template, stage = use_case_05(1)
    check_runner(wizard, template, stage, case=1)

#------------------------------------------------------------------------------
def test_runner_case_05_02():
    """Check runner: use case 05, choice 2"""
    _, wizard, template, stage = use_case_05(2)
    check_runner(wizard, template, stage, case=2)

#------------------------------------------------------------------------------
def test_runner_case_05_03():
    """Check runner: use case 05, choice 3"""
    _, wizard, template, stage = use_case_05(3)
    check_runner(wizard, template, stage, case=3)

#------------------------------------------------------------------------------
def test_runner_case_05_04():
    """Check runner: use case 05, choice 4"""
    _, wizard, template, stage = use_case_05(4)
    check_runner(wizard, template, stage, case=4)

#------------------------------------------------------------------------------
def check_generator_2_runner(declaration, template, stage, case=None):
    runner = Runner(None)
    wizard = generate_wizard_from_string(declaration)
    runner.wizard_data = str(wizard)
    runner.template_data = template
    runner.createWizard()
    from asterstudy.assistant.widgets import TableWidget, Choices

    for widget in runner.wizard.widgets:
        if isinstance(widget, TableWidget):
            widget._addRow() # table shouldn't be empty
        if isinstance(widget, Choices) and case is not None:
            choices = list(widget.choices.keys())
            choices[case-1].setChecked(True)

    def _mock_function(cls, int):
        return True

    runner.wizard.__class__.hasVisitedPage = classmethod(_mock_function)

    uids = runner.wizard.pageIds()
    for uid in uids:
        runner.wizard.page(uid).validatePage()

    runner._wizardFinished(1) # Q.QDialog.Accepted
    assert_that(runner.stage_data, equal_to(stage))

#------------------------------------------------------------------------------
def test_generator_2_runner_case_01():
    """Check generator -> runner: use case 01"""
    declaration, _, template, stage = use_case_01()
    check_generator_2_runner(declaration, template, stage)

#------------------------------------------------------------------------------
def test_generator_2_runner_case_02():
    """Check generator -> runner: use case 02"""
    declaration, _, template, stage = use_case_02()
    check_generator_2_runner(declaration, template, stage)

#------------------------------------------------------------------------------
def test_generator_2_runner_case_03():
    """Check generator -> runner: use case 03"""
    declaration, _, template, stage = use_case_03()
    check_generator_2_runner(declaration, template, stage)

def test_generator_2_runner_case_04():
    """Check generator -> runner: use case 04"""
    declaration, _, template, stage = use_case_04()
    check_generator_2_runner(declaration, template, stage)

#------------------------------------------------------------------------------
def test_generator_2_runner_case_05_01():
    """Check generator -> runner: use case 05, choice 1"""
    declaration, _, template, stage = use_case_05(1)
    check_generator_2_runner(declaration, template, stage, case=1)

#------------------------------------------------------------------------------
def test_generator_2_runner_case_05_02():
    """Check generator -> runner: use case 05, choice 2"""
    declaration, _, template, stage = use_case_05(2)
    check_generator_2_runner(declaration, template, stage, case=2)

#------------------------------------------------------------------------------
def test_generator_2_runner_case_05_03():
    """Check generator -> runner: use case 05, choice 3"""
    declaration, _, template, stage = use_case_05(3)
    check_generator_2_runner(declaration, template, stage, case=3)

#------------------------------------------------------------------------------
def test_generator_2_runner_case_05_04():
    """Check generator -> runner: use case 05, choice 4"""
    declaration, _, template, stage = use_case_05(4)
    check_generator_2_runner(declaration, template, stage, case=4)

#------------------------------------------------------------------------------
def test_runner_duplicated_param():
    """Check runner: duplicated parameter"""
    wizard = \
"""
from asterstudy.assistant import widgets as AW
class Wizard(AW.Wizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.register("PARAM1", None)
        self.register("PARAM1", None)

def create_wizard(parent):
    return Wizard(parent)
"""
    assert_that(calling(check_runner).with_args(wizard, '', ''), raises(KeyError))

#------------------------------------------------------------------------------
def test_runner_table_unnamed_column():
    """Check runner: table with unnamed column"""
    wizard = \
"""
from asterstudy.assistant import widgets as AW
class Wizard(AW.Wizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        widget = AW.TableWidget('')
        widget.addColumn("", "aaaa")

def create_wizard(parent):
    return Wizard(parent)
"""
    assert_that(calling(check_runner).with_args(wizard, '', ''), raises(KeyError))

#------------------------------------------------------------------------------
def test_runner_table_duplicated_column():
    """Check runner: table with duplicated column"""
    wizard = \
"""
from asterstudy.assistant import widgets as AW
class Wizard(AW.Wizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        widget = AW.TableWidget('')
        widget.addColumn("aaaa", "aaaa")
        widget.addColumn("aaaa", "bbbb")

def create_wizard(parent):
    return Wizard(parent)
"""
    assert_that(calling(check_runner).with_args(wizard, '', ''), raises(KeyError))

#------------------------------------------------------------------------------
def test_runner_api():
    """Check runner: api usage"""
    from asterstudy.assistant.widgets import MeshSelector

    _, wizard, template, stage = use_case_04()
    runner = Runner(None)
    runner.wizard_data = wizard
    runner.template_data = template
    runner.createWizard()
    wizard = runner.wizard

    assert_that(wizard.uid('AAA'), none())
    widget = wizard.widget('INPUT_FILE')
    assert_that(widget, not_none())
    assert_that(wizard.uid(widget), equal_to('INPUT_FILE'))
    assert_that(wizard.widget('MESH', typ=MeshSelector), not_none())
    assert_that(wizard.widget(None, typ=MeshSelector), not_none())
    assert_that(wizard.widget(None), not_none())
    assert_that(wizard.widget('AAA'), none())

#------------------------------------------------------------------------------
def test_runner_logic():
    """Check runner: api business logic"""
    _, wizard, template, stage = use_case_04()
    runner = Runner(None)
    runner.wizard_data = wizard
    runner.template_data = template
    runner.createWizard()
    wizard = runner.wizard
    uids = wizard.pageIds()

    def _mock_function(*args, **kwargs):
        raise RuntimeError('invalid input')

    Q.QMessageBox.critical = classmethod(_mock_function)

    widget = wizard.widget('INPUT_FILE')
    # check default value
    assert_that(widget._filters(), has_length(3))
    assert_that(widget.isEmpty(), equal_to(False))
    assert_that(widget.fileName(), equal_to('bar.txt'))
    assert_that(widget.value(), equal_to({21:'bar.txt'}))
    # set empty value
    widget.setValue('')
    assert_that(widget.isEmpty(), equal_to(True))
    assert_that(widget.fileName(), equal_to(''))
    assert_that(widget.value(), equal_to({21:None}))
    # try to validate
    page = wizard.page(uids[0])
    assert_that(calling(page.validatePage), raises(RuntimeError))
    # set good value
    widget.setValue('foobar.xyz')
    assert_that(calling(page.validatePage), not_(raises(RuntimeError)))

    widget = wizard.widget('MESH')
    assert_that(widget._filters(), has_length(2))
    assert_that(widget.fileName(), equal_to('foo.med'))
    #path = osp.join(os.getenv('ASTERSTUDYDIR'), 'test', 'squish', 'shared', 'testdata', 'Mesh_recette.med')
    # try to set null value
    widget.setValue(None)
    assert_that(widget.fileName(), equal_to('foo.med'))
    # insert some new file (simulate browsing via Open File dialog)
    widget.setValue('aaa.med')
    assert_that(widget.fileName(), equal_to('aaa.med'))
    # choose original file (simulate selecting from combo box)
    widget.setValue('foo.med')
    assert_that(widget.fileName(), equal_to('foo.med'))

#------------------------------------------------------------------------------
def test_runner_empty_choice():
    """Check runner: empty choice"""
    declaration = """
{
  "title": "Test calculation assistant",
  "format": "2.1",
  "pages": [
    {
      "title": "Page 1",
      "parameters": [
        {
          "name": "CHOICE",
          "typ": "choice",
          "choices": [
            {
              "name": "CHOICE_1"
            },
            {
              "name": "CHOICE_2"
            }
          ]
        }
      ]
    }
  ]
}
"""
    wizard = generate_wizard_from_string(declaration)
    runner = Runner(None)
    runner.wizard_data = str(wizard)
    runner.createWizard()
    wizard = runner.wizard
    uids = wizard.pageIds()
    page = wizard.page(uids[0])

    def _mock_function(*args, **kwargs):
        raise RuntimeError('invalid input')

    Q.QMessageBox.critical = classmethod(_mock_function)

    assert_that(calling(page.validatePage), raises(RuntimeError))

#------------------------------------------------------------------------------
def test_config_from_file():
    """Check reading wizard data from config file"""
    path = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'assistant', 'simple1', 'wizard.conf')
    declaration, wizard, template = from_config(path)
    assert_that(declaration, not(equal_to('')))
    assert_that(wizard, not(equal_to('')))
    assert_that(template, not(equal_to('')))

#------------------------------------------------------------------------------
def test_config_from_dir():
    """Check reading wizard data from directory with config file"""
    path = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'assistant', 'simple1')
    declaration, wizard, template = from_config(path)
    assert_that(declaration, not(equal_to('')))
    assert_that(wizard, not(equal_to('')))
    assert_that(template, not(equal_to('')))

#------------------------------------------------------------------------------
def test_noconfig_from_dir():
    """Check reading wizard data from directory without config file"""
    path = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'assistant', 'simple2', 'wizard.conf')
    declaration, wizard, template = from_config(path)
    assert_that(declaration, not(equal_to('')))
    assert_that(wizard, not(equal_to('')))
    assert_that(template, not(equal_to('')))

#------------------------------------------------------------------------------
def test_noconfig_from_dir():
    """Check reading wizard data from directory without config file"""
    path = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'assistant', 'simple2')
    declaration, wizard, template = from_config(path)
    assert_that(declaration, not(equal_to('')))
    assert_that(wizard, not(equal_to('')))
    assert_that(template, not(equal_to('')))

#------------------------------------------------------------------------------
def test_config_not_exist():
    """Check reading wizard data from wrong config file"""
    path = osp.join('bbbbbbbbbbbbbbbbbbbbbbb')
    declaration, wizard, template = from_config(path)
    assert_that(declaration, equal_to(''))
    assert_that(wizard, equal_to(''))
    assert_that(template, equal_to(''))

#------------------------------------------------------------------------------
@tempdir
def test_config_bad_cfg(tmpdir):
    """Check reading wizard data from badly written config file"""
    file_name = osp.join(tmpdir, 'wizard.conf')
    cfg = \
"""
declaration = declaration.json
wizard = wizard.py
template = template.comm
"""
    with open(file_name, 'w') as f:
        f.write(cfg)
    declaration, wizard, template = from_config(file_name)
    assert_that(declaration, equal_to(''))
    assert_that(wizard, equal_to(''))
    assert_that(template, equal_to(''))

#------------------------------------------------------------------------------
def test_writer():
    """Check writer"""
    from asterstudy.assistant.generator import Writer
    writer = Writer()
    writer << 'aaa'
    writer << 'bbb'
    writer.indent()
    writer << 'ccc'
    writer.indent()
    writer << 'ddd'
    writer.unindent()
    writer << 'eee'
    writer.reset()
    writer << 'fff'
    ref = """aaa
bbb
    ccc
        ddd
    eee
fff
"""
    assert_that(writer.get(), equal_to(ref))

#------------------------------------------------------------------------------
def test_value2str():
    """Check value2str"""
    from asterstudy.assistant.generator import value2str
    # check int
    assert_that(value2str(10), equal_to('10'))
    # check float
    assert_that(value2str(1.2), equal_to('1.2'))
    # check string
    assert_that(value2str('aaa'), equal_to('"aaa"'))
    # check list
    assert_that(value2str([1,2,3]), equal_to('[1, 2, 3]'))
    assert_that(value2str([1.2,2.3,3.4]), equal_to('[1.2, 2.3, 3.4]'))
    assert_that(value2str(['aaa', 'bbb', 'ccc']), equal_to('["aaa", "bbb", "ccc"]'))
    # check tuple
    assert_that(value2str((1,2,3)), equal_to('(1, 2, 3)'))
    assert_that(value2str((1.2,2.3,3.4)), equal_to('(1.2, 2.3, 3.4)'))
    assert_that(value2str(('aaa', 'bbb', 'ccc')), equal_to('("aaa", "bbb", "ccc")'))
    # check dict
    assert_that(value2str({1:'aaa',2:'bbb',3:'ccc'}), equal_to('{1: "aaa", 2: "bbb", 3: "ccc"}'))
    # check more complex case
    assert_that(value2str(({123:('rrr','ttt',[9.8,7.6])},{'aaa':[1,2,3,('a','b')]}, [9,8,{7:1.2}])), \
                    equal_to('({123: ("rrr", "ttt", [9.8, 7.6])}, {"aaa": [1, 2, 3, ("a", "b")]}, [9, 8, {7: 1.2}])'))

#------------------------------------------------------------------------------
def test_str2value():
    """Check str2value"""
    from asterstudy.assistant.widgets import str2value
    # check int
    assert_that(str2value('10', {'typ':'int'}), equal_to(10))
    # check float
    assert_that(str2value('1.2', {'typ':'float'}), equal_to(1.2))
    # check string
    assert_that(str2value('aaa', {'typ':'string'}), equal_to('aaa'))
    # check tuple
    assert_that(str2value(('1','2','3'), {'typ':'int'}), equal_to((1,2,3)))
    # check list
    assert_that(str2value(['aaa','bbb','ccc'], {'typ':'string'}), equal_to(('aaa','bbb','ccc')))
    # check empty
    assert_that(str2value('', {}), none())
    assert_that(str2value((), {}), none())
    assert_that(str2value([], {}), none())

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
