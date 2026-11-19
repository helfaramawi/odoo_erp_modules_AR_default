# -*- coding: utf-8 -*-
"""
امتداد غير هدّام لمولّد بيانات الاختبار الحكومي (demo_gov_uat_tools) —
يضيف توليد بيانات اختبار واقعية لحزمة الموارد البشرية والرواتب الحكومية
الكاملة، من غير ما يعدّل أي ملف من الموديول الأصلي (_inherit فقط).
"""
import logging
from datetime import timedelta

from odoo import models, api
from odoo.addons.demo_gov_uat_tools.models.uat_data_generator import UAT_BATCH, TODAY

_logger = logging.getLogger(__name__)


class UATDataGeneratorHR(models.AbstractModel):
    _inherit = 'arabic.government.uat.generator'

    # ------------------------------------------------------------------ #
    #  ENTRY POINT — extends the base generate_all without touching it     #
    # ------------------------------------------------------------------ #
    @api.model
    def generate_all(self, options, log_record):
        total = super().generate_all(options, log_record) or 0

        hr_jobs = [
            ('generate_hr_leave_cases', 'الإجازات', self._generate_hr_leave),
            ('generate_hr_training_cases', 'التدريب', self._generate_hr_training),
            ('generate_hr_recruitment_cases', 'التوظيف', self._generate_hr_recruitment),
            ('generate_hr_performance_cases', 'تقييم الأداء والتظلمات', self._generate_hr_performance),
            ('generate_hr_transfer_cases', 'النقل والندب والإعارة والترقيات', self._generate_hr_transfer),
            ('generate_hr_payroll_cases', 'الرواتب', self._generate_hr_payroll),
            ('generate_hr_takaful_cases', 'صندوق التكافل', self._generate_hr_takaful),
            ('generate_hr_pension_cases', 'المعاشات', self._generate_hr_pension),
            ('generate_hr_disclosure_cases', 'الإفصاح المالي', self._generate_hr_disclosure),
            ('generate_hr_positions_cases', 'موازنة الوظائف', self._generate_hr_positions),
        ]

        results = []
        extra_total = 0
        for opt_key, label, fn in hr_jobs:
            if not options.get(opt_key):
                continue
            try:
                with self.env.cr.savepoint():
                    count = fn()
                results.append((label, count, 'ok', ''))
                extra_total += count
            except Exception as exc:
                _logger.exception('UAT HR generator error in %s', label)
                results.append((label, 0, 'error', str(exc)[:200]))

        seq = 500
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
                _logger.warning('Could not write HR UAT log line for %s: %s', label, exc)
            seq += 10

        new_total = total + extra_total
        if results:
            try:
                extra_summary = '\n'.join(f'• {r[0]}: {r[1]} سجل ({r[2]})' for r in results)
                existing_summary = log_record.result_summary or ''
                summary = (existing_summary + '\n' + extra_summary).strip()
                log_record.write({'result_summary': summary, 'total_created': new_total})
            except Exception as exc:
                _logger.warning('Could not update HR UAT summary: %s', exc)

        return new_total

    # ------------------------------------------------------------------ #
    #  HR / PAYROLL GENERATORS                                              #
    # ------------------------------------------------------------------ #
    def _generate_hr_leave(self):
        Employee = self.env['hr.employee']
        LeaveType = self.env['hr.leave.type']
        Leave = self.env['hr.leave']

        employees = Employee.search([], limit=27)
        if not employees:
            return 0

        leave_types = LeaveType.search([('requires_allocation', '=', 'no')])
        if not leave_types:
            leave_types = LeaveType.search([], limit=1)
        if not leave_types:
            return 0

        count = 0
        for i, emp in enumerate(employees):
            name = f'{UAT_BATCH} - إجازة {emp.name}'
            if Leave.search([('employee_id', '=', emp.id), ('name', '=', name)], limit=1):
                continue
            leave_type = leave_types[i % len(leave_types)]
            date_from = TODAY - timedelta(days=5 + (i * 3) % 55)
            date_to = date_from + timedelta(days=1 + i % 4)
            try:
                leave = Leave.create({
                    'employee_id': emp.id,
                    'holiday_status_id': leave_type.id,
                    'request_date_from': date_from,
                    'request_date_to': date_to,
                    'name': name,
                })
            except Exception:
                continue
            count += 1
            try:
                if i % 3 != 0:
                    leave.action_approve()
            except Exception:
                pass
        return count

    def _generate_hr_training(self):
        Course = self.env['demo_gov.hr.training.course']
        Registration = self.env['demo_gov.hr.training.registration']
        Instructor = self.env['demo_gov.hr.training.instructor']
        Need = self.env['demo_gov.hr.training.need']
        Employee = self.env['hr.employee']

        count = 0
        instructor_name = f'{UAT_BATCH} - مدرب داخلي'
        instructor = Instructor.search([('name', '=', instructor_name)], limit=1)
        if not instructor:
            instructor = Instructor.create({
                'name': instructor_name,
                'instructor_type': 'internal',
                'specialization': 'التنمية الإدارية',
            })
            count += 1

        course_defs = [
            ('دورة الحوكمة الرشيدة والشفافية', 'internal', 'قاعة التدريب - الديوان العام'),
            ('دورة نظم المعلومات الإدارية', 'internal', 'مركز معلومات الجهة الحكومية'),
            ('دورة اللغة الإنجليزية للعاملين', 'external', 'مركز تدريب خارجي معتمد'),
        ]
        courses = []
        for name, ctype, loc in course_defs:
            full_name = f'{UAT_BATCH} - {name}'
            course = Course.search([('name', '=', full_name)], limit=1)
            if not course:
                course = Course.create({
                    'name': full_name,
                    'course_type': ctype,
                    'instructor_id': instructor.id,
                    'location': loc,
                    'start_date': TODAY - timedelta(days=30),
                    'end_date': TODAY - timedelta(days=25),
                    'seats': 20,
                })
                count += 1
            courses.append(course)

        employees = Employee.search([], limit=27)
        for i, emp in enumerate(employees):
            course = courses[i % len(courses)]
            if Registration.search(
                    [('employee_id', '=', emp.id), ('course_id', '=', course.id)], limit=1):
                continue
            reg = Registration.create({
                'course_id': course.id,
                'employee_id': emp.id,
                'performance_before': str(2 + i % 3),
            })
            count += 1
            try:
                reg.action_request()
                reg.action_manager_approve()
                reg.action_confirm_by_training_dept()
                if i % 2 == 0:
                    reg.write({'performance_after': str(min(5, int(reg.performance_before) + 1))})
                    reg.action_complete()
            except Exception:
                pass

        dept = self.env['hr.department'].search([], limit=1)
        if dept:
            need_name = f'{UAT_BATCH} - احتياج تدريبي: مهارات القيادة الإدارية'
            if not Need.search([('name', '=', need_name)], limit=1):
                Need.create({
                    'name': need_name,
                    'department_id': dept.id,
                    'priority': 'high',
                })
                count += 1
        return count

    def _generate_hr_recruitment(self):
        Project = self.env['demo_gov.hr.recruitment.project']
        Applicant = self.env['hr.applicant']
        Job = self.env['hr.job']

        count = 0
        job_defs = ['محاسب حكومي', 'أخصائي موارد بشرية', 'مهندس صيانة']
        projects = []
        for jname in job_defs:
            job = Job.search([('name', '=', jname)], limit=1)
            if not job:
                job = Job.create({'name': jname})
                count += 1
            pname = f'{UAT_BATCH} - مشروع تعيين {jname}'
            project = Project.search([('name', '=', pname)], limit=1)
            if not project:
                project = Project.create({
                    'name': pname,
                    'job_id': job.id,
                    'planned_positions': 2,
                    'state': 'screening',
                })
                count += 1
            projects.append(project)

        applicant_names = [
            'محمد إبراهيم الشريف', 'نورا سيد أحمد', 'أحمد جلال منصور',
            'رانيا فتحي السيد', 'عمر خالد نجيب', 'هدير محمود سالم',
        ]
        for i, aname in enumerate(applicant_names):
            project = projects[i % len(projects)]
            if Applicant.search([
                    ('partner_name', '=', aname),
                    ('recruitment_project_id', '=', project.id)], limit=1):
                continue
            Applicant.create({
                'partner_name': aname,
                'recruitment_project_id': project.id,
                'job_id': project.job_id.id,
                'email_from': 'applicant%d@example.com' % (i + 1),
            })
            count += 1
        return count

    def _generate_hr_performance(self):
        Appraisal = self.env['demo_gov.hr.performance.appraisal']
        Grievance = self.env['demo_gov.hr.performance.grievance']
        Employee = self.env['hr.employee']

        ratings = ['excellent', 'very_good', 'good', 'acceptable', 'weak']
        count = 0
        employees = Employee.search([], limit=27)
        year = str(TODAY.year)
        for i, emp in enumerate(employees):
            appraisal = Appraisal.search(
                [('employee_id', '=', emp.id), ('fiscal_year', '=', year)], limit=1)
            if not appraisal:
                appraisal = Appraisal.create({
                    'employee_id': emp.id,
                    'fiscal_year': year,
                    'goals_text': 'تحقيق أهداف الخطة التشغيلية للإدارة',
                    'rating': ratings[i % len(ratings)],
                })
                count += 1
                try:
                    appraisal.write({'state': 'finalized'})
                except Exception:
                    pass
            if i % 6 == 0 and not Grievance.search(
                    [('appraisal_id', '=', appraisal.id)], limit=1):
                Grievance.create({
                    'appraisal_id': appraisal.id,
                    'grievance_text': 'تظلم بخصوص عدم احتساب المشاركة في مشروع تطويري ضمن التقييم.',
                })
                count += 1
        return count

    def _generate_hr_transfer(self):
        Transfer = self.env['demo_gov.hr.transfer']
        Promotion = self.env['demo_gov.hr.promotion']
        Employee = self.env['hr.employee']

        employees = Employee.search([], limit=27)
        count = 0
        transfer_defs = [
            ('secondment', 'diwan_general', 30),
            ('loan', 'districts', 45),
            ('internal_transfer', 'diwan_general', None),
        ]
        for i, emp in enumerate(employees[:9]):
            ttype, from_entity, dur = transfer_defs[i % len(transfer_defs)]
            key = '%s-transfer-%d' % (UAT_BATCH, emp.id)
            if Transfer.search([('employee_id', '=', emp.id), ('decision_number', '=', key)], limit=1):
                continue
            vals = {
                'employee_id': emp.id,
                'transfer_type': ttype,
                'from_entity': from_entity,
                'decision_number': key,
                'decision_date': TODAY - timedelta(days=20),
                'start_date': TODAY - timedelta(days=15),
            }
            if dur:
                vals['end_date'] = TODAY + timedelta(days=dur)
            transfer = Transfer.create(vals)
            count += 1
            try:
                transfer.action_approve()
                transfer.action_activate()
            except Exception:
                pass

        for emp in employees[9:13]:
            key = '%s-promo-%d' % (UAT_BATCH, emp.id)
            if Promotion.search([('employee_id', '=', emp.id), ('decision_number', '=', key)], limit=1):
                continue
            promo = Promotion.create({
                'employee_id': emp.id,
                'new_grade': 'الدرجة الثانية',
                'decision_number': key,
                'decision_date': TODAY - timedelta(days=10),
            })
            count += 1
            try:
                promo.action_send_to_committee()
                promo.action_approve()
            except Exception:
                pass
        return count

    def _generate_hr_payroll(self):
        Salary = self.env['demo_gov.hr.employee.salary']
        Run = self.env['demo_gov.hr.payroll.run']
        Employee = self.env['hr.employee']

        basic = self.env.ref('demo_gov_hr_payroll_structure.component_basic', raise_if_not_found=False)
        if not basic:
            return 0
        housing = self.env.ref('demo_gov_hr_payroll_structure.component_housing', raise_if_not_found=False)
        transport = self.env.ref('demo_gov_hr_payroll_structure.component_transport', raise_if_not_found=False)

        employees = Employee.search([], limit=27)
        count = 0
        for i, emp in enumerate(employees):
            if Salary.search([('employee_id', '=', emp.id)], limit=1):
                continue
            job_wage = 3000 + (i % 10) * 250
            line_vals = [(0, 0, {'component_id': basic.id, 'amount': job_wage})]
            if housing:
                line_vals.append((0, 0, {'component_id': housing.id, 'amount': 300}))
            if transport:
                line_vals.append((0, 0, {'component_id': transport.id, 'amount': 150}))
            Salary.create({
                'employee_id': emp.id,
                'job_wage': job_wage,
                'disbursement_entity': 'diwan',
                'salary_line_ids': line_vals,
            })
            count += 1

        month = str(TODAY.month)
        year = str(TODAY.year)
        run = Run.search([
            ('month', '=', month), ('year', '=', year),
            ('disbursement_entity', '=', 'diwan')], limit=1)
        if not run:
            run = Run.create({'month': month, 'year': year, 'disbursement_entity': 'diwan'})
            count += 1
        try:
            if run.state == 'draft':
                run.action_compute_payslips()
            if run.state == 'computed':
                for slip in run.payslip_ids:
                    if slip.state != 'completed':
                        slip.action_mark_completed()
                run.action_submit_for_review()
            if run.state == 'under_review':
                run.action_approve()
            if run.state == 'approved':
                run.action_post()
        except Exception:
            _logger.exception('UAT HR generator: could not advance payroll run %s', run.name)
        return count

    def _generate_hr_takaful(self):
        Member = self.env['demo_gov.hr.takaful.member']
        Contribution = self.env['demo_gov.hr.takaful.contribution']
        Payout = self.env['demo_gov.hr.takaful.payout']
        Employee = self.env['hr.employee']

        employees = Employee.search([], limit=27)
        count = 0
        members = []
        for emp in employees[:15]:
            member = Member.search([('employee_id', '=', emp.id)], limit=1)
            if not member:
                member = Member.create({'employee_id': emp.id, 'monthly_contribution': 50.0})
                count += 1
            members.append(member)

        for member in members:
            for m in range(3):
                trans_date = TODAY - timedelta(days=30 * (m + 1))
                if Contribution.search(
                        [('member_id', '=', member.id), ('trans_date', '=', trans_date)], limit=1):
                    continue
                contribution = Contribution.create({
                    'member_id': member.id,
                    'amount': member.monthly_contribution,
                    'trans_date': trans_date,
                })
                count += 1
                try:
                    contribution.action_post()
                except Exception:
                    pass

        reasons_cycle = ['marriage', 'birth', 'death']
        for i, member in enumerate(members[:3]):
            reason = reasons_cycle[i % len(reasons_cycle)]
            if Payout.search([('member_id', '=', member.id), ('payout_reason', '=', reason)], limit=1):
                continue
            payout = Payout.create({'member_id': member.id, 'payout_reason': reason})
            count += 1
            try:
                payout.action_compute_amount()
                payout.action_approve()
            except Exception:
                pass
        return count

    def _generate_hr_pension(self):
        Plan = self.env['demo_gov.hr.pension.plan']
        Enrollment = self.env['demo_gov.hr.pension.enrollment']
        Settlement = self.env['demo_gov.hr.pension.settlement']
        Employee = self.env['hr.employee']

        count = 0
        plan = Plan.search([('name', '=', 'خطة معاش الشيخوخة الحكومي الأساسي')], limit=1)
        if not plan:
            plan = Plan.create({
                'name': 'خطة معاش الشيخوخة الحكومي الأساسي',
                'plan_type': 'retirement_pension',
                'employee_contribution_pct': 11.0,
                'employer_contribution_pct': 18.0,
            })
            count += 1
        health_plan = Plan.search([('name', '=', 'خطة التأمين الصحي الشامل')], limit=1)
        if not health_plan:
            health_plan = Plan.create({
                'name': 'خطة التأمين الصحي الشامل',
                'plan_type': 'comprehensive_health',
                'employee_contribution_pct': 1.0,
                'employer_contribution_pct': 4.0,
            })
            count += 1

        employees = Employee.search([], limit=27)
        for emp in employees:
            for pl in (plan, health_plan):
                if not Enrollment.search(
                        [('employee_id', '=', emp.id), ('plan_id', '=', pl.id)], limit=1):
                    Enrollment.create({'employee_id': emp.id, 'plan_id': pl.id})
                    count += 1

        candidates = employees.filtered(lambda e: e.gov_termination_type) if \
            'gov_termination_type' in employees._fields else employees.browse()
        if not candidates:
            candidates = employees[:2]
        for emp in candidates[:2]:
            if Settlement.search([('employee_id', '=', emp.id)], limit=1):
                continue
            settlement = Settlement.create({
                'employee_id': emp.id,
                'final_pensionable_salary': 4500.0,
            })
            count += 1
            try:
                settlement.action_compute()
                settlement.action_approve()
            except Exception:
                pass
        return count

    def _generate_hr_disclosure(self):
        Disclosure = self.env['demo_gov.hr.disclosure']
        Employee = self.env['hr.employee']

        employees = Employee.search([], limit=27)
        count = 0
        for i, emp in enumerate(employees):
            if Disclosure.search([('employee_id', '=', emp.id)], limit=1):
                continue
            disc = Disclosure.create({
                'employee_id': emp.id,
                'disclosure_type': 'first_appointment',
                'real_estate_value': 200000 + i * 5000,
                'vehicle_value': 50000,
                'bank_deposits': 30000,
                'liabilities': 10000,
            })
            count += 1
            try:
                if i % 4 == 1:
                    disc.action_notify_employee()
                elif i % 4 == 2:
                    disc.action_notify_employee()
                    disc.action_submit()
                elif i % 4 == 3:
                    disc.action_notify_employee()
                    disc.action_submit()
                    disc.action_approve()
            except Exception:
                pass
        return count

    def _generate_hr_positions(self):
        Job = self.env['hr.job']
        Budget = self.env['demo_gov.hr.position.budget']
        Department = self.env['hr.department']

        dept = Department.search([], limit=1)
        count = 0
        job_defs = [
            ('محاسب حكومي', 6),
            ('أخصائي موارد بشرية', 4),
            ('مهندس صيانة', 3),
            ('سكرتير تنفيذي', 5),
        ]
        year = str(TODAY.year)
        for jname, budgeted in job_defs:
            job = Job.search([('name', '=', jname)], limit=1)
            if not job:
                vals = {'name': jname}
                if dept:
                    vals['department_id'] = dept.id
                job = Job.create(vals)
                count += 1
            if not Budget.search([('job_id', '=', job.id), ('fiscal_year', '=', year)], limit=1):
                Budget.create({
                    'job_id': job.id,
                    'fiscal_year': year,
                    'budgeted_positions': budgeted,
                })
                count += 1
        return count
