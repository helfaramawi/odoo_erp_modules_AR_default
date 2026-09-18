# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # ── إصابة العمل — إجراء رقم 7 من الـ FRD ──────────────────────────────
    is_work_injury = fields.Boolean(string='إجازة إصابة عمل', compute='_compute_is_work_injury', store=True)
    injury_date = fields.Date(string='تاريخ الإصابة')
    injury_type = fields.Char(string='نوع الإصابة')
    medical_committee_ref = fields.Char(string='رقم محضر القومسيون الطبي')

    # ── تأكيد قسم الإجازات — الخطوة الثالثة بعد اعتماد المدير ────────────
    leave_dept_confirmed = fields.Boolean(string='مؤكَّدة من قسم الإجازات', copy=False, tracking=True)
    leave_dept_confirmed_by = fields.Many2one('res.users', string='أكَّدها', readonly=True, copy=False)
    leave_dept_confirmed_date = fields.Datetime(string='تاريخ التأكيد', readonly=True, copy=False)

    @api.depends('holiday_status_id')
    def _compute_is_work_injury(self):
        work_injury_type = self.env.ref('demo_gov_hr_leave.hr_leave_type_work_injury', raise_if_not_found=False)
        for rec in self:
            rec.is_work_injury = bool(work_injury_type) and rec.holiday_status_id.id == work_injury_type.id

    def action_confirm_by_leave_dept(self):
        for rec in self:
            if rec.state != 'validate':
                raise UserError(_('لازم الإجازة تكون معتمدة من المدير أولاً قبل تأكيد قسم الإجازات.'))
            rec.write({
                'leave_dept_confirmed': True,
                'leave_dept_confirmed_by': self.env.uid,
                'leave_dept_confirmed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('✅ تم التحقق النهائي وتسجيل الإجازة بواسطة قسم الإجازات — %s') % self.env.user.name)
