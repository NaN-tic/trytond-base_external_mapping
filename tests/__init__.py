# This file is part base_external_mapping module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
try:
    from trytond.modules.base_external_mapping.tests.test_suite import suite
except ImportError:
    from .test_base_external_mapping import suite

__all__ = ['suite']
