# This file is part of base_external_mapping module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from . import base_external_mapping


def register():
    Pool.register(
        base_external_mapping.BaseExternalMapping,
        base_external_mapping.BaseExternalMappingLine,
        module='base_external_mapping', type_='model')
