Base External Mapping Module
############################

The base_external_mapping module manage mappings to external services, for example e-commerce tools, migration data, etc.

In Administration/Models/Base External Mapping you can add yours mapping. Every mapping is related a model (product.product, party.party, ...)

= How to call this methods =

== External -> Tryton ==

map_external_to_tryton params: Get external dictionary of values and process it to Tryton dictionary values

 * @param name: Str with the identifier of the base.external.mapping model
 * @param values: dictionary with external values
 * @param context: dictionary with context values (optional)
 * @return: dictionary with recalculated Tryton values

== Example ==

An example connection XML by Proteus is:

    from proteus import config, Model, Wizard
    conf = config.set_xmlrpc('http://user:passwd@server:8069/Database')
    Mapping = Model.get('base.external.mapping')

    name = 'mapping.test.code'
    values= {
        'nombre': 'Raimon',
        'precio': 23.50,
        'prova': 'Test',
        'activo': 0,
        'identificador': 23,
        'categoria': 'Test',
    }
    context = {'language':'es_ES'}
    result = Mapping.map_external_to_tryton(name, values, context, conf.context)
    {'active': False, 'category': [3, 4], 'id': 23, 'name': 'Raimon Zikzakmedia', 'cost_price': 23.5}

 * nombre -> name: In function, we add 'Zikzakmedia' (result = values+' Zikzakmedia')
 * precio -> cost_price: Is float field
 * activo -> active: Boolean
 * identificador -> id: Integer
 * categoria -> category: In function field, we search a category by name

We send an another field '''prova''', but this field is not available in your mapping and don't return it.

In this example, external dictionary use spanish names and it's returned by Tryton field names (mapping).

== Tryton -> External ==

map_tryton_to_external: Get Tryton dictionary of values and process it to external dictionary values

@param name: Str with the identifier of the base.external.mapping model
@param record_ids: Identifiers of the values to export
@param langs: List of codes of languages to export
@return:
    * List of dictionaries with mapped external values
    * If not code or ids, return blank list

An example connection XML by Proteus is:

    from proteus import config, Model, Wizard
    conf = config.set_xmlrpc('http://user:passwd@server:8069/Database')
    Mapping = Model.get('base.external.mapping')

    name = 'product.test'
    record_ids = [1,2]
    context = {'language':'es_ES'} #optional
    langs = ['es_ES'] #optional. If don't specify (empty list), return all languages translatable
    result = Mapping.map_tryton_to_external(name, record_ids, langs, context, conf.context)
    [{'categoria': 4, 'identificador': 1, 'id': 1, 'activo': True, 'nombre': 'Producto 1', 'price': 44.05}, 
    {'nombre': 'Producto 2', 'price': 30.0, 'activo': True, 'identificador': 2, 'id': 2}]

== Exclude fields ==

There is another method to exclude some keys in your dictonary (if you like update, you can remove some keys)

    result = {'nombre': 'Producto 2', 'price': 30.0, 'activo': True}
    result = Mapping.map_del_keys(name, result, conf.context)
    {'price': 30.0, 'activo': True}

In this example, we are removed name field.

To active some fields to remove when update, you can check Exclude Update field.

= Fields =

== Translate ==

Only Tryton -> External option available, return this field add prefix locale. For example:

    {
        name_en':'Product',
        name_es':'Producto',
    }

== In function ==

Type the python code for mapping this field. You can use:

 * self: To make reference to this mapping record.
 * pool: To make reference to the data base objects.
 * values: The value of this field.
 
You must return a variable called "result" with the result of the compute.

An example search method in 'In function' could be:

    result = []
    categories = pool.get('product.category').search([('name','=',values)])
    for category in pool.get('product.category').read(categories, ['name']):
        result.append(category['id'])
 
An example of one2many field could be:

    result = False
    model_obj = pool.get('product.product')
    model_values = model_obj.search([('code','=',values)])
    if model_values:
        result = model_values[0]

== Out funtion ==

Type the python code for mapping this field. You can use:

 * self: To make reference to this mapping record.
 * pool: To make reference to the data base objects.
 * values: The value of this field.
 * record_ids: List IDs you call.
 * record_id: ID you call.
 * transaction: Transaction()
 * context: Dictonary context

You must return a variable called "result" with the result of the compute.

An example browse method in 'Out function'' could be:

    with transaction.set_context(**context):
        product = pool.get('product.product').browse(record_id)
        result = product.name
