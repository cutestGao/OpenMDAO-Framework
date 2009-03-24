"""
Test of basic NPSS operations.
Essentially stolen from test script for pyNPSS.
"""

import unittest

import numpy
from numpy.testing import assert_equal

from npsscomponent import NPSScomponent

# this string contains an NPSS input string, just because I wanted this test
# to be self-contained and not require a separate NPSS input file.
NPSS_INPUT = """
class Sample extends Element {
    int i=42;
    int i1d[] = { 1,2,3,4 };
    int i2d[][] = { {1,2,3,4},{5,6,7,8} };
    real r=3.14;
    real r1d[] = { 1, 2, 3 };
    real r2d[][] = { {1,2,3},{4,5,6} };
    real r3d[][][] = { {{1,2,3},{4,5,6}},{{7,8,9},{10,11,12}} };
    string s="foo";
    string s1d[] = { "a","b","c" };
    string s2d[][] = { {"a","b","c"},{"d","e","f"} };

    Table table(real in) {
       in = { 1, 2, 3 }
      out = { 1, 4, 9 }
    }

    void calculate() {
        //message("Sample::calculate called for session "+toStr(getSessionID()));
        //message("  i="+toStr(i)+", r="+toStr(r)+", s="+s);
    }

    void printError() {
        error("This is an error");
    }

    void throwException() {
        throwError("This is an exception");
    }

    real real_adder(real a, real b) {
        return a+b;
    }

    int int_adder(int a, int b) {
        return a+b;
    }

    string s_concat(string s1,string s2) {
        return s1+s2;
    }

    // return a list with two entries for each entry of the list passed in
    int[] dupI1D(int lst[]) {
        int newlist[]={};
        int i;
        for (i=0; i<lst.entries(); ++i) {
            newlist.append(lst[i]);
            newlist.append(lst[i]);
        }
        return newlist;
    }

    // return a 2d list with each row equal to the 1d list
    int[][] I1DtoI2D(int lst[]) {
        int newlist[][]={};
        newlist.append(lst);
        newlist.append(lst);
        return newlist;
    }

    // return a list with two entries for each entry of the list passed in
    real[] dupR1D(real lst[]) {
        real newlist[]={};
        int i;
        for (i=0; i<lst.entries(); ++i) {
            newlist.append(lst[i]);
            newlist.append(lst[i]);
        }
        return newlist;
    }

    // return a 2d list with each row equal to the 1d list
    real[][] R1DtoR2D(real lst[]) {
        real newlist[][]={};
        newlist.append(lst);
        newlist.append(lst);
        return newlist;
    }

    // return a 2d list with each row equal to the 1d list
    real[][][] R2DtoR3D(real lst[][]) {
        real newlist[][][]={};
        newlist.append(lst);
        newlist.append(lst);
        return newlist;
    }

    // return a list with two entries for each entry of the list passed in
    string[] dupS1D(string lst[]) {
        string newlist[]={};
        int i;
        for (i=0; i<lst.entries(); ++i) {
            newlist.append(lst[i]);
            newlist.append(lst[i]);
        }
        return newlist;
    }

    // return a 2d list with each row equal to the 1d list
    string[][] S1DtoS2D(string lst[]) {
        string newlist[][]={{}};
        newlist.append(lst);
        newlist.append(lst);
        return newlist;
    }

    void init() {
    }

    void setup() {
    }
}

"""


class NPSSmodel(NPSScomponent):
    """ Used to test inheritance. """

    def __init__(self, npssmodelclass, npssargs=None, **kwargs):
        """npss model class is a string with the name of the model class"""
        super(NPSSmodel, self).__init__(arglist=npssargs)

        if 'parse_str' in kwargs:
            self.parseString(kwargs['parse_str'])

        self.create_in_model(npssmodelclass, npssmodelclass, 'model')
        self.setTop('model')
        self.init()

    def execute(self):
        """ Invoke model 'setup' function and then run model. """
        self.setup()
        return super(NPSSmodel, self).execute()


class NPSSTestCase(unittest.TestCase):

    def setUp(self):
        """called before each test in this class"""
        self.npss = NPSScomponent()
        self.npss.parseString(NPSS_INPUT)
        self.sample = self.npss.create_in_model('Sample', 'Sample', 'sample')

    def tearDown(self):
        """called after each test in this class"""
        try:
            self.npss.pre_delete()
        except RuntimeError, err:
            # Some tests close the session.
            self.assertEqual('no active session', str(err))
        self.npss = None
        self.sample = None

    def test_gets(self):
        self.assertEqual(self.sample.i, 42)
        assert_equal(self.sample.i1d, [1, 2, 3, 4])
        assert_equal(self.sample.i2d, [[1, 2, 3, 4], [5, 6, 7, 8]])

        self.assertEqual(self.sample.r, 3.14)
        assert_equal(self.sample.r1d, [1, 2, 3])
        assert_equal(self.sample.r2d, [[1, 2, 3], [4, 5, 6]])
        assert_equal(self.sample.r3d,
                     [[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])

        self.assertEqual(self.sample.s, 'foo')
        self.assertEqual(self.sample.s1d, ['a', 'b', 'c'])
        self.assertEqual(self.sample.s2d, [['a', 'b', 'c'], ['d', 'e', 'f']]) 

    def test_set_then_get(self):
        self.sample.i = 91919
        self.assertEqual(self.npss.get('sample.i'), 91919)
 
    def test_get_then_set(self):
        self.assertEqual(self.sample.i, 42)
        self.sample.i = 91919
        self.assertEqual(self.npss.get('sample.i'), 91919)

    def test_nested_npss_object_access(self):
        self.sample.create('Sample', 'Sample', 'child')
        self.sample.r = 1.2222
        self.sample.child.r = 987.654
        self.assertEqual(self.npss.get('sample.r'), 1.2222)
        self.assertEqual(self.npss.get('sample.child.r'), 987.654)

    def test_getref(self):
        self.sample.create('Sample', 'Sample', 'child')
        child2 = self.sample.getref('child')
        child2.r = 222.2222
        self.assertEqual(self.npss.get('sample.child.r'), child2.r)
        try:
            self.sample.getref('blah')
        except AttributeError, err:
            self.assertEqual('sample.blah not found', str(err))
        else:
            self.fail('AttributeError expected')
 
    def test_getting_nonexistent_variable(self):
        try:
            x = self.sample.blah
        except AttributeError, err:
            self.assertEqual('sample.blah not found', str(err))
        else:
            self.fail('AttributeError expected')

    def test_setting_nonexistent_variable(self):
        try:
            self.sample.blah = 1
        except AttributeError, err:
            self.assertEqual('sample.blah not found', str(err))
        else:
            self.fail('AttributeError expected')

    def test_setting_npss_var_to_wrong_type(self):
        try:
            self.sample.i = 'goo'
        except RuntimeError, err:
            self.assertEqual("Can't set 'sample.i': ERROR(91041001) NCPVal error - tried to read a STRING as a INT", str(err))
        else:
            self.fail('RuntimeError expected')

    def test_functions(self):
        self.assertEqual(self.sample.int_adder(5, 3), 8)
        self.assertEqual(self.sample.s_concat('foo', 'bar'), 'foobar')
        assert_equal(self.sample.dupI1D([1, 2]), [1, 1, 2, 2])
        assert_equal(self.sample.I1DtoI2D([1, 2, 3]),
                     [[1, 2, 3], [1, 2, 3]])
        assert_equal(self.sample.dupR1D([1.1, 2.2]),
                     [1.1, 1.1, 2.2, 2.2])
        assert_equal(self.sample.R1DtoR2D([1.1, 2.2]),
                     [[1.1, 2.2], [1.1, 2.2]])
        assert_equal(self.sample.R2DtoR3D([[1.1, 2.2], [1.1, 2.2]]),
                     [[[1.1, 2.2], [1.1, 2.2]], [[1.1, 2.2], [1.1, 2.2]]])
        self.assertEqual(self.sample.dupS1D(['a', 'b']),
                         ['a', 'a', 'b', 'b'])
        self.assertEqual(self.sample.S1DtoS2D(['a', 'b']),
                         [['a', 'b'], ['a', 'b']])

    def test_invalid_command_args(self):
        self.assertRaises(TypeError, NPSScomponent, farglist=['-I .'])

        try:
            NPSScomponent(arglist=['-foobar'])
        except ValueError, err:
            self.assertEqual("NPSS: illegal option '-foobar'", str(err))
        else:
            self.fail('ValueError expected')

        try:
            NPSScomponent(top=99)
        except TypeError, err:
            self.assertEqual('top must be a string', str(err))
        else:
            self.fail('TypeError expected')

        try:
            NPSScomponent(arglist=['-I .', 99])
        except ValueError, err:
            self.assertEqual("NPSS: illegal option '-I .'", str(err))
        else:
            self.fail('ValueError expected')

        try:
            NPSScomponent(arglist=99)
        except TypeError, err:
            self.assertEqual("'int' object is not iterable", str(err))
        else:
            self.fail('TypeError expected')

        try:
            NPSScomponent(arglist=['-I'])
        except ValueError, err:
            self.assertEqual('NPSS: expected include path', str(err))
        else:
            self.fail('ValueError expected')

        try:
            NPSScomponent(arglist=['-D'])
        except ValueError, err:
            self.assertEqual('NPSS: expected preprocessor value', str(err))
        else:
            self.fail('ValueError expected')

        try:
            NPSScomponent(arglist=['-a'])
        except ValueError, err:
            self.assertEqual('NPSS: expected default access type', str(err))
        else:
            self.fail('ValueError expected')

        try:
            NPSScomponent(arglist=['-l'])
        except ValueError, err:
            self.assertEqual('NPSS: expected DLM path', str(err))
        else:
            self.fail('ValueError expected')

        try:
            NPSScomponent(arglist=['somefilethatdoesnotexist.npss'])
        except RuntimeError, err:
            self.assertEqual("parseFile() failed: ERROR(991031001) in MemberFunction 'parseFile': Couldn't find file 'somefilethatdoesnotexist.npss'", str(err))
        else:
            self.fail('RuntimeError expected')

    def test_various_empty_values(self):
        #setting to an empty array/list is special, because we have to
        #query NPSS to see what the type is supposed to be
        self.sample.i1d = []
        self.sample.r1d = []
        self.sample.s1d = []

        self.sample.i2d = [[]]
        self.sample.r2d = [[]]
        self.sample.s2d = [[]] 

        self.sample.r3d = [[[]]]

        assert_equal(self.sample.i1d, [])
        assert_equal(self.sample.r1d, [])
        self.assertEqual(self.sample.s1d, [])
        assert_equal(self.sample.i2d, [[]])
        assert_equal(self.sample.r2d, [[]])
        self.assertEqual(self.sample.s2d, [[]])
        assert_equal(self.sample.r3d, [[[]]])
 
    def test_partial_empty(self):
        self.sample.i2d = [[], [1, 2, 3]]
        self.assertEqual(self.sample.i2d, [[], [1, 2, 3]])

        self.sample.r2d = [[], [3.14], []]
        self.assertEqual(self.sample.r2d, [[], [3.14], []])

        sarr = [[], ['a', 'b'], ['c'], [], ['d', 'e']]
        self.sample.s2d = sarr
        self.assertEqual(self.sample.s2d, sarr)

        self.sample.r3d = [ [ [], [1, 2, 3] ] , [ [], [1, 2, 3] ]  ]
        self.assertEqual(self.sample.r3d, [[[], [1, 2, 3]], [[], [1, 2, 3]]])

    def test_inheritance(self):
        mod = NPSSmodel('Sample', parse_str=NPSS_INPUT)
        mod.execute()

    def test_closing_session(self):
        self.sample.closeSession()

    def test_after_session_closed(self):
        child = self.sample.create('Sample', 'Sample', 'kid')
        self.sample.closeSession()
        try:
            self.sample.i = 8
        except RuntimeError, err:
            self.assertEqual('exists(sample.i) failed: no active session', str(err))
        else:
            self.fail('RuntimeError expected')
        try:
            child.exists('foobar')
        except RuntimeError, err:
            self.assertEqual('exists(kid.foobar) failed: no active session', str(err))
        else:
            self.fail('RuntimeError expected')

    def test_after_child_session_closed(self):
        child = self.sample.create('Sample', 'Sample', 'kid')
        child.closeSession()
        try:
            self.sample.i = 8
        except RuntimeError, err:
            self.assertEqual('exists(sample.i) failed: no active session', str(err))
        else:
            self.fail('RuntimeError expected')

    def test_numpy(self):
        eye = numpy.eye(3)
        self.sample.r2d = eye
        assert_equal(self.sample.r2d, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])

        zips = numpy.ones(4)
        self.sample.r1d = zips
        assert_equal(self.sample.r1d, [1, 1, 1, 1])

#    def test_table(self):
#        """ Test accessing a table. Currently this is expected to fail. """
## Immediately fails here.  Expected results data is hand-generated from
## running equivalent commands in NPSS.
#        self.assertEqual(self.sample.table.isA(), 'Table')
#
#        self.assertEqual(self.sample.table.listInterfaces(),
#                         ['Table', 'Function', 'VCInterface'])
#
#        self.assertEqual(self.sample.table.list('Variable'),
#                         ['sample.table.a_rtn',
#                          'sample.table.description',
#                          'sample.table.extrapHighIsError',
#                          'sample.table.extrapLowIsError',
#                          'sample.table.iDescription',
#                          'sample.table.printExtrap',
#                          'sample.table.s_rtn'])
#
#        self.assertEqual(self.sample.table.s_rtn, 1.)
#        self.assertEqual(self.sample.table(2.5), 6.5)
#
#        self.sample.table.s_rtn = 10.
#        self.assertEqual(self.sample.table(2.5), 65)


if __name__ == '__main__':
    unittest.main()
