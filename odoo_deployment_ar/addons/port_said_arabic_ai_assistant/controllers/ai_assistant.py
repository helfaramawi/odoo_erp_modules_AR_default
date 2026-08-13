# -*- coding: utf-8 -*-
import json
import re
from datetime import date, timedelta

import requests

from odoo import http, fields
from odoo.http import request, Response


class PortSaidArabicAIAssistant(http.Controller):
    ALLOWED_PREFIXES = ('port_said.', 'stock.', 'procurement.', 'l10n_eg.', 'eta.', 'c10.')
    EXTRA_ALLOWED_MODELS = {
        'res.partner', 'hr.employee', 'account.move', 'account.move.line',
        'purchase.order', 'purchase.order.line', 'product.product',
        'product.template', 'account.payment', 'account.bank.statement.line',
    }
    DENIED_MODELS = {
        'ir.config_parameter', 'ir.attachment', 'ir.model', 'ir.model.fields',
        'ir.model.access', 'res.users', 'res.users.apikeys',
        'res.config.settings', 'mail.message', 'mail.mail',
    }
    SENSITIVE_FIELD_PARTS = (
        'password', 'secret', 'token', 'api_key', 'apikey', 'private',
        'signature', 'certificate', 'client_secret', 'access_token',
        'refresh_token', 'hash', 'salt', 'key',
    )
    FIELD_PRIORITY = (
        'name', 'display_name', 'sequence_number', 'commitment_number',
        'cheque_number', 'po_number', 'number', 'reference', 'ref',
        'partner_id', 'vendor_id', 'beneficiary_id', 'employee_id',
        'department_name', 'subject_display_name',
        'amount', 'total_amount', 'amount_total', 'total_budget', 'total_actual',
        'variance_amount', 'variance_percent',
        'state', 'date', 'issue_date', 'received_date', 'due_date',
        'create_date',
    )
    MODEL_ALIASES = {
        'الموردين': 'res.partner', 'موردين': 'res.partner', 'المورد': 'res.partner', 'مورد': 'res.partner',
        'العملاء': 'res.partner', 'عميل': 'res.partner',
        'الموظفين': 'hr.employee', 'موظف': 'hr.employee',
        'اوامر الشراء': 'purchase.order', 'امر شراء': 'purchase.order', 'أمر شراء': 'purchase.order',
        'فواتير': 'account.move', 'فاتورة': 'account.move', 'فاتوره': 'account.move',
        'شيكات': 'port_said.cheque', 'شيك': 'port_said.cheque',
        'جزاءات': 'port_said.penalty', 'جزاء': 'port_said.penalty',
        'ارتباطات': 'port_said.commitment', 'ارتباط': 'port_said.commitment',
        'الموازنة': 'port_said.budget.plan', 'الموازنه': 'port_said.budget.plan', 'موازنة': 'port_said.budget.plan', 'موازنه': 'port_said.budget.plan',
        'سلفة': 'port_said.advance', 'سلفه': 'port_said.advance', 'سلف': 'port_said.advance',
        'eta': 'eta.invoice', 'الفاتورة الالكترونية': 'eta.invoice', 'الفاتوره الالكترونيه': 'eta.invoice',
        'المنتجات': 'product.product', 'منتجات': 'product.product', 'منتج': 'product.product',
        'دفتر 55': 'port_said.daftar55', 'دفتر 224': 'port_said.daftar224',
    }

    @http.route('/portsaid/ai_assistant', type='http', auth='user', website=False)
    def assistant_page(self, **kwargs):
        html = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>اسألني بالعربي — Ollama Fixed</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0D1B2A;color:#F0ECE3;font-family:Tahoma,Arial,sans-serif;direction:rtl}
.wrap{min-height:100vh;padding:22px;background:radial-gradient(ellipse 80% 50% at 20% 0%,rgba(201,168,76,.08),transparent 60%),#0D1B2A}
.header{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:18px;border-bottom:1px solid rgba(201,168,76,.22);padding-bottom:14px}
.brand{display:flex;align-items:center;gap:12px}.logo{width:48px;height:48px;border:2px solid #C9A84C;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(201,168,76,.1);font-size:22px}
h1{margin:0;color:#E8C87A;font-size:22px}.sub{color:#9BAAB8;font-size:13px;margin-top:4px}.back{color:#E8C87A;text-decoration:none;border:1px solid rgba(201,168,76,.4);padding:9px 13px;border-radius:10px}
.panel{background:rgba(255,255,255,.04);border:1px solid rgba(201,168,76,.22);border-radius:16px;padding:16px;margin-bottom:14px}.askrow{display:flex;gap:10px}
#q{flex:1;background:rgba(255,255,255,.06);border:1px solid rgba(201,168,76,.25);border-radius:12px;color:#fff;padding:14px;font-size:15px;outline:none}
#ask{border:0;background:#C9A84C;color:#0D1B2A;font-weight:bold;border-radius:12px;padding:0 20px;cursor:pointer}#ask:disabled{opacity:.55}
.examples{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.ex{background:rgba(201,168,76,.09);border:1px solid rgba(201,168,76,.25);color:#E8C87A;border-radius:20px;padding:7px 11px;font-size:12px;cursor:pointer}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:12px}.card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:12px}
.lbl{color:#9BAAB8;font-size:11px}.val{font-size:16px;color:#E8C87A;font-weight:bold;margin-top:4px}.summary{line-height:1.8;color:#F0ECE3;background:rgba(39,169,154,.08);border:1px solid rgba(39,169,154,.25);border-radius:12px;padding:12px;margin-bottom:12px}
.err{background:rgba(231,76,60,.1);border-color:rgba(231,76,60,.35);color:#ffb3aa}table{width:100%;border-collapse:collapse;background:rgba(255,255,255,.03);border-radius:12px;overflow:hidden}
th,td{padding:9px;border-bottom:1px solid rgba(255,255,255,.07);font-size:12px;text-align:right;vertical-align:top}th{color:#E8C87A;background:rgba(201,168,76,.08)}
.small{font-size:12px;color:#9BAAB8;margin-top:8px}.badge{display:inline-block;border-radius:20px;padding:3px 8px;background:rgba(33,150,243,.16);color:#90CAF9}
.badge2{display:inline-block;border-radius:20px;padding:3px 8px;background:rgba(201,168,76,.16);color:#E8C87A}
@media(max-width:700px){.askrow{flex-direction:column}#ask{padding:12px}.header{flex-direction:column;align-items:flex-start}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header"><div class="brand"><div class="logo">🤖</div><div><h1>اسألني بالعربي</h1><div class="sub">Ollama JSON Fixed + Local Router — قراءة آمنة فقط</div></div></div><a class="back" href="/portsaid/dashboard">← العودة للوحة القيادة</a></div>
  <div class="panel">
    <div class="askrow"><input id="q" placeholder="اكتب أي سؤال عن بيانات Odoo..."/><button id="ask">اسأل</button></div>
    <div class="examples">
      <button class="ex">ما هو عدد الموردين؟</button><button class="ex">اعرض الموردين</button><button class="ex">اعرض أوامر الشراء</button>
      <button class="ex">ما هي أكبر 10 مبالغ في الشيكات؟</button><button class="ex">إيه إجمالي الجزاءات الربع ده؟</button>
      <button class="ex">السلف المتأخرة كام؟</button><button class="ex">اعرض فواتير ETA المرفوضة</button>
    </div>
    <div class="small">الأسئلة الواضحة تعمل Local. Ollama يستخدم فقط عند ضعف الفهم.</div>
  </div>
  <div id="out"></div>
</div>
<script>
const q=document.getElementById('q'),askBtn=document.getElementById('ask'),out=document.getElementById('out');
document.querySelectorAll('.ex').forEach(b=>b.addEventListener('click',()=>{q.value=b.textContent;ask()}));
askBtn.addEventListener('click',ask);q.addEventListener('keydown',e=>{if(e.key==='Enter')ask()});
function esc(v){if(v===null||v===undefined)return'';if(Array.isArray(v))return esc(v[1]||v[0]);return String(v).replace(/[&<>"']/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]))}
async function ask(){const question=q.value.trim();if(!question)return;askBtn.disabled=true;askBtn.textContent='جاري التحليل...';out.innerHTML='<div class="panel">جاري تحليل السؤال...</div>';try{const r=await fetch('/ai/nl_to_orm',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},body:JSON.stringify({jsonrpc:'2.0',method:'call',id:Date.now(),params:{question}})});const j=await r.json();if(j.error)throw new Error(j.error.data?.message||j.error.message||'Server error');render(j.result)}catch(e){out.innerHTML='<div class="panel summary err">حدث خطأ: '+esc(e.message)+'</div>'}finally{askBtn.disabled=false;askBtn.textContent='اسأل'}}
function render(res){if(!res.success){out.innerHTML='<div class="panel summary err">'+esc(res.message||'لم أستطع فهم السؤال')+'</div>';return}let html='<div class="panel"><div class="summary">'+esc(res.answer_summary||'')+'</div><div class="meta">';
html+='<div class="card"><div class="lbl">الموديل</div><div class="val">'+esc(res.model_label||res.model)+'</div></div>';
html+='<div class="card"><div class="lbl">نوع الاستعلام</div><div class="val">'+esc(res.query_type)+'</div></div>';
html+='<div class="card"><div class="lbl">عدد النتائج</div><div class="val">'+esc(res.count)+'</div></div>';
html+='<div class="card"><div class="lbl">الثقة</div><div class="val">'+esc(res.confidence||0)+'%</div></div>';
html+='<div class="card"><div class="lbl">المصدر</div><div class="val">'+(res.used_ollama?'<span class="badge2">Ollama</span>':'<span class="badge">Local</span>')+'</div></div>';
html+='<div class="card"><div class="lbl">الأمان</div><div class="val"><span class="badge">Read-only</span></div></div></div>';
if(res.rows&&res.rows.length){const fields=res.fields||Object.keys(res.rows[0]);html+='<table><thead><tr>'+fields.map(f=>'<th>'+esc(res.field_labels?.[f]||f)+'</th>').join('')+'</tr></thead><tbody>';for(const row of res.rows){html+='<tr>'+fields.map(f=>'<td>'+esc(row[f])+'</td>').join('')+'</tr>'}html+='</tbody></table>'}else{html+='<div class="small">لا توجد سجلات مطابقة.</div>'}
html+='<div class="small">Domain: '+esc(JSON.stringify(res.domain||[]))+'</div></div>';out.innerHTML=html}
</script>
</body></html>"""
        return Response(html, content_type='text/html;charset=utf-8')

    @http.route('/ai/nl_to_orm', type='json', auth='user', methods=['POST'], csrf=False)
    def nl_to_orm(self, question=None, **kwargs):
        question = (question or '').strip()
        log_vals = {'question': question, 'normalized_question': self._normalize_ar(question), 'success': False, 'query_type': 'unknown'}
        try:
            if not question:
                return {'success': False, 'message': 'من فضلك اكتب السؤال أولاً.'}

            plan = self._plan_query(question)

            if (not plan.get('success')) or plan.get('confidence', 0) < 30:
                ollama_plan = self._ollama_plan(question)
                if ollama_plan.get('success'):
                    plan = ollama_plan
                elif plan.get('success'):
                    # Keep local plan if Ollama failed.
                    plan['answer_summary'] = (plan.get('answer_summary') or '') + ' — تم تجاهل Ollama لأن رده لم يكن صالحاً.'
                else:
                    plan['message'] = ollama_plan.get('message') or plan.get('message')

            log_vals.update({
                'model_name': plan.get('model'),
                'model_description': plan.get('model_label'),
                'query_type': plan.get('query_type', 'unknown'),
                'domain_text': json.dumps(plan.get('domain', []), ensure_ascii=False, default=str),
                'fields_text': json.dumps(plan.get('fields', []), ensure_ascii=False),
                'confidence': plan.get('confidence', 0.0),
                'used_ollama': plan.get('used_ollama', False),
                'ollama_raw': plan.get('ollama_raw', ''),
            })

            if not plan.get('success'):
                log_vals['error_message'] = plan.get('message')
                self._create_log(log_vals)
                return plan

            model_name = plan['model']
            Model = request.env[model_name].sudo()
            fields_list = plan['fields']
            domain = plan['domain']
            query_type = plan['query_type']
            limit = plan.get('limit', 50)

            if query_type == 'count':
                count = Model.search_count(domain)
                rows = [{'count': count}]
                summary = plan.get('answer_summary') or 'عدد السجلات المطابقة هو: %s' % count
            elif query_type == 'read_group':
                rows = Model.read_group(domain, plan.get('aggregates') or [], plan.get('groupby') or [], lazy=False)
                count = len(rows)
                summary = plan.get('answer_summary') or 'تم تنفيذ التجميع وعرض النتائج.'
            else:
                rows = Model.search_read(domain, fields_list, limit=limit, order=plan.get('order') or 'id desc')
                count = len(rows)
                summary = plan.get('answer_summary') or 'تم العثور على %s سجل مطابق.' % count

            log_vals.update({'answer_summary': summary, 'result_count': count, 'success': True})
            self._create_log(log_vals)

            return {
                'success': True,
                'question': question,
                'model': model_name,
                'model_label': plan.get('model_label') or model_name,
                'query_type': query_type,
                'domain': domain,
                'fields': fields_list if query_type != 'count' else ['count'],
                'field_labels': self._field_labels(model_name, fields_list),
                'rows': rows,
                'count': count,
                'confidence': round(plan.get('confidence', 0.0), 1),
                'used_ollama': plan.get('used_ollama', False),
                'answer_summary': summary,
            }
        except Exception as e:
            log_vals['error_message'] = str(e)
            self._create_log(log_vals)
            return {'success': False, 'message': 'حدث خطأ أثناء تنفيذ السؤال: %s' % str(e)}

    def _create_log(self, vals):
        try:
            request.env['port_said.ai.assistant.log'].sudo().create(vals)
        except Exception:
            pass

    def _normalize_ar(self, text):
        text = (text or '').strip().lower()
        replacements = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ة': 'ه', 'ى': 'ي', 'ؤ': 'و', 'ئ': 'ي', 'إيه': 'ايه', 'أيه': 'ايه', 'فين': 'اين', 'كام': 'كم'}
        for a, b in replacements.items():
            text = text.replace(a, b)
        return re.sub(r'\s+', ' ', text)

    def _tokens(self, text):
        q = self._normalize_ar(text)
        stop = {'ما', 'هو', 'هي', 'من', 'في', 'على', 'عن', 'الى', 'هذا', 'هذه', 'اللي', 'التي', 'مع', 'كل'}
        return [t for t in re.split(r'[\s,،؟?؛;:]+', q) if len(t) > 1 and t not in stop]

    def _is_allowed_model(self, model_name):
        if not model_name or model_name in self.DENIED_MODELS:
            return False
        if model_name in self.EXTRA_ALLOWED_MODELS:
            return True
        return model_name.startswith(self.ALLOWED_PREFIXES)

    def _safe_fields_for_model(self, model_name):
        Model = request.env[model_name]
        fields_dict = Model._fields
        safe = []
        for fname in self.FIELD_PRIORITY:
            if fname in fields_dict and self._is_safe_field(fname, fields_dict[fname]):
                safe.append(fname)
        for fname, fobj in fields_dict.items():
            if len(safe) >= 10:
                break
            if fname in safe:
                continue
            if self._is_safe_field(fname, fobj):
                safe.append(fname)
        return safe[:10] or ['id']

    def _is_safe_field(self, fname, fobj):
        low = fname.lower()
        if any(part in low for part in self.SENSITIVE_FIELD_PARTS):
            return False
        if getattr(fobj, 'type', '') in ('binary', 'html', 'one2many', 'many2many'):
            return False
        return True

    def _model_exists(self, model_name):
        try:
            request.env[model_name]
            return True
        except Exception:
            return False

    def _model_label(self, model_name):
        try:
            im = request.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
            return im.name or model_name
        except Exception:
            return model_name

    def _catalog(self, limit=None):
        records = request.env['ir.model'].sudo().search([])
        result = []
        for rec in records:
            if self._is_allowed_model(rec.model) and self._model_exists(rec.model):
                result.append({'model': rec.model, 'label': rec.name or rec.model})
        return result[:limit] if limit else result

    def _resolve_model(self, question):
        q = self._normalize_ar(question)
        tokens = self._tokens(q)
        for alias, model in sorted(self.MODEL_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
            if self._normalize_ar(alias) in q and self._is_allowed_model(model) and self._model_exists(model):
                return model, 95.0

        best_model, best_score = None, 0.0
        for item in self._catalog():
            model_name = item['model']
            label = self._normalize_ar(item['label'])
            technical = self._normalize_ar(model_name.replace('.', ' '))
            score = 0.0
            for tok in tokens:
                if tok in label:
                    score += 20
                if tok in technical:
                    score += 12
            try:
                Model = request.env[model_name]
                for fname, fobj in Model._fields.items():
                    if not self._is_safe_field(fname, fobj):
                        continue
                    f_label = self._normalize_ar(getattr(fobj, 'string', '') or '')
                    for tok in tokens:
                        if tok and tok in f_label:
                            score += 4
            except Exception:
                pass
            if score > best_score:
                best_score, best_model = score, model_name
        return best_model, min(best_score, 90.0)

    def _find_date_field(self, model_name):
        Model = request.env[model_name]
        for fname in ('date', 'issue_date', 'received_date', 'due_date', 'submission_date', 'validation_date', 'invoice_date', 'create_date', 'write_date'):
            if fname in Model._fields:
                return fname
        return False

    def _find_state_field(self, model_name):
        Model = request.env[model_name]
        for fname in ('state', 'status'):
            if fname in Model._fields:
                return fname
        return False

    def _find_amount_field(self, model_name):
        Model = request.env[model_name]
        candidates = ('amount', 'total_amount', 'amount_total', 'total_budget', 'total_actual', 'variance_amount', 'price_total', 'balance')
        for fname in candidates:
            if fname in Model._fields and Model._fields[fname].type in ('float', 'monetary', 'integer'):
                return fname
        for fname, fobj in Model._fields.items():
            if fobj.type in ('float', 'monetary', 'integer') and any(x in fname.lower() for x in ['amount', 'total', 'balance', 'qty', 'quantity']):
                return fname
        return False

    def _date_domain(self, date_field, q):
        if not date_field:
            return []
        today = fields.Date.context_today(request.env.user)
        qn = self._normalize_ar(q)
        if 'الربع' in qn:
            month = today.month
            q_start_month = ((month - 1) // 3) * 3 + 1
            start = date(today.year, q_start_month, 1)
            end_month = q_start_month + 2
            end = date(today.year, 12, 31) if end_month == 12 else date(today.year, end_month + 1, 1) - timedelta(days=1)
            return [(date_field, '>=', start), (date_field, '<=', end)]
        if 'الشهر' in qn:
            start = date(today.year, today.month, 1)
            end = date(today.year, 12, 31) if today.month == 12 else date(today.year, today.month + 1, 1) - timedelta(days=1)
            return [(date_field, '>=', start), (date_field, '<=', end)]
        if 'السنه دي' in qn or 'السنة دي' in qn or 'هذا العام' in qn:
            return [(date_field, '>=', date(today.year, 1, 1)), (date_field, '<=', date(today.year, 12, 31))]
        if 'من اكتر من شهر' in qn or 'اكثر من شهر' in qn:
            return [(date_field, '<=', today - timedelta(days=30))]
        if 'اليوم' in qn:
            return [(date_field, '=', today)]
        return []

    def _plan_query(self, question):
        model, confidence = self._resolve_model(question)
        if not model or confidence < 8:
            return {'success': False, 'message': 'لم أستطع تحديد الموديل المناسب للسؤال.', 'confidence': confidence}
        return self._build_plan_from_model(question, model, confidence, used_ollama=False)

    def _build_plan_from_model(self, question, model, confidence=80.0, used_ollama=False, ollama_raw=''):
        q = self._normalize_ar(question)
        Model = request.env[model]
        fields_list = self._safe_fields_for_model(model)
        date_field = self._find_date_field(model)
        state_field = self._find_state_field(model)
        amount_field = self._find_amount_field(model)
        domain, groupby, aggregates = [], [], []
        query_type = 'search_read'
        answer_summary = ''

        if model == 'res.partner':
            if any(w in q for w in ['مورد', 'المورد', 'موردين', 'الموردين']):
                if 'supplier_rank' in Model._fields:
                    domain.append(('supplier_rank', '>', 0))
            elif any(w in q for w in ['عميل', 'العملاء']):
                if 'customer_rank' in Model._fields:
                    domain.append(('customer_rank', '>', 0))

        if model == 'account.move' and any(w in q for w in ['فاتوره', 'فاتورة', 'فواتير']):
            if 'move_type' in Model._fields:
                domain.append(('move_type', 'in', ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']))

        domain += self._date_domain(date_field, question)

        if state_field:
            if any(w in q for w in ['مرفوض', 'مرفوضه', 'مرفوضة', 'invalid', 'فاشل', 'failed']):
                domain.append((state_field, 'in', ['invalid', 'rejected', 'returned', 'failed', 'needs_correction']))
            elif any(w in q for w in ['مسوده', 'مسودة', 'draft']):
                domain.append((state_field, '=', 'draft'))
            elif any(w in q for w in ['متاخر', 'متاخره', 'متأخر', 'متأخرة', 'overdue']):
                if 'due_date' in Model._fields:
                    domain.append(('due_date', '<', fields.Date.context_today(request.env.user)))
                else:
                    domain.append((state_field, 'ilike', 'overdue'))
            elif 'تجنيب' in q:
                domain.append((state_field, 'ilike', 'reserve'))

        if any(w in q for w in ['كم', 'كام', 'عدد', 'ما هو عدد']):
            query_type = 'count'
            fields_list = ['count']
            answer_summary = 'تم حساب عدد السجلات المطابقة للسؤال.'

        if any(w in q for w in ['اعرض', 'اظهر', 'هات', 'فين', 'اين', 'قائمه', 'قائمة']):
            query_type = 'search_read'
            fields_list = self._safe_fields_for_model(model)
            answer_summary = 'تم عرض السجلات المطابقة للسؤال.'

        if any(w in q for w in ['اجمالي', 'إجمالي', 'مجموع', 'قيمه', 'قيمة', 'مبلغ']):
            if amount_field:
                query_type = 'read_group'
                aggregates = [amount_field + ':sum']
                fields_list = [amount_field]
                answer_summary = 'تم حساب الإجمالي حسب السؤال.'

        order, limit = 'id desc', 50
        if any(w in q for w in ['اكبر', 'أكبر', 'اعلى', 'أعلى']) and amount_field:
            query_type = 'search_read'
            fields_list = self._safe_fields_for_model(model)
            order = amount_field + ' desc'
            limit = 10
            answer_summary = 'تم عرض أعلى السجلات حسب المبلغ.'

        return {
            'success': True, 'model': model, 'model_label': self._model_label(model),
            'query_type': query_type, 'domain': domain, 'fields': fields_list,
            'groupby': groupby, 'aggregates': aggregates, 'limit': limit,
            'order': order, 'confidence': confidence, 'answer_summary': answer_summary,
            'used_ollama': used_ollama, 'ollama_raw': ollama_raw,
        }

    def _ollama_plan(self, question):
        try:
            catalog = self._catalog(limit=80)
            catalog_text = '\\n'.join(['- %s: %s' % (x['model'], x['label']) for x in catalog])
            prompt = (
                'اختر موديل Odoo واحد فقط من القائمة بناء على السؤال العربي. '
                'ارجع JSON فقط بدون markdown وبدون شرح. '
                'الصيغة المطلوبة: {"model":"res.partner","query_type":"count"}\\n\\n'
                'السؤال: %s\\n\\nالقائمة:\\n%s'
            ) % (question, catalog_text)

            resp = requests.post(
                self._ollama_url().rstrip('/') + '/api/generate',
                json={
                    'model': self._ollama_model(),
                    'prompt': prompt,
                    'stream': False,
                    'format': 'json',
                    'options': {'temperature': 0.0, 'num_predict': 80},
                },
                timeout=120,
            )
            raw = resp.text
            if resp.status_code != 200:
                return {'success': False, 'message': 'Ollama returned HTTP %s: %s' % (resp.status_code, raw)}
            data = resp.json()
            text = (data.get('response') or '').strip()
            parsed = self._extract_json(text)
            if not parsed:
                return {'success': False, 'message': 'Ollama لم يرجع JSON مفهوم.', 'ollama_raw': text}

            model_name = parsed.get('model')
            if not self._is_allowed_model(model_name) or not self._model_exists(model_name):
                return {'success': False, 'message': 'Ollama اختار موديل غير مسموح أو غير موجود: %s' % model_name, 'ollama_raw': text}

            query_type = parsed.get('query_type') or 'search_read'
            if query_type not in ('count', 'search_read', 'read_group'):
                query_type = 'search_read'

            plan = self._build_plan_from_model(question, model_name, confidence=75.0, used_ollama=True, ollama_raw=text)
            plan['query_type'] = query_type
            if query_type == 'count':
                plan['fields'] = ['count']
            elif query_type == 'read_group':
                amount_field = self._find_amount_field(model_name)
                if amount_field:
                    plan['aggregates'] = [amount_field + ':sum']
                    plan['fields'] = [amount_field]
                else:
                    plan['query_type'] = 'search_read'
            return plan
        except Exception as e:
            return {'success': False, 'message': 'تعذر الاتصال بـ Ollama: %s' % str(e)}

    def _ollama_url(self):
        return request.env['ir.config_parameter'].sudo().get_param('port_said_ai_assistant.ollama_url', 'http://host.docker.internal:11434')

    def _ollama_model(self):
        return request.env['ir.config_parameter'].sudo().get_param('port_said_ai_assistant.ollama_model', 'llama3.2:1b')

    def _extract_json(self, text):
        try:
            return json.loads(text)
        except Exception:
            pass
        m = re.search(r'\{.*\}', text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return False
        return False

    def _field_labels(self, model_name, fields_list):
        labels = {}
        try:
            model = request.env[model_name]
            for f in fields_list:
                labels[f] = model._fields[f].string if f in model._fields else f
        except Exception:
            labels = {f: f for f in fields_list}
        return labels
