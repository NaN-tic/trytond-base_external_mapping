#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# This file is partbase_external_mapping module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
from decimal import Decimal

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
    u'numeric': 'str',
    u'text': 'str',
}


class BaseExternalMappingTestCase(unittest.TestCase):
    'Test BaseExternalMapping module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('product')
        trytond.tests.test_tryton.install_module('base_external_mapping')
        self.mapping = POOL.get('base.external.mapping')
        self.mapping_line = POOL.get('base.external.mapping.line')
        self.uom = POOL.get('product.uom')
        self.category = POOL.get('product.category')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')

    def test0005views(self):
        'Test views'
        test_view('base_external_mapping')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010create_mapping(self):
        '''
        Create Mapping.
        '''
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            Model = POOL.get('ir.model')

            model = Model.search([
                ('model', '=', 'product.template'),
                ], limit=1)[0]
            mapping1 = self.mapping.create([{
                'name': 'mapping.product',
                'model': model,
                'state': 'draft',
                }])[0]
            self.assert_(mapping1)

            model = Model.search([
                ('model', '=', 'product.product'),
                ], limit=1)[0]
            mapping1 = self.mapping.create([{
                'name': 'mapping.product.variant',
                'model': model,
                'state': 'draft',
                'render_tags': True,
                'engine': 'genshi',
                }])[0]
            self.assert_(mapping1)

            transaction.cursor.commit()

    def test0020create_mapping_lines(self):
        '''
        Create Mapping Line.
        '''
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            Model = POOL.get('ir.model')
            models = Model.search([
                ('model', 'in', ('product.product', 'product.template')),
                ])
            Field = POOL.get('ir.model.field')
            fields = Field.search([
                ('model', 'in', models),
                ])

            line_number = {
                'name': 1,
                'cost_price': 2,
            }
            mapping1 = self.mapping.search([
                ('name', '=', 'mapping.product'),
                ], limit=1)[0]
            mapping_lines = []
            for field in Field.browse(fields):
                if field.name not in line_number:
                    continue
                mapping_line = self.mapping_line.create([{
                    'mapping': mapping1,
                    'field': field.id,
                    'mapping_type': 'in_out',
                    'external_type': field_type[field.ttype],
                    'external_field': field.name,
                    'sequence': line_number[field.name],
                    }])[0]
                mapping_lines.append(mapping_line)
                self.assert_(mapping_line)
            transaction.cursor.commit()
            mappings = self.mapping.search([
                ('mapping_lines', 'in', mapping_lines),
                ])
            mapping = mappings[0]
            self.assertEqual(mapping, mapping1)

            line_number = {
                'template': 1,
                'code': 2,
                'description': 3,
            }
            mapping2 = self.mapping.search([
                ('name', '=', 'mapping.product.variant'),
                ], limit=1)[0]
            mapping_lines = []
            for field in Field.browse(fields):
                if field.name not in line_number:
                    continue
                mapping_line = self.mapping_line.create([{
                    'mapping': mapping2,
                    'field': field.id,
                    'mapping_type': 'in_out',
                    'external_type': field_type[field.ttype],
                    'external_field': field.name,
                    'sequence': line_number[field.name],
                    }])[0]
                mapping_lines.append(mapping_line)
                self.assert_(mapping_line)
            mappings = self.mapping.search([
                ('mapping_lines', 'in', mapping_lines),
                ])
            mapping = mappings[0]
            self.assertEqual(mapping, mapping2)
            transaction.cursor.commit()

    def test0030write_mapping_line(self):
        '''
        Write Mapping Line.
        '''
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            mapping_lines = self.mapping_line.search([
                ('field', '=', 'name'),
                ])
            self.mapping_line.write(mapping_lines, {
                    'translate': True,
                    'exclude_update': True,
                })
            transaction.cursor.commit()

    def test0040copy_mapping(self):
        '''
        Copy Mapping.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            mapping1 = self.mapping.search([
                ('name', '=', 'mapping.product'),
                ], limit=1)
            mapping2 = self.mapping.copy(mapping1)
            self.assert_(mapping2)

    def test0050create_product(self):
        '''
        Create Product
        '''
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            uom, = self.uom.search([
                    ('name', '=', 'Unit'),
                    ])
            category, = self.category.create([{
                    'name': 'Category',
                    }])
            template, = self.template.create([{
                    'name': 'Ball',
                    'default_uom': uom.id,
                    'category': category.id,
                    'type': 'service',
                    'list_price': Decimal(0),
                    'cost_price': Decimal(0),
                    }])
            product, = self.product.create([{
                    'template': template.id,
                    'code': '123456789012',
                    'description': 'Description of the product ${record.code}',
                    }])
            self.assert_(product)
            transaction.cursor.commit()

    def test0060map_external_to_tryton(self):
        '''
        Map external data to tryton dictionary value (to import the record)
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            name = 'mapping.product'
            values = {
                'name': 'Ball',
                'cost_price': 23.50,
            }
            result = self.mapping.map_external_to_tryton(name, values)
            self.assertEqual(result,  {
                    'name': 'Ball',
                    'cost_price': 23.50,
                })

    def test0070map_tryton_to_external(self):
        '''
        Map tryton data to external dictionary (to export the record)
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            templates = POOL.get('product.template').search([
                ('name', '=', 'Ball'),
                ], limit=1)
            name = 'mapping.product'
            template_ids = [t.id for t in templates]
            result = self.mapping.map_tryton_to_external(name, template_ids)
            self.assertEqual(result, [{
                    'id': 1,
                    'name_en': 'Ball',
                    'cost_price': '',
                }])

            products = POOL.get('product.product').search([
                    ('template', 'in', template_ids),
                    ], limit=1)
            name = 'mapping.product.variant'
            product_ids = [p.id for p in products]
            result = self.mapping.map_tryton_to_external(name, product_ids)
            self.assertEqual(result, [{
                    'id': product_ids[0],
                    'template': template_ids[0],
                    'code': '123456789012',
                    'description': 'Description of the product 123456789012',
                }])

    def test0080map_exclude_update(self):
        '''
        Delete key from dict
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            name = 'mapping.product'
            result = {'name': 'Ball', 'cost_price': 30.0, 'active': True}
            result = self.mapping.map_exclude_update(name, result)
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
