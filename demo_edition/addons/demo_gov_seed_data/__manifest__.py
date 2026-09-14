{
    'name': 'Demo Governorate — Seed Data',
    'summary': 'Synthetic master data (employees, vendors, customers, items) for the Demo Edition',
    'description': """
        Populates the Demo Edition with realistic-looking, entirely synthetic
        master data so dashboards, lists and reports are not empty:

        - Demo employees, one per demo.* user (see l10n_eg_custody/data/demo_users.xml)
        - Demo vendors and customers
        - Demo inventory items

        None of this data references any real person, company, or
        government entity. See docs/demo/DEMO_DATA.md for the full
        dataset description and docs/demo/DEMO_GUIDE.md for how to layer
        end-to-end transactions (purchase requisition -> PO -> receipt,
        auction, custody assignment, etc.) on top of it through the UI.

        A post-install hook applies the DEMO_USERS_PASSWORD environment
        variable (if set) to all demo.* accounts, so the same seed data
        can be reused safely across environments without a hard-coded
        password. See scripts/demo-seed/README.md.
    """,
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'author': 'Enterprise Solutions Demo',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'hr', 'stock', 'purchase', 'sale',
        'l10n_eg_custody', 'demo_branding',
    ],
    'data': [
        'data/demo_partners.xml',
        'data/demo_products.xml',
        'data/demo_employees.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
