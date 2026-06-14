# -*- coding: utf-8 -*-
"""
مولّد بيانات الاختبار الحكومي العربي
يولّد بيانات اختبار واقعية لبيئة UAT محافظة بورسعيد
"""
import logging
from datetime import date, timedelta
from odoo import models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

UAT_BATCH = 'UAT-AR-GOV-2026'
TODAY = date.today()
FY_START = date(TODAY.year, 1, 1)
FY_END = date(TODAY.year, 12, 31)

DEPARTMENTS = [
    'ديوان عام المحافظة',
    'مديرية الشؤون المالية',
    'إدارة المشتريات',
    'إدارة المخازن',
    'إدارة الموارد البشرية',
    'إدارة المشروعات',
    'مركز معلومات المحافظة',
    'إدارة الطرق',
    'إدارة النظافة',
    'إدارة الصيانة',
    'إدارة الشؤون القانونية',
    'إدارة التخطيط والمتابعة',
    'إدارة الحسابات',
    'إدارة الموازنة',
]

VENDORS = [
    'شركة النظم المتكاملة للتوريدات',
    'شركة القناة للمقاولات والصيانة',
    'مؤسسة الدلتا للأجهزة والمعدات',
    'شركة الجمهورية لتوريد المستلزمات',
    'شركة بورسعيد للخدمات العامة',
    'شركة الأمل للصيانة والتشغيل',
]

PURCHASE_DESCRIPTIONS = [
    'توريد أجهزة حاسب آلي لمركز معلومات المحافظة',
    'صيانة عاجلة لشبكة الكهرباء بمبنى الديوان العام',
    'شراء مستلزمات نظافة للأحياء',
    'أعمال رصف وصيانة طريق رئيسي',
    'توريد قطع غيار لمعدات النظافة',
    'صيانة أجهزة التكييف بمبنى خدمة المواطنين',
    'تطوير منظومة الأرشفة الإلكترونية',
    'توريد أثاث مكتبي للإدارات الجديدة',
    'إعداد مبنى الخدمات الإلكترونية الجديد',
    'توريد معدات شبكة الاتصالات للمديريات',
    'صيانة وتأهيل مبنى الشؤون المالية',
    'توريد سيارات خدمة لإدارة النظافة',
]


class UATDataGenerator(models.AbstractModel):
    _name = 'arabic.government.uat.generator'
    _description = 'مولّد بيانات الاختبار الحكومي'

    # ------------------------------------------------------------------ #
    #  PUBLIC ENTRY POINT                                                  #
    # ------------------------------------------------------------------ #
    @api.model
    def generate_all(self, options, log_record):
        """
        نقطة الدخول الرئيسية. تستقبل قاموس خيارات وسجل جلسة التوليد.
        """
        results = []
        total = 0

        def run(label, fn):
            nonlocal total
            try:
                with self.env.cr.savepoint():
                    count = fn()
                results.append((label, count, 'ok', ''))
                total += count
            except Exception as exc:
                _logger.exception('UAT generator error in %s', label)
                results.append((label, 0, 'error', str(exc)[:200]))

        if options.get('generate_budget_cases'):
            run('الموازنة', self._generate_budget)
        if options.get('generate_commitment_cases'):
            run('الارتباطات', self._generate_commitments)
        if options.get('generate_procurement_cases'):
            run('المشتريات', self._generate_procurement)
        if options.get('generate_dossier_cases'):
            run('الاضبارة', self._generate_dossiers)
        if options.get('generate_disbursement_cases'):
            run('الصرف', self._generate_disbursements)
        if options.get('generate_accounting_cases'):
            run('المحاسبة', self._generate_accounting)
        if options.get('generate_project_cases'):
            run('المشروعات', self._generate_projects)
        if options.get('generate_inventory_cases'):
            run('المخازن', self._generate_inventory)
        if options.get('generate_hr_cases'):
            run('الموارد البشرية', self._generate_hr)
        if options.get('generate_ai_agent_cases'):
            run('سيناريوهات الذكاء الاصطناعي', self._generate_ai_scenarios)
        if options.get('generate_report_cases'):
            run('سيناريوهات التقارير', self._generate_report_scenarios)

        # Always generate UAT scenario records
        scenario_count = self._generate_uat_scenarios()
        results.append(('سيناريوهات الاختبار', scenario_count, 'ok', ''))
        total += scenario_count

        # Write log lines
        seq = 10
        for label, count, status, msg in results:
            self.env['arabic.government.uat.generation.log.line'].create({
                'log_id': log_record.id,
                'sequence': seq,
                'category': label,
                'description': f'توليد بيانات: {label}',
                'record_count': count,
                'status': status,
                'message': msg,
            })
            seq += 10

        summary_lines = [f'• {r[0]}: {r[1]} سجل ({r[2]})' for r in results]
        summary = f'إجمالي السجلات المنشأة: {total}\n' + '\n'.join(summary_lines)
        log_record.write({'result_summary': summary, 'total_created': total, 'state': 'done'})
        return total

    # ------------------------------------------------------------------ #
    #  HELPERS                                                              #
    # ------------------------------------------------------------------ #
    def _get_company(self):
        return self.env.company

    def _get_or_create_vendor(self, name):
        partner = self.env['res.partner'].search([('name', '=', name), ('supplier_rank', '>', 0)], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': name,
                'supplier_rank': 1,
                'company_type': 'company',
                'country_id': self.env.ref('base.eg').id,
                'comment': UAT_BATCH,
            })
        return partner

    def _get_or_create_product(self, name, uom_name='Units'):
        product = self.env['product.product'].search([('name', '=', name)], limit=1)
        if not product:
            uom = self.env['uom.uom'].search([('name', 'ilike', uom_name)], limit=1)
            if not uom:
                uom = self.env['uom.uom'].search([], limit=1)
            product = self.env['product.product'].create({
                'name': name,
                'type': 'product',
                'uom_id': uom.id,
                'uom_po_id': uom.id,
                'description': f'{UAT_BATCH} - {name}',
            })
        return product

    def _already_exists(self, model, domain):
        return bool(self.env[model].search(domain, limit=1))

    def _uat_domain(self, field='name'):
        return [(field, 'ilike', UAT_BATCH)]

    def _get_account(self, account_type='expense'):
        """Get any available account of given type."""
        account = self.env['account.account'].search(
            [('account_type', '=', account_type), ('company_id', '=', self._get_company().id)],
            limit=1
        )
        if not account:
            account = self.env['account.account'].search(
                [('company_id', '=', self._get_company().id)], limit=1
            )
        return account

    def _get_journal(self, jtype='purchase'):
        return self.env['account.journal'].search(
            [('type', '=', jtype), ('company_id', '=', self._get_company().id)], limit=1
        )

    # ------------------------------------------------------------------ #
    #  BUDGET GENERATION                                                   #
    # ------------------------------------------------------------------ #
    def _generate_budget(self):
        count = 0
        Budget = self.env['port_said.budget.plan']
        BudgetLine = self.env['port_said.budget.line']

        budget_scenarios = [
            {
                'name': f'{UAT_BATCH} - موازنة ديوان عام المحافظة {TODAY.year}',
                'department': 'ديوان عام المحافظة',
                'state': 'active',
                'lines': [
                    ('بند المرتبات والأجور', 5_000_000, 4_200_000),
                    ('بند المستلزمات السلعية', 2_000_000, 1_800_000),
                    ('بند الخدمات العامة', 1_500_000, 1_400_000),
                    ('بند المشروعات الرأسمالية', 10_000_000, 8_500_000),
                ],
            },
            {
                'name': f'{UAT_BATCH} - موازنة إدارة الطرق {TODAY.year}',
                'department': 'إدارة الطرق',
                'state': 'active',
                'lines': [
                    ('أعمال الرصف والصيانة', 8_000_000, 7_800_000),
                    ('مستلزمات الإنشاء', 3_000_000, 2_950_000),
                    ('معدات وآليات', 5_000_000, 4_200_000),
                ],
            },
            {
                'name': f'{UAT_BATCH} - موازنة إدارة النظافة {TODAY.year}',
                'department': 'إدارة النظافة',
                'state': 'active',
                'lines': [
                    ('مستلزمات النظافة', 1_200_000, 900_000),
                    ('قطع غيار معدات النظافة', 800_000, 600_000),
                    ('مصروفات التشغيل', 600_000, 400_000),
                ],
            },
            {
                'name': f'{UAT_BATCH} - موازنة مركز المعلومات (تكنولوجيا) {TODAY.year}',
                'department': 'مركز معلومات المحافظة',
                'state': 'approved',
                'lines': [
                    ('أجهزة حاسب آلي وبنية تحتية', 3_000_000, 0),
                    ('برمجيات وتراخيص', 500_000, 0),
                    ('صيانة الشبكات والأنظمة', 700_000, 0),
                ],
            },
            {
                'name': f'{UAT_BATCH} - موازنة إدارة الصيانة {TODAY.year}',
                'department': 'إدارة الصيانة',
                'state': 'draft',
                'lines': [
                    ('أعمال الصيانة الدورية', 2_000_000, 0),
                    ('قطع غيار وتوريدات', 1_000_000, 0),
                ],
            },
            {
                'name': f'{UAT_BATCH} - موازنة مديرية الشؤون المالية {TODAY.year}',
                'department': 'مديرية الشؤون المالية',
                'state': 'submitted',
                'lines': [
                    ('مصروفات تشغيلية', 900_000, 0),
                    ('مستلزمات مكتبية', 300_000, 0),
                ],
            },
        ]

        account = self._get_account('expense')

        for scenario in budget_scenarios:
            existing = Budget.search([('name', '=', scenario['name'])], limit=1)
            if existing:
                continue

            vals = {
                'name': scenario['name'],
                'fiscal_year': str(TODAY.year),
                'date_from': FY_START,
                'date_to': FY_END,
                'state': 'draft',
                'notes': f'بيانات اختبار القبول - {UAT_BATCH}',
            }
            # Add department field if the model supports it
            try:
                Budget._fields['department_id']
                dept = self.env['hr.department'].search([('name', 'ilike', scenario['department'])], limit=1)
                if dept:
                    vals['department_id'] = dept.id
            except KeyError:
                pass

            budget = Budget.create(vals)

            for line_name, allocated, consumed in scenario.get('lines', []):
                line_vals = {
                    'budget_id': budget.id,
                    'name': line_name,
                    'planned_amount': allocated,
                }
                if 'account_id' in BudgetLine._fields and account:
                    line_vals['account_id'] = account.id
                try:
                    BudgetLine.create(line_vals)
                except Exception:
                    pass

            # Move to target state
            target_state = scenario['state']
            try:
                if target_state in ('submitted', 'approved', 'active', 'closed'):
                    budget.action_submit()
                if target_state in ('approved', 'active', 'closed'):
                    budget.action_approve()
                if target_state == 'active':
                    if hasattr(budget, 'action_activate'):
                        budget.action_activate()
            except Exception:
                budget.write({'state': target_state})

            count += 1

        return count

    # ------------------------------------------------------------------ #
    #  COMMITMENTS GENERATION                                              #
    # ------------------------------------------------------------------ #
    def _generate_commitments(self):
        count = 0
        Commitment = self.env['port_said.commitment']

        scenarios = [
            ('approved',   'ارتباط معتمد - توريد حاسب آلي',         45_000),
            ('approved',   'ارتباط معتمد - صيانة مبنى الديوان',      120_000),
            ('draft',      'ارتباط مسودة - مستلزمات نظافة',          18_000),
            ('submitted',  'ارتباط مقدم - أعمال رصف الطريق',         350_000),
            ('cancelled',  'ارتباط ملغي - معدات متنازل عنها',         75_000),
            ('paid',       'ارتباط مدفوع - توريد أثاث مكتبي',         55_000),
            ('reserved',   'ارتباط محجوز - تطوير منظومة أرشفة',      280_000),
            ('cleared',    'ارتباط منتهي - صيانة تكييف',              40_000),
        ]

        dept = self.env['res.partner'].search([('supplier_rank', '>', 0)], limit=1)
        for state, desc, amount in scenarios:
            if self._already_exists('port_said.commitment', [('description', 'ilike', desc[:30])]):
                continue

            vals = {
                'description': f'{UAT_BATCH} - {desc}',
                'amount_requested': amount,
                'fiscal_year': TODAY.year,
                'budget_line_code': f'UAT-{count+1:03d}',
                'date_requested': TODAY - timedelta(days=30),
            }
            if dept and 'department_id' in Commitment._fields:
                vals['department_id'] = dept.id

            # Attach vendor if field exists
            vendor_name = VENDORS[count % len(VENDORS)]
            vendor = self._get_or_create_vendor(vendor_name)
            if 'partner_id' in Commitment._fields:
                vals['partner_id'] = vendor.id

            commitment = Commitment.create(vals)
            try:
                if state in ('submitted', 'approved', 'reserved', 'cleared', 'paid', 'cancelled'):
                    commitment.action_submit()
                if state in ('approved', 'reserved', 'cleared', 'paid'):
                    commitment.action_approve()
                if state == 'reserved' and hasattr(commitment, 'action_reserve'):
                    commitment.action_reserve()
                if state == 'cleared' and hasattr(commitment, 'action_clear'):
                    commitment.action_clear()
                if state == 'paid' and hasattr(commitment, 'action_pay'):
                    commitment.action_pay()
                if state == 'cancelled':
                    commitment.action_cancel()
            except Exception:
                commitment.write({'state': state})

            count += 1

        return count

    # ------------------------------------------------------------------ #
    #  PROCUREMENT / REQUISITIONS                                          #
    # ------------------------------------------------------------------ #
    def _generate_procurement(self):
        count = 0
        Req = self.env['port_said.requisition']

        requisition_scenarios = [
            ('draft',      'طلب احتياج مسودة - أجهزة حاسب آلي',             35_000),
            ('submitted',  'طلب احتياج مقدم - مستلزمات نظافة الأحياء',       22_000),
            ('approved',   'طلب احتياج معتمد - توريد قطع غيار معدات',         48_000),
            ('approved',   'طلب احتياج معتمد - صيانة شبكة كهرباء (عاجل)',    95_000),
            ('po_created', 'طلب احتياج تحول لأمر شراء - أثاث مكتبي',         60_000),
            ('cancelled',  'طلب احتياج ملغي - تجهيزات صوتية',               15_000),
            ('submitted',  'طلب احتياج مقدم - تحت الحد 50 ألف - مياه',       8_000),
            ('approved',   'طلب احتياج فوق الحد 50 ألف - رصف طريق',         550_000),
            ('draft',      'طلب احتياج بدون بند موازنة - مستلزمات طارئة',    12_000),
        ]

        dept = self.env['res.partner'].search([('supplier_rank', '>', 0)], limit=1)
        for state, desc, amount in requisition_scenarios:
            if self._already_exists('port_said.requisition', [('description', 'ilike', desc[:30])]):
                continue

            vendor_name = VENDORS[count % len(VENDORS)]
            vendor = self._get_or_create_vendor(vendor_name)

            vals = {
                'description': f'{UAT_BATCH} - {desc}',
                'date_request': TODAY - timedelta(days=20),
                'budget_line': f'UAT-{count+1:03d}',
            }
            if dept and 'department_id' in Req._fields:
                vals['department_id'] = dept.id
            if 'partner_id' in Req._fields:
                vals['partner_id'] = vendor.id
            if 'amount_total' in Req._fields:
                vals['amount_total'] = amount

            req = Req.create(vals)

            # Add line item
            try:
                product = self._get_or_create_product(desc[:40])
                line_vals = {
                    'requisition_id': req.id,
                    'product_id': product.id,
                    'qty': 1,
                    'price_unit': amount,
                    'description': desc[:60],
                }
                if 'uom_id' in self.env['port_said.requisition.line']._fields:
                    line_vals['uom_id'] = product.uom_id.id
                self.env['port_said.requisition.line'].create(line_vals)
            except Exception:
                pass

            try:
                if state in ('submitted', 'approved', 'po_created', 'cancelled'):
                    req.action_submit()
                if state in ('approved', 'po_created'):
                    req.action_approve()
                if state == 'cancelled':
                    req.action_cancel()
            except Exception:
                req.write({'state': state})

            count += 1

        return count

    # ------------------------------------------------------------------ #
    #  DOSSIER / DAFTAR                                                    #
    # ------------------------------------------------------------------ #
    def _generate_dossiers(self):
        count = 0
        Dossier = self.env['port_said.dossier']

        dossier_scenarios = [
            ('open',   'اضبارة مكتملة - توريد أجهزة حاسب آلي',    True),
            ('open',   'اضبارة ناقصة فاتورة - صيانة مبنى',          False),
            ('open',   'اضبارة ناقصة عقد - توريد أثاث',            False),
            ('closed', 'اضبارة مغلقة ومعتمدة - رصف طريق',          True),
            ('open',   'اضبارة ناقصة محضر استلام - معدات نظافة',   False),
            ('open',   'اضبارة تجاوز CFO - مدفوعات طارئة',          True),
        ]

        for state, desc, complete in dossier_scenarios:
            vals = {
                'budget_line': f'UAT-DOS-{count+1:03d}',
                'fiscal_year': TODAY.year,
            }
            if 'state' in Dossier._fields:
                vals['state'] = state
            if 'is_complete' in Dossier._fields:
                vals['is_complete'] = complete
            if 'notes' in Dossier._fields:
                vals['notes'] = f'{UAT_BATCH} - {desc}'

            try:
                dossier = Dossier.create(vals)
                count += 1
            except Exception as e:
                _logger.warning('Dossier creation failed: %s', e)

        return count

    # ------------------------------------------------------------------ #
    #  DAFTAR 55 / DISBURSEMENTS                                           #
    # ------------------------------------------------------------------ #
    def _generate_disbursements(self):
        count = 0
        D55 = self.env['port_said.daftar55']

        disbursement_scenarios = [
            ('draft',    'دفتر 55 مسودة - مرتبات يناير',               120_000),
            ('received', 'دفتر 55 مستلم - مستلزمات سلعية',             45_000),
            ('reviewed', 'دفتر 55 قيد المراجعة - خدمات عامة',          78_000),
            ('cleared',  'دفتر 55 موافق عليه - أعمال صيانة',           200_000),
            ('posted',   'دفتر 55 مرحّل - توريد معدات',                350_000),
            ('archived', 'دفتر 55 مؤرشف - صرفيات قديمة',               55_000),
        ]

        journal = self._get_journal('purchase')
        vendor = self._get_or_create_vendor(VENDORS[0])

        for state, desc, amount in disbursement_scenarios:
            vals = {
                'department_name': f'إدارة الاختبار - {UAT_BATCH}',
                'date_received': TODAY - timedelta(days=10),
                'form50_ref': f'UAT-F50-{count+1:03d}',
                'vendor_id': vendor.id,
                'budget_line': f'UAT-D55-{count+1:03d}',
                'amount_gross': amount,
            }
            if 'notes' in D55._fields:
                vals['notes'] = f'{UAT_BATCH} - {desc}'
            if 'journal_id' in D55._fields and journal:
                vals['journal_id'] = journal.id

            try:
                d55 = D55.create(vals)
                try:
                    if state in ('received', 'reviewed', 'cleared', 'posted', 'archived'):
                        d55.action_receive()
                    if state in ('reviewed', 'cleared', 'posted', 'archived'):
                        d55.action_review()
                    if state in ('cleared', 'posted', 'archived'):
                        d55.action_clear()
                    if state in ('posted', 'archived'):
                        d55.action_post()
                    if state == 'archived' and hasattr(d55, 'action_archive_record'):
                        d55.action_archive_record()
                except Exception:
                    d55.write({'state': state})
                count += 1
            except Exception as e:
                _logger.warning('Daftar55 creation failed: %s', e)

        # Generate Daftar224
        D224 = self.env['port_said.daftar224']
        for i, desc_pair in enumerate([
            ('صرفيات', 'قيد صرفيات يومي - مشتريات'),
            ('تسويات', 'قيد تسويات - ضرائب'),
        ]):
            reg_type, desc = desc_pair
            try:
                vals = {
                    'entry_date': TODAY - timedelta(days=i + 1),
                    'notes': f'{UAT_BATCH} - دفتر 224 - {desc}',
                }
                if 'register_type' in D224._fields:
                    vals['register_type'] = 'sarfiyat' if 'صرفيات' in reg_type else 'taswiyat'
                D224.create(vals)
                count += 1
            except Exception as e:
                _logger.warning('Daftar224 creation failed: %s', e)

        return count

    # ------------------------------------------------------------------ #
    #  ACCOUNTING / FINANCE                                                #
    # ------------------------------------------------------------------ #
    def _generate_accounting(self):
        count = 0
        Move = self.env['account.move']

        journal = self._get_journal('purchase')
        expense_account = self._get_account('expense')
        payable_account = self._get_account('liability_payable')
        vendor = self._get_or_create_vendor(VENDORS[1])

        bill_scenarios = [
            (f'{UAT_BATCH} - فاتورة مورد - توريد حاسب آلي',   45_000, 'draft'),
            (f'{UAT_BATCH} - فاتورة مورد - أعمال صيانة طريق', 185_000, 'posted'),
            (f'{UAT_BATCH} - فاتورة مورد - مستلزمات نظافة',    22_000, 'draft'),
            (f'{UAT_BATCH} - فاتورة مورد - توريد أثاث مكتبي', 60_000, 'posted'),
        ]

        for ref, amount, state in bill_scenarios:
            if self._already_exists('account.move', [('ref', '=', ref), ('move_type', '=', 'in_invoice')]):
                continue
            try:
                move_vals = {
                    'move_type': 'in_invoice',
                    'ref': ref,
                    'partner_id': vendor.id,
                    'invoice_date': TODAY - timedelta(days=15),
                    'journal_id': journal.id if journal else False,
                    'invoice_line_ids': [(0, 0, {
                        'name': ref,
                        'quantity': 1,
                        'price_unit': amount,
                        'account_id': expense_account.id if expense_account else False,
                    })],
                }
                move = Move.create(move_vals)
                if state == 'posted':
                    move.action_post()
                count += 1
            except Exception as e:
                _logger.warning('Account move creation failed: %s', e)

        # Payment orders
        PayOrder = self.env['port_said.payment_order']
        po_scenarios = [
            ('draft',     'أمر دفع مسودة - دفع مرتبات',    50_000),
            ('received',  'أمر دفع مستلم - دفع موردين',     75_000),
            ('registered','أمر دفع مسجل - سداد فاتورة صيانة', 185_000),
            ('cleared',   'أمر دفع موافق عليه',             120_000),
            ('posted',    'أمر دفع مرحّل',                  200_000),
            ('cancelled', 'أمر دفع ملغي',                   30_000),
        ]
        for state, desc, amount in po_scenarios:
            if self._already_exists('port_said.payment_order', [('purpose', 'ilike', desc[:20])]):
                continue
            try:
                vals = {
                    'po_reference': f'UAT-PO-{count+1:03d}',
                    'issuing_entity_name': f'إدارة الاختبار - {UAT_BATCH}',
                    'amount': amount,
                    'issue_date': TODAY - timedelta(days=15),
                    'purpose': f'{UAT_BATCH} - {desc}',
                }
                if 'partner_id' in PayOrder._fields:
                    vals['partner_id'] = vendor.id
                po = PayOrder.create(vals)
                try:
                    if state in ('received', 'registered', 'cleared', 'posted', 'cancelled'):
                        po.action_receive()
                    if state in ('registered', 'cleared', 'posted'):
                        po.action_register()
                    if state in ('cleared', 'posted'):
                        po.action_clear()
                    if state == 'posted':
                        po.action_post()
                    if state == 'cancelled':
                        po.action_cancel()
                except Exception:
                    po.write({'state': state})
                count += 1
            except Exception as e:
                _logger.warning('Payment order creation failed: %s', e)

        return count

    # ------------------------------------------------------------------ #
    #  PROJECTS                                                            #
    # ------------------------------------------------------------------ #
    def _generate_projects(self):
        count = 0
        Project = self.env['project.project']

        project_scenarios = [
            ('مشروع تطوير البنية التحتية للطرق الرئيسية',     8_000_000, '75'),
            ('مشروع التحول الرقمي لمركز معلومات المحافظة',    3_000_000, '40'),
            ('مشروع إعادة تأهيل مبنى الخدمات الإلكترونية',   5_000_000, '90'),
            ('مشروع تطوير منظومة إدارة النفايات الصلبة',     12_000_000, '20'),
            ('مشروع صيانة وتأهيل شبكة الصرف الصحي',          6_500_000, '60'),
        ]

        for proj_name, budget, progress in project_scenarios:
            full_name = f'{UAT_BATCH} - {proj_name}'
            if self._already_exists('project.project', [('name', '=', full_name)]):
                continue
            try:
                vals = {
                    'name': full_name,
                    'description': f'بيانات اختبار القبول - {UAT_BATCH}\n{proj_name}',
                }
                if 'budget_amount' in Project._fields:
                    vals['budget_amount'] = budget
                if 'allocated_hours' in Project._fields:
                    vals['allocated_hours'] = budget / 1000
                Project.create(vals)
                count += 1
            except Exception as e:
                _logger.warning('Project creation failed: %s', e)

        return count

    # ------------------------------------------------------------------ #
    #  INVENTORY                                                           #
    # ------------------------------------------------------------------ #
    def _generate_inventory(self):
        count = 0
        # Generate inspection committees and warehouse additions
        Committee = self.env.get('port_said.inspection_committee')
        if Committee:
            for i, desc in enumerate([
                'لجنة فحص واستلام أجهزة الحاسب الآلي',
                'لجنة فحص واستلام معدات النظافة',
                'لجنة فحص واستلام قطع الغيار',
            ]):
                name = f'{UAT_BATCH} - {desc}'
                if not self._already_exists('port_said.inspection_committee', [('name', '=', name)]):
                    try:
                        Committee.create({'name': name, 'notes': f'{UAT_BATCH}'})
                        count += 1
                    except Exception as e:
                        _logger.warning('Committee creation failed: %s', e)

        Addition = self.env.get('port_said.warehouse_addition')
        if Addition:
            for desc in [
                'إضافة مخزن - حاسبات مركز المعلومات',
                'إضافة مخزن - مستلزمات النظافة',
            ]:
                name = f'{UAT_BATCH} - {desc}'
                if not self._already_exists('port_said.warehouse_addition', [('name', '=', name)]):
                    try:
                        Addition.create({'name': name, 'notes': f'{UAT_BATCH}'})
                        count += 1
                    except Exception as e:
                        _logger.warning('Warehouse addition creation failed: %s', e)

        return count

    # ------------------------------------------------------------------ #
    #  HR                                                                  #
    # ------------------------------------------------------------------ #
    def _generate_hr(self):
        count = 0
        Advance = self.env['port_said.advance']

        advance_scenarios = [
            ('draft',      'سلفة مسودة - موظف جديد',                  5_000),
            ('submitted',  'سلفة مقدمة - موظف في إجازة مرضية',        8_000),
            ('approved',   'سلفة معتمدة - موظف رحلة عمل',             12_000),
            ('disbursed',  'سلفة صُرفت - موظف سفر خارجي',             15_000),
            ('settled',    'سلفة تمت تسويتها - موظف سبق صرفه سلفة',   10_000),
            ('cancelled',  'سلفة ملغاة - طلب لم يستوفِ الشروط',        6_000),
        ]

        for state, desc, amount in advance_scenarios:
            name = f'{UAT_BATCH} - {desc}'
            if self._already_exists('port_said.advance', [('name', '=', name)]):
                continue
            try:
                employee = self.env['hr.employee'].search([], limit=1)
                vals = {
                    'name': name,
                    'amount': amount,
                    'notes': f'بيانات اختبار القبول - {UAT_BATCH}',
                }
                if 'employee_id' in Advance._fields and employee:
                    vals['employee_id'] = employee.id
                adv = Advance.create(vals)
                try:
                    if state in ('submitted', 'approved', 'disbursed', 'settled', 'cancelled'):
                        adv.action_submit()
                    if state in ('approved', 'disbursed', 'settled'):
                        adv.action_approve()
                    if state in ('disbursed', 'settled') and hasattr(adv, 'action_disburse'):
                        adv.action_disburse()
                    if state == 'settled' and hasattr(adv, 'action_settle'):
                        adv.action_settle()
                    if state == 'cancelled':
                        adv.action_cancel()
                except Exception:
                    adv.write({'state': state})
                count += 1
            except Exception as e:
                _logger.warning('Advance creation failed: %s', e)

        # Bank guarantees
        Guarantee = self.env['port_said.bank.guarantee']
        guarantee_scenarios = [
            ('draft',     'ضمان بنكي مسودة - عطاء توريد معدات',    500_000, 90),
            ('active',    'ضمان بنكي نشط - عقد صيانة طريق',      1_000_000, 365),
            ('extended',  'ضمان بنكي ممتد - مشروع إنشاء',         2_000_000, 180),
            ('released',  'ضمان بنكي محرر - عقد منتهي',             300_000,  0),
            ('forfeited', 'ضمان بنكي مصادر - عقد مخالف',           750_000,  0),
        ]
        for state, desc, amount, days in guarantee_scenarios:
            name = f'{UAT_BATCH} - {desc}'
            if self._already_exists('port_said.bank.guarantee', [('name', '=', name)]):
                continue
            try:
                vals = {
                    'name': name,
                    'amount': amount,
                    'notes': f'بيانات اختبار القبول - {UAT_BATCH}',
                }
                if 'expiry_date' in Guarantee._fields and days:
                    vals['expiry_date'] = TODAY + timedelta(days=days)
                guar = Guarantee.create(vals)
                try:
                    if state in ('active', 'extended', 'released', 'forfeited'):
                        guar.action_activate()
                    if state in ('extended',) and hasattr(guar, 'action_extend'):
                        guar.action_extend()
                    if state == 'released' and hasattr(guar, 'action_release'):
                        guar.action_release()
                    if state == 'forfeited' and hasattr(guar, 'action_forfeit'):
                        guar.action_forfeit()
                except Exception:
                    guar.write({'state': state})
                count += 1
            except Exception as e:
                _logger.warning('Bank guarantee creation failed: %s', e)

        return count

    # ------------------------------------------------------------------ #
    #  AI AGENT SCENARIOS                                                  #
    # ------------------------------------------------------------------ #
    def _generate_ai_scenarios(self):
        """Record AI scenarios as UAT scenario entries — no separate AI model exists."""
        return 0  # handled in _generate_uat_scenarios below

    # ------------------------------------------------------------------ #
    #  REPORT SCENARIOS                                                    #
    # ------------------------------------------------------------------ #
    def _generate_report_scenarios(self):
        return 0  # handled in _generate_uat_scenarios below

    # ------------------------------------------------------------------ #
    #  UAT SCENARIO RECORDS                                                #
    # ------------------------------------------------------------------ #
    def _generate_uat_scenarios(self):
        count = 0
        Scenario = self.env['arabic.government.uat.scenario']
        if Scenario.search([('batch_reference', '=', UAT_BATCH)], limit=1):
            return 0  # already generated

        scenarios = [
            # BUDGET
            ('BDG-001', 'اعتماد موازنة ديوان عام المحافظة', 'budget', 'الموازنة',
             'وجود موازنة تقديرية في مرحلة المسودة',
             '1. افتح وحدة الموازنة\n2. ابحث عن موازنة ديوان عام المحافظة\n3. اضغط "اعتماد"',
             'تنتقل الموازنة لحالة معتمدة وتظهر في لوحة القيادة',
             f'{UAT_BATCH} - موازنة ديوان عام المحافظة',
             'مدير مالي', 'pending'),
            ('BDG-002', 'تنبيه تجاوز الموازنة', 'budget', 'الموازنة',
             'وجود ارتباط يتجاوز الرصيد المتاح',
             '1. حاول إنشاء ارتباط بمبلغ يتجاوز الرصيد المتاح\n2. لاحظ رسالة التحذير',
             'يظهر تحذير واضح بعدم كفاية الرصيد',
             f'{UAT_BATCH} - ارتباط يتجاوز الموازنة',
             'مسؤول موازنة', 'pending'),
            ('BDG-003', 'نسبة تنفيذ عالية (فوق 90%)', 'budget', 'الموازنة',
             'وجود موازنة منفذة بنسبة فوق 90%',
             '1. افتح لوحة قيادة الموازنة\n2. لاحظ الموازنات ذات التنفيذ العالي',
             'تظهر تنبيهات حمراء للموازنات فوق 90%',
             f'{UAT_BATCH} - موازنة إدارة الطرق',
             'مدير مالي', 'pending'),
            # COMMITMENT
            ('CMT-001', 'إنشاء ارتباط يدوي واعتماده', 'commitment', 'الارتباطات',
             'وجود موازنة معتمدة برصيد كافٍ',
             '1. افتح وحدة الارتباطات\n2. أنشئ ارتباط جديد\n3. أدخل البيانات\n4. قدم للاعتماد',
             'يعتمد الارتباط ويخصم من رصيد الموازنة',
             f'{UAT_BATCH} - ارتباط معتمد - توريد حاسب آلي',
             'مسؤول موازنة', 'pending'),
            ('CMT-002', 'رفض ارتباط فوق الحد المسموح', 'commitment', 'الارتباطات',
             'وجود ارتباط يتطلب اعتماد مستوى أعلى',
             '1. أنشئ ارتباط بمبلغ فوق حد الصلاحية\n2. قدمه للاعتماد',
             'يُحال الارتباط للمستوى الأعلى أو يُرفض',
             f'{UAT_BATCH} - ارتباط مقدم - أعمال رصف الطريق',
             'مسؤول موازنة', 'pending'),
            ('CMT-003', 'إلغاء ارتباط وإعادة الرصيد', 'commitment', 'الارتباطات',
             'وجود ارتباط معتمد',
             '1. افتح الارتباط المعتمد\n2. اضغط "إلغاء"',
             'يُلغى الارتباط ويعود الرصيد للموازنة',
             f'{UAT_BATCH} - ارتباط ملغي - معدات متنازل عنها',
             'مدير مالي', 'pending'),
            # PROCUREMENT
            ('PRC-001', 'دورة طلب الاحتياج الكاملة', 'procurement', 'المشتريات',
             'وجود موازنة معتمدة وبيانات أساسية',
             '1. أنشئ طلب احتياج\n2. أضف البنود\n3. قدم للاعتماد\n4. راجع واعتمد',
             'يُعتمد الطلب وينشأ ارتباط تلقائياً',
             f'{UAT_BATCH} - طلب احتياج معتمد - توريد قطع غيار معدات',
             'مسؤول مشتريات', 'pending'),
            ('PRC-002', 'طلب احتياج عاجل فوق 50,000 جنيه', 'procurement', 'المشتريات',
             'وجود طلب احتياج عاجل بمبلغ كبير',
             '1. افتح الطلب العاجل\n2. لاحظ آلية الاعتماد المختلفة',
             'يتطلب الطلب اعتماد لجنة مشتريات',
             f'{UAT_BATCH} - طلب احتياج معتمد - صيانة شبكة كهرباء (عاجل)',
             'مسؤول مشتريات', 'pending'),
            ('PRC-003', 'رفض طلب احتياج', 'procurement', 'المشتريات',
             'وجود طلب احتياج في مرحلة المراجعة',
             '1. افتح الطلب المقدم\n2. اضغط "رفض" مع إدخال السبب',
             'يُرفض الطلب ويُخطر مقدم الطلب',
             f'{UAT_BATCH} - طلب احتياج ملغي - تجهيزات صوتية',
             'مدير مشتريات', 'pending'),
            # DOSSIER
            ('DOS-001', 'فحص اضبارة مكتملة', 'dossier', 'الاضبارة',
             'وجود اضبارة مكتملة المستندات',
             '1. افتح وحدة الاضبارة\n2. ابحث عن الاضبارة المكتملة\n3. افحص المستندات',
             'تظهر الاضبارة مكتملة وجاهزة للصرف',
             f'{UAT_BATCH} - اضبارة مكتملة - توريد أجهزة حاسب آلي',
             'مراجع', 'pending'),
            ('DOS-002', 'رفض صرف بسبب نقص مستندات', 'dossier', 'الاضبارة',
             'وجود اضبارة ناقصة المستندات',
             '1. افتح الاضبارة الناقصة\n2. حاول الإحالة للصرف',
             'يُرفض الصرف مع بيان المستند الناقص',
             f'{UAT_BATCH} - اضبارة ناقصة فاتورة - صيانة مبنى',
             'مسؤول صرف', 'pending'),
            ('DOS-003', 'تجاوز CFO لنقص مستندات', 'dossier', 'الاضبارة',
             'وجود اضبارة ناقصة وصلاحية CFO',
             '1. افتح الاضبارة الناقصة\n2. استخدم تجاوز CFO مع إدخال المبرر',
             'يُصرف المبلغ مع تسجيل التجاوز في السجل',
             f'{UAT_BATCH} - اضبارة تجاوز CFO - مدفوعات طارئة',
             'مدير مالي', 'pending'),
            # DISBURSEMENT
            ('DIS-001', 'دورة دفتر 55 الكاملة', 'disbursement', 'دفتر 55',
             'وجود أوامر صرف جاهزة',
             '1. أنشئ قيد دفتر 55\n2. راجع\n3. وافق\n4. رحّل',
             'يُرحّل القيد وينعكس على الحسابات',
             f'{UAT_BATCH} - دفتر 55 مرحّل - توريد معدات',
             'مسؤول صرف', 'pending'),
            ('DIS-002', 'صرف جزئي مرتبط بارتباط', 'disbursement', 'دفتر 55',
             'وجود ارتباط مستهلك جزئياً',
             '1. افتح دفتر الصرف المرتبط بارتباط\n2. لاحظ المبلغ المتبقي في الارتباط',
             'يظهر الارتباط مستهلكاً جزئياً والرصيد المتبقي',
             f'{UAT_BATCH} - دفتر 55 موافق عليه - أعمال صيانة',
             'مسؤول صرف', 'pending'),
            # ACCOUNTING
            ('ACC-001', 'ترحيل فاتورة مورد', 'accounting', 'المحاسبة',
             'وجود فاتورة مورد في مرحلة المسودة',
             '1. افتح وحدة الفواتير\n2. ابحث عن فاتورة UAT\n3. اضغط "ترحيل"',
             'تُرحّل الفاتورة وتظهر في ميزان المراجعة',
             f'{UAT_BATCH} - فاتورة مورد - توريد حاسب آلي',
             'محاسب', 'pending'),
            ('ACC-002', 'دفع فاتورة مورد ومطابقتها', 'accounting', 'المحاسبة',
             'وجود فاتورة مرحّلة',
             '1. افتح الفاتورة المرحّلة\n2. اضغط "تسجيل دفع"\n3. طابق الدفع',
             'تنتهي الفاتورة وتُسجّل حركة الدفع',
             f'{UAT_BATCH} - فاتورة مورد - أعمال صيانة طريق',
             'مسؤول مدفوعات', 'pending'),
            # PROJECTS
            ('PRJ-001', 'متابعة ميزانية مشروع', 'project', 'المشروعات',
             'وجود مشروع له ميزانية محددة',
             '1. افتح وحدة المشروعات\n2. ابحث عن مشروع UAT\n3. راجع التقرير المالي',
             'تظهر نسبة تنفيذ الميزانية والمبلغ المتبقي',
             f'{UAT_BATCH} - مشروع تطوير البنية التحتية للطرق الرئيسية',
             'مدير مشروع', 'pending'),
            # INVENTORY
            ('INV-001', 'استلام ومحضر فحص', 'inventory', 'المخازن',
             'وجود أمر شراء مكتمل ولجنة فحص',
             '1. افتح لجنة الفحص والاستلام\n2. أدخل نتائج الفحص\n3. اعتمد الاستلام',
             'يُثبّت المخزن ويُحدث رصيد المستودع',
             f'{UAT_BATCH} - لجنة فحص واستلام أجهزة الحاسب الآلي',
             'أمين مخزن', 'pending'),
            # HR
            ('HR-001', 'اعتماد سلفة موظف', 'hr', 'الموارد البشرية',
             'وجود طلب سلفة في مرحلة التقديم',
             '1. افتح وحدة السلف\n2. ابحث عن الطلب المقدم\n3. اعتمده',
             'تُعتمد السلفة وتُرسل إشعار للموظف',
             f'{UAT_BATCH} - سلفة معتمدة - موظف رحلة عمل',
             'مدير موارد بشرية', 'pending'),
            ('HR-002', 'ضمان بنكي نشط - متابعة تاريخ الانتهاء', 'hr', 'الموارد البشرية',
             'وجود ضمان بنكي نشط',
             '1. افتح وحدة الضمانات البنكية\n2. راجع تواريخ الانتهاء\n3. لاحظ التنبيهات',
             'يظهر تنبيه للضمانات قريبة الانتهاء',
             f'{UAT_BATCH} - ضمان بنكي نشط - عقد صيانة طريق',
             'مسؤول ضمانات', 'pending'),
            # AI
            ('AI-001', 'تنبيه مراقبة الموازنة الآلي', 'ai', 'الذكاء الاصطناعي',
             'وجود موازنة تجاوزت نسبة تنفيذ 90%',
             '1. افتح لوحة قيادة الموازنة\n2. لاحظ التنبيهات الآلية\n3. راجع التوصيات',
             'تظهر توصية بتجميد أو إعادة توزيع الاعتمادات',
             'لوحة قيادة الموازنة - محافظة بورسعيد',
             'مدير مالي', 'pending'),
            ('AI-002', 'فحص اكتمال الاضبارة الآلي', 'ai', 'الذكاء الاصطناعي',
             'وجود اضبارة ناقصة',
             '1. افتح الاضبارة الناقصة\n2. شغّل فحص الاكتمال الآلي\n3. راجع قائمة المستندات الناقصة',
             'تظهر قائمة مفصلة بالمستندات الناقصة باللغة العربية',
             f'{UAT_BATCH} - اضبارة ناقصة فاتورة - صيانة مبنى',
             'مراجع', 'pending'),
            # SECURITY
            ('SEC-001', 'منع وصول غير مصرح به', 'security', 'الأمان',
             'وجود مستخدم بصلاحيات محدودة',
             '1. سجّل دخول بمستخدم محدود الصلاحية\n2. حاول الوصول لقائمة الاعتماد',
             'يُمنع الوصول مع ظهور رسالة واضحة',
             'إعدادات المستخدمين والمجموعات',
             'مسؤول نظام', 'pending'),
            # REPORTS
            ('RPT-001', 'تقرير تنفيذ الموازنة', 'report', 'التقارير',
             'وجود بيانات موازنة كاملة',
             '1. افتح وحدة التقارير\n2. شغّل تقرير تنفيذ الموازنة\n3. اختر الفترة الزمنية',
             'يظهر تقرير مفصل بنسب التنفيذ لكل إدارة',
             'وحدة التقارير - محافظة بورسعيد',
             'مدير مالي', 'pending'),
            ('RPT-002', 'تقرير الارتباطات التراكمية', 'report', 'التقارير',
             'وجود ارتباطات في حالات مختلفة',
             '1. افتح لوحة قيادة الارتباطات\n2. راجع ملخص الارتباطات',
             'يظهر تقرير يقارن الارتباطات المعتمدة والمدفوعة والملغاة',
             'لوحة القيادة التنفيذية',
             'مدير مالي', 'pending'),
        ]

        for tc_id, name, cat, arabic_module, pre, steps, expected, ref, role, status in scenarios:
            Scenario.create({
                'test_case_id': tc_id,
                'name': name,
                'batch_reference': UAT_BATCH,
                'module': cat,
                'arabic_module_name': arabic_module,
                'category': cat,
                'precondition': pre,
                'steps': steps,
                'expected_result': expected,
                'record_ref': ref,
                'user_role': role,
                'status': status,
            })
            count += 1

        return count
