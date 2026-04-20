# -*- coding: utf-8 -*-
import os
import json
from odoo import http
from odoo.http import request, Response
from datetime import date, timedelta


class PortSaidDashboard(http.Controller):

    @http.route('/portsaid/dashboard', type='http', auth='user', website=False)
    def dashboard_page(self, **kwargs):
        try:
            data = self._collect_data()
        except Exception as e:
            data = self._empty_data()
            data['_error'] = str(e)

        data_json = json.dumps(data, ensure_ascii=False, default=str)

        html_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'static', 'src', 'dashboard.html'
        ))

        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
        except Exception as e:
            return Response(
                f'<h1>Dashboard Error</h1><p>Cannot read HTML file: {e}</p>'
                f'<p>Path: {html_path}</p>',
                content_type='text/html;charset=utf-8',
                status=500
            )

        html = html.replace(
            '/* __ODOO_DATA_PLACEHOLDER__ */',
            f'window.ODOO_DATA = {data_json};'
        )
        return Response(html, content_type='text/html;charset=utf-8')

    @http.route('/portsaid/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        try:
            return self._collect_data()
        except Exception as e:
            pass

        # ── Finance & Accounting KPIs ──────────────────────────────
        finance = {}
        try:
            # دفتر 55
            D55 = env['port_said.daftar55'].sudo()
            d55_states = ['draft','received','reviewed','cleared','posted','archived']
            for s in d55_states:
                finance[f'd55_{s}'] = sc('port_said.daftar55', [('state','=',s)])
            finance['daftar55_count'] = sum(finance[f'd55_{s}'] for s in d55_states)
            top_recs = D55.search([('state','in',['posted','archived','cleared'])], limit=10, order='amount_gross desc')
            finance['total_payments'] = sum(r.amount_gross or 0 for r in D55.search([('state','in',['posted','archived'])]))
            finance['top_payments'] = [{'seq': r.sequence_number, 'dept': r.department_name or '—',
                'amount': r.amount_gross or 0, 'state': r.state} for r in top_recs]
        except Exception:
            pass

        try:
            # الارتباطات
            COM = env['port_said.commitment'].sudo()
            c_states = ['draft','submitted','approved','reserved','cleared','paid']
            for s in c_states:
                finance[f'c_{s}'] = sc('port_said.commitment', [('state','=',s)])
            finance['commitments_total'] = sum(finance[f'c_{s}'] for s in c_states)
            finance['commitments_approved'] = finance.get('c_approved', 0) + finance.get('c_reserved', 0) + finance.get('c_cleared', 0)
            finance['commitments_reserved'] = finance.get('c_reserved', 0)
            active_coms = COM.search([('state','in',['approved','reserved','cleared'])])
            finance['commitments_amount'] = sum(r.amount_requested or 0 for r in active_coms)
            finance['available_balance'] = sum(r.available_balance or 0 for r in active_coms)
        except Exception:
            pass

        try:
            # عقود الإيجار والمزادات
            leases = env['auction.lease.contract'].sudo().search([('state','=','active')])
            finance['lease_active'] = len(leases)
            finance['lease_collected'] = sum(r.total_collected or 0 for r in leases)
            finance['lease_outstanding'] = sum(r.total_outstanding or 0 for r in leases)
            finance['auction_revenue'] = sum(r.contract_value or 0 for r in leases)
            finance['overdue_payments'] = pyo
            finance['py_paid'] = pypa
            finance['py_pending'] = pyp
            finance['py_overdue'] = pyo
            finance['py_partial'] = pypr
        except Exception:
            pass

        return {'error': str(e), **self._empty_data()}

    def _safe_count(self, model, domain):
        try:
            return request.env[model].sudo().search_count(domain)
        except Exception:
            return 0

    def _empty_data(self):
        empty_states = {s: 0 for s in
            ['draft','technical_open','financial_open','adjudicated',
             'awarded','po_created','cancelled']}
        # ── Finance & Accounting KPIs ──────────────────────────────
        finance = {}
        try:
            # دفتر 55
            D55 = env['port_said.daftar55'].sudo()
            d55_states = ['draft','received','reviewed','cleared','posted','archived']
            for s in d55_states:
                finance[f'd55_{s}'] = sc('port_said.daftar55', [('state','=',s)])
            finance['daftar55_count'] = sum(finance[f'd55_{s}'] for s in d55_states)
            top_recs = D55.search([('state','in',['posted','archived','cleared'])], limit=10, order='amount_gross desc')
            finance['total_payments'] = sum(r.amount_gross or 0 for r in D55.search([('state','in',['posted','archived'])]))
            finance['top_payments'] = [{'seq': r.sequence_number, 'dept': r.department_name or '—',
                'amount': r.amount_gross or 0, 'state': r.state} for r in top_recs]
        except Exception:
            pass

        try:
            # الارتباطات
            COM = env['port_said.commitment'].sudo()
            c_states = ['draft','submitted','approved','reserved','cleared','paid']
            for s in c_states:
                finance[f'c_{s}'] = sc('port_said.commitment', [('state','=',s)])
            finance['commitments_total'] = sum(finance[f'c_{s}'] for s in c_states)
            finance['commitments_approved'] = finance.get('c_approved', 0) + finance.get('c_reserved', 0) + finance.get('c_cleared', 0)
            finance['commitments_reserved'] = finance.get('c_reserved', 0)
            active_coms = COM.search([('state','in',['approved','reserved','cleared'])])
            finance['commitments_amount'] = sum(r.amount_requested or 0 for r in active_coms)
            finance['available_balance'] = sum(r.available_balance or 0 for r in active_coms)
        except Exception:
            pass

        try:
            # عقود الإيجار والمزادات
            leases = env['auction.lease.contract'].sudo().search([('state','=','active')])
            finance['lease_active'] = len(leases)
            finance['lease_collected'] = sum(r.total_collected or 0 for r in leases)
            finance['lease_outstanding'] = sum(r.total_outstanding or 0 for r in leases)
            finance['auction_revenue'] = sum(r.contract_value or 0 for r in leases)
            finance['overdue_payments'] = pyo
            finance['py_paid'] = pypa
            finance['py_pending'] = pyp
            finance['py_overdue'] = pyo
            finance['py_partial'] = pypr
        except Exception:
            pass

        return {
            'committees':   {'total':0,'active':0,'draft':0,'closed':0,'detail':[]},
            'adjudication': {'total':0,'by_state':empty_states,'total_estimated':0,
                             'total_awarded':0,'saving_pct':0,'tender_types':{},'detail':[]},
            'permits':      {'total':0,'draft':0,'posted':0,'cancelled':0,
                             'inspection':{'done':0,'rejected':0,'draft':0},'detail':[]},
            'stocktaking':  {'total':0,'draft':0,'counting':0,'done':0,'validated':0,
                             'surplus_pct':0,'deficit_pct':0,'detail':[]},
            'custody':      {'total':0,'active':0,'transferred':0,'returned':0,
                             'cancelled':0,'overdue':0,'total_value':0,
                             'by_type':{'personal':0,'shared':0,'transferred':0},
                             'detail':[],'overdue_detail':[]},
            'auction':      {'total':0,'by_state':{s:0 for s in
                                ['draft','confirmed','session_open','bidding',
                                 'awarded','done','cancelled']},
                             'lease':{'active':0,'expired':0,'draft':0},
                             'payments':{'pending':0,'paid':0,'overdue':0,'partial':0},
                             'detail':[]},
            'monthly':      [{'label': m, 'count': 0} for m in
                             ['يناير','فبراير','مارس','أبريل','مايو','يونيو',
                              'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'][-6:]],
            'finance':      {
                'total_payments':0,'daftar55_count':0,
                'commitments_total':0,'commitments_approved':0,'commitments_reserved':0,
                'commitments_amount':0,'available_balance':0,
                'auction_revenue':0,'lease_active':0,'lease_outstanding':0,
                'lease_collected':0,'overdue_payments':0,
                'c_draft':0,'c_submitted':0,'c_approved':0,'c_reserved':0,'c_cleared':0,'c_paid':0,
                'd55_draft':0,'d55_received':0,'d55_reviewed':0,'d55_cleared':0,'d55_posted':0,'d55_archived':0,
                'py_paid':0,'py_pending':0,'py_overdue':0,'py_partial':0,
                'top_payments':[],
            },
            'alerts':       [],
            'meta':         {'date': str(date.today()), 'total_ops': 0},
        }

    def _collect_data(self):
        env   = request.env
        today = date.today()
        sc    = self._safe_count

        # ── Committees ──────────────────────────────────────────
        ca = sc('procurement.committee', [('state','=','active')])
        cd = sc('procurement.committee', [('state','=','draft')])
        cc = sc('procurement.committee', [('state','=','closed')])

        c_detail = []
        try:
            for r in env['procurement.committee'].sudo().search(
                    [], limit=20, order='id desc'):
                c_detail.append({
                    'ref':   r.ref or str(r.id),
                    'name':  r.name or '',
                    'type':  {'technical':'فنية','financial':'مالية',
                              'opening':'فض مظاريف','inspection':'فحص'
                              }.get(r.committee_type or '', '—'),
                    'state': {'draft':'مسودة','active':'نشطة','closed':'منتهية'
                              }.get(r.state or '', r.state or ''),
                    'members': len(r.member_ids),
                    'date':  str(r.formation_date) if r.formation_date else '—',
                })
        except Exception:
            pass

        # ── Adjudication ─────────────────────────────────────────
        states_adj = ['draft','technical_open','financial_open',
                      'adjudicated','awarded','po_created','cancelled']
        ast_ = {s: sc('procurement.adjudication', [('state','=',s)])
                for s in states_adj}
        atot = sum(ast_.values())

        t_est = t_awd = sav = 0
        tt = {}
        a_detail = []
        try:
            arecs = env['procurement.adjudication'].sudo().search(
                [], limit=20, order='id desc')
            t_est = sum(r.estimated_value or 0 for r in arecs)
            t_awd = sum(r.awarded_amount  or 0 for r in arecs)
            sav   = round((t_est - t_awd) / t_est * 100, 1) if t_est else 0
            for r in env['procurement.adjudication'].sudo().search([]):
                k = r.tender_type or 'other'
                tt[k] = tt.get(k, 0) + 1
            tl = {'public':'مناقصة عامة','local':'مناقصة محلية',
                  'limited':'مناقصة محدودة','negotiation':'ممارسة',
                  'direct_supply':'أمر مباشر','direct_private':'اتفاق مباشر'}
            sl = {'draft':'مسودة','technical_open':'مظاريف فنية مفتوحة',
                  'financial_open':'مظاريف مالية مفتوحة',
                  'adjudicated':'تمت المقارنة','awarded':'إخطار الترسية',
                  'po_created':'أمر شراء صادر','cancelled':'ملغي'}
            a_detail = [{
                'ref':      r.ref or r.name or '',
                'name':     r.name or '',
                'state':    sl.get(r.state, r.state or ''),
                'tender':   tl.get(r.tender_type or '', r.tender_type or '—'),
                'estimated': r.estimated_value or 0,
                'awarded':   r.awarded_amount  or 0,
                'supplier':  r.awarded_supplier_id.name
                             if r.awarded_supplier_id else '—',
            } for r in arecs]
        except Exception:
            pass

        # ── Permits ──────────────────────────────────────────────
        pd = sc('stock.addition.permit', [('state','=','draft')])
        pp = sc('stock.addition.permit', [('state','=','posted')])
        pc = sc('stock.addition.permit', [('state','=','cancel')])
        id_= sc('stock.inspection.report', [('state','=','done')])
        ir_= sc('stock.inspection.report', [('state','=','rejected')])
        idr= sc('stock.inspection.report', [('state','=','draft')])

        p_detail = []
        try:
            for r in env['stock.addition.permit'].sudo().search(
                    [], limit=15, order='id desc'):
                p_detail.append({
                    'ref':  r.ref or str(r.id),
                    'name': r.name or '',
                    'state': {'draft':'مسودة','posted':'مرحّل','cancel':'ملغي'
                              }.get(r.state or '', r.state or ''),
                    'qty':  r.qty or 0,
                    'warehouse': r.warehouse_id.name if r.warehouse_id else '—',
                    'date': str(r.date) if r.date else '—',
                })
        except Exception:
            pass

        # ── Stocktaking ───────────────────────────────────────────
        sd  = sc('stock.stocktaking.session', [('state','=','draft')])
        sc_ = sc('stock.stocktaking.session', [('state','=','counting')])
        sdn = sc('stock.stocktaking.session', [('state','=','done')])
        sv  = sc('stock.stocktaking.session', [('state','=','validated')])

        sp = dp = 0
        s_detail = []
        try:
            ltot  = sc('stock.stocktaking.line', [])
            lsurp = sc('stock.stocktaking.line', [('difference_type','=','surplus')])
            ldef  = sc('stock.stocktaking.line', [('difference_type','=','deficit')])
            sp = round(lsurp / ltot * 100, 1) if ltot else 0
            dp = round(ldef  / ltot * 100, 1) if ltot else 0
            for r in env['stock.stocktaking.session'].sudo().search(
                    [], limit=10, order='id desc'):
                s_detail.append({
                    'name':     r.name or '',
                    'state':    {'draft':'مسودة','counting':'جاري الجرد',
                                 'done':'منتهي','validated':'معتمد'
                                 }.get(r.state or '', r.state or ''),
                    'warehouse': r.warehouse_id.name if r.warehouse_id else '—',
                    'year':     r.fiscal_year or '—',
                    'chairman': r.committee_chairman_id.name
                                if r.committee_chairman_id else '—',
                })
        except Exception:
            pass

        # ── Custody ───────────────────────────────────────────────
        cua = sc('custody.assignment', [('state','=','active')])
        cut = sc('custody.assignment', [('state','=','transferred')])
        cur = sc('custody.assignment', [('state','=','returned')])
        cuc = sc('custody.assignment', [('state','=','cancelled')])

        cuov = cuval = 0
        cup = cush = cutr = 0
        ovd_d = cu_d = []
        try:
            ovd  = env['custody.assignment'].sudo().search([
                ('state','in',['active','transferred']),
                ('expected_return_date','<', today.isoformat()),
            ])
            cuov = len(ovd)
            acus = env['custody.assignment'].sudo().search(
                [('state','in',['active','transferred'])])
            cuval = sum(c.estimated_value or 0 for c in acus)
            cup  = sc('custody.assignment',
                      [('custody_type','=','personal'),
                       ('state','in',['active','transferred'])])
            cush = sc('custody.assignment',
                      [('custody_type','=','shared'),
                       ('state','in',['active','transferred'])])
            cutr = sc('custody.assignment',
                      [('custody_type','=','transferred'),
                       ('state','in',['active','transferred'])])
            ovd_d = [{'ref': c.name,
                      'employee': c.employee_id.name if c.employee_id else '—',
                      'value': c.estimated_value or 0,
                      'due':   str(c.expected_return_date)
                               if c.expected_return_date else '—'}
                     for c in ovd[:10]]
            cu_d  = [{'ref': c.name,
                      'employee': c.employee_id.name if c.employee_id else '—',
                      'state': {'draft':'مسودة','active':'نشطة',
                                'transferred':'محوّلة','returned':'مُرتجعة',
                                'cancelled':'ملغية'}.get(c.state, c.state),
                      'value': c.estimated_value or 0,
                      'due':   str(c.expected_return_date)
                               if c.expected_return_date else '—'}
                     for c in env['custody.assignment'].sudo().search(
                         [('state','in',['active','transferred'])],
                         limit=20, order='id desc')]
        except Exception:
            pass

        # ── Auction ───────────────────────────────────────────────
        au_states = ['draft','confirmed','session_open','bidding',
                     'awarded','done','cancelled']
        aus = {s: sc('auction.request', [('state','=',s)]) for s in au_states}
        la = sc('auction.lease.contract', [('state','=','active')])
        le = sc('auction.lease.contract', [('state','=','expired')])
        ld = sc('auction.lease.contract', [('state','=','draft')])
        pyp = sc('payment.schedule.line', [('state','=','pending')])
        pypa= sc('payment.schedule.line', [('state','=','paid')])
        pyo = sc('payment.schedule.line', [('state','=','overdue')])
        pypr= sc('payment.schedule.line', [('state','=','partial')])

        au_d = []
        try:
            ausl = {'draft':'مسودة','confirmed':'معتمد',
                    'session_open':'الجلسة مفتوحة','bidding':'تسجيل العروض',
                    'awarded':'تم الترسية','done':'منتهي','cancelled':'ملغي'}
            au_d = [{'ref':  r.ref or r.name or '',
                     'name': r.name or '',
                     'type': 'بيع' if r.auction_type == 'sale' else 'إيجار',
                     'state': ausl.get(r.state, r.state or ''),
                     'estimated': r.estimated_value or 0,
                     'awarded':   r.awarded_amount  or 0}
                    for r in env['auction.request'].sudo().search(
                        [], limit=10, order='id desc')]
        except Exception:
            pass

        # ── Monthly trend ─────────────────────────────────────────
        monthly = []
        ar_m = ['يناير','فبراير','مارس','أبريل','مايو','يونيو',
                'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
        try:
            for i in range(5, -1, -1):
                ms = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
                me = (ms.replace(month=ms.month % 12 + 1, day=1)
                      if ms.month < 12
                      else ms.replace(year=ms.year + 1, month=1, day=1))
                cnt = (
                    sc('procurement.committee',
                       [('formation_date','>=',str(ms)),('formation_date','<',str(me))]) +
                    sc('procurement.adjudication',
                       [('date','>=',str(ms)),('date','<',str(me))]) +
                    sc('stock.addition.permit',
                       [('date','>=',str(ms)),('date','<',str(me))])
                )
                monthly.append({'label': ar_m[ms.month - 1], 'count': cnt})
        except Exception:
            monthly = [{'label': ar_m[i], 'count': 0} for i in range(6)]

        # ── Alerts ────────────────────────────────────────────────
        alerts = []
        if cuov:  alerts.append({'type':'danger', 'icon':'⚠️',
            'title':f'{cuov} عهدات متأخرة الاسترداد',
            'desc':'تجاوزت تاريخ الاسترداد المتوقع'})
        if pyo:   alerts.append({'type':'danger', 'icon':'💸',
            'title':f'{pyo} دفعات إيجار متأخرة',
            'desc':'مطلوب متابعة التحصيل'})
        if sdn:   alerts.append({'type':'warning','icon':'📊',
            'title':f'{sdn} جلسة جرد بانتظار الاعتماد',
            'desc':'رئيس لجنة الجرد لم يعتمد'})
        if pd:    alerts.append({'type':'warning','icon':'📦',
            'title':f'{pd} أذونات إضافة بانتظار الترحيل',
            'desc':'مدير المخازن لم يرحّل'})
        if cd:    alerts.append({'type':'info',   'icon':'👥',
            'title':f'{cd} لجنة في حالة مسودة',
            'desc':'لم يتم تفعيلها'})

        total = (ca+cd+cc+atot+pd+pp+pc+sd+sc_+sdn+sv
                 +cua+cut+cur+cuc+sum(aus.values()))

        # ── Finance & Accounting KPIs ──────────────────────────────
        finance = {}
        try:
            # دفتر 55
            D55 = env['port_said.daftar55'].sudo()
            d55_states = ['draft','received','reviewed','cleared','posted','archived']
            for s in d55_states:
                finance[f'd55_{s}'] = sc('port_said.daftar55', [('state','=',s)])
            finance['daftar55_count'] = sum(finance[f'd55_{s}'] for s in d55_states)
            top_recs = D55.search([('state','in',['posted','archived','cleared'])], limit=10, order='amount_gross desc')
            finance['total_payments'] = sum(r.amount_gross or 0 for r in D55.search([('state','in',['posted','archived'])]))
            finance['top_payments'] = [{'seq': r.sequence_number, 'dept': r.department_name or '—',
                'amount': r.amount_gross or 0, 'state': r.state} for r in top_recs]
        except Exception:
            pass

        try:
            # الارتباطات
            COM = env['port_said.commitment'].sudo()
            c_states = ['draft','submitted','approved','reserved','cleared','paid']
            for s in c_states:
                finance[f'c_{s}'] = sc('port_said.commitment', [('state','=',s)])
            finance['commitments_total'] = sum(finance[f'c_{s}'] for s in c_states)
            finance['commitments_approved'] = finance.get('c_approved', 0) + finance.get('c_reserved', 0) + finance.get('c_cleared', 0)
            finance['commitments_reserved'] = finance.get('c_reserved', 0)
            active_coms = COM.search([('state','in',['approved','reserved','cleared'])])
            finance['commitments_amount'] = sum(r.amount_requested or 0 for r in active_coms)
            finance['available_balance'] = sum(r.available_balance or 0 for r in active_coms)
        except Exception:
            pass

        try:
            # عقود الإيجار والمزادات
            leases = env['auction.lease.contract'].sudo().search([('state','=','active')])
            finance['lease_active'] = len(leases)
            finance['lease_collected'] = sum(r.total_collected or 0 for r in leases)
            finance['lease_outstanding'] = sum(r.total_outstanding or 0 for r in leases)
            finance['auction_revenue'] = sum(r.contract_value or 0 for r in leases)
            finance['overdue_payments'] = pyo
            finance['py_paid'] = pypa
            finance['py_pending'] = pyp
            finance['py_overdue'] = pyo
            finance['py_partial'] = pypr
        except Exception:
            pass

        return {
            'committees':   {'total':ca+cd+cc,'active':ca,'draft':cd,
                             'closed':cc,'detail':c_detail},
            'adjudication': {'total':atot,'by_state':ast_,
                             'total_estimated':t_est,'total_awarded':t_awd,
                             'saving_pct':sav,'tender_types':tt,'detail':a_detail},
            'permits':      {'total':pd+pp+pc,'draft':pd,'posted':pp,'cancelled':pc,
                             'inspection':{'done':id_,'rejected':ir_,'draft':idr},
                             'detail':p_detail},
            'stocktaking':  {'total':sd+sc_+sdn+sv,'draft':sd,'counting':sc_,
                             'done':sdn,'validated':sv,
                             'surplus_pct':sp,'deficit_pct':dp,'detail':s_detail},
            'custody':      {'total':cua+cut+cur+cuc,'active':cua,
                             'transferred':cut,'returned':cur,'cancelled':cuc,
                             'overdue':cuov,'total_value':cuval,
                             'by_type':{'personal':cup,'shared':cush,'transferred':cutr},
                             'detail':cu_d,'overdue_detail':ovd_d},
            'auction':      {'total':sum(aus.values()),'by_state':aus,
                             'lease':{'active':la,'expired':le,'draft':ld},
                             'payments':{'pending':pyp,'paid':pypa,
                                         'overdue':pyo,'partial':pypr},
                             'detail':au_d},
            'finance':      finance,
            'monthly':      monthly,
            'alerts':       alerts,
            'meta':         {'date':str(today),'total_ops':total},
        }
