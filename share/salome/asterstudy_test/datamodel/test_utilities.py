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

"""Automatic tests for utilities."""


import getpass
import os
import os.path as osp
import shutil
import tempfile
import unittest
from functools import partial

import asterstudy
from asterstudy.common import (CFG, AsterStudySession, ConfigurationError,
                               ConversionError, debug_caller, format_code,
                               get_absolute_dirname, hms2s, is_localhost,
                               localhost_server, ping, recursive_items,
                               split_text, tail_file, bold, italic, underline,
                               preformat, font, image, href, div, clean_text,
                               is_child, is_subclass, contains_word, to_words,
                               from_words, hms2s, secs2hms, check_version,
                               recursive_setter, make_dirs)
from asterstudy.common.conversion import ConversionReport
from asterstudy.datamodel.aster_parser import change_text
from asterstudy.datamodel.aster_syntax import import_aster
from asterstudy.datamodel.catalogs import CATA
from hamcrest import *
from testutils import attr
from testutils.tools import check_text_diff

change_text_wrap = partial(change_text, report=ConversionReport())


def test_configuration():
    """Test for configuration object"""
    packagedir = get_absolute_dirname(osp.dirname(asterstudy.__file__))
    assert_that(CFG.installdir, equal_to(packagedir))
    assert_that(osp.exists(CFG.apprc))

    assert_that("General", is_in(CFG.sections()))
    assert_that("MainWindow", is_in(CFG.sections()))
    assert_that(CFG.installdir, equal_to(CFG.get("General", "installdir")))

    assert_that(calling(CFG.options).with_args("unknown section"),
                raises(ConfigurationError))

    defvers = CFG.get("General", "default_version")
    assert_that(defvers, equal_to("stable"))
    defpath = CFG.get("Versions", defvers)
    assert_that(defpath, equal_to(osp.join(CFG.installdir, "asterstudy",
                                  "code_aster_version")))

    assert_that(CFG.business_translation_url(), matches_regexp('^http://'))


def test_wckey():
    """Test for wckey getter"""
    assert_that(CFG.get_wckey(), none())


@attr(skip_on_install=CFG.is_installed)
@unittest.skipIf(CFG.is_installed, "can't be run on install")
def test_versions_imports():
    """Test for versions imports"""
    import sys
    path0 = sys.path[:]
    path1 = osp.join(CFG.installdir, "_test_data", "stable")
    path2 = osp.join(CFG.installdir, "_test_data", "light")

    cmd1 = import_aster(path1)["Commands"]
    assert_that(hasattr(cmd1, "DEBUT"))
    assert_that(hasattr(cmd1, "LIRE_MAILLAGE"))

    cmd2 = import_aster(path2)["Commands"]
    assert_that(hasattr(cmd2, "DEBUT"))
    assert_that(hasattr(cmd2, "LIRE_MAILLAGE"), is_(False))

    # failures
    assert_that(calling(import_aster).with_args(path1 + "_badname"),
                raises(ImportError))
    CATA.read_catalogs("unknown_version")

    # restore default catalog for other tests
    CATA.read_catalogs()

    # sys.path must not change
    assert_that(sys.path, contains(*path0))


def test_aster_parser():
    """Test for user variables and comments replacement"""
    text = \
"""
# Keep comments unchanged
DEBUT()

var = 2. * pi

FIN()
"""
    expected = \
"""
_CONVERT_COMMENT(EXPR='Keep comments unchanged')
DEBUT()

var = _CONVERT_VARIABLE(EXPR='2. * pi')

FIN()
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(eoi, has_length(3))
    assert_that(eoi, contains(3, 5, 7))
    changed = format_code(changed)
    assert_that(check_text_diff(changed, expected))


def test_parser_var():
    """Test for user variables and comments replacement"""
    text = \
"""
Epdalle = 25.0E-02;NbCouche=5
"""
    expected = \
"""
Epdalle = _CONVERT_VARIABLE(EXPR='25.0E-02')
NbCouche = _CONVERT_VARIABLE(EXPR='5')
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(eoi, has_length(1))
    assert_that(eoi, contains(2))
    changed = format_code(changed)
    assert_that(check_text_diff(changed, expected))


def test_parser_py():
    """Test for detection of Python code"""
    text = \
"""
import matplotlib
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(changed, contains_string("Python statements"))
    assert_that(eoi, has_length(1))

    text = \
"""
if(False):
    print 'hello'

assert True
"""
    report = ConversionReport()
    eoi, changed = change_text(text, 0, report)
    assert_that(changed, contains_string("Python statements"))
    assert_that(eoi, has_length(1))

    warn = [i for i in report.iter_warnings()]
    assert_that(warn, has_length(2))
    assert_that(report.get_warnings(), contains_string("'assert' statements"))
    assert_that(report.get_warnings(), contains_string("'print' statements"))

    text = \
"""
form = FORMULE()
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(changed, is_not(contains_string("Python statements")))
    assert_that(eoi, has_length(1))

def test_parser_df():
    """Test for detection of DEFI_FICHIER"""
    text = \
"""
unite=DEFI_FICHIER(ACTION='ASSOCIER', FICHIER='./REPE_OUT/carelem1.concept',ACCES='NEW')
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(changed, contains_string("is not supported in graphical mode"))
    assert_that(eoi, has_length(1))
    text = \
"""
Mesh=LIRE_MAILLAGE()
#unite=DEFI_FICHIER(ACTION='ASSOCIER', FICHIER='./REPE_OUT/carelem1.concept',ACCES='NEW')
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(changed, is_not(contains_string("is not supported in graphical mode")))
    assert_that(eoi, has_length(1))

def test_parser_in():
    """Test for detection of INCLUDE"""
    text = \
"""
INCLUDE(UNITE=33)
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(changed, contains_string("MissingInclude"))
    assert_that(eoi, has_length(1))
    text = \
"""
Mesh=LIRE_MAILLAGE()
#INCLUDE(UNITE=33)
"""
    eoi, changed = change_text_wrap(text, 0)
    assert_that(changed, is_not(contains_string("MissingInclude")))
    assert_that(eoi, has_length(1))

def test_parser_tokenerror():
    """Test for detection of TokenError"""
    text = \
"""
x = [1,
     2,
"""
    assert_that(calling(change_text_wrap).with_args(text, 0),
                raises(ConversionError, "TokenError.*Uncompleted.*expression"))


def test_parser_inactive():
    text = \
"""
# comment
a = 1
#comment: MAIL_Q = LIRE_MAILLAGE(UNITE=22)
b = 2
"""
    expected = \
"""
_CONVERT_COMMENT(EXPR='comment')
a = _CONVERT_VARIABLE(EXPR='1')
_DISABLE_COMMANDS(globals())
MAIL_Q = LIRE_MAILLAGE(UNITE=22)
_ENABLE_COMMANDS(globals())
b = _CONVERT_VARIABLE(EXPR='2')
"""
    eoi, changed = change_text_wrap(text, 0)
    # print(); print("DEBUG:", eoi)
    # assert_that(eoi, has_length(3))
    # assert_that(eoi, contains(3, 4, 5))
    changed = format_code(changed)
    assert_that(check_text_diff(changed, expected))


def test_parser_N():
    commfile = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'export', '_forma07a.comm')
    with open(commfile) as fobj:
        text = fobj.read()

    expected = \
r"""
DEBUT(LANG='G (J.m\S-2_N)')
DEBUT(LANG=r'G (J.m\S-2\N)')
DEBUT(LANG='\N{GREEK CAPITAL LETTER DELTA}')
"""
    eoi, changed = change_text_wrap(text, 0)
    changed = format_code(changed)
    assert_that(check_text_diff(changed, expected))


def test_valid_filename():
    """Test for user variables and comments replacement"""
    from asterstudy.common import valid_filename
    assert_that(valid_filename("stage:9"), equal_to("stage_9"))
    assert_that(valid_filename("strange/name"), equal_to("strange_name"))
    assert_that(valid_filename("&année"), equal_to("ann_e"))
    assert_that(valid_filename("EXPR=u'2. * pi'"), equal_to("EXPR_u_2_pi"))


def test_session():
    """Test for session informations"""
    CATA.read_catalogs()
    assert_that(AsterStudySession.use_cata())


def test_recursive_items():
    """Test for recursive_items"""
    test = {'a': 1, 'b': 'ok',
            'c': {'u': 10, 'v': 20},
            'd': ({'x': 9, 'y': 8, 'z': 7}, {'x': 4, 'y': 5, 'z': [6, 7]}),
            'e': {'m': (1, 2, 3)},
            'f': ['hello', 'world'],
            'g': {'p': [{'q': (4, 3)}, {'r': 6}]}}
    pairs = []
    for k, v in recursive_items(test):
        pairs.append((k, v))
    assert_that(pairs, has_length(19))
    assert_that(pairs, has_item((('a', None), 1)))
    assert_that(pairs, has_item((('b', None), 'ok')))
    assert_that(pairs, has_item((('c', None, 'u', None), 10)))
    assert_that(pairs, has_item((('c', None, 'v', None), 20)))
    assert_that(pairs, has_item((('d', 0, 'x', None), 9)))
    assert_that(pairs, has_item((('d', 0, 'y', None), 8)))
    assert_that(pairs, has_item((('d', 0, 'z', None), 7)))
    assert_that(pairs, has_item((('d', 1, 'x', None), 4)))
    assert_that(pairs, has_item((('d', 1, 'y', None), 5)))
    assert_that(pairs, has_item((('d', 1, 'z', 0), 6)))
    assert_that(pairs, has_item((('d', 1, 'z', 1), 7)))
    assert_that(pairs, has_item((('e', None, 'm', 0), 1)))
    assert_that(pairs, has_item((('e', None, 'm', 1), 2)))
    assert_that(pairs, has_item((('e', None, 'm', 2), 3)))
    assert_that(pairs, has_item((('f', 0), 'hello')))
    assert_that(pairs, has_item((('f', 1), 'world')))
    assert_that(pairs, has_item((('g', None, 'p', 0, 'q', 0), 4)))
    assert_that(pairs, has_item((('g', None, 'p', 0, 'q', 1), 3)))
    assert_that(pairs, has_item((('g', None, 'p', 1, 'r', None), 6)))

    # example for update of the dict
    for path, value in recursive_items(test):
        if isinstance(value, int) and 3 <= value <= 8:
            recursive_setter(test, path, '+' * value)
        elif isinstance(value, str):
            recursive_setter(test, path, len(value))

    pairs = []
    for k, v in recursive_items(test):
        pairs.append((k, v))
    assert_that(pairs, has_length(19))
    assert_that(pairs, has_item((('a', None), 1)))
    assert_that(pairs, has_item((('b', None), 2)))
    assert_that(pairs, has_item((('c', None, 'u', None), 10)))
    assert_that(pairs, has_item((('c', None, 'v', None), 20)))
    assert_that(pairs, has_item((('d', 0, 'x', None), 9)))
    assert_that(pairs, has_item((('d', 0, 'y', None), "++++++++")))
    assert_that(pairs, has_item((('d', 0, 'z', None), "+++++++")))
    assert_that(pairs, has_item((('d', 1, 'x', None), "++++")))
    assert_that(pairs, has_item((('d', 1, 'y', None), "+++++")))
    assert_that(pairs, has_item((('d', 1, 'z', 0), "++++++")))
    assert_that(pairs, has_item((('d', 1, 'z', 1), "+++++++")))
    assert_that(pairs, has_item((('e', None, 'm', 0), 1)))
    assert_that(pairs, has_item((('e', None, 'm', 1), 2)))
    assert_that(pairs, has_item((('e', None, 'm', 2), "+++")))
    assert_that(pairs, has_item((('f', 0), 5)))
    assert_that(pairs, has_item((('f', 1), 5)))
    assert_that(pairs, has_item((('g', None, 'p', 0, 'q', 0), "++++")))
    assert_that(pairs, has_item((('g', None, 'p', 0, 'q', 1), "+++")))
    assert_that(pairs, has_item((('g', None, 'p', 1, 'r', None), "++++++")))


def test_logfile():
    """Test for asrun logfile"""
    from asterstudy.common import LogFiles
    expected = osp.join(tempfile.gettempdir(),
                        'asterstudy-main-{}.log'.format(getpass.getuser()))
    assert_that(LogFiles.filename(), equal_to(expected))
    # check failover
    os.chmod(expected, 0o400)
    tmpf = LogFiles.filename(nocache=True)
    os.chmod(expected, 0o600)
    assert_that(LogFiles.filename(), is_not(equal_to(expected)))
    os.remove(tmpf)
    # reset
    LogFiles.filename(nocache=True)


def test_text_splitter():
    """Test for split_text"""
    text = os.linesep.join([str(i + 1) for i in range(10)])
    part1, part2 = split_text(text, 5)
    assert_that(part1.splitlines(), has_length(5))
    assert_that(part2.splitlines(), has_length(5))

    part1, part2 = split_text(text, 0)
    assert_that(part1.splitlines(), has_length(0))
    assert_that(part2.splitlines(), has_length(10))

    part1, part2 = split_text(text, 99)
    assert_that(part1.splitlines(), has_length(10))
    assert_that(part2.splitlines(), has_length(0))


def test_ping():
    """Test for ping utility"""
    assert_that(ping("localhost"), equal_to(True))
    assert_that(ping("unexpected_hostname.local"), equal_to(False))


def test_tail():
    """Test for tail_file utilities"""
    assert_that(tail_file("unknown file", 99), empty())
    text = tail_file(os.path.splitext(__file__)[0] + ".py", 2)
    assert_that(text, contains_string("TextTestRunner"))
    assert_that(text, is_not(contains_string("__main__")))


def test_debug_caller():
    stack = debug_caller()
    assert_that(stack, contains_string("test_debug_caller@test_utilities"))


def test_localhost():
    name = localhost_server()
    assert_that(name, contains_string("localhost"))
    assert_that(is_localhost(name), equal_to(True))


def test_html_utils():
    """Test for wrapping of text with HTML tags"""
    assert_that(bold('aaa'), equal_to('<b>aaa</b>'))
    assert_that(italic('aaa'), equal_to('<i>aaa</i>'))
    assert_that(underline('aaa'), equal_to('<u>aaa</u>'))
    assert_that(preformat('aaa'), equal_to('<pre>aaa</pre>'))
    assert_that(div('aaa'), equal_to('<div id="aaa"></div>'))
    assert_that(font('aaa', color='red'), equal_to('<font color="red">aaa</font>'))
    assert_that(image('aaa.png', height="100"), equal_to('<img alt="aaa.png" height="100" src="aaa.png"></img>'))
    assert_that(href('aaa', 'www.aaa.org', target='bbb'), equal_to('<a href="www.aaa.org" target="bbb">aaa</a>'))
    assert_that(bold(italic(underline('aaa'))), equal_to('<b><i><u>aaa</u></i></b>'))


def test_various_utils():
    """Test for various utils"""
    assert_that(clean_text('&File'), equal_to('File'))

    class a:
        def __init__(self, parent):
            self.p = parent
        def parent(self):
            return self.p
    a1 = a(None)
    a2 = a(a1)
    a3 = a(a2)
    a4 = a(a3)
    assert_that(is_child(a1, None), equal_to(False))
    assert_that(is_child(a2, a1), equal_to(True))
    assert_that(is_child(a3, a1), equal_to(True))
    assert_that(is_child(a4, a1), equal_to(True))
    assert_that(is_child(a4, a2), equal_to(True))
    assert_that(is_child(a4, a3), equal_to(True))
    assert_that(is_child(a3, a4), equal_to(False))

    assert_that(is_subclass(a, object), equal_to(True))
    assert_that(is_subclass(object, a), equal_to(False))
    assert_that(is_subclass(None, object), equal_to(False))

    assert_that(contains_word('aaa_bbb_ccc', 'aaa'), equal_to(True))
    assert_that(contains_word('aaa_bbb_ccc', 'bbb'), equal_to(True))
    assert_that(contains_word('aaa_bbb_ccc', 'ccc'), equal_to(True))
    assert_that(contains_word('aaa_bbb_ccc', 'ddd'), equal_to(False))
    assert_that(contains_word('aaa_bbb_ccc', 'aaaa'), equal_to(False))
    assert_that(contains_word('aaa_bbb_ccc', 'bb'), equal_to(False))
    assert_that(contains_word('aaa_bbb_ccc', ['ddd', 'aaa']), equal_to(True))

    assert_that(to_words('abc'), equal_to(['abc']))
    assert_that(to_words('abcDef'), equal_to(['abc', 'Def']))
    assert_that(to_words('Abc Def Ghi'), equal_to(['Abc', 'Def', 'Ghi']))
    assert_that(from_words('abc'), equal_to('abc'))
    assert_that(from_words('abcDef'), equal_to('abc Def'))
    assert_that(from_words('AbcDefGhi'), equal_to('Abc Def Ghi'))

    assert_that(hms2s('0'), equal_to(0))
    assert_that(hms2s('0:10'), equal_to(10))
    assert_that(hms2s('0:10:10'), equal_to(610))
    assert_that(hms2s('1'), equal_to(1))
    assert_that(hms2s('1:10'), equal_to(70))
    assert_that(hms2s('1:10:10'), equal_to(4210))
    assert_that(hms2s('300'), equal_to(300))
    assert_that(hms2s(300), equal_to(300))
    assert_that(hms2s('5:00'), equal_to(300))
    assert_that(hms2s('3:5:07'), equal_to(11107))

    assert_that(secs2hms(300), equal_to("00:05:00"))
    assert_that(secs2hms(11107), equal_to("03:05:07"))
    assert_that(secs2hms(55), equal_to("00:00:55"))

    assert_that(check_version('2', '2.0', 'eq'), equal_to(True))
    assert_that(check_version('2', '2.0', 'ne'), equal_to(False))
    assert_that(check_version('2', '2.0', 'le'), equal_to(True))
    assert_that(check_version('2', '2.0', 'lt'), equal_to(False))
    assert_that(check_version('2', '2.0', 'ge'), equal_to(True))
    assert_that(check_version('2', '2.0', 'gt'), equal_to(False))
    assert_that(check_version('2.0', '2.1', 'eq'), equal_to(False))
    assert_that(check_version('2.0', '2.1', 'ne'), equal_to(True))
    assert_that(check_version('2.0', '2.1', 'le'), equal_to(True))
    assert_that(check_version('2.0', '2.1', 'lt'), equal_to(True))
    assert_that(check_version('2.0', '2.1', 'ge'), equal_to(False))
    assert_that(check_version('2.0', '2.1', 'gt'), equal_to(False))
    assert_that(check_version('4.3.2', '2.1', 'eq'), equal_to(False))
    assert_that(check_version('4.3.2', '2.1', 'ne'), equal_to(True))
    assert_that(check_version('4.3.2', '2.1', 'le'), equal_to(False))
    assert_that(check_version('4.3.2', '2.1', 'lt'), equal_to(False))
    assert_that(check_version('4.3.2', '2.1', 'ge'), equal_to(True))
    assert_that(check_version('4.3.2', '2.1', 'gt'), equal_to(True))

    tmpdir = tempfile.mktemp()
    assert_that(osp.exists(tmpdir), is_not(equal_to(True)))
    make_dirs(tmpdir)
    assert_that(osp.exists(tmpdir), equal_to(True))
    shutil.rmtree(tmpdir)

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
