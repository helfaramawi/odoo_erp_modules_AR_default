{
    'name': 'Demo Branding & Environment Banner',
    'summary': 'Centralized demo branding (app/org name, support contact) and DEMO ENVIRONMENT banner',
    'description': """
        Centralizes the identity shown across the Demo Edition: application name,
        organization name, environment label, and support contact.

        Values are stored as ir.config_parameter entries (editable from
        Settings > General Settings > Demo Branding) so that reports, the
        login screen, and other modules read one source of truth instead of
        hard-coded strings.

        Also shows a small, non-intrusive "DEMO ENVIRONMENT" banner on the
        login screen when demo_branding.environment is set to 'demo'.
    """,
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'author': 'Enterprise Solutions Demo',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': ['base', 'base_setup', 'web'],
    'data': [
        'data/demo_branding_data.xml',
        'views/res_config_settings_views.xml',
        'views/webclient_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
