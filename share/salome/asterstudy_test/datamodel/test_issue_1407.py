
import unittest

from hamcrest import *
from testutils import attr

from asterstudy.datamodel import CATA, History, Validity, comm2study

def _add_custom_commands():
    stx = CATA.package("Syntax")
    macro = stx.MACRO
    oper = stx.OPER
    simp = stx.SIMP
    nume_ddl_sdaster = stx.DS.nume_ddl_sdaster
    co = stx.DS.CO

    def _func(self, VAR, **args):
        if VAR.is_typco():
            self.type_sdprod(VAR,nume_ddl_sdaster)
        return None

    cmd1 = macro(nom="CMD1",
                sd_prod=_func,
                VAR=simp(statut='o',typ=(nume_ddl_sdaster,co)))
    cmd2 = oper(nom="CMD2",
                VAR=simp(statut='o',typ=nume_ddl_sdaster))

    dic = {'CMD1':cmd1, 'CMD2':cmd2,}
    CATA._catalogs.update(dic)

#------------------------------------------------------------------------------
@attr('fixit')
def test():
    #--------------------------------------------------------------------------
    _add_custom_commands()

    #--------------------------------------------------------------------------
    h = History()
    cc = h.current_case

    #--------------------------------------------------------------------------
    s1 = cc.create_stage('s1')
    text = """
CMD1(VAR=CO('asdas'))
"""
    comm2study(text, s1)

    #--------------------------------------------------------------------------
    s2 = cc.create_stage('s2')
    text = """
CMD2(VAR=asdas)
"""
    comm2study(text, s2)

    #--------------------------------------------------------------------------
    def _check_validity(_case):
        _s1 = _case['s1']
        _s2 = _case['s2']

        assert_that(_s1, has_length(2))
        assert_that(_s1[1].name, equal_to("asdas"))
        assert_that(_s1[1], is_in(_s1[0].child_nodes))
        assert_that(_s1[0].check(), equal_to(Validity.Nothing))
        assert_that(_s1[1].check(), equal_to(Validity.Nothing))
        assert_that(_s1.check(), equal_to(Validity.Nothing))

        assert_that(_s2, has_length(1))
        assert_that(_s2[0], is_in(_s1[1].child_nodes))
        assert_that(_s2[0].check(), equal_to(Validity.Nothing))
        assert_that(_s2.check(), equal_to(Validity.Nothing))

    _check_validity(h.current_case)

    #--------------------------------------------------------------------------
    rc1 = h.create_run_case(name='rc1')
    _check_validity(h.current_case)

    #--------------------------------------------------------------------------
    rc2 = h.create_run_case(name='rc2')
    _check_validity(h.current_case)

    #--------------------------------------------------------------------------
    rc1.delete()
    _check_validity(h.current_case)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
