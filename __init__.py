#This file is part of base_external_mapping module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.pool import Pool
from .base_external_mapping import *

def register():
    Pool.register(
        BaseExternalMapping,
        BaseExternalMappingLine,
        module='base_external_mapping', type_='model')
