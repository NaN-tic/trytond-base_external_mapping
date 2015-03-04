=====================================
Base External Mapping (Mapeo externo)
=====================================

Este módulo permite la conversión de datos de aplicaciones externas a Tryton y de Tryton a
externas aplicaciones. Es un módulo técnico creador para plataformas de comercio electrónico
como e-Sale o Magento donde se requiere un mapeo de campos y cálculos de estos. También se usa
este módulo para la importación de ficheros CSV complejos.

La configuración del módulo se realiza a través del menú |menu_base_external_mapping|. 
Todos los mapeos están relacionados con un modelo (producto, tercero, etc...).

.. |menu_base_external_mapping| tryref:: base_external_mapping.base_external_mapping_menu/complete_name

Mapeo
-----

Un mapeo nos pemite relacionar con que objecto va relacionado y los campos de Tryton a que
campos "exterior" corresponen (campo tryton <-> campo externo).

Cada campo de podemos marcar en que dirección lo queremos calcular:

* campo tryton <-> campo externo
* campo tryton -> campo externo
* campo tryton <- campo externo

Ejemplos
--------

Mapeo Tercero
#############

El mapeo del tercero irá relacionado con el modelo "party". En las líneas del mapeo relacionaremos
los campos de Tryton con los campos externos (campo tryton <-> campo externo). Por ejemplo, el campo
de Tryton y un campo externo podría ser:

* name <-> nombre
* vat_number <-> cif
* reference <-> code

Otra de las funcionalidades del Base External Mapping es hacer búsquedas o cálculos con los datos. En los campos
"Importar a Tryton" o "Exportar a Tryton" podemos añadir código del framework de Tryton para cálculos. En este
ejemplo buscaremos productos por código.

.. code-block:: python

    result = None
    Product = pool.get('product.product')
    products = Product.search([('code', '=', values)])
    if products:
        result = products[0]

==============================
Base External Mapping. Técnico
==============================

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

Renderizar etiquetas
--------------------

Si en el mapeo se activa la opción "Renderizar etiquetas" activará la conversión
de etiquetas a su valor.

Por ejemplo, si a un producto a la descripción dispone de la etiqueta:

.. code:: python

    ${record.name}

El valor resultante será el nombre del producto (record es el objeto orígen).

Campos diccionarios
-------------------

Si en nuestro mapeo usamos algún campo del tipo diccionario, no mapearemos el campo ya con valores del diccionario.
Por cada elemento del diccionario, será una columna de entrada y al final si el campo es del tipo diccionario, este
se transformará a diccionario.

Por ejemplo, tenemos un campo diccionario que tiene tres valores. Cada campo, será una columna d'entrada, por ejemplo un CSV seria

.. code:: python

    campo1,campo2,campo3

Si el campo es un diccionario, ya nos creará los valores en formato diccionario:

.. code:: python

    {'campo1': 'valor1', 'campo2': 'valor2', 'campo3': valor3'}
