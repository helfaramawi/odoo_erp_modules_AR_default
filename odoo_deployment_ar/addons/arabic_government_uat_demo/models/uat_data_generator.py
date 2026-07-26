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
        if options.get('generate_custody_cases'):
            run('العهد', self._generate_custody)
        if options.get('generate_auction_cases'):
            run('المزادات', self._generate_auctions)
        if options.get('generate_cheque_cases'):
            run('الشيكات', self._generate_cheques)
        if options.get('generate_penalty_cases'):
            run('الجزاءات', self._generate_penalties)
        if options.get('generate_stocktaking_cases'):
            run('الجرد الحكومي', self._generate_stocktaking)
        if options.get('generate_fixed_asset_cases'):
            run('الأصول الثابتة', self._generate_fixed_assets)
        if options.get('generate_ai_agent_cases'):
            run('سيناريوهات الذكاء الاصطناعي', self._generate_ai_scenarios)
        if options.get('generate_report_cases'):
            run('سيناريوهات التقارير', self._generate_report_scenarios)

        # Always generate UAT scenario records (wrapped in savepoint like other generators)
        run('سيناريوهات الاختبار', self._generate_uat_scenarios)

        # Write log lines — each in its own savepoint to avoid aborting the transaction
        seq = 10
        for label, count, status, msg in results:
            try:
                with self.env.cr.savepoint():
                    self.env['arabic.government.uat.generation.log.line'].create({
                        'log_id': log_record.id,
                        'sequence': seq,
                        'category': label,
                        'description': f'توليد بيانات: {label}',
                        'record_count': count,
                        'status': status,
                        'message': msg,
                    })
            except Exception as exc:
                _logger.warning('Could not write log line for %s: %s', label, exc)
            seq += 10

        summary_lines = [f'• {r[0]}: {r[1]} سجل ({r[2]})' for r in results]
        summary = f'إجمالي السجلات المنشأة: {total}\n' + '\n'.join(summary_lines)
        try:
            log_record.write({'result_summary': summary, 'total_created': total, 'state': 'done'})
        except Exception as exc:
            _logger.warning('Could not finalize generation log: %s', exc)
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
            try:
                with self.env.cr.savepoint():
                    if self._already_exists('account.move', [('ref', '=', ref), ('move_type', '=', 'in_invoice')]):
                        continue
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
            try:
                with self.env.cr.savepoint():
                    if self._already_exists('port_said.payment_order', [('purpose', 'ilike', desc[:20])]):
                        continue
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

        employee = self.env['hr.employee'].search([], limit=1)
        for state, desc, amount in advance_scenarios:
            name = f'{UAT_BATCH} - {desc}'
            try:
                with self.env.cr.savepoint():
                    if self._already_exists('port_said.advance', [('name', '=', name)]):
                        continue
                    vals = {
                        'name': name,
                        'amount': amount,
                        'advance_date': TODAY - timedelta(days=5),
                        'due_date': TODAY + timedelta(days=90),
                        'purpose': f'بيانات اختبار القبول - {UAT_BATCH}',
                    }
                    if 'employee_id' in Advance._fields and employee:
                        vals['employee_id'] = employee.id
                    adv = Advance.create(vals)
                    try:
                        with self.env.cr.savepoint():
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
                        pass
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
        bank = self.env['res.bank'].search([], limit=1)
        for state, desc, amount, days in guarantee_scenarios:
            name = f'{UAT_BATCH} - {desc}'
            try:
                with self.env.cr.savepoint():
                    if self._already_exists('port_said.bank.guarantee', [('name', '=', name)]):
                        continue
                    vals = {
                        'name': name,
                        'amount': amount,
                        'issue_date': TODAY - timedelta(days=10),
                        'expiry_date': TODAY + timedelta(days=days if days else 30),
                        'issuing_bank': bank.name if bank else 'بنك الاستثمار القومي',
                    }
                    if 'notes' in Guarantee._fields:
                        vals['notes'] = f'بيانات اختبار القبول - {UAT_BATCH}'
                    guar = Guarantee.create(vals)
                    try:
                        with self.env.cr.savepoint():
                            if state in ('active', 'extended', 'released', 'forfeited'):
                                guar.action_activate()
                            if state in ('extended',) and hasattr(guar, 'action_extend'):
                                guar.action_extend()
                            if state == 'released' and hasattr(guar, 'action_release'):
                                guar.action_release()
                            if state == 'forfeited' and hasattr(guar, 'action_forfeit'):
                                guar.action_forfeit()
                    except Exception:
                        pass
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
            # ═══════════════════════════════════════════════════════════════
            # BUDGET — الموازنة (8 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('BDG-004', 'تعديل اعتماد موازنة بند محدد', 'budget', 'الموازنة',
             'وجود موازنة معتمدة وصلاحية تعديل',
             '1. افتح الموازنة المعتمدة\n2. اضغط "تعديل الاعتماد"\n3. أدخل المبلغ الجديد\n4. قدم للاعتماد',
             'يُعتمد التعديل ويُسجّل في سجل التغييرات',
             f'{UAT_BATCH} - موازنة إدارة النظافة',
             'مدير مالي', 'pending'),
            ('BDG-005', 'تحويل اعتماد بين بندين', 'budget', 'الموازنة',
             'وجود بند بفائض واحتياج لبند آخر',
             '1. افتح أداة نقل الاعتماد\n2. حدد البند المحيل والمحال إليه\n3. أدخل المبلغ والمبرر',
             'يُنقل الاعتماد مع توثيق العملية في السجل',
             f'{UAT_BATCH} - موازنة مركز المعلومات (تكنولوجيا)',
             'مدير مالي', 'pending'),
            ('BDG-006', 'إغلاق موازنة السنة المالية المنتهية', 'budget', 'الموازنة',
             'وجود موازنة سنة منتهية',
             '1. افتح الموازنة المنتهية\n2. شغّل معالج الإغلاق\n3. راجع الأرصدة الختامية',
             'تُغلق الموازنة وتظهر التقارير الختامية',
             f'{UAT_BATCH} - موازنة مديرية الشؤون المالية',
             'مدير مالي', 'pending'),
            ('BDG-007', 'لوحة قيادة الموازنة - رسم بياني', 'budget', 'الموازنة',
             'وجود بيانات موازنة للسنة الحالية',
             '1. افتح لوحة قيادة الموازنة\n2. راجع الرسوم البيانية للتنفيذ',
             'تظهر رسوم بيانية واضحة لنسب التنفيذ لكل إدارة',
             'لوحة قيادة الموازنة - محافظة بورسعيد',
             'مدير مالي', 'pending'),
            ('BDG-008', 'طباعة تقرير الموازنة التقديرية', 'budget', 'الموازنة',
             'وجود موازنة معتمدة',
             '1. افتح الموازنة\n2. اضغط "طباعة"\n3. اختر نموذج الموازنة التقديرية',
             'يُطبع التقرير بصيغة PDF بالعربية',
             f'{UAT_BATCH} - موازنة إدارة الصيانة',
             'مسؤول موازنة', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # COMMITMENT — الارتباطات (6 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('CMT-004', 'تعديل مبلغ ارتباط قبل الاعتماد', 'commitment', 'الارتباطات',
             'وجود ارتباط في مرحلة المسودة',
             '1. افتح الارتباط المسودة\n2. عدّل المبلغ المطلوب\n3. احفظ التعديل',
             'يُحفظ التعديل ويُحدّث رصيد الموازنة المتوقع',
             f'{UAT_BATCH} - ارتباط مسودة - مستلزمات نظافة',
             'مسؤول موازنة', 'pending'),
            ('CMT-005', 'ارتباط محجوز - ربط بأمر شراء', 'commitment', 'الارتباطات',
             'وجود ارتباط معتمد وأمر شراء',
             '1. افتح الارتباط المعتمد\n2. اربطه بأمر الشراء\n3. تحقق من الحالة',
             'يُحجز الارتباط ويظهر مرتبطاً بأمر الشراء',
             f'{UAT_BATCH} - ارتباط محجوز - تطوير منظومة أرشفة',
             'مسؤول مشتريات', 'pending'),
            ('CMT-006', 'تقرير الارتباطات حسب الإدارة', 'commitment', 'الارتباطات',
             'وجود ارتباطات لعدة إدارات',
             '1. افتح تقارير الارتباطات\n2. صفّ حسب الإدارة\n3. راجع الإجماليات',
             'يظهر تقرير مجمّع يوضح ارتباطات كل إدارة ونسبة تنفيذها',
             'لوحة القيادة التنفيذية',
             'مدير مالي', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # PROCUREMENT — المشتريات (8 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('PRC-004', 'تشكيل لجنة المشتريات', 'procurement', 'المشتريات',
             'وجود طلب احتياج معتمد يستدعي لجنة',
             '1. افتح وحدة لجان المشتريات\n2. أنشئ لجنة جديدة\n3. أضف الأعضاء\n4. حدد الطلب',
             'تُشكّل اللجنة وتُخطر الأعضاء بالمهمة',
             f'{UAT_BATCH} - طلب احتياج معتمد - توريد قطع غيار معدات',
             'مسؤول مشتريات', 'pending'),
            ('PRC-005', 'إجراء البت الفني والمالي', 'procurement', 'المشتريات',
             'وجود عروض أسعار مقدمة',
             '1. افتح نموذج البت\n2. أدخل تقييم العروض\n3. اختر أفضل عرض',
             'يُختار العرض الأفضل ويُوثّق قرار اللجنة',
             f'{UAT_BATCH} - طلب احتياج معتمد - صيانة شبكة كهرباء (عاجل)',
             'رئيس لجنة مشتريات', 'pending'),
            ('PRC-006', 'إنشاء أمر شراء من البت', 'procurement', 'المشتريات',
             'وجود بت فني ومالي مكتمل',
             '1. افتح البت المكتمل\n2. اضغط "إنشاء أمر شراء"\n3. راجع البيانات',
             'يُنشأ أمر الشراء تلقائياً بيانات المورد الفائز',
             f'{UAT_BATCH} - طلب احتياج تحول لأمر شراء - أثاث مكتبي',
             'مسؤول مشتريات', 'pending'),
            ('PRC-007', 'متابعة تسليم أمر الشراء', 'procurement', 'المشتريات',
             'وجود أمر شراء مرسل للمورد',
             '1. افتح أمر الشراء\n2. سجّل الاستلام الجزئي\n3. راجع الكميات',
             'تُحدّث كميات الاستلام ويظهر الرصيد المتبقي',
             f'{UAT_BATCH} - طلب احتياج مسودة - أجهزة حاسب آلي',
             'أمين مخزن', 'pending'),
            ('PRC-008', 'تقرير الموردين المعتمدين', 'procurement', 'المشتريات',
             'وجود قاعدة بيانات موردين',
             '1. افتح تقارير المشتريات\n2. اختر "الموردين المعتمدين"\n3. صدّر التقرير',
             'يظهر تقرير بأسماء الموردين وتاريخ الاعتماد وآخر توريد',
             'وحدة التقارير - المشتريات',
             'مدير مشتريات', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # DOSSIER — الاضبارة (6 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('DOS-004', 'إرفاق مستند بالاضبارة', 'dossier', 'الاضبارة',
             'وجود اضبارة ناقصة مستند',
             '1. افتح الاضبارة الناقصة\n2. اضغط "إضافة مرفق"\n3. ارفع ملف PDF\n4. حدد نوع المستند',
             'يُرفق المستند وتتحول الاضبارة لمكتملة إن اكتملت المستندات',
             f'{UAT_BATCH} - اضبارة ناقصة عقد - توريد أثاث',
             'مسؤول اضبارة', 'pending'),
            ('DOS-005', 'تاريخ اضبارة وسجل التعديلات', 'dossier', 'الاضبارة',
             'وجود اضبارة لها تاريخ تعديلات',
             '1. افتح الاضبارة\n2. اضغط تبويب "السجل"\n3. راجع التعديلات',
             'تظهر قائمة زمنية بجميع التغييرات والمستخدم المسؤول',
             f'{UAT_BATCH} - اضبارة مغلقة ومعتمدة - رصف طريق',
             'مراجع', 'pending'),
            ('DOS-006', 'تقرير الاضبارات المعلقة', 'dossier', 'الاضبارة',
             'وجود اضبارات في حالات مختلفة',
             '1. افتح تقارير الاضبارة\n2. فلتر "الاضبارات المفتوحة"\n3. رتّب حسب التاريخ',
             'يظهر تقرير بالاضبارات التي تجاوزت 30 يوماً دون حسم',
             'وحدة التقارير - الاضبارة',
             'مدير مالي', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # DISBURSEMENT — دفتر 55 والصرف (8 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('DIS-003', 'طباعة استمارة 50 — معاينة', 'disbursement', 'دفتر 55',
             'وجود قيد دفتر 55 مكتمل البيانات',
             '1. افتح قيد دفتر 55\n2. اضغط "معاينة استمارة 50"\n3. راجع التخطيط',
             'تظهر معاينة الاستمارة بجميع البيانات مرتبة على النموذج',
             f'{UAT_BATCH} - دفتر 55 مرحّل - توريد معدات',
             'مسؤول صرف', 'pending'),
            ('DIS-004', 'طباعة استمارة 50 — نهائية', 'disbursement', 'دفتر 55',
             'وجود صلاحية مدير مالي وقيد مكتمل',
             '1. سجّل دخول كمدير مالي\n2. افتح القيد\n3. اضغط "طباعة نهائية ★"',
             'تُطبع الاستمارة الرسمية PDF بخلفية النموذج الحكومي وتُسجّل الطباعة',
             f'{UAT_BATCH} - دفتر 55 موافق عليه - أعمال صيانة',
             'مدير مالي', 'pending'),
            ('DIS-005', 'إعادة طباعة استمارة 50 مع تسجيل السبب', 'disbursement', 'دفتر 55',
             'وجود قيد مطبوع مسبقاً',
             '1. افتح القيد المطبوع\n2. اضغط "إعادة طباعة"\n3. أدخل سبب الإعادة\n4. اطبع',
             'تُسجّل إعادة الطباعة مع السبب والمستخدم والتاريخ',
             f'{UAT_BATCH} - دفتر 55 مرحّل - توريد معدات',
             'مدير مالي', 'pending'),
            ('DIS-006', 'فحص جاهزية طباعة دفتر 55', 'disbursement', 'دفتر 55',
             'وجود قيد ناقص بعض البيانات',
             '1. افتح قيداً ناقصاً\n2. اضغط "فحص جاهزية الطباعة"',
             'تظهر قائمة بالمتطلبات الناقصة مع إرشادات التصحيح',
             f'{UAT_BATCH} - دفتر 55 مسودة - مرتبات يناير',
             'مسؤول صرف', 'pending'),
            ('DIS-007', 'دفتر 224 — قيد صرفيات يومي', 'disbursement', 'دفتر 224',
             'وجود حركات صرف يومية',
             '1. افتح دفتر 224\n2. أنشئ قيد صرفيات جديد\n3. أدخل البيانات\n4. احفظ',
             'يُسجّل القيد في الدفتر بالتسلسل اليومي الصحيح',
             f'{UAT_BATCH} - دفتر 224 - قيد صرفيات يومي - مشتريات',
             'محاسب', 'pending'),
            ('DIS-008', 'دفتر 224 — كشف يومي مجمّع', 'disbursement', 'دفتر 224',
             'وجود قيود متعددة ليوم واحد',
             '1. افتح دفتر 224\n2. فلتر بتاريخ اليوم\n3. اضغط "الكشف اليومي"',
             'يظهر كشف مجمّع بجميع حركات اليوم مع الإجماليات',
             f'{UAT_BATCH} - دفتر 224 - قيد تسويات - ضرائب',
             'مراجع', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # PAYMENT ORDERS — أوامر الدفع (6 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('PAY-001', 'استلام أمر دفع من الخزينة', 'disbursement', 'أوامر الدفع',
             'وجود أمر دفع مُصدَر من وزارة المالية',
             '1. افتح وحدة أوامر الدفع\n2. أنشئ أمر جديد\n3. أدخل بيانات الأمر\n4. سجّل الاستلام',
             'يُسجّل أمر الدفع ويظهر في القيود',
             f'{UAT_BATCH} - أمر دفع مستلم - دفع موردين',
             'محاسب', 'pending'),
            ('PAY-002', 'قيد أمر الدفع في دفتر 224', 'disbursement', 'أوامر الدفع',
             'وجود أمر دفع مستلم',
             '1. افتح أمر الدفع المستلم\n2. اضغط "قيد في دفتر 224"',
             'يُقيّد أمر الدفع تلقائياً في دفتر 224 بالتاريخ الصحيح',
             f'{UAT_BATCH} - أمر دفع مسجل - سداد فاتورة صيانة',
             'محاسب', 'pending'),
            ('PAY-003', 'تحصيل أمر الدفع (إيداع بنك)', 'disbursement', 'أوامر الدفع',
             'وجود أمر دفع مسجل',
             '1. افتح أمر الدفع المسجل\n2. أدخل بيانات الإيداع البنكي\n3. اضغط "تحصيل"',
             'يُسجّل الإيداع ويتحول أمر الدفع لحالة محصّل',
             f'{UAT_BATCH} - أمر دفع موافق عليه',
             'محاسب', 'pending'),
            ('PAY-004', 'إلغاء أمر دفع ومبرراته', 'disbursement', 'أوامر الدفع',
             'وجود أمر دفع في مرحلة المسودة',
             '1. افتح أمر الدفع\n2. اضغط "إلغاء"\n3. أدخل سبب الإلغاء',
             'يُلغى أمر الدفع ويُسجّل السبب في السجل',
             f'{UAT_BATCH} - أمر دفع ملغي',
             'مدير مالي', 'pending'),
            ('PAY-005', 'تقرير أوامر الدفع حسب الحالة', 'disbursement', 'أوامر الدفع',
             'وجود أوامر دفع بحالات متنوعة',
             '1. افتح تقارير أوامر الدفع\n2. فلتر حسب الحالة\n3. صدّر التقرير',
             'يظهر تقرير مجمّع بأعداد ومبالغ الأوامر لكل حالة',
             'وحدة التقارير - أوامر الدفع',
             'مدير مالي', 'pending'),
            ('PAY-006', 'مطابقة أمر الدفع مع الشيك', 'disbursement', 'أوامر الدفع',
             'وجود أمر دفع وشيك صادر',
             '1. افتح أمر الدفع\n2. اربطه بالشيك المقابل\n3. تأكد المطابقة',
             'يظهر الشيك مرتبطاً بأمر الدفع وتُسجّل العملية',
             f'{UAT_BATCH} - أمر دفع مرحّل',
             'محاسب', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # ACCOUNTING — المحاسبة (8 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('ACC-003', 'تسوية حساب المورد', 'accounting', 'المحاسبة',
             'وجود دفعات ومديونيات للمورد',
             '1. افتح حساب المورد\n2. شغّل المطابقة التلقائية\n3. راجع الأرصدة',
             'تُوفّق الدفعات مع الفواتير ويظهر الرصيد الصافي',
             f'{UAT_BATCH} - فاتورة مورد - مستلزمات نظافة',
             'محاسب', 'pending'),
            ('ACC-004', 'ميزان المراجعة الشهري', 'accounting', 'المحاسبة',
             'وجود قيود محاسبية للشهر',
             '1. افتح وحدة التقارير المحاسبية\n2. شغّل ميزان المراجعة\n3. حدد الشهر',
             'يظهر ميزان مراجعة متوازن بالمدين والدائن',
             'وحدة التقارير - المحاسبة',
             'مراجع', 'pending'),
            ('ACC-005', 'قيد يدوي لتسوية فروقات', 'accounting', 'المحاسبة',
             'وجود فروق محاسبية تحتاج تسوية',
             '1. افتح وحدة القيود اليدوية\n2. أنشئ قيداً جديداً\n3. أدخل المبلغ والحسابات\n4. رحّل',
             'يُرحّل القيد ويُحدّث الأرصدة',
             f'{UAT_BATCH} - فاتورة مورد - توريد أثاث مكتبي',
             'محاسب', 'pending'),
            ('ACC-006', 'كشف حساب مورد بفترة زمنية', 'accounting', 'المحاسبة',
             'وجود حركات للمورد',
             '1. افتح بطاقة المورد\n2. اضغط "كشف الحساب"\n3. حدد الفترة',
             'يظهر كشف حساب مفصّل بجميع الحركات والرصيد التراكمي',
             f'{UAT_BATCH} - فاتورة مورد - أعمال صيانة طريق',
             'مسؤول مدفوعات', 'pending'),
            ('ACC-007', 'تقرير المصروفات حسب البند', 'accounting', 'المحاسبة',
             'وجود مصروفات موزّعة على بنود موازنة',
             '1. افتح تقارير المصروفات\n2. جمّع حسب بند الموازنة',
             'يظهر تقرير بإجمالي المصروفات لكل بند ونسبته من الاعتماد',
             'وحدة التقارير - المحاسبة',
             'مدير مالي', 'pending'),
            ('ACC-008', 'إقفال الفترة المحاسبية', 'accounting', 'المحاسبة',
             'وجود قيود شهر مكتملة',
             '1. افتح إعدادات الفترات\n2. حدد الشهر المنتهي\n3. اضغط "إقفال"',
             'تُقفل الفترة ويُمنع إدخال قيود بتواريخ سابقة',
             'إعدادات المحاسبة - الفترات',
             'مدير مالي', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # CHEQUES & CASH BOOKS — الشيكات ودفاتر النقدية (5 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('CHQ-001', 'إنشاء دفتر شيكات جديد', 'disbursement', 'الشيكات',
             'وجود حساب بنكي نشط',
             '1. افتح وحدة الشيكات\n2. أنشئ دفتر شيكات\n3. أدخل نطاق الأرقام',
             'يُسجّل الدفتر ويصبح جاهزاً لإصدار الشيكات',
             'وحدة أوامر الدفع والشيكات',
             'محاسب', 'pending'),
            ('CHQ-002', 'إصدار شيك لمورد', 'disbursement', 'الشيكات',
             'وجود دفتر شيكات نشط وأمر دفع',
             '1. افتح دفتر الشيكات\n2. أصدر شيكاً جديداً\n3. أدخل بيانات المورد والمبلغ',
             'يُسجّل الشيك ويُخصم من رصيد الدفتر',
             'وحدة أوامر الدفع والشيكات',
             'محاسب', 'pending'),
            ('CHQ-003', 'تتبع حالة الشيك (صُرف / لم يُصرف)', 'disbursement', 'الشيكات',
             'وجود شيكات صادرة بحالات مختلفة',
             '1. افتح قائمة الشيكات\n2. فلتر حسب الحالة\n3. راجع الشيكات المتأخرة',
             'تظهر الشيكات الصادرة منذ أكثر من 30 يوماً مع تنبيه',
             'وحدة أوامر الدفع والشيكات',
             'مدير مالي', 'pending'),
            ('CHQ-004', 'إلغاء شيك وإعادة الرقم', 'disbursement', 'الشيكات',
             'وجود شيك لم يُسلّم للمستفيد',
             '1. افتح الشيك\n2. اضغط "إلغاء"\n3. أدخل سبب الإلغاء',
             'يُلغى الشيك ويُعاد الرقم لمجموعة المتاحة',
             'وحدة أوامر الدفع والشيكات',
             'محاسب', 'pending'),
            ('CHQ-005', 'كشف نقدي يومي', 'disbursement', 'الشيكات',
             'وجود حركات نقدية اليوم',
             '1. افتح وحدة الكشف النقدي\n2. اختر التاريخ\n3. راجع الرصيد',
             'يظهر كشف بالحركات النقدية ورصيد الخزينة',
             'وحدة أوامر الدفع والشيكات',
             'أمين الخزينة', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # ADVANCES — السلف (6 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('ADV-001', 'تقديم طلب سلفة دائمة', 'hr', 'السلف',
             'وجود موظف في النظام',
             '1. افتح وحدة السلف\n2. أنشئ طلب سلفة\n3. أدخل الغرض والمبلغ\n4. قدّم',
             'يُقدَّم الطلب ويُخطر المدير للاعتماد',
             f'{UAT_BATCH} - سلفة مقدمة - موظف في إجازة مرضية',
             'موظف', 'pending'),
            ('ADV-002', 'اعتماد سلفة موظف', 'hr', 'السلف',
             'وجود طلب سلفة في مرحلة التقديم',
             '1. افتح وحدة السلف\n2. ابحث عن الطلب المقدم\n3. اعتمده',
             'تُعتمد السلفة وتُرسل إشعار للموظف',
             f'{UAT_BATCH} - سلفة معتمدة - موظف رحلة عمل',
             'مدير موارد بشرية', 'pending'),
            ('ADV-003', 'صرف السلفة للموظف', 'hr', 'السلف',
             'وجود سلفة معتمدة',
             '1. افتح السلفة المعتمدة\n2. اضغط "صرف"\n3. أدخل بيانات الدفع',
             'تُصرف السلفة وتُسجّل حركة الصرف',
             f'{UAT_BATCH} - سلفة صُرفت - موظف سفر خارجي',
             'أمين الخزينة', 'pending'),
            ('ADV-004', 'تسوية سلفة بعد العودة', 'hr', 'السلف',
             'وجود سلفة مصروفة',
             '1. افتح السلفة\n2. اضغط "تسوية"\n3. أدخل المبالغ المنفقة\n4. أرفق الإيصالات',
             'تُسوّى السلفة ويُعاد الفائض أو تُطالب العجز',
             f'{UAT_BATCH} - سلفة تمت تسويتها - موظف سبق صرفه سلفة',
             'محاسب', 'pending'),
            ('ADV-005', 'رفض طلب سلفة مع السبب', 'hr', 'السلف',
             'وجود طلب سلفة لا يستوفي الشروط',
             '1. افتح الطلب\n2. اضغط "رفض"\n3. أدخل سبب الرفض',
             'يُرفض الطلب مع إخطار الموظف بالسبب',
             f'{UAT_BATCH} - سلفة ملغاة - طلب لم يستوفِ الشروط',
             'مدير موارد بشرية', 'pending'),
            ('ADV-006', 'تقرير السلف المعلقة (غير مسوّاة)', 'hr', 'السلف',
             'وجود سلف مصروفة لم تُسوَّ',
             '1. افتح تقارير السلف\n2. فلتر "غير مسوّاة"\n3. رتّب حسب تاريخ الاستحقاق',
             'يظهر تقرير بالسلف المتأخرة مع أسماء الموظفين',
             'وحدة التقارير - السلف',
             'مدير مالي', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # BANK GUARANTEES — الضمانات البنكية (4 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('BGU-001', 'استلام خطاب ضمان جديد', 'hr', 'الضمانات البنكية',
             'وجود عقد يستلزم ضماناً بنكياً',
             '1. افتح وحدة الضمانات\n2. أنشئ خطاب ضمان جديد\n3. أدخل البيانات',
             'يُسجّل خطاب الضمان ويظهر في لوحة المراقبة',
             f'{UAT_BATCH} - ضمان بنكي نشط - عقد صيانة طريق',
             'مسؤول ضمانات', 'pending'),
            ('BGU-002', 'تنبيه انتهاء صلاحية الضمان', 'hr', 'الضمانات البنكية',
             'وجود ضمان بنكي قريب الانتهاء (30 يوم)',
             '1. افتح لوحة القيادة\n2. لاحظ تنبيهات الضمانات',
             'يظهر تنبيه برتقالي للضمانات التي تنتهي خلال 30 يوماً',
             f'{UAT_BATCH} - ضمان بنكي نشط - عقد صيانة طريق',
             'مدير مالي', 'pending'),
            ('BGU-003', 'الإفراج عن خطاب ضمان بعد انتهاء العقد', 'hr', 'الضمانات البنكية',
             'وجود عقد منتهٍ وضمان نشط',
             '1. افتح خطاب الضمان\n2. اضغط "إفراج"\n3. أدخل تاريخ الإفراج والمرجع',
             'يتحول الضمان لحالة "محرر" ويُخطر البنك',
             f'{UAT_BATCH} - ضمان بنكي محرر - عقد منتهي',
             'مدير مالي', 'pending'),
            ('BGU-004', 'مصادرة ضمان لعقد مخالف', 'hr', 'الضمانات البنكية',
             'وجود مورد أخلّ بشروط العقد',
             '1. افتح خطاب الضمان\n2. اضغط "مصادرة"\n3. أدخل سبب المصادرة',
             'تُصادر قيمة الضمان وتُسجّل العملية في السجل القانوني',
             f'{UAT_BATCH} - ضمان بنكي مصادر - عقد مخالف',
             'مدير مالي', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # PROJECTS — المشروعات (4 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('PRJ-001', 'متابعة ميزانية مشروع', 'project', 'المشروعات',
             'وجود مشروع له ميزانية محددة',
             '1. افتح وحدة المشروعات\n2. ابحث عن مشروع UAT\n3. راجع التقرير المالي',
             'تظهر نسبة تنفيذ الميزانية والمبلغ المتبقي',
             f'{UAT_BATCH} - مشروع تطوير البنية التحتية للطرق الرئيسية',
             'مدير مشروع', 'pending'),
            ('PRJ-002', 'تحديث نسبة إنجاز مشروع', 'project', 'المشروعات',
             'وجود مشروع قيد التنفيذ',
             '1. افتح المشروع\n2. أدخل نسبة الإنجاز الجديدة\n3. أضف ملاحظات التقدم',
             'تُحدّث نسبة الإنجاز وتظهر في لوحة القيادة',
             f'{UAT_BATCH} - مشروع إعادة تأهيل مبنى الخدمات الإلكترونية',
             'مدير مشروع', 'pending'),
            ('PRJ-003', 'تقرير المشروعات المتأخرة', 'project', 'المشروعات',
             'وجود مشاريع تجاوزت الجدول الزمني',
             '1. افتح تقارير المشروعات\n2. فلتر "متأخرة"\n3. راجع أسباب التأخير',
             'يظهر تقرير بالمشاريع المتأخرة مع نسب الإنجاز المقابلة',
             'وحدة التقارير - المشروعات',
             'مدير تنفيذي', 'pending'),
            ('PRJ-004', 'ربط مشروع بارتباط مالي', 'project', 'المشروعات',
             'وجود مشروع وارتباط مالي',
             '1. افتح المشروع\n2. أضف الارتباط المالي المرتبط به',
             'يظهر الارتباط في تبويب التمويل ويُحسب الرصيد المتبقي',
             f'{UAT_BATCH} - مشروع التحول الرقمي لمركز معلومات المحافظة',
             'مدير مالي', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # INVENTORY — المخازن (5 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('INV-001', 'استلام ومحضر فحص', 'inventory', 'المخازن',
             'وجود أمر شراء مكتمل ولجنة فحص',
             '1. افتح لجنة الفحص والاستلام\n2. أدخل نتائج الفحص\n3. اعتمد الاستلام',
             'يُثبّت المخزن ويُحدث رصيد المستودع',
             f'{UAT_BATCH} - لجنة فحص واستلام أجهزة الحاسب الآلي',
             'أمين مخزن', 'pending'),
            ('INV-002', 'إصدار إذن صرف من المخزن', 'inventory', 'المخازن',
             'وجود أصناف في المخزن وطلب احتياج',
             '1. افتح وحدة أذونات الصرف\n2. أنشئ إذن جديد\n3. أدخل الأصناف والكميات',
             'يُصدر الإذن ويُخصم المخزون',
             f'{UAT_BATCH} - لجنة فحص واستلام معدات النظافة',
             'أمين مخزن', 'pending'),
            ('INV-003', 'إضافة صنف جديد للمخزن', 'inventory', 'المخازن',
             'وجود أمر استلام معتمد',
             '1. افتح وحدة الإضافات\n2. أنشئ إضافة مخزن جديدة\n3. أدخل الأصناف\n4. اعتمد',
             'تُضاف الأصناف للمخزون وتُحدّث الكميات',
             f'{UAT_BATCH} - إضافة مخزن - حاسبات مركز المعلومات',
             'أمين مخزن', 'pending'),
            ('INV-004', 'كشف رصيد المخزون الحالي', 'inventory', 'المخازن',
             'وجود حركات مخزنية سابقة',
             '1. افتح وحدة المخازن\n2. اضغط "كشف الرصيد"\n3. فلتر حسب الصنف',
             'يظهر كشف بالأرصدة الحالية لكل صنف وموقعه',
             'وحدة المخازن - الرصيد الحالي',
             'أمين مخزن', 'pending'),
            ('INV-005', 'تقرير حركة صنف خلال فترة', 'inventory', 'المخازن',
             'وجود حركات لصنف محدد',
             '1. افتح تقارير المخازن\n2. اختر الصنف والفترة\n3. اعرض الحركات',
             'يظهر تقرير بالوارد والصادر والرصيد لكل حركة',
             'وحدة التقارير - المخازن',
             'مدير مشتريات', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # HR — الموارد البشرية (3 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('HR-003', 'سجل الموظف — عرض السلف والضمانات', 'hr', 'الموارد البشرية',
             'وجود موظف له سجل سلف وضمانات',
             '1. افتح بطاقة الموظف\n2. اضغط تبويب "السلف والضمانات"\n3. راجع السجل',
             'تظهر كل سلف الموظف وضماناته ورصيده الحالي',
             f'{UAT_BATCH} - سلفة معتمدة - موظف رحلة عمل',
             'مدير موارد بشرية', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # REPORTS — التقارير (8 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('RPT-003', 'تصدير تقرير Excel', 'report', 'التقارير',
             'وجود بيانات في أي وحدة',
             '1. افتح أي تقرير\n2. اضغط "تصدير"\n3. اختر صيغة Excel',
             'يُصدَّر الملف بتنسيق Excel قابل للتحرير',
             'وحدة التقارير',
             'مدير مالي', 'pending'),
            ('RPT-004', 'لوحة القيادة التنفيذية', 'report', 'التقارير',
             'وجود بيانات تشغيلية',
             '1. افتح لوحة القيادة التنفيذية\n2. راجع المؤشرات الرئيسية',
             'تظهر KPIs واضحة: الموازنة المنفذة، الارتباطات النشطة، المدفوعات',
             'لوحة القيادة التنفيذية',
             'مدير تنفيذي', 'pending'),
            ('RPT-005', 'تقرير المدفوعات الشهرية', 'report', 'التقارير',
             'وجود مدفوعات للشهر',
             '1. افتح تقارير المدفوعات\n2. حدد الشهر\n3. جمّع حسب الجهة',
             'يظهر تقرير بإجمالي المدفوعات لكل جهة مستفيدة',
             'وحدة التقارير - المدفوعات',
             'مدير مالي', 'pending'),
            ('RPT-006', 'تقرير مقارنة الموازنات سنوياً', 'report', 'التقارير',
             'وجود موازنات لسنتين على الأقل',
             '1. افتح تقارير الموازنة\n2. اختر "مقارنة سنوية"\n3. حدد السنوات',
             'يظهر تقرير مقارن بالتطور السنوي للإنفاق',
             'وحدة التقارير - الموازنة',
             'مدير مالي', 'pending'),
            ('RPT-007', 'طباعة تقرير بالعربية (PDF)', 'report', 'التقارير',
             'وجود تقرير جاهز',
             '1. افتح أي تقرير\n2. اضغط "طباعة PDF"\n3. تحقق من الاتجاه RTL',
             'يُطبع التقرير بالعربية من اليمين لليسار بخط واضح',
             'وحدة التقارير',
             'مسؤول نظام', 'pending'),
            ('RPT-008', 'تقرير ذمم الموردين المستحقة', 'report', 'التقارير',
             'وجود فواتير موردين غير مدفوعة',
             '1. افتح تقارير المحاسبة\n2. اختر "ذمم الموردين"\n3. فلتر المتأخرة',
             'يظهر تقرير بالمبالغ المستحقة لكل مورد وأعمارها',
             'وحدة التقارير - المحاسبة',
             'مدير مالي', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # AI — الذكاء الاصطناعي (5 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
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
            ('AI-003', 'توصية تحسين سير العمل', 'ai', 'الذكاء الاصطناعي',
             'وجود بيانات عمليات',
             '1. افتح لوحة الذكاء الاصطناعي\n2. اضغط "تحليل سير العمل"\n3. راجع التوصيات',
             'تظهر توصيات محددة لتحسين وقت معالجة الطلبات',
             'لوحة قيادة الذكاء الاصطناعي',
             'مدير تنفيذي', 'pending'),
            ('AI-004', 'كشف شذوذ في المدفوعات', 'ai', 'الذكاء الاصطناعي',
             'وجود بيانات مدفوعات تاريخية',
             '1. افتح وحدة كشف الشذوذ\n2. شغّل التحليل\n3. راجع النتائج',
             'تُكشف أي مدفوعات غير معتادة مع بيان درجة الخطورة',
             'وحدة الذكاء الاصطناعي - المراقبة',
             'مدير مالي', 'pending'),
            ('AI-005', 'تنبيه تلقائي لارتباط على وشك الانتهاء', 'ai', 'الذكاء الاصطناعي',
             'وجود ارتباط تاريخ انتهائه خلال 15 يوماً',
             '1. افتح لوحة القيادة\n2. لاحظ تنبيهات الارتباطات\n3. اضغط على التنبيه',
             'يُعرض الارتباط المعني مع اقتراح تمديد أو إغلاق',
             f'{UAT_BATCH} - ارتباط معتمد - صيانة مبنى الديوان',
             'مسؤول موازنة', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # SECURITY — الأمان (4 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('SEC-001', 'منع وصول غير مصرح به', 'security', 'الأمان',
             'وجود مستخدم بصلاحيات محدودة',
             '1. سجّل دخول بمستخدم محدود الصلاحية\n2. حاول الوصول لقائمة الاعتماد',
             'يُمنع الوصول مع ظهور رسالة واضحة',
             'إعدادات المستخدمين والمجموعات',
             'مسؤول نظام', 'pending'),
            ('SEC-002', 'سجل تدقيق العمليات الحساسة', 'security', 'الأمان',
             'وجود عمليات تمت بصلاحيات خاصة',
             '1. افتح وحدة سجل التدقيق\n2. فلتر العمليات الحساسة\n3. راجع التفاصيل',
             'يظهر سجل تفصيلي بالمستخدم والوقت والعملية',
             'إعدادات الأمان - سجل التدقيق',
             'مسؤول نظام', 'pending'),
            ('SEC-003', 'تغيير كلمة المرور وإعادة تعيينها', 'security', 'الأمان',
             'وجود مستخدم نشط',
             '1. افتح إعدادات المستخدم\n2. اضغط "تغيير كلمة المرور"\n3. أدخل القديمة والجديدة',
             'تُغير كلمة المرور ويُخطر المستخدم',
             'إعدادات المستخدمين',
             'مسؤول نظام', 'pending'),
            ('SEC-004', 'قفل حساب مستخدم بعد محاولات فاشلة', 'security', 'الأمان',
             'وجود سياسة أمان فعّالة',
             '1. حاول الدخول بكلمة مرور خاطئة 5 مرات\n2. لاحظ الرسالة',
             'يُقفل الحساب تلقائياً ويُخطر المسؤول',
             'إعدادات الأمان',
             'مسؤول نظام', 'pending'),
            # ═══════════════════════════════════════════════════════════════
            # REPORTS (continued)
            # ═══════════════════════════════════════════════════════════════
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
            # ═══════════════════════════════════════════════════════════════
            # SYSTEM / GENERAL — عام (6 سيناريوهات)
            # ═══════════════════════════════════════════════════════════════
            ('SYS-001', 'واجهة اللغة العربية — اتجاه RTL', 'system', 'النظام العام',
             'تثبيت النظام باللغة العربية',
             '1. سجّل الدخول\n2. افتح أي شاشة\n3. تحقق من الاتجاه والخطوط',
             'جميع النصوص من اليمين لليسار والأرقام بالترتيب الصحيح',
             'لوحة قيادة الموازنة - محافظة بورسعيد',
             'مسؤول نظام', 'pending'),
            ('SYS-002', 'البحث السريع في أي وحدة', 'system', 'النظام العام',
             'وجود بيانات في النظام',
             '1. اضغط شريط البحث في الأعلى\n2. اكتب رقم مرجع أو اسم\n3. انقر النتيجة',
             'تظهر النتائج المطابقة فوراً من جميع الوحدات',
             'شريط البحث العام',
             'أي مستخدم', 'pending'),
            ('SYS-003', 'الإشعارات والتنبيهات التلقائية', 'system', 'النظام العام',
             'وجود طلبات تحتاج موافقة',
             '1. افتح قائمة الإشعارات (الجرس)\n2. راجع الإشعارات الواردة',
             'تظهر الإشعارات مرتبة حسب الأولوية باللغة العربية',
             'شريط الإشعارات',
             'أي مستخدم', 'pending'),
            ('SYS-004', 'استيراد بيانات من Excel', 'system', 'النظام العام',
             'وجود ملف Excel بالبيانات',
             '1. افتح أي قائمة\n2. اضغط "استيراد"\n3. ارفع ملف Excel\n4. طابق الأعمدة',
             'تُستورَد البيانات بنجاح مع تقرير بالسجلات المنشأة والأخطاء',
             'أداة الاستيراد العامة',
             'مسؤول نظام', 'pending'),
            ('SYS-005', 'النسخ الاحتياطي والاستعادة', 'system', 'النظام العام',
             'وجود صلاحية مسؤول النظام',
             '1. افتح إعدادات النظام\n2. اضغط "نسخ احتياطي"\n3. حمّل الملف',
             'يُنشأ ملف نسخة احتياطية كاملة يمكن استعادتها',
             'إعدادات النظام - النسخ الاحتياطي',
             'مسؤول نظام', 'pending'),
            ('SYS-006', 'تعدد المستخدمين — جلسات متزامنة', 'system', 'النظام العام',
             'وجود عدة مستخدمين',
             '1. سجّل دخول مستخدمين مختلفين في نفس الوقت\n2. أنشئ نفس السجل\n3. لاحظ القفل',
             'يُحمى السجل من التعديل المتزامن برسالة واضحة',
             'إعدادات المستخدمين والمجموعات',
             'مسؤول نظام', 'pending'),
        ]

        # Valid category values for the Selection field
        _valid_cats = {
            'budget', 'commitment', 'procurement', 'dossier', 'disbursement',
            'payment', 'cheques', 'accounting', 'project', 'inventory',
            'hr', 'advances', 'bank_guarantee', 'ai', 'security', 'system', 'report',
        }

        for tc_id, name, cat, arabic_module, pre, steps, expected, ref, role, status in scenarios:
            vals = {
                'test_case_id': tc_id,
                'name': name,
                'batch_reference': UAT_BATCH,
                'module': cat,
                'arabic_module_name': arabic_module,
                'precondition': pre,
                'steps': steps,
                'expected_result': expected,
                'record_ref': ref,
                'user_role': role,
                'status': status,
            }
            if cat in _valid_cats:
                vals['category'] = cat
            Scenario.create(vals)
            count += 1

        return count

    # ------------------------------------------------------------------ #
    #  CUSTODY GENERATION — العهد                                          #
    # ------------------------------------------------------------------ #
    def _generate_custody(self):
        count = 0
        Custody = self.env['custody.assignment']
        Employee = self.env['hr.employee']

        employees = Employee.search([('active', '=', True)], limit=6)
        if not employees:
            _logger.warning('UAT custody: no active employees found, skipping')
            return 0

        items = [
            ('حاسب آلي محمول Dell', '12345678901234', 2500.0, 'active'),
            ('طابعة ليزر HP LaserJet', '23456789012345', 800.0, 'active'),
            ('جهاز عرض بروجكتور', '34567890123456', 1200.0, 'active'),
            ('هاتف مكتبي IP', '45678901234567', 300.0, 'active'),
            ('كاميرا رقمية Canon', '56789012345678', 1800.0, 'returned'),
            ('جهاز ماسح ضوئي Epson', '67890123456789', 600.0, 'draft'),
        ]

        for i, (item_name, national_id, cost, state) in enumerate(items):
            emp = employees[i % len(employees)]
            existing = Custody.search([
                ('employee_id', '=', emp.id),
                ('form_193_ref', '=', f'UAT-193-{i+1:03d}'),
            ], limit=1)
            if existing:
                continue

            product = self._get_or_create_product(item_name)
            vals = {
                'form_193_ref': f'UAT-193-{i+1:03d}',
                'employee_id': emp.id,
                'national_id': national_id,
                'product_id': product.id,
                'qty': 1.0,
                'standard_price': cost,
                'issue_date': TODAY - timedelta(days=30 * (i + 1)),
                'notes': f'بيانات اختبار - {UAT_BATCH}',
            }
            try:
                rec = Custody.create(vals)
                if state == 'active':
                    rec.action_activate()
                elif state == 'returned':
                    rec.action_activate()
                count += 1
            except Exception as exc:
                _logger.warning('UAT custody create failed: %s', exc)

        return count

    # ------------------------------------------------------------------ #
    #  AUCTION GENERATION — المزادات                                       #
    # ------------------------------------------------------------------ #
    def _generate_auctions(self):
        count = 0
        Auction = self.env['auction.request']

        scenarios = [
            {
                'description': f'{UAT_BATCH} - مزاد بيع منقولات حكومية — آليات وسيارات',
                'auction_type': 'sale',
                'sale_type': 'movables',
                'tender_method': 'public',
                'estimated_value': 450000.0,
                'state': 'awarded',
            },
            {
                'description': f'{UAT_BATCH} - مزاد إيجار مبنى إداري — شارع 23 يوليو',
                'auction_type': 'lease',
                'sale_type': False,
                'tender_method': 'public',
                'estimated_value': 120000.0,
                'state': 'done',
            },
            {
                'description': f'{UAT_BATCH} - مزاد بيع معدات مكتبية متقادمة',
                'auction_type': 'sale',
                'sale_type': 'movables',
                'tender_method': 'local',
                'estimated_value': 80000.0,
                'state': 'bidding',
            },
            {
                'description': f'{UAT_BATCH} - مزاد بيع عقار — أرض بورسعيد الجديدة',
                'auction_type': 'sale',
                'sale_type': 'property',
                'tender_method': 'public',
                'estimated_value': 2500000.0,
                'state': 'session_open',
            },
            {
                'description': f'{UAT_BATCH} - مزاد إيجار محل تجاري — سوق العرب',
                'auction_type': 'lease',
                'sale_type': False,
                'tender_method': 'public',
                'estimated_value': 36000.0,
                'state': 'confirmed',
            },
            {
                'description': f'{UAT_BATCH} - مزاد بيع سيارة خدمة قديمة',
                'auction_type': 'sale',
                'sale_type': 'movables',
                'tender_method': 'local',
                'estimated_value': 25000.0,
                'state': 'draft',
            },
        ]

        from datetime import datetime
        state_order = ['draft', 'confirmed', 'session_open', 'bidding', 'awarded', 'done', 'cancelled']

        for s in scenarios:
            existing = Auction.search([('description', '=', s['description'])], limit=1)
            if existing:
                continue
            vals = {
                'description': s['description'],
                'auction_type': s['auction_type'],
                'tender_method': s['tender_method'],
                'estimated_value': s['estimated_value'],
                'venue': 'قاعة الاجتماعات الرئيسية — ديوان عام المحافظة',
                'asset_description': s['description'],
                'auction_date': fields.Datetime.now(),
            }
            if s.get('sale_type'):
                vals['sale_type'] = s['sale_type']
            try:
                rec = Auction.create(vals)
                target = s['state']
                transitions = ['confirmed', 'session_open', 'bidding', 'awarded', 'done']
                for t in transitions:
                    if rec.state == target:
                        break
                    try:
                        if t == 'confirmed':
                            rec.action_confirm()
                        elif t == 'session_open':
                            rec.action_open_session()
                        elif t == 'bidding':
                            rec.action_start_bidding()
                        elif t == 'awarded':
                            rec.action_award()
                        elif t == 'done':
                            rec.action_done()
                    except Exception:
                        break
                count += 1
            except Exception as exc:
                _logger.warning('UAT auction create failed: %s', exc)

        return count

    # ------------------------------------------------------------------ #
    #  CHEQUE GENERATION — الشيكات                                         #
    # ------------------------------------------------------------------ #
    def _generate_cheques(self):
        count = 0
        OutgoingPO = self.env['port_said.outgoing_po']
        ChequeBook = self.env['port_said.cheque.book']

        # Create a cheque book first
        book = ChequeBook.search([('bank_name', '=', 'البنك الأهلي المصري — فرع بورسعيد')], limit=1)
        if not book:
            try:
                book = ChequeBook.create({
                    'bank_name': 'البنك الأهلي المصري — فرع بورسعيد',
                    'book_reference': f'UAT-BK-001',
                    'first_cheque_number': 1001,
                    'last_cheque_number': 1100,
                    'issue_date': FY_START,
                })
                book.action_activate()
            except Exception as exc:
                _logger.warning('UAT cheque book create failed: %s', exc)
                book = None

        journal = self._get_journal('bank')
        partner = self._get_or_create_vendor(VENDORS[0])

        scenarios = [
            (f'{UAT_BATCH} - صرف شيك — توريد أجهزة حاسب آلي', 85000.0, 'cleared'),
            (f'{UAT_BATCH} - صرف شيك — أعمال صيانة المبنى', 42000.0, 'sent'),
            (f'{UAT_BATCH} - صرف شيك — توريد مستلزمات نظافة', 18500.0, 'registered'),
            (f'{UAT_BATCH} - صرف شيك — خدمات استشارية', 95000.0, 'draft'),
            (f'{UAT_BATCH} - صرف شيك — توريد قطع غيار', 33000.0, 'cleared'),
        ]

        for i, (desc, amount, state) in enumerate(scenarios):
            existing = OutgoingPO.search([('notes', '=', desc)], limit=1)
            if existing:
                continue
            vals = {
                'partner_id': partner.id,
                'amount': amount,
                'payment_date': TODAY - timedelta(days=10 * (i + 1)),
                'payment_method': 'cheque',
                'notes': desc,
            }
            if book:
                vals['cheque_book_id'] = book.id
            if journal:
                vals['journal_id'] = journal.id
            try:
                rec = OutgoingPO.create(vals)
                if state in ('registered', 'sent', 'cleared'):
                    rec.action_register()
                if state in ('sent', 'cleared'):
                    rec.action_send()
                if state == 'cleared':
                    rec.action_clear()
                count += 1
            except Exception as exc:
                _logger.warning('UAT cheque create failed (%s): %s', desc, exc)

        return count

    # ------------------------------------------------------------------ #
    #  PENALTIES GENERATION — الجزاءات                                     #
    # ------------------------------------------------------------------ #
    def _generate_penalties(self):
        count = 0
        Penalty = self.env['port_said.penalty']
        Employee = self.env['hr.employee']

        employees = Employee.search([('active', '=', True)], limit=5)

        scenarios = [
            ('انقطاع عن العمل بدون إذن لمدة 3 أيام', 'warning', 'approved'),
            ('تأخر متكرر في الحضور', 'salary_deduction', 'recorded'),
            ('إهمال في تنفيذ المهام الوظيفية', 'warning', 'executed'),
            ('مخالفة لوائح استخدام الحاسب الآلي', 'warning', 'draft'),
            ('تغيب بدون إذن — إجراءات تأديبية', 'suspension', 'approved'),
        ]

        for i, (reason, penalty_type, state) in enumerate(scenarios):
            desc = f'{UAT_BATCH} - {reason}'
            existing = Penalty.search([('violation_description', '=', desc)], limit=1)
            if existing:
                continue
            vals = {
                'violation_description': desc,
                'penalty_type': penalty_type,
                'violation_date': TODAY - timedelta(days=20 * (i + 1)),
                'subject_type': 'employee',
                'notes': f'بيانات اختبار - {UAT_BATCH}',
            }
            if employees:
                vals['employee_id'] = employees[i % len(employees)].id
            try:
                rec = Penalty.create(vals)
                if state in ('recorded', 'approved', 'executed'):
                    rec.action_record()
                if state in ('approved', 'executed'):
                    rec.action_approve()
                if state == 'executed':
                    try:
                        rec.action_execute()
                    except Exception:
                        pass
                count += 1
            except Exception as exc:
                _logger.warning('UAT penalty create failed (%s): %s', reason, exc)

        return count

    # ------------------------------------------------------------------ #
    #  STOCKTAKING GENERATION — الجرد الحكومي                              #
    # ------------------------------------------------------------------ #
    def _generate_stocktaking(self):
        count = 0
        Session = self.env['stock.stocktaking.session']
        Warehouse = self.env['stock.warehouse']

        warehouse = Warehouse.search([], limit=1)
        if not warehouse:
            _logger.warning('UAT stocktaking: no warehouse found, skipping')
            return 0

        partner_chairman = self.env['res.users'].search([('active', '=', True)], limit=1).partner_id

        products = [
            ('ورق A4', 500.0, 480.0),
            ('حبر طابعة أسود', 20.0, 18.0),
            ('أقلام جاف زرقاء', 200.0, 220.0),
            ('دباسة مكتبية', 15.0, 12.0),
            ('ملفات كرتون', 100.0, 95.0),
        ]

        sessions = [
            (f'{UAT_BATCH} - جرد مخزن الديوان العام {TODAY.year}', 'validated'),
            (f'{UAT_BATCH} - جرد مخزن إدارة الطرق {TODAY.year}', 'done'),
            (f'{UAT_BATCH} - جرد مخزن إدارة النظافة {TODAY.year}', 'counting'),
            (f'{UAT_BATCH} - جرد مخزن مركز المعلومات {TODAY.year}', 'draft'),
        ]

        for i, (session_name, target_state) in enumerate(sessions):
            existing = Session.search([('name', 'ilike', UAT_BATCH)], limit=1)
            # Use unique notes field unavailable; check by stocktaking_date+warehouse combo
            existing = Session.search([
                ('notes', '=', session_name),
            ], limit=1)
            if existing:
                continue

            vals = {
                'stocktaking_date': TODAY - timedelta(days=30 * i),
                'fiscal_year': str(TODAY.year),
                'warehouse_id': warehouse.id,
                'notes': session_name,
                'committee_members': f'أحمد محمد، سامي علي، هدى إبراهيم — {UAT_BATCH}',
            }
            if partner_chairman:
                vals['committee_chairman_id'] = partner_chairman.id
                vals['storekeeper_id'] = partner_chairman.id

            try:
                session = Session.create(vals)
                if target_state != 'draft':
                    # Load stock then add lines manually
                    try:
                        session.action_load_stock()
                    except Exception:
                        # If action_load_stock unavailable, create lines manually
                        Line = self.env['stock.stocktaking.line']
                        for pname, sys_qty, phys_qty in products:
                            product = self._get_or_create_product(pname)
                            Line.create({
                                'session_id': session.id,
                                'product_id': product.id,
                                'system_qty': sys_qty,
                                'physical_qty': phys_qty,
                            })

                    if target_state in ('done', 'validated'):
                        try:
                            session.action_post()
                        except Exception:
                            pass
                    if target_state == 'validated':
                        try:
                            session.action_validate()
                        except Exception:
                            pass
                count += 1
            except Exception as exc:
                _logger.warning('UAT stocktaking create failed (%s): %s', session_name, exc)

        return count

    # ------------------------------------------------------------------ #
    #  FIXED ASSETS GENERATION — الأصول الثابتة                            #
    # ------------------------------------------------------------------ #
    def _generate_fixed_assets(self):
        count = 0
        Asset = self.env['port_said.fixed.asset']
        Category = self.env['port_said.asset.category']

        category = Category.search([], limit=1)
        if not category:
            _logger.warning('UAT fixed assets: no category found, trying to create one')
            try:
                category = Category.create({
                    'name': 'أجهزة ومعدات',
                    'depreciation_rate': 10.0,
                    'useful_life_years': 10,
                    'method': 'straight_line',
                })
            except Exception as exc:
                _logger.warning('UAT fixed asset category create failed: %s', exc)
                return 0

        assets = [
            ('سيارة خدمة كيا', 180000.0, '2020-03-15', 'active'),
            ('جهاز تكييف مركزي — ديوان عام', 45000.0, '2021-06-01', 'active'),
            ('مولد كهربائي احتياطي', 120000.0, '2019-09-10', 'suspended'),
            ('خادم شبكة IBM', 95000.0, '2022-01-20', 'active'),
            ('معدة رصف آسفلت', 650000.0, '2018-05-05', 'active'),
            ('سيارة نظافة مرسيدس', 380000.0, '2017-08-15', 'draft'),
        ]

        from datetime import date as date_type
        for i, (asset_name, value, acq_date_str, state) in enumerate(assets):
            desc = f'{UAT_BATCH} - {asset_name}'
            existing = Asset.search([('name', '=', desc)], limit=1)
            if existing:
                continue

            y, m, d = [int(x) for x in acq_date_str.split('-')]
            acq_date = date_type(y, m, d)
            vals = {
                'name': desc,
                'category_id': category.id,
                'purchase_value': value,
                'acquisition_date': acq_date,
                'activation_date': acq_date,
                'location': DEPARTMENTS[i % len(DEPARTMENTS)],
                'condition': 'good',
                'notes': f'بيانات اختبار - {UAT_BATCH}',
            }
            try:
                rec = Asset.create(vals)
                if state in ('active', 'suspended'):
                    rec.action_activate()
                if state == 'suspended':
                    rec.action_suspend()
                count += 1
            except Exception as exc:
                _logger.warning('UAT fixed asset create failed (%s): %s', asset_name, exc)

        return count
