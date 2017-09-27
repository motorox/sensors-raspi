#!/usr/bin/env python

import unittest
from sensor_utils import floatfromhex, tosigned, tosignedbyte
from sensor_utils import calcAccel, calcGyro, calcHum, calcMagn, calcTmpTarget
from sensor_callbacks import SensorCallbacks

class UtilFunctionsTestCase(unittest.TestCase):
    def test_floatfromhex(self):
        self.assertEqual(floatfromhex('EFFEC'), 917485.0)
        self.assertEqual(floatfromhex('A'), 10.0)

    def test_tosigned(self):
        self.assertEqual(tosigned(12345), 12345.0)
        self.assertEqual(tosigned(-12345), -12345.0)

    def test_tosignedbyte(self):
        self.assertEqual(tosignedbyte(-123.67), -123.67)
        self.assertEqual(tosignedbyte(980.34), 724.34)

    def test_calcTmpTarget(self):
        self.assertEqual(calcTmpTarget(2496, 3456), 75.05803446521622)

    def test_calcHum(self):
        self.assertEqual(calcHum(26592, 27548), (24.450449218750002, 46.54364013671875))

    def test_calcAccel(self):
        self.assertEqual(calcAccel(61337, 110, 65132), ([954.390625, 1.71875, 1013.6875], 1392.2739553858296))

    def test_calcMagn(self):
        self.assertEqual(calcMagn(191, 382, 730), [5.828857421875, 11.65771484375, 22.27783203125])

    def test_calcGyro(self):
        self.assertEqual(calcGyro(32768, 32767, 26766), [-250.0, 249.99237060546875, 204.2083740234375])

class CallbacksTestCase(unittest.TestCase):
    def setUp(self):
        self.clbk = SensorCallbacks("ASDFGHJKL")
    def tearDown(self):
        self.clbk = None

    def test_sensor(self):
        self.assertEqual(self.clbk.data['addr'], 'ASDFGHJKL')
        self.assertEqual(self.clbk.data['keys'], 0)

        self.clbk.tmp007([168L, 9L, 228L, 12L])
        self.assertEqual(self.clbk.data['ambtemp'], 25.78125)
        self.assertEqual(self.clbk.data['celsiustemp'], 23.302163132520725)

        self.clbk.lux([168L, 228L])
        self.assertEqual(self.clbk.data['lux'], 58536L)

        self.clbk.keys([3])
        self.assertEqual(self.clbk.data['keys'], 3)

        self.clbk.humidity([4L, 102L, 72L, 96L])
        self.assertEqual(self.clbk.data['humdtemp'], 23.17416259765624)
        self.assertEqual(self.clbk.data['humd'], 41.0123291015625)

        self.clbk.baro([50L, 10L, 0L, 139L, 140L, 1L])
        self.assertEqual(self.clbk.data['barotemp'], 26.1)
        self.assertEqual(self.clbk.data['baropress'], 1015.15)

        self.clbk.movement([43L, 191L, 99L, 37L, 224L, 53L, 243L, 0L, 7L, 247L, 45L, 242L, 57L, 1L, 188L, 0L, 217L, 1L])
        self.assertEqual(self.clbk.data['magnx'], 9.552001953125)
        self.assertEqual(self.clbk.data['magny'], 5.7373046875)
        self.assertEqual(self.clbk.data['magnz'], 14.434814453125)
        self.assertEqual(self.clbk.data['accelx'], -0.203125)
        self.assertEqual(self.clbk.data['accely'], 984.109375)
        self.assertEqual(self.clbk.data['accelz'], 964.703125)
        self.assertEqual(self.clbk.data['gyrox'], -126.62506103515625)
        self.assertEqual(self.clbk.data['gyroy'], 73.02093505859375)
        self.assertEqual(self.clbk.data['gyroz'], 105.224609375)

def load_tests(loader):
    test_cases = (UtilFunctionsTestCase, CallbacksTestCase)
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(load_tests(unittest.TestLoader()))#
