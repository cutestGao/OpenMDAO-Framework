import bson
import json
import os.path
import unittest

from struct import unpack
from cStringIO import StringIO

from openmdao.main.api import Assembly, Case, set_as_top
from openmdao.main.datatypes.api import Instance
from openmdao.test.execcomp import ExecComp
from openmdao.lib.casehandlers.api import JSONCaseRecorder, BSONCaseRecorder
from openmdao.lib.drivers.api import SensitivityDriver, CaseIteratorDriver, \
                                     SLSQPdriver
from openmdao.util.testutil import assert_raises


class TExecComp(ExecComp):

    data = Instance(iotype='in', desc='Used to check bad JSON data')


class TestCase(unittest.TestCase):

    def setUp(self):
        self.top = top = set_as_top(Assembly())
        driver = top.add('driver', CaseIteratorDriver())
        top.add('comp1', TExecComp(exprs=['z=x+y']))
        top.add('comp2', ExecComp(exprs=['z=x+1']))
        top.connect('comp1.z', 'comp2.x')
        driver.workflow.add(['comp1', 'comp2'])

        # now create some Cases
        outputs = ['comp1.z', 'comp2.z']
        cases = []
        for i in range(10):
            inputs = [('comp1.x', i), ('comp1.y', i*2)]
            cases.append(Case(inputs=inputs, outputs=outputs))

        Case.set_vartree_inputs(driver, cases)
        driver.add_responses(outputs)

    def tearDown(self):
        self.top = None

    def test_jsonrecorder(self):
        sout = StringIO()
        self.top.recorders = [JSONCaseRecorder(sout)]
        self.top.run()

#        with open('jsonrecorder.new', 'w') as out:
#            out.write(sout.getvalue())
        self.verify(sout, 'jsonrecorder.json')

    def test_multiple_objectives(self):
        sout = StringIO()
        self.top.add('driver', SensitivityDriver())
        self.top.driver.workflow.add(['comp1', 'comp2'])
        self.top.driver.add_parameter(['comp1.x'], low=-100, high=100)
        self.top.driver.add_objective('comp1.z')
        self.top.driver.add_objective('comp2.z')

        self.top.recorders = [JSONCaseRecorder(sout)]
        self.top.run()

#        with open('multiobj.new', 'w') as out:
#            out.write(sout.getvalue())
        self.verify(sout, 'multiobj.json')

    def test_nested(self):
        asm3 = Assembly()
        asm3.add('comp1', ExecComp(exprs=['z=x+y']))
        driver = asm3.add('driver', SLSQPdriver())
        driver.workflow.add('comp1')
        driver.add_parameter('comp1.y', low=-1, high=1, start=0)
        driver.add_objective('comp1.z')
        driver.add_constraint('comp1.z >= 0')
        asm3.create_passthrough('comp1.x')
        asm3.create_passthrough('comp1.z')

        asm2 = Assembly()
        asm2.add('comp1', ExecComp(exprs=['z=x+y']))
        asm2.add('asm3', asm3)
        asm2.connect('comp1.z', 'asm3.x')
        driver = asm2.add('driver', SLSQPdriver())
        driver.workflow.add(('comp1', 'asm3'))
        driver.add_parameter('comp1.y', low=-1, high=1, start=0)
        driver.add_objective('asm3.z')
        driver.add_constraint('comp1.z >= 0')
        asm2.create_passthrough('comp1.x')
        asm2.create_passthrough('asm3.z')

        asm1 = set_as_top(Assembly())
        asm1.add('comp1', ExecComp(exprs=['z=x+y']))
        asm1.add('asm2', asm2)
        asm1.connect('comp1.z', 'asm2.x')
        driver = asm1.add('driver', SLSQPdriver())
        driver.workflow.add(('comp1', 'asm2'))
        driver.add_parameter('comp1.y', low=-1, high=1, start=0)
        driver.add_objective('asm2.z')
        driver.add_constraint('comp1.z >= 0')

        sout = StringIO()
        asm1.recorders = [JSONCaseRecorder(sout)]
        asm1.run()

#        with open('nested.new', 'w') as out:
#            out.write(sout.getvalue())
        self.verify(sout, 'nested.json')

    def verify(self, sout, filename):
        lines = sout.getvalue().split('\n')

        directory = os.path.dirname(__file__)
        path = os.path.join(directory, filename)
        with open(path, 'r') as inp:
            expected = inp.read().split('\n')

        for i in range(len(expected)):
            expect = expected[i]
            if expect.startswith('    "_driver_id":'):
                self.assertTrue(lines[i].startswith('    "_driver_id":'))
            elif expect.startswith('    "_id":'):
                self.assertTrue(lines[i].startswith('    "_id":'))
            elif expect.startswith('    "_parent_id":'):
                self.assertTrue(lines[i].startswith('    "_parent_id":'))
            elif expect.startswith('    "uuid":'):
                self.assertTrue(lines[i].startswith('    "uuid":'))
            elif expect.startswith('    "timestamp":'):
                self.assertTrue(lines[i].startswith('    "timestamp":'))
            elif expect.startswith('            "pcomp_name":'):
                self.assertTrue(lines[i].startswith('            "pcomp_name":'))
            else:
                self.assertEqual(lines[i], expect)

    def test_close(self):
        sout = StringIO()
        self.top.recorders = [JSONCaseRecorder(sout)]
        self.top.recorders[0].close()
        self.top.run()
        self.assertEqual(sout.getvalue(), '')

    def test_badval(self):
        sout = StringIO()
        self.top.recorders = [JSONCaseRecorder(sout)]
        self.top.comp1.data = self.test_badval.__func__
        assert_raises(self, 'self.top.run()', globals(), locals(), RuntimeError,
                      "JSON write failed for simulation_info.constants:"
                      " keys ['comp1.data']: <function test_badval at")

    def test_bsonrecorder(self):
        # Verify bson output can be read and that it matches json.
        bson_out = StringIO()
        json_out = StringIO()
        self.top.recorders = [BSONCaseRecorder(bson_out),
                              JSONCaseRecorder(json_out)]
        self.top.run()

        json_run = json.loads(json_out.getvalue())

        inp = StringIO(bson_out.getvalue())
        reclen = unpack('<L', inp.read(4))[0]
        data = inp.read(reclen)
        obj = bson.loads(data)  # simulation_info
        keys = sorted(obj.keys())
        self.assertEqual(keys, sorted(json_run['simulation_info'].keys()))
        for key in keys:
            if key not in ('uuid',):
                self.assertEqual(obj[key], json_run['simulation_info'][key])

        driver_count = 1
        case_count = 1
        data = inp.read(4)
        while data:
            reclen = unpack('<L', data)[0]
            data = inp.read(reclen)
            obj = bson.loads(data)  # driver_info or iteration_case
            keys = sorted(obj.keys())

            if '_driver_id' in obj:  # iteration_case
                case = 'iteration_case_%s' % case_count
                self.assertEqual(keys, sorted(json_run[case].keys()))
                for key in keys:
                    if key not in ('_driver_id', '_id', '_parent_id',
                                   'timestamp'):
                        self.assertEqual(obj[key], json_run[case][key])
                case_count += 1
            else:  # driver_info
                driver = 'driver_info_%s' % driver_count
                self.assertEqual(keys, sorted(json_run[driver].keys()))
                for key in keys:
                    if key not in ('_id',):
                        self.assertEqual(obj[key], json_run[driver][key])
                driver_count += 1

            data = inp.read(4)


if __name__ == '__main__':
    unittest.main()

