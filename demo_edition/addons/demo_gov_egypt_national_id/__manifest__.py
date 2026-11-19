{
    'name': 'التحقق من صحة تركيب الرقم القومي المصري',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية',
    'summary': 'يضيف تحقق تركيبي رسمي (تاريخ الميلاد، كود المحافظة) على كل حقل رقم قومي في التطبيق',
    'description': """
        امتداد غير هدّام (_inherit فقط) على كل موديل فيه حقل يخزّن الرقم
        القومي المصري (14 رقماً)، يضيف تحقق تركيبي حسب التعريف الرسمي
        لمصلحة الأحوال المدنية:
        - الخانة 1: قرن الميلاد (2 أو 3)
        - الخانتان 2-3 / 4-5 / 6-7: سنة / شهر / يوم الميلاد (تاريخ حقيقي)
        - الخانتان 8-9: كود المحافظة (جدول رسمي)
        - الخانة 13: تحدد النوع (فردي = ذكر، زوجي = أنثى) — استخراج فقط،
          بدون فرض تطابق مع أي حقل نوع آخر
        - الخانة 14: رقم تحقق — لا يوجد نشر رسمي موثّق لصيغة حسابه، فيُكتفى
          بالتأكد من وجوده كرقم واحد

        لا يعدّل أي ملف من الموديولات الأصلية — كل التحقق مُضاف عبر
        _inherit على النماذج التالية:
        hr.employee (national_id, ssnid, identification_id) |
        custody.assignment (national_id) | custody.transfer (to_national_id) |
        new.custody.wizard (national_id) | demo_gov.surety (guarantor_national_id) |
        demo_gov.hr.payroll.non.employee.reward (national_id) |
        demo_gov.hr.payroll.external.salary (national_id) |
        demo_gov.cash_transfer (receiver_id_number)

        ملاحظة: حقل "رقم القومي / رقم الحساب" في demo_gov_daftar55 استُثني
        عمداً — الحقل مزدوج الغرض (رقم قومي لمورد فرد، أو رقم حساب بنكي
        لمورد شركة)، فتطبيق تحقق صارم عليه كان هيرفض أرقام حسابات صحيحة.
    """,
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'demo_gov_hr_employee',
        'l10n_eg_custody',
        'demo_gov_cash_books',
        'demo_gov_hr_payroll_run',
        'demo_gov_cash_transfers',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
}
