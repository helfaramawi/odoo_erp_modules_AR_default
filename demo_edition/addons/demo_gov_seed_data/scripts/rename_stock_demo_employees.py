# -*- coding: utf-8 -*-
"""أداة صيانة تُشغَّل مرة واحدة يدويًا عبر `odoo shell` — لا تُحمَّل تلقائيًا
مع الموديول ولا تُنفَّذ أثناء التثبيت/الترقية.

الغرض: قاعدة البيانات التجريبية بتتحمّل ومعاها بيانات أودو التجريبية
القياسية (hr/base demo data) — موظفين بأسماء إنجليزية زي "Mitchell Admin"
أو "Doris Cole" مش من إنتاج موديولاتنا. السكريبت ده بيدّي كل موظف نشط
مش من ضمن السبعة اللي بيعرّفهم demo_gov_seed_data اسم عربي ومسمى وظيفي
عربي (تقريبي) ويحدد جنسيته مصر، من غير ما يمسح أو يؤرشف حد.

طريقة التشغيل (بعد docker compose up -d --build عشان السكريبت يبقى
موجود جوه الكونتينر على /mnt/demo-addons):

    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_seed_data/scripts/rename_stock_demo_employees.py

آمن التكرار: تشغيله أكتر من مرة مش هيعمل مشكلة — هيعيد نفس التوزيع
بترتيب المعرّفات، وموظفينا السبعة الأصليين مستثنين دايمًا.
"""

OUR_XMLIDS = [
    'demo_gov_seed_data.employee_director_general',
    'demo_gov_seed_data.employee_contracts_manager',
    'demo_gov_seed_data.employee_contracts_officer',
    'demo_gov_seed_data.employee_adjudication_chairman',
    'demo_gov_seed_data.employee_warehouse_manager',
    'demo_gov_seed_data.employee_storekeeper',
    'demo_gov_seed_data.employee_inspector',
]

ARABIC_NAME_POOL = [
    'محمد أنور فؤاد', 'سارة عبد الحميد', 'إسلام رمضان علي', 'نهى شوقي حسن',
    'عمرو صلاح الدين', 'داليا أشرف زكي', 'وليد جمعة إبراهيم', 'رشا هشام محمود',
    'طارق سعيد عبد الله', 'إيمان محسن فتحي', 'خالد نبيل عثمان', 'هبة الله كمال',
    'شريف مجدي حلمي', 'أميرة عادل نصر', 'حسام الدين رفعت', 'ندى إبراهيم صادق',
    'عادل توفيق راشد', 'مروة عصام الغمري', 'يوسف عبد الناصر', 'سلمى فاروق عبيد',
    'باسم عزت شحاتة', 'دينا محمود العطار', 'فادي رمزي جرجس', 'أسماء لطفي حجازي',
    'مينا وديع بشرى', 'غادة صابر منصور', 'أيمن رأفت السباعي', 'لبنى وجدي قنديل',
]

JOB_TITLE_MAP = {
    'Consultant': 'مستشار',
    'Experienced Developer': 'مطور خبير',
    'Marketing and Community Manager': 'مدير تسويق ومجتمع',
    'Human Resources Manager': 'مدير موارد بشرية',
    'Team Leader': 'قائد فريق',
    'Chief Executive Officer': 'الرئيس التنفيذي',
    False: 'موظف',
    '': 'موظف',
}


def run(env):
    exclude_ids = set()
    for xmlid in OUR_XMLIDS:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            exclude_ids.add(rec.id)

    egypt = env.ref('base.eg')
    employees = env['hr.employee'].search(
        [('id', 'not in', list(exclude_ids))], order='id asc')

    updated = 0
    for i, emp in enumerate(employees):
        arabic_name = ARABIC_NAME_POOL[i % len(ARABIC_NAME_POOL)]
        arabic_title = JOB_TITLE_MAP.get(emp.job_title, emp.job_title or 'موظف')
        emp.write({
            'name': arabic_name,
            'job_title': arabic_title,
            'country_id': egypt.id,
        })
        updated += 1

    env.cr.commit()
    print('تم تحديث %d موظف (استُثني %d من موظفي الديمو الحكومي الأصليين).'
          % (updated, len(exclude_ids)))


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
