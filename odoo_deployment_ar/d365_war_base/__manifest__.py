{
    'name': 'D365 War Room Base',
    'version': '17.0.1.0.0',
    'summary': 'War-room governance baseline for D365 to Odoo transition',
    'category': 'Project',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/war_room_security.xml',
        'security/ir.model.access.csv',
        'data/war_room_sequence.xml',
        'views/war_room_item_views.xml',
        'views/war_room_menu.xml',
    ],
    'installable': True,
    'application': True,
}
