# -*- coding: utf-8 -*-
{
    'name': "Manager All Approvals",

    'summary': """
        Approval On All Document""",

    'description': """
        Approval On All Document
    """,

    'author': "Viltco",
    'website': "http://www.viltco.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'All',
    'version': '14.0.0.0',
    'sequence': 1,

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'sale', 'mrp'],

    # always loaded
    'data': [
        'security/security.xml',
        'views/approval_all_manager_views.xml',
    ],

}
