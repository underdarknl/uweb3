import unittest
from uweb3tests import testrunner

suite = unittest.TestLoader().loadTestsFromModule(testrunner)
unittest.TextTestRunner().run(suite)
