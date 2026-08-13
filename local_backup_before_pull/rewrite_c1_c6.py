import os

base = '/mnt/extra-addons'

# ── MINIMAL C6 ────────────────────────────────────────────────────────────────
os.makedirs(f'{base}/c6_cost_centre/models', exist_ok=True)
os.makedirs(f'{base}/c6_cost_centre/views', exist_ok=True)

open(f'{base}/c6_cost_centre/__manifest__.py', 'w').write("""{
    'name': 'Cost Centre on Requisitions',
    'version': '17.0.1.0.0',
    'category': 'Purchase',
    'depends': ['purchase', 'c5_financial_dimensions'],
    'data': ['views/purchase_cost_centre_views.xml'],
    'installable': True,
    'license': 'LGPL-3',
}""")

open(f'{base}/c6_cost_centre/__init__.py', 'w').write("from . import models\n")
open(f'{base}/c6_cost_centre/models/__init__.py', 'w').write("from . import purchase_cost_centre\n")

open(f'{base}/c6_cost_centre/models/purchase_cost_centre.py', 'w').write("""from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    x_cost_centre_id = fields.Many2one(
        'financial.dimension',
        string='Cost Centre',
        domain=[('dimension_type', '=', 'department')],
    )
""")

open(f'{base}/c6_cost_centre/views/purchase_cost_centre_views.xml', 'w').write("""<?xml version="1.0" encoding="utf-8"?>
<odoo>
  <record id="view_purchase_order_cost_centre" model="ir.ui.view">
    <field name="name">purchase.order.cost.centre</field>
    <field name="model">purchase.order</field>
    <field name="inherit_id" ref="purchase.purchase_order_form"/>
    <field name="arch" type="xml">
      <xpath expr="//field[@name='partner_id']" position="after">
        <field name="x_cost_centre_id"/>
      </xpath>
    </field>
  </record>
</odoo>""")

print("c6 rewritten")

# ── MINIMAL C1 ────────────────────────────────────────────────────────────────
os.makedirs(f'{base}/c1_purchase_approval_matrix/models', exist_ok=True)
os.makedirs(f'{base}/c1_purchase_approval_matrix/wizard', exist_ok=True)
os.makedirs(f'{base}/c1_purchase_approval_matrix/views', exist_ok=True)
os.makedirs(f'{base}/c1_purchase_approval_matrix/security', exist_ok=True)
os.makedirs(f'{base}/c1_purchase_approval_matrix/data', exist_ok=True)

open(f'{base}/c1_purchase_approval_matrix/__manifest__.py', 'w').write("""{
    'name': 'PO Approval Matrix',
    'version': '17.0.1.0.0',
    'category': 'Purchase',
    'depends': ['purchase', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_matrix_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}""")

open(f'{base}/c1_purchase_approval_matrix/__init__.py', 'w').write("from . import models\nfrom . import wizard\n")
open(f'{base}/c1_purchase_approval_matrix/models/__init__.py', 'w').write("from . import approval_matrix\nfrom . import purchase_order\n")
open(f'{base}/c1_purchase_approval_matrix/wizard/__init__.py', 'w').write("from . import rejection_wizard\n")

open(f'{base}/c1_purchase_approval_matrix/models/approval_matrix.py', 'w').write("""from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseApprovalThreshold(models.Model):
    _name = 'purchase.approval.threshold'
    _description = 'Purchase Approval Threshold'
    _order = 'tier asc'

    name = fields.Char(string='Name', required=True)
    tier = fields.Selection([
        ('1', 'Tier 1'),
        ('2', 'Tier 2'),
        ('3', 'Tier 3'),
    ], string='Tier', required=True)
    min_amount = fields.Monetary(string='Min Amount', currency_field='currency_id', required=True)
    max_amount = fields.Monetary(string='Max Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    approver_ids = fields.Many2many('res.users', string='Approvers', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_approvers_for_amount(self, amount, company_id=None):
        domain = [('min_amount', '<=', amount), ('active', '=', True)]
        if company_id:
            domain.append(('company_id', '=', company_id))
        thresholds = self.search(domain, order='tier asc')
        return thresholds.filtered(lambda t: not t.max_amount or t.max_amount >= amount)


class PurchaseApprovalLog(models.Model):
    _name = 'purchase.approval.log'
    _description = 'Purchase Approval Log'
    _order = 'create_date desc'

    purchase_id = fields.Many2one('purchase.order', required=True, ondelete='cascade', index=True)
    tier = fields.Char(string='Tier')
    action = fields.Selection([
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reset', 'Reset'),
    ], required=True)
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user)
    comment = fields.Text(string='Comment')
""")

open(f'{base}/c1_purchase_approval_matrix/models/purchase_order.py', 'w').write("""from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_t1', 'Pending T1'),
        ('pending_t2', 'Pending T2'),
        ('pending_t3', 'Pending T3'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', copy=False, tracking=True)

    current_approver_ids = fields.Many2many(
        'res.users', 'po_current_approver_rel', 'order_id', 'user_id',
        string='Pending Approvers', copy=False)
    approval_log_ids = fields.One2many('purchase.approval.log', 'purchase_id', readonly=True)
    rejection_comment = fields.Text(copy=False, tracking=True)
    requires_approval = fields.Boolean(compute='_compute_requires_approval', store=True)

    @api.depends('amount_total', 'company_id')
    def _compute_requires_approval(self):
        Threshold = self.env['purchase.approval.threshold']
        for po in self:
            po.requires_approval = bool(
                Threshold.get_approvers_for_amount(po.amount_total, po.company_id.id))

    def button_confirm(self):
        for po in self:
            if po.state not in ('draft', 'sent'):
                continue
            if po.requires_approval and po.approval_state not in ('approved',):
                po._submit_for_approval()
                return
        return super().button_confirm()

    def _submit_for_approval(self):
        self.ensure_one()
        Threshold = self.env['purchase.approval.threshold']
        thresholds = Threshold.get_approvers_for_amount(
            self.amount_total, self.company_id.id).sorted('tier')
        if not thresholds:
            return super().button_confirm()
        first = thresholds[0]
        self.write({
            'approval_state': 'pending_t%s' % first.tier,
            'current_approver_ids': [(6, 0, first.approver_ids.ids)],
        })
        self._log_approval('submitted', first.tier)

    def action_approve(self):
        self.ensure_one()
        if self.env.user not in self.current_approver_ids:
            raise UserError(_('Not authorised to approve.'))
        current_tier = self.approval_state.replace('pending_t', '')
        Threshold = self.env['purchase.approval.threshold']
        all_t = Threshold.get_approvers_for_amount(
            self.amount_total, self.company_id.id).sorted('tier')
        next_t = all_t.filtered(lambda t: int(t.tier) > int(current_tier))
        self._log_approval('approved', current_tier)
        if next_t:
            nxt = next_t[0]
            self.write({
                'approval_state': 'pending_t%s' % nxt.tier,
                'current_approver_ids': [(6, 0, nxt.approver_ids.ids)],
            })
        else:
            self.write({'approval_state': 'approved', 'current_approver_ids': [(5,)]})
            super(PurchaseOrder, self).button_confirm()

    def action_reject(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Purchase Order'),
            'res_model': 'purchase.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_purchase_id': self.id},
        }

    def action_reset_to_draft(self):
        self._log_approval('reset', '')
        self.write({'approval_state': 'draft', 'current_approver_ids': [(5,)]})

    def _log_approval(self, action, tier):
        self.env['purchase.approval.log'].create({
            'purchase_id': self.id,
            'tier': str(tier),
            'action': action,
            'user_id': self.env.user.id,
        })
""")

open(f'{base}/c1_purchase_approval_matrix/wizard/rejection_wizard.py', 'w').write("""from odoo import models, fields, _
from odoo.exceptions import UserError

class PurchaseRejectionWizard(models.TransientModel):
    _name = 'purchase.rejection.wizard'
    _description = 'Purchase Order Rejection'

    purchase_id = fields.Many2one('purchase.order', required=True, readonly=True)
    rejection_comment = fields.Text(required=True)

    def action_confirm_rejection(self):
        self.ensure_one()
        po = self.purchase_id
        if self.env.user not in po.current_approver_ids:
            raise UserError(_('Not authorised to reject.'))
        tier = po.approval_state.replace('pending_t', '')
        po._log_approval('rejected', tier)
        po.write({
            'approval_state': 'rejected',
            'current_approver_ids': [(5,)],
            'rejection_comment': self.rejection_comment,
        })
        return {'type': 'ir.actions.act_window_close'}
""")

open(f'{base}/c1_purchase_approval_matrix/security/ir.model.access.csv', 'w').write(
    "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"
    "access_purchase_approval_threshold,purchase.approval.threshold,model_purchase_approval_threshold,purchase.group_purchase_manager,1,1,1,1\n"
    "access_purchase_approval_threshold_user,purchase.approval.threshold.user,model_purchase_approval_threshold,,1,0,0,0\n"
    "access_purchase_approval_log,purchase.approval.log,model_purchase_approval_log,base.group_user,1,0,1,0\n"
    "access_purchase_rejection_wizard,purchase.rejection.wizard,model_purchase_rejection_wizard,base.group_user,1,1,1,1\n"
)

open(f'{base}/c1_purchase_approval_matrix/views/approval_matrix_views.xml', 'w').write("""<?xml version="1.0" encoding="utf-8"?>
<odoo>
  <record id="view_approval_threshold_tree" model="ir.ui.view">
    <field name="name">purchase.approval.threshold.tree</field>
    <field name="model">purchase.approval.threshold</field>
    <field name="arch" type="xml">
      <tree string="Approval Thresholds" editable="bottom">
        <field name="name"/>
        <field name="tier"/>
        <field name="min_amount"/>
        <field name="max_amount"/>
        <field name="approver_ids" widget="many2many_tags"/>
        <field name="active"/>
      </tree>
    </field>
  </record>
  <record id="action_approval_threshold" model="ir.actions.act_window">
    <field name="name">Approval Thresholds</field>
    <field name="res_model">purchase.approval.threshold</field>
    <field name="view_mode">tree,form</field>
  </record>
</odoo>""")

open(f'{base}/c1_purchase_approval_matrix/views/purchase_order_views.xml', 'w').write("""<?xml version="1.0" encoding="utf-8"?>
<odoo>
  <record id="view_purchase_order_form_approval" model="ir.ui.view">
    <field name="name">purchase.order.form.approval</field>
    <field name="model">purchase.order</field>
    <field name="inherit_id" ref="purchase.purchase_order_form"/>
    <field name="arch" type="xml">
      <xpath expr="//header/button[@name='button_confirm']" position="after">
        <button name="action_approve" string="Approve" type="object" class="btn-success"
                invisible="approval_state not in ('pending_t1','pending_t2','pending_t3')"/>
        <button name="action_reject" string="Reject" type="object" class="btn-danger"
                invisible="approval_state not in ('pending_t1','pending_t2','pending_t3')"/>
        <button name="action_reset_to_draft" string="Reset to Draft" type="object"
                invisible="approval_state != 'rejected'"/>
      </xpath>
      <xpath expr="//notebook" position="inside">
        <page string="Approval Log" invisible="not requires_approval">
          <field name="approval_log_ids" readonly="1">
            <tree create="false" delete="false" edit="false">
              <field name="create_date"/>
              <field name="tier"/>
              <field name="action"/>
              <field name="user_id"/>
              <field name="comment"/>
            </tree>
          </field>
        </page>
      </xpath>
    </field>
  </record>

  <record id="view_rejection_wizard_form" model="ir.ui.view">
    <field name="name">purchase.rejection.wizard.form</field>
    <field name="model">purchase.rejection.wizard</field>
    <field name="arch" type="xml">
      <form string="Reject Purchase Order">
        <group>
          <field name="purchase_id" readonly="1"/>
          <field name="rejection_comment"/>
        </group>
        <footer>
          <button name="action_confirm_rejection" string="Confirm Rejection"
                  type="object" class="btn-danger"/>
          <button string="Cancel" special="cancel"/>
        </footer>
      </form>
    </field>
  </record>
</odoo>""")

print("c1 rewritten")
print("Both modules ready. Now run force_install.py")
