import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo.tools import config
config.parse_config(['--config=/etc/odoo/odoo.conf', '--database=odoo17', '--no-http'])

import odoo.modules.registry as registry_mod

reg = registry_mod.Registry.new('odoo17')

with reg.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    IrUiMenu = env['ir.ui.menu']
    IrActWindow = env['ir.actions.act_window']

    top_menu = IrUiMenu.search([('name', '=', 'ERP Migration'), ('parent_id', '=', False)])
    if not top_menu:
        top_menu = IrUiMenu.create({'name': 'ERP Migration', 'parent_id': False, 'sequence': 99})
        print(f"Created top menu: {top_menu.id}")
    else:
        print(f"Top menu exists: {top_menu.id}")

    items = [
        ('purchase.approval.threshold', 'Approval Matrix', 10),
        ('batch.posting.config', 'Batch Posting', 20),
        ('aging.report.wizard', 'Aging Report', 30),
        ('financial.dimension', 'Financial Dimensions', 50),
        ('credit.bureau.config', 'Credit Bureau Config', 70),
        ('contract.price', 'Contract Prices', 80),
        ('inventory.revaluation.wizard', 'Inventory Revaluation', 90),
        ('ic.recharge.rule', 'IC Recharge Rules', 110),
        ('tax.xml.wizard', 'Tax XML Export', 120),
    ]

    for model, name, seq in items:
        if model not in env:
            print(f"  SKIP: {model}")
            continue
        action = IrActWindow.search([('res_model', '=', model)], limit=1)
        if not action:
            action = IrActWindow.create({'name': name, 'res_model': model, 'view_mode': 'tree,form'})
        existing = IrUiMenu.search([('name', '=', name), ('parent_id', '=', top_menu.id)])
        if not existing:
            IrUiMenu.create({
                'name': name,
                'parent_id': top_menu.id,
                'sequence': seq,
                'action': f'ir.actions.act_window,{action.id}',
            })
            print(f"  Created: {name}")
        else:
            print(f"  Exists: {name}")

    cr.commit()
    print("Done! Refresh browser.")
