#This file is part of base_external_mapping module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Equal, Not
from trytond.tools import safe_eval, datetime_strftime
from trytond.transaction import Transaction
import logging

class BaseExternalMapping(ModelSQL, ModelView):
    'Base External Mapping'
    _name = 'base.external.mapping'
    _description = __doc__

    name = fields.Char('Code', required=True,
        states={
            'readonly': Eval('state').in_(['done']),
            },
        depends=['state'], 
        help='Use lowercase, az09 characters and separated by . (dot)')
    model = fields.Many2One('ir.model', 'Model', required=True,
        ondelete='CASCADE',
        states={
            'readonly': Eval('state').in_(['done']),
            },
        depends=['state'])
    mapping_lines = fields.One2Many('base.external.mapping.line', 'mapping',
            'Mapping Lines',)
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')],
        "State", required=True, readonly=True)

    def __init__(self):
        super(BaseExternalMapping, self).__init__()
        self._rpc.update({
            'map_external_to_tryton': True,
            'map_tryton_to_external': True,
            'map_del_keys': True,
        })
        self._error_messages.update({
            'syntax_error': ('Syntax Error:\n%s'),
            'unknown_error': ('Unknown Error:\n%s'),
            })
        self._sql_constraints += [('name_uniq', 'UNIQUE (name)',
                'The name of the Mapping must be unique!')]

    def create(self, vals):
        vals['state'] = 'done'
        return super(BaseExternalMapping, self).create(vals)

    def copy(self, ids, default=None):
        """ Duplicates record with given id updating it with default values
            @param ids: Identifiers of records to copy,
            @param default: Dictionary of field values to change before saving
                the duplicated object,
            @return: List of identifier records duplicated
        """
        if not default:
            default = {}
        res = []
        for mapping in self.browse(ids):
            name = mapping.name + '-copy'
            while self.search([('name', '=', name)]):
                name += '-copy'
            default['name'] = name
            res.append(super(BaseExternalMapping, self).copy(mapping.id,
                    default=default))
        return res

    def default_state(self):
        return 'draft'

    def map_external_to_tryton(self, name, values={}, context={}):
        """ Get external dictionary of values and process it to Tryton
                dictionary values
            @param name: Str with the identifier of the
                base.external.mapping model
            @param values: dictionary with external values
            @param context: dictionary with context values (optional)
            @return: dictionary with recalculated Tryton values
        """
        results = {}
        logger = logging.getLogger('base_external_mapping')
        mappings = self.search([('name','=',name)])
        if not len(mappings)>0:
            logger.info('Not code available mapping: %s' % name)
            return False
        external_mapping = self.browse(mappings[0])
        for mapping_line in external_mapping.mapping_lines:
            if mapping_line.external_field in values and \
                    (mapping_line.mapping_type == 'in_out' or \
                     mapping_line.mapping_type == 'in') and \
                     mapping_line.active == True:
                if mapping_line.in_function:
                    localspace = {
                        "self": self,
                        "pool": Pool(),
                        "values": values[mapping_line.external_field],
                    }
                    with Transaction().set_context(**context):
                        try:
                            exec mapping_line.in_function in localspace
                            # It is possible that if there is an error in the code
                            # of the field, when execute it, the database raises an
                            # error too, so it could be necessary to make a commit
                            # or a roolback. I don't know yet.
                        except SyntaxError, e:
                            logger.error('Syntax Error in mapping %s, line %s. Error: %s' %
                                (mapping_line.mapping.name, mapping_line.field.name, e))
                            return False
                        except NameError, e:
                            logger.error('Syntax Error in mapping %s, line %s. Error: %s' %
                                (mapping_line.mapping.name, mapping_line.field.name, e))
                            return False
                        except Exception, e:
                            logger.error('Unknown Error in mapping %s, line %s. Message: %s' %
                                (mapping_line.mapping.name, mapping_line.field.name, e))
                            return False
                        result = localspace['result'] if 'result' in localspace \
                                else False
                else:
                    result = values[mapping_line.external_field]
                # Force type of result to be float, int or bool (default is str)
                if mapping_line.external_type == 'float':
                    try:
                        result = float(result)
                    except:
                        pass
                if mapping_line.external_type == 'int':
                    try:
                        result = int(result)
                    except:
                        pass
                if mapping_line.external_type == 'bool':
                    if result:
                        result = True
                    else:
                        result = False
                results[mapping_line.field.name] = result
        return results

    def map_tryton_to_external(self, name, record_ids=[], langs=[], context={}):
        """ Get Tryton dictionary of values and process it to external
                dictionary values
            @param name: Str with the identifier of the
                base.external.mapping model
            @param record_ids: Identifiers of the values to export
            @param langs: List of codes of languages to export
            @return:
                * List of dictionaries with mapped external values
                * If not code or ids, return blank list
        """
        res=[]
        relational_fields = ['many2one', 'one2many','many2many']
        logger = logging.getLogger('base_external_mapping')

        if isinstance(record_ids, (int, long)):
            record_ids = [record_ids]
        if not len(record_ids)>0:
            logger.error('Not set IDs from %s' % name)
            return res
        mappings = self.search([('name','=',name)])
        if not len(mappings)>0:
            logger.info('Not code available mapping: %s' % name)
            return False
        external_mapping = self.browse(mappings[0])
        if not len(langs)>0:
            langs = Pool().get('ir.lang').get_translatable_languages()

        for record_id in record_ids:
            data_values = {'id': record_id}
            model_name = external_mapping.model.model
            model_obj = Pool().get(model_name)
            ids = model_obj.search([('id','=',record_id)])
            if not len(ids)>0:
                continue
            with Transaction().set_context(**context):
                model = model_obj.browse(record_id)
            for mapping_line in external_mapping.mapping_lines:
                if not mapping_line.active:
                    continue
                if not mapping_line.mapping_type in ('out', 'in_out'):
                    continue
                field =  mapping_line.field.name
                external_field = mapping_line.external_field
                if mapping_line.translate:
                    for lang in langs:
                        if lang != 'en_US':
                            trans_obj = Pool().get('ir.translation')
                            trans_ids = trans_obj.search([
                                ('lang', '=', lang),
                                ('name', '=', model_name + ',' + field),
                                ('res_id', '=', record_id)
                            ])
                            if trans_ids:
                                translation = Pool().get('ir.translation').\
                                        browse(trans_ids[0])
                                trans_value = translation.value
                            else:
                                trans_value = getattr(model, field) or ''
                        else:
                            trans_value = getattr(model, field) or ''
                        data_values[external_field + '_' + lang[:2]] = \
                                trans_value
                else:
                    ttype = mapping_line.field.ttype
                    out_function = mapping_line.out_function
                    if out_function:
                        localspace = {
                            "self": self,
                            "pool": Pool(),
                            "record_ids": record_ids,
                            "record_id": record_id,
                            "transaction": Transaction(),
                            "context": context,
                        }
                        try:
                            exec out_function in localspace
                        except Exception, e:
                            logger.error('Unknown Error exporting line with'\
                                    ' id %s. Message: %s' % \
                                    (mapping_line.id, e))
                            return False
                        data_value = 'result' in localspace and \
                                localspace['result'] or False
                    elif ttype in relational_fields:
                        if ttype == 'many2one':
                            data_value = getattr(model, field).id
                        else: # Many2Many or One2Many fields, create list
                            data_value = []
                            values = getattr(model, field)
                            for val in values:
                                data_value.append(val.id)
                    else:
                        data_value = getattr(model, field)
                    if ttype == 'char' and not data_value:
                        data_value = ''
                    external_field = mapping_line.external_field
                    if ttype == 'boolean' and not data_value:
                        data_values[external_field] = False
                    if ttype == 'numeric':
                        data_value = float(data_value)
                    if data_value:
                        data_values[external_field] = data_value
            res.append(data_values)
        return res

    def map_del_keys(self, name, values={}):
        """
        Exclude some keys in values from mapping
        @param name: Str with the identifier of the
            base.external.mapping model
        @param values: dictionary with external values
        :return vals dicc values recalculated
        """
        exclude_lines = []
        mappings = self.search([('name','=',name)])

        if not len(mappings)>0:
            logger.info('Not code available mapping: %s' % name)
            return False
        for line in self.browse(mappings[0]).mapping_lines:
            if line.update:
                exclude_lines.append(line.field.name)
        for line in exclude_lines:
            if line in values:
                del values[line]
        return values

BaseExternalMapping()

class BaseExternalMappingLine(ModelSQL, ModelView):
    'Base External Mapping Line'
    _name = 'base.external.mapping.line'
    _description = __doc__

    mapping = fields.Many2One('base.external.mapping', 'External Mapping',
            ondelete='CASCADE')
    field = fields.Many2One('ir.model.field', 'Field',
        domain=[('model', '=', Eval('_parent_mapping', {}).get('model'))],
        select=True, required=True)
    external_field = fields.Char('External Field', required=True,
            on_change=['field', 'external_field'],)
    mapping_type = fields.Selection([
        ('in', 'Tryton <- External'),
        ('in_out', 'Tryton <-> External'),
        ('out', 'Tryton -> External'),
    ], 'Type', required=True)
    external_type = fields.Selection([
        ('str', 'String'),
        ('bool', 'Boolean'),
        ('int', 'Integer'),
        ('float', 'Float'),
    ], 'External Type', required=True)
    translate = fields.Boolean('Translate',
            help='Check this option to export fields with locale sufix. ' + \
            'Example: name_en'
    )
    active = fields.Boolean('Active')
    update = fields.Boolean('Exclude Update',
            help='When update data (write), this field is excluded')
    sequence = fields.Integer('Sequence',
            help='The order you want to relate columns of the file with' + \
            ' fields of Tryton.')
    in_function = fields.Text('Import to Tryton',
            help='Type the python code for mapping this field.\n' + \
                'You can use:\n' + \
                '  * self: To make reference to this mapping record.\n' + \
                '  * pool: To make reference to the data base objects.\n' + \
                '  * values: The value of this field.\n' + \
                'You must return a variable called "result" with the' + \
                ' result of the compute.'
            )
    out_function = fields.Text('Export from Tryton',
            help='Type the python code for mapping this field.\n' + \
                'You can use:\n' + \
                '  * self: To make reference to this mapping record.\n' + \
                '  * pool: To make reference to the data base objects.\n' + \
                '  * record_ids: List IDs you call.\n' + \
                '  * record_id: ID you call.\n' + \
                '  * transaction: Transaction()\n' + \
                '  * context: Dictonary context\n' + \
                'You must return a variable called "result" with the' + \
                ' result of the compute.' 
            )

    def __init__(self):
        super(BaseExternalMappingLine, self).__init__()
        self._order.insert(0, ('sequence', 'ASC'))

    def default_active(self):
        return True

    def on_change_field(self, vals):
        model_obj = Pool().get('ir.model.field')
        if vals['field']:
            return {'name': model_obj.browse(vals['field']).name}
        else:
            return {'name': vals['external_field']}

    def on_change_external_field(self, vals):
        return self.on_change_field(vals)

BaseExternalMappingLine()
