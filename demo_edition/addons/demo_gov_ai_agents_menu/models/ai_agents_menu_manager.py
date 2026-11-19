# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DemoGovAIAgentsMenuManager(models.TransientModel):
    _name = 'demo_gov.ai.agents.menu.manager'
    _description = 'مدير قائمة وكلاء AI'

    AI_AGENT_MODULES = [
        'demo_gov_commitment_ai_agent',
        'procurement_adjudication_ai_agent',
        'demo_gov_vendor_penalty_ai_agent',
        'demo_gov_payment_anomaly_ai_agent',
        'demo_gov_eta_retry_ai_agent',
        'demo_gov_arabic_ai_assistant',
        'demo_gov_budget_forecast_ai_agent',
        'demo_gov_conflict_interest_ai_agent',
        'demo_gov_procurement_splitting_ai_agent',
        'demo_gov_vendor_data_quality_ai_agent',
        'demo_gov_vendor_performance_ai_agent',
        'demo_gov_dead_stock_ai_agent',
        'demo_gov_daftar55_reconcile_ai_agent',
        'demo_gov_payment_cycle_delay_ai_agent',
        'demo_gov_duplicate_claim_ai_agent',
        'demo_gov_budget_reallocation_ai_agent',
        'demo_gov_procurement_legal_compliance_ai_agent',
        'demo_gov_executive_briefing_ai_agent',
    ]

    AI_MENU_KEYWORDS = [
        'وكيل',
        'AI',
        'الذكاء الاصطناعي',
        'المساعد',
        'الملخص التنفيذي',
        'توقع',
        'توصية',
        'مخزون راكد',
        'مطابقة دفتر 55',
        'تأخيرات دورة الصرف',
        'تكرار المستندات',
        'الالتزام القانوني',
    ]

    @api.model
    def action_refresh_ai_agents_menu(self):
        root = self._get_or_create_root_menu()
        moved = self._move_agent_root_menus(root)
        self._fix_root_menu(root)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تحديث مجموعة وكلاء AI'),
                'message': _('تم نقل/تجميع %s قائمة تحت مجموعة وكلاء AI.') % moved,
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_or_create_root_menu(self):
        Menu = self.env['ir.ui.menu'].sudo()
        xml = self.env['ir.model.data'].sudo().search([
            ('module', '=', 'demo_gov_ai_agents_menu'),
            ('name', '=', 'menu_ai_agents_root'),
            ('model', '=', 'ir.ui.menu'),
        ], limit=1)

        if xml and xml.res_id:
            root = Menu.browse(xml.res_id)
            if root.exists():
                return root

        root = Menu.search([('name', '=', 'مجموعة وكلاء AI')], limit=1)
        if not root:
            root = Menu.create({
                'name': 'مجموعة وكلاء AI',
                'sequence': 64,
                'parent_id': False,
                'action': False,
            })

        self.env['ir.model.data'].sudo().create({
            'module': 'demo_gov_ai_agents_menu',
            'name': 'menu_ai_agents_root',
            'model': 'ir.ui.menu',
            'res_id': root.id,
            'noupdate': True,
        })
        return root

    def _fix_root_menu(self, root):
        root.sudo().write({
            'parent_id': False,
            'action': False,
            'sequence': 64,
        })

    def _move_agent_root_menus(self, root):
        Menu = self.env['ir.ui.menu'].sudo()
        Data = self.env['ir.model.data'].sudo()

        moved = 0
        seen = set()

        # 1) Move menus by module XML IDs.
        data_records = Data.search([
            ('model', '=', 'ir.ui.menu'),
            ('module', 'in', self.AI_AGENT_MODULES),
        ])

        for data in data_records:
            menu = Menu.browse(data.res_id)
            if not menu.exists() or menu.id == root.id or menu.id in seen:
                continue

            # Move only top-level agent menus, not their children.
            if not menu.parent_id:
                menu.write({
                    'parent_id': root.id,
                    'sequence': self._agent_sequence(data.module, menu),
                })
                moved += 1
                seen.add(menu.id)

        # 2) Fallback: move top-level menus whose name looks like an AI agent menu.
        top_menus = Menu.search([('parent_id', '=', False)])
        for menu in top_menus:
            if menu.id == root.id or menu.id in seen:
                continue
            if self._looks_like_ai_agent_menu(menu):
                menu.write({
                    'parent_id': root.id,
                    'sequence': 100 + moved,
                })
                moved += 1
                seen.add(menu.id)

        return moved

    def _agent_sequence(self, module_name, menu):
        order = {
            'demo_gov_budget_ai_agent': 10,
            'demo_gov_dossier_ai_agent': 20,
            'demo_gov_commitment_ai_agent': 30,
            'procurement_adjudication_ai_agent': 40,
            'demo_gov_vendor_penalty_ai_agent': 50,
            'demo_gov_payment_anomaly_ai_agent': 60,
            'demo_gov_eta_retry_ai_agent': 70,
            'demo_gov_arabic_ai_assistant': 80,
            'demo_gov_budget_forecast_ai_agent': 90,
            'demo_gov_conflict_interest_ai_agent': 100,
            'demo_gov_procurement_splitting_ai_agent': 110,
            'demo_gov_vendor_data_quality_ai_agent': 120,
            'demo_gov_vendor_performance_ai_agent': 130,
            'demo_gov_dead_stock_ai_agent': 140,
            'demo_gov_daftar55_reconcile_ai_agent': 150,
            'demo_gov_payment_cycle_delay_ai_agent': 160,
            'demo_gov_duplicate_claim_ai_agent': 170,
            'demo_gov_budget_reallocation_ai_agent': 180,
            'demo_gov_procurement_legal_compliance_ai_agent': 190,
            'demo_gov_executive_briefing_ai_agent': 200,
        }
        return order.get(module_name, menu.sequence or 500)

    def _looks_like_ai_agent_menu(self, menu):
        name = menu.name or ''
        if name == 'مجموعة وكلاء AI':
            return False
        return any(keyword.lower() in name.lower() for keyword in self.AI_MENU_KEYWORDS)
