# This file is part of the base_external_mapping module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class BaseExternalMappingTestCase(ModuleTestCase):
    'Test Base External Mapping module'
    module = 'base_external_mapping'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        BaseExternalMappingTestCase))
    return suite