==================
Mapeo externo base
==================

Este módulo permite la conversión de datos de externos a Tryton y de Tryton a
externos. Es un módulo técnico creador para plataformas de comercio electrónico
como e-Sale o Magento donde se requiere una mapeo de campos y cálculos de estos.

Configuración
=============

La configuración del módulo se realiza a través del menú |menu_base_external_mapping|\ .
Todos los mapeos están relacionados con un modelo (producto, tercero, etc...).

.. |menu_base_external_mapping| tryref:: base_external_mapping.base_external_mapping_menu/complete_name

Cómo llamar estos métodos
=========================

Externo -> Tryton
-----------------

**map_external_to_tryton** Toma un diccionario externo de valores y lo
procesa a un diccionario de valores Tryton:

* @param name: Cadena de caracteres con identificador del modelo base.external.mapping
* @param values: Diccionario con los valores externos
* @param context: Dictionary con los valores de contexto (opcional)
* @return: Diccionario con los valores recalculados Tryton

Ejemplo
#######

Ejemplo de conexión mediante el protocolo XML proporcionado por Proteus:

.. code:: python

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

* nombre -> name: El método añade 'Zikzakmedia' (resultado = values['name'] + ' Zikzakmedia')
* precio -> cost_price: Es un campo de coma flotante
* activo -> active: Un campo booleano
* identificador -> id: Entero
* categoria -> category: Es un campo funcional que busca una categoría por su nombre
  y devuelbe su identificador

Además se envía un campo de más, **test**, pero como este campo no está
disponible en el mapeo, no lo devuelve. 

En este ejemplo, el diccionario externo utiliza el nombre de los campos en
castellano y en el mapeo los devuelve tal y como Tryton los tiene definidos.

Tryton -> Externo
-----------------

**map_tryton_to_external:** Toma un diccionario de valores Tryton, lo procesa
y devuelve un diccionario externo.

* @param name: Cadena de caracteres con el identificador del modelo base.external.mapping
* @param record_ids: Identificadores de los valores a exportar
* @param langs: Lista de códigos de idiomas a exportar
* @return:
  * Lista de diccionarios con los valores del mapeo externo
  * Si no hay valores, devuelve una lista vacía

Ejemplo
#######

Ejemplo de conexión mediante el protocolo XML proporcionado por Proteus:

.. code:: python

    from proteus import config, Model, Wizard
    conf = config.set_xmlrpc('http://user:passwd@server:8069/Database')
    Mapping = Model.get('base.external.mapping')
    
    name = 'product.test'
    record_ids = [1,2]
    context = {'language':'es_ES'} #optional
    langs = ['es_ES'] #optional. If don't specify (empty list), return all languages translatable
    result = Mapping.map_tryton_to_external(name, record_ids, langs, context, conf.context)
    [{'categoria': 4, 'identificador': 1, 'id': 1, 'activo': True, 'nombre': 'Producto 1', 'price': 44.05}, 
    {'nombre': 'Producto 2', 'price': 30.0, 'aivo': True, 'identificador': 2, 'id': 2}]

Excluir campos
--------------

Hay un método para excluir algunos valores del diccionario (si desea actualizar,
puede borrar algunos campos)

Ejemplo
#######

Para borrar el campo name:

.. code:: python

    result = {'nombre': 'Producto 2', 'price': 30.0, 'activo': True}
    result = Mapping.map_del_keys(name, result, conf.context)
    {'price': 30.0, 'acto': True}

To active some fields to remove when update, you can check Exclude Update field.

Campos
======

Traducción
----------

Esta opción sólo está disponible en mapeos Tryton -> Externo. Devuelve el nombre
del campo con el sufijo del locale. Por ejemplo:

.. code:: python

    {
        name_en':'Product',
        name_es':'Producto',
    }

Función de entrada
------------------

Escriba la función Python para que mapee este campo. Puede utilizar:

* self: Para hacer referencia al registro a mapear.
* pool: Para hacer referencia a los objetos de la base de datos.
* values: Los valores de este campo.

Debe devolver una variable denominada **result** con el resultado del cálculo.

Ejemplo
#######

Un ejemplo de método de búsqueda para un campo **Función de entrada** One2Many
podría ser:

.. code:: python

    result = []
    categories = pool.get('product.category').search([('name','=',values)])
    for category in pool.get('product.category').read(categories, ['name']):
        result.append(category['id'])

Ejemplo
#######

Un ejemplo de método de búsqueda para un campo **Función de entrada** Many2One
podría ser:

.. code:: python

    result = False
    model_obj = pool.get('product.product')
    model_values = model_obj.search([('code','=',values)])
    if model_values:
        result = model_values[0]

Función de salida
-----------------

Escriba el código Python para mapear este campo. Puede utilizar:

 * self: Para hacer referencia a este registro de mapeo.
 * pool: Para hacer referencia a los objetos de la base de datos.
 * values: El valor de este campo.
 * record_ids: Lista de identificadores que llama.
 * record_id: Identificador que llama.
 * transaction: Transaction()
 * context: Diccionario de contexto

Debe devolver una variable denominada **result** con el resultado del cálculo.

Ejemplo
#######

Un ejemplo de método browse para un campo **Función de salida** podría ser:

.. code:: python

    with transaction.set_context(**context):
        product = pool.get('product.product').browse(record_id)
        result = product.name
