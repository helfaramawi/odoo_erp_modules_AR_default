#!/usr/bin/env python3
"""
إنشاء استمارة 50 تجريبية كاملة الحقول — مسودة فقط للمعاينة
شغّل: python3 create_test_form50.py
"""
import xmlrpc.client, sys

HOST     = 'http://localhost:8069'
DB       = 'odoo17_db'
USER     = 'admin'
# غيّر كلمة المرور لو الـ admin عندك مختلفة
PASSWORD = 'admin'

# ── اتصال ─────────────────────────────────────────────────────────────────────
common = xmlrpc.client.ServerProxy(f'{HOST}/xmlrpc/2/common')
try:
    uid = common.authenticate(DB, USER, PASSWORD, {})
except Exception as e:
    print(f'[ERROR] فشل الاتصال: {e}')
    print('تأكد أن Odoo شغّال على المنفذ 8069')
    sys.exit(1)

if not uid:
    print('[ERROR] فشل تسجيل الدخول — تحقق من كلمة المرور')
    sys.exit(1)

models = xmlrpc.client.ServerProxy(f'{HOST}/xmlrpc/2/object')
print(f'[OK] متصل — uid={uid}')


def call(model, method, *args, **kw):
    return models.execute_kw(DB, uid, PASSWORD, model, method, list(args), kw)


# ── جلب أو إنشاء شريك (مورد) ──────────────────────────────────────────────
partner_ids = call('res.partner', 'search', [('name', 'like', 'شركة الاختبار')], limit=1)
if partner_ids:
    partner_id = partner_ids[0]
    print(f'[OK] شريك موجود id={partner_id}')
else:
    partner_id = call('res.partner', 'create', {
        'name':  'شركة الاختبار والتطوير للتجارة',
        'vat':   '123456789',
        'phone': '01001234567',
        'email': 'test@example.eg',
        'city':  'بورسعيد',
        'country_id': call('res.country', 'search', [('code', '=', 'EG')], limit=1)[0],
    })
    print(f'[OK] أُنشئ شريك جديد id={partner_id}')

# ── جلب مستخدمين للتوقيعات ──────────────────────────────────────────────────
user_ids = call('res.users', 'search', [], limit=5)
users    = call('res.users', 'read', user_ids, ['id', 'name'])
admin_id = user_ids[0]
reviewer_id = user_ids[1] if len(user_ids) > 1 else admin_id
auditor_id  = user_ids[2] if len(user_ids) > 2 else admin_id
head_id     = user_ids[3] if len(user_ids) > 3 else admin_id
print(f'[OK] مستخدمون: {[u["name"] for u in users[:4]]}')

# ── حذف أي سجل تجريبي قديم بنفس رقم الاستمارة ─────────────────────────────
old = call('port_said.daftar55', 'search', [('form50_ref', '=', 'TEST-50-2024-001')])
if old:
    call('port_said.daftar55', 'unlink', old)
    print(f'[OK] حُذف سجل قديم id={old}')

# ── إنشاء السجل الرئيسي ──────────────────────────────────────────────────────
record_id = call('port_said.daftar55', 'create', {
    # قسم أ
    'department_name':  'مصلحة الشؤون المالية',
    'division_name':    'إدارة المشتريات والمخازن',
    'date_received':    '2024-11-15',
    'date_returned':    '2024-11-18',
    'form50_ref':       'TEST-50-2024-001',
    'register_z_ref':   'ز/2024/0042',
    'writer_assigned':  'محمد أحمد السيد',
    'attachment_count_declared': 7,

    # بيانات صاحب الحق
    'vendor_id':        partner_id,
    'national_id':      '24011200300123',
    'bank_name':        'بنك مصر',
    'bank_branch':      'فرع بورسعيد الرئيسي',
    'bank_account_no':  '012345678901234',
    'iban':             'EG380019000500000012345678901',
    'payment_method':   'bank_transfer',

    # الموازنة
    'budget_line':  'أثاث ومعدات مكتبية',
    'budget_bab':   '2',
    'budget_fasle': '3',

    # المبلغ — الكود سيحسب الاستقطاعات تلقائياً
    'amount_gross': 48410.00,

    # نوع العملية
    'transaction_type': 'inventory_purchase',

    # قسم ج — المراجعة
    'reviewer_id':         reviewer_id,
    'reviewer_stamp_date': '2024-11-20',
    'auditor_id':          auditor_id,
    'accounts_head_id':    head_id,
    'section_head_id':     admin_id,

    # قسم د
    'daftar224_sequence': '224/2024/0155',
    'crossout_signed':    True,
    'crossout_signed_by': 'أحمد محمد علي',

    # روابط
    'payment_order_ref': 'PO-2024-0387',
    'commitment_ref':    'CMT-2024-112',

    'notes': 'سجل تجريبي كامل لمعاينة مواضع الحقول — لا يُرحَّل',
    'state': 'draft',
})
print(f'[OK] أُنشئ سجل دفتر 55 id={record_id}')

# ── سطور الفواتير ─────────────────────────────────────────────────────────────
invoice_lines = [
    {
        'daftar55_id':    record_id,
        'sequence':       10,
        'invoice_ref':    'INV-2024-0801',
        'invoice_date':   '2024-10-05',
        'description':    'توريد أثاث مكتبي (مكاتب وكراسي)',
        'amount_pounds':  18500,
        'amount_piasters': 0,
    },
    {
        'daftar55_id':    record_id,
        'sequence':       20,
        'invoice_ref':    'INV-2024-0802',
        'invoice_date':   '2024-10-12',
        'description':    'توريد أجهزة حاسب آلي وطابعات',
        'amount_pounds':  22000,
        'amount_piasters': 0,
    },
    {
        'daftar55_id':    record_id,
        'sequence':       30,
        'invoice_ref':    'INV-2024-0803',
        'invoice_date':   '2024-10-20',
        'description':    'توريد معدات وأدوات مكتبية متنوعة',
        'amount_pounds':  7910,
        'amount_piasters': 0,
    },
]

line_ids = []
for line in invoice_lines:
    lid = call('port_said.form50.invoice.line', 'create', line)
    line_ids.append(lid)
    print(f'[OK] سطر فاتورة أُنشئ id={lid}: {line["description"][:30]}')

# ── تحقق سريع ────────────────────────────────────────────────────────────────
rec = call('port_said.daftar55', 'read', [record_id], [
    'sequence_number', 'form50_ref', 'amount_gross',
    'amount_net', 'amount_words', 'total_deductions', 'state',
    'invoices_total_pounds',
])[0]

print('\n' + '='*60)
print(f'  رقم المسلسل     : {rec["sequence_number"]}')
print(f'  رقم الاستمارة  : {rec["form50_ref"]}')
print(f'  إجمالي الأصل   : {rec["amount_gross"]:,.2f} جنيه')
print(f'  إجمالي الاستق  : {rec["total_deductions"]:,.2f} جنيه')
print(f'  الصافي          : {rec["amount_net"]:,.2f} جنيه')
print(f'  التفقيط         : {rec["amount_words"]}')
print(f'  إجمالي الفواتير : {rec["invoices_total_pounds"]:,} جنيه')
print(f'  الحالة          : {rec["state"]}')
print('='*60)
print(f'\n✅ افتح Odoo ← دفتر 55 ← ابحث عن رقم {rec["sequence_number"]}')
print(f'   أو مباشرةً: {HOST}/odoo/port-said-daftar55/{record_id}')
print(f'   ثم اضغط "معاينة استمارة 50" لرؤية جميع الحقول\n')
