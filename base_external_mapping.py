#This file is part of base_external_mapping module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from genshi.template import NewTextTemplate as TextTemplate
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Bool, Eval, Not
from trytond.tools import safe_eval
from trytond.transaction import Transaction
from trytond.rpc import RPC
from datetime import datetime
from decimal import Decimal
import logging
try:
    from jinja2 import Template as Jinja2Template
    jinja2_loaded = True
except ImportError:
    jinja2_loaded = False
    logging.getLogger('base_extenal_mapping').error(
        'Unable to import jinja2. Install jinja2 package.')

__all__ = ['BaseExternalMapping', 'BaseExternalMappingLine']


class BaseExternalMapping(ModelSQL, ModelView):
    'Base External Mapping'
    __name__ = 'base.external.mapping'
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
    render_tags = fields.Boolean('Render Tags')
    engine = fields.Selection('get_engines', 'Engine', states={
        'required': Bool(Eval('render_tags')),
        'invisible': Not(Bool(Eval('render_tags'))),
        })

    @classmethod
    def __setup__(cls):
        super(BaseExternalMapping, cls).__setup__()
        cls.__rpc__.update({
            'map_external_to_tryton': RPC(),
            'map_tryton_to_external': RPC(),
            'map_exclude_update': RPC(),
        })
        cls._error_messages.update({
            'syntax_error': ('Syntax Error:\n%s'),
            'unknown_error': ('Unknown Error:\n%s'),
            })
        cls._sql_constraints += [('name_uniq', 'UNIQUE (name)',
                'The name of the Mapping must be unique!')]

    @staticmethod
    def default_engine():
        '''Default Engine'''
        return 'genshi'

    @classmethod
    def get_engines(cls):
        '''Returns the engines as list of tuple

        :return: List of tuples
        '''
        engines = [
            ('python', 'Python'),
            ('genshi', 'Genshi'),
            ]
        if jinja2_loaded:
            engines.append(('jinja2', 'Jinja2'))
        return engines

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            vals['state'] = 'done'
        return super(BaseExternalMapping, cls).create(vlist)

    @classmethod
    def copy(cls, records, default=None):
        """ Duplicates record with given id updating it with default values
            @param records: Identifiers of records to copy,
            @param default: Dictionary of field values to change before saving
                the duplicated object,
            @return: List of identifier records duplicated
        """
        if default is None:
            default = {}
        res = []
        default = default.copy()
        for mapping in records:
            name = mapping.name + '-copy'
            while cls.search([('name', '=', name)]):
                name += '-copy'
            default['name'] = name
            new_mapping, = super(BaseExternalMapping, cls).copy([mapping],
                    default=default)
            res.append(new_mapping)
        return res

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def map_external_to_tryton(cls, name, values={}, context={}):
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
        mappings = cls.search([('name', '=', name)])
        if not len(mappings) > 0:
            logger.info('Not code available mapping: %s' % name)
            return False
        external_mapping = cls(mappings[0])
        for mapping_line in external_mapping.mapping_lines:
            if mapping_line.external_field in values and \
                    (mapping_line.mapping_type == 'in_out' or \
                     mapping_line.mapping_type == 'in') and \
                     mapping_line.active == True:
                if mapping_line.in_function:
                    localspace = {
                        "self": cls,
                        "pool": Pool(),
                        "value": values[mapping_line.external_field],
                        "values": values,
                    }
                    with Transaction().set_context(**context):
                        try:
                            exec mapping_line.in_function in localspace
                            # It is possible that if there is an error in the
                            # code of the field, when execute it, the database
                            # raises an error too, so it could be necessary
                            # to make a commit or a roolback. I don't know yet.
                        except SyntaxError, e:
                            logger.error('Syntax Error in mapping %s, line %s.'
                                ' Error: %s' %
                                (mapping_line.mapping.name,
                                    mapping_line.field.name, e))
                            return False
                        except NameError, e:
                            logger.error('Syntax Error in mapping %s, line %s.'
                                ' Error: %s' %
                                (mapping_line.mapping.name,
                                    mapping_line.field.name, e))
                            return False
                        except Exception, e:
                            logger.error('Unknown Error in mapping %s, line '
                                '%s. Message: %s' %
                                (mapping_line.mapping.name,
                                    mapping_line.field.name, e))
                            return False
                        result = (localspace['result']
                            if 'result' in localspace else False)
                else:
                    result = values[mapping_line.external_field]
                # Force type of result to be float, int decimal or bool (def is str)
                if mapping_line.external_type == 'float':
                    try:
                        result = float(result)
                    except:
                        pass
                elif mapping_line.external_type == 'int':
                    try:
                        result = int(result)
                    except:
                        pass
                elif mapping_line.external_type == 'decimal':
                    try:
                        result = Decimal(result)
                    except:
                        pass
                elif mapping_line.external_type == 'bool':
                    if result:
                        result = True
                    else:
                        result = False
                elif mapping_line.external_type == 'date':
                    try:
                        result = datetime.strptime(result, '%Y-%m-%d')
                    except:
                        pass
                elif mapping_line.external_type == 'str':
                    if result:
                        result = '%s' % result
                    else:
                        result = None

                # Add in dict all fields type dict
                if mapping_line.field.ttype == 'dict':
                    old_result = {}
                    if mapping_line.field.name in results:
                        old_result = results.get(mapping_line.field.name)
                    new_result = {mapping_line.external_field: result}
                    result = dict(old_result.items() + new_result.items())

                results[mapping_line.field.name] = result
        return results

    @classmethod
    def map_tryton_to_external(cls, name, records=[], langs=[], context={}):
        """ Get Tryton dictionary of values and process it to external
                dictionary values
            @param name: Str with the identifier of the
                base.external.mapping model
            @param records: Identifiers of the values to export
            @param langs: List of codes of languages to export
            @return:
                * List of dictionaries with mapped external values
                * If not code or ids, return blank list
        """
        res = []
        relational_fields = ['many2one', 'one2many', 'many2many']
        logger = logging.getLogger('base_external_mapping')

        if isinstance(records, (int, long)):
            records = [records]
        if not len(records) > 0:
            logger.error('Not set IDs from %s' % name)
            return res
        mappings = cls.search([('name', '=', name)])
        if not len(mappings) > 0:
            logger.info('Not code available mapping: %s' % name)
            return False
        external_mapping = cls(mappings[0])
        if not len(langs) > 0:
            langs = Pool().get('ir.lang').get_translatable_languages()

        for record in records:
            data_values = {'id': record}
            model_name = external_mapping.model.model
            Model = Pool().get(model_name)
            ids = Model.search([('id', '=', record)])
            if not len(ids) > 0:
                continue
            with Transaction().set_context(**context):
                model = Model(record)
            for mapping_line in external_mapping.mapping_lines:
                if not mapping_line.active:
                    continue
                if not mapping_line.mapping_type in ('out', 'in_out'):
                    continue
                field = mapping_line.field.name
                external_field = mapping_line.external_field
                ttype = mapping_line.field.ttype
                if mapping_line.translate:
                    for lang in langs:
                        if lang != 'en_US':
                            Translation = Pool().get('ir.translation')
                            trans_ids = Translation.search([
                                ('lang', '=', lang),
                                ('name', '=', model_name + ',' + field),
                                ('res_id', '=', record)
                            ])
                            if trans_ids:
                                translation = Pool().get('ir.translation')(
                                    trans_ids[0])
                                trans_value = translation.value
                            else:
                                trans_value = getattr(model, field, '')
                        else:
                            trans_value = getattr(model, field, '')
                        if (ttype in ('char', 'text')
                                and external_mapping.render_tags):
                            data_values[external_field + '_' + lang[:2]] = (
                                external_mapping.eval(getattr(model, field),
                                        model))
                        else:
                            data_values[external_field + '_' + lang[:2]] = (
                                    trans_value)
                else:
                    external_field = mapping_line.external_field
                    out_function = mapping_line.out_function

                    if out_function:
                        localspace = {
                            "self": cls,
                            "pool": Pool(),
                            "records": records,
                            "record": record,
                            "transaction": Transaction(),
                            "context": context,
                        }
                        try:
                            exec out_function in localspace
                        except Exception, e:
                            logger.error('Unknown Error exporting line with'
                                ' id %s. Message: %s' % (mapping_line.id, e))
                            return False
                        data_value = localspace.get('result')
                        if not data_value:
                            data_values[external_field] = ''
                    elif ttype in relational_fields:
                        if ttype == 'many2one':
                            data_value = getattr(model, field)
                            if data_value is not None:
                                data_value = data_value.id
                        # Many2Many or One2Many fields, create list
                        else:
                            data_value = []
                            values = getattr(model, field)
                            for val in values:
                                data_value.append(val.id)
                    else:
                        data_value = getattr(model, field)

                    if ttype == 'numeric' and not data_value:
                        data_values[external_field] = ''
                    if ttype == 'char' and not data_value:
                        data_values[external_field] = ''
                    if ttype == 'boolean' and not data_value:
                        data_values[external_field] = False
                    if ttype == 'selection' and not data_value:
                        data_values[external_field] = ''

                    # Extract dict value
                    if mapping_line.field.ttype == 'dict' and data_value:
                        data_value = data_value.get(external_field)

                    if data_value:
                        if (ttype in ('char', 'text')
                                and external_mapping.render_tags):
                            data_values[external_field] = (
                                external_mapping.eval(data_value, model))
                        else:
                            data_values[external_field] = data_value
            res.append(data_values)
        return res

    @classmethod
    def map_exclude_update(cls, name, values={}):
        """
        Exclude some keys in values from mapping
        @param name: Str with the identifier of the
            base.external.mapping model
        @param values: dictionary with external values
        :return vals dicc values recalculated
        """
        exclude_lines = []
        mappings = cls.search([('name', '=', name)])
        logger = logging.getLogger('base_external_mapping')
        if not len(mappings) > 0:
            logger.info('Not code available mapping: %s' % name)
            return False
        for line in cls(mappings[0]).mapping_lines:
            if line.exclude_update:
                exclude_lines.append(line.field.name)
        for line in exclude_lines:
            if line in values:
                del values[line]
        return values

    def eval(self, expression, record):
        '''Evaluates the given :attr:expression

        :param template: Browse record of the template
        :param expression: Expression to evaluate
        :param record: The browse record of the record
        '''
        engine_method = getattr(self, '_engine_' + self.engine)
        return engine_method(expression, record)

    def template_context(self, record):
        """ Generate the template context
        This is mainly to assist in the inheritance pattern
        """
        return {'record': record}

    def _engine_python(self, expression, record):
        '''Evaluate the pythonic expression and return its value
        '''
        if expression is None:
            return u''
        assert self is not None, 'Record is undefined'
        template_context = self.template_context()
        return safe_eval(expression, template_context)

    def _engine_genshi(self, expression, record):
        '''
        :param expression: Expression to evaluate
        :param record: Browse record
        '''
        if not expression:
            return u''
        template = TextTemplate(expression)
        template_context = self.template_context(record)
        return template.generate(**template_context).render(encoding='UTF-8')

    def _engine_jinja2(self, expression, record):
        '''
        :param expression: Expression to evaluate
        :param record: Browse record
        '''
        if not expression:
            return u''
        template = Jinja2Template(expression)
        template_context = self.template_context()
        return template.render(template_context).encode('utf-8')

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class BaseExternalMappingLine(ModelSQL, ModelView):
    'Base External Mapping Line'
    __name__ = 'base.external.mapping.line'
    mapping = fields.Many2One('base.external.mapping', 'External Mapping',
        required=True, ondelete='CASCADE')
    field = fields.Many2One('ir.model.field', 'Field',
        domain=[('model', '=', Eval('_parent_mapping', {}).get('model'))],
        select=True, required=True)
    external_field = fields.Char('External Field', required=True)
    mapping_type = fields.Selection([
        ('in', 'Tryton <- External'),
        ('in_out', 'Tryton <-> External'),
        ('out', 'Tryton -> External'),
        ], 'Type', required=True)
    external_type = fields.Selection([
        ('str', 'String'),
        ('bool', 'Boolean'),
        ('int', 'Integer'),
        ('decimal','Decimal'),
        ('float', 'Float'),
        ('date', 'Date'),
        ], 'External Type', required=True)
    translate = fields.Boolean('Translate',
        help='Check this option to export fields with locale sufix.'
            'Example: name_en')
    active = fields.Boolean('Active')
    exclude_update = fields.Boolean('Exclude Update',
        help='When update data (write), this field is excluded')
    sequence = fields.Integer('Sequence',
        help='The order you want to relate columns of the file with fields'
            'of Tryton')
    in_function = fields.Text('Import to Tryton',
        help='Type the python code for mapping this field.\n'
            'You can use:\n'
            '  * self: To make reference to this mapping record.\n'
            '  * pool: To make reference to the data base objects.\n'
            '  * value: The value of this field.\n'
            '  * values: Values dict (key is from external data).\n'
            'You must return a variable called "result" with the'
            ' result of the compute.')
    out_function = fields.Text('Export from Tryton',
        help='Type the python code for mapping this field.\n'
            'You can use:\n'
            '  * self: To make reference to this mapping record.\n'
            '  * pool: To make reference to the data base objects.\n'
            '  * records: List IDs you call.\n'
            '  * record: ID you call.\n'
            '  * transaction: Transaction()\n'
            '  * context: Dictonary context\n'
            'You must return a variable called "result" with the'
            ' result of the compute.')

    @classmethod
    def __setup__(cls):
        super(BaseExternalMappingLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_mapping_type():
        return 'in'

    @staticmethod
    def default_external_type():
        return 'str'

    @staticmethod
    def default_sequence():
        return 1

    def on_change_field(self):
        if self.field:
            return {'name': self.field.name}
        else:
            return {'name': self.external_field}

    @fields.depends('field', 'external_field')
    def on_change_external_field(self):
        return self.on_change_field()

    @classmethod
    def check_xml_record(cls, records, values):
        return True
