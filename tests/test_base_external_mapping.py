#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#This file is part base_external_mapping module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

import sys
import os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction

field_type = {
    u'char': 'str',
    u'datetime': 'str',
    u'selection': 'str',
    u'many2one': 'str',
    u'one2many': 'str',
    u'many2many': 'str',
    u'integer': 'int',
    u'numeric': 'str'
}

class BaseExternalMappingTestCase(unittest.TestCase):
    '''
    Test BaseExternalMapping module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('product')
        trytond.tests.test_tryton.install_module('base_external_mapping')
        self.mapping = POOL.get('base.external.mapping')
        self.mapping_line = POOL.get('base.external.mapping.line')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('base_external_mapping')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()

    def test0010create_mapping(self):
        '''
        Create Mapping.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            model_obj = POOL.get('ir.model')
            model_id = model_obj.search([
                ('model', '=', 'product.template'),
                ], limit=1)[0]
            mapping1_id = self.mapping.create({
                'name': 'mapping.product',
                'model': model_id,
                'state': 'draft'
                })
            self.assert_(mapping1_id)
            transaction.cursor.commit()

    def test0020create_mapping_lines(self):
        '''
        Create Mapping Line.
        '''
        line_number = {
            'name': 1,
            'cost_price': 2,
        }
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            model_obj = POOL.get('ir.model')
            model_ids = model_obj.search([
                ('model', 'in', ('product.product', 'product.template')),
                ])
            field_obj = POOL.get('ir.model.field')
            field_ids = field_obj.search([
                ('model', 'in', model_ids),
                ])
            mapping1_id = self.mapping.search([
                ('name', '=', 'mapping.product'),
                ], limit=1)[0]
            mapping_line_ids = []
            for field in field_obj.browse(field_ids):
                if field.name not in line_number: continue
                mapping_line_id = self.mapping_line.create({
                    'mapping': mapping1_id,
                    'field': field.id,
                    'mapping_type': 'in_out',
                    'external_type': field_type[field.ttype],
                    'external_field': field.name,
                    'sequence': line_number[field.name],
                    })
                mapping_line_ids.append(mapping_line_id)
                self.assert_(mapping_line_id)
            transaction.cursor.commit()
            mapping_ids = self.mapping.search([
                ('mapping_lines', 'in', mapping_line_ids),
                ])
            mapping_id = mapping_ids[0]
            self.assertEqual(mapping_id, mapping1_id)

    def test0030write_mapping_line(self):
        '''
        Write Mapping Line.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            mapping_lines = self.mapping_line.search([
                ('field', '=', 'name'),
                ])
            self.mapping_line.write(mapping_lines, {
                    'translate': True,
                    'update': True,
                })
            transaction.cursor.commit()

    def test0040copy_mapping(self):
        '''
        Copy Mapping.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            mapping1_id = self.mapping.search([
                ('name', '=', 'mapping.product'),
                ], limit=1)
            mapping2_id = self.mapping.copy(mapping1_id)
            self.assert_(mapping2_id)
            transaction.cursor.commit()

    def test0050create_product(self):
        '''
        Create Product
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            cat_obj = POOL.get('product.category')
            cat_id = cat_obj.create({'name': 'Toys'})
            self.assert_(cat_id)

            uom_obj = POOL.get('product.uom')
            values = {
                'name': 'unit',
                'symbol': 'u',
                'category': cat_id,
                'rate': 1,
                'factor': 1,
                'rounding': 2,
                'digits': 2,
            }
            uom_id = uom_obj.create(values)
            self.assert_(uom_id)

            prod_obj = POOL.get('product.product')
            values = {
                'name': 'Ball',
                'list_price': '345.32',
                'cost_price': '345.32',
                'type': 'goods',
                'default_uom': uom_id,
                'cost_price_method': 'fixed',
                'code':'TEST',
            }
            prod_id = prod_obj.create(values)
            self.assert_(prod_id)
            transaction.cursor.commit()

    def test0060map_external_to_tryton(self):
        '''
        Map external data to tryton dictionary value (to import the record)
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            name = 'mapping.product'
            values= {
                'name': 'Ball',
                'cost_price': 23.50,
            }
            result = self.mapping.map_external_to_tryton(name, values)
            self.assertEqual(result,  {
                    'name': 'Ball',
                    'cost_price': 23.5
                })
    
    def test0070map_tryton_to_external(self):
        '''
        Map tryton data to external dictionary (to export the record)
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            record_ids = POOL.get('product.product').search([
                ('code', '=', 'TEST'),
                ], limit=1)
            name = 'mapping.product'
            result = self.mapping.map_tryton_to_external(name, record_ids)
            self.assertEqual(result, [{
                    'id': 1, 
                    'name_en': 'Ball',
                    'cost_price': 345.32,
                }])

    def test0080map_del_keys(self):
        '''
        Delete key from dict
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as transaction:
            name = 'mapping.product'
            result = {'name': 'Ball', 'cost_price': 30.0, 'active': True}
            result = self.mapping.map_del_keys(name, result)
            self.assertEqual(result, {
                    'active': True,
                    'cost_price': 30.0,
                })

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        BaseExternalMappingTestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
