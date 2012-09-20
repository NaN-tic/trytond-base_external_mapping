#This file is part of base_external_mapping module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
{
    'name': 'Base External Mapping',
    'name_ca_ES': 'Base External Mapping',
    'name_es_ES': 'Base External Mapping',
    'version': '2.4.0',
    'author': 'Zikzakmedia',
    'email': 'zikzak@zikzakmedia.com',
    'website': 'http://www.zikzakmedia.com/',
    'description': '''Tryton integration to External Mapping (webservices, etc.)''',
    'description_ca_ES': '''Integració Tryton per assignacions externes (serveis web, etc.)''',
    'description_es_ES': '''Integración Tryton para asignaciones externas (servicios web, etc.)''',
    'depends': [
        'ir',
        'res',
    ],
    'xml': [
        'base_external_mapping.xml',
    ],
    'translation': [
        'locale/ca_ES.po',
        'locale/es_ES.po',
    ]
}
