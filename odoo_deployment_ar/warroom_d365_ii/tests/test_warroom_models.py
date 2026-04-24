from odoo.tests.common import TransactionCase


class TestWarroomModels(TransactionCase):

    def _make(self, model_name, name='Test', **kw):
        vals = {'name': name}
        vals.update(kw)
        return self.env[model_name].create(vals)

    def test_all_models_create_with_defaults(self):
        for n in range(1, 5):
            rec = self._make(f'x_warroom_model_{n}', name=f'Model {n} record')
            self.assertEqual(rec.state, 'draft')
            self.assertEqual(rec.x_validation_status, 'draft')

    def test_x_validation_status_defaults_to_draft(self):
        rec = self.env['x_warroom_model_1'].create({'name': 'Auto Status'})
        self.assertEqual(rec.x_validation_status, 'draft')

    def test_state_defaults_to_draft(self):
        rec = self._make('x_warroom_model_1')
        self.assertEqual(rec.state, 'draft')

    def test_full_state_machine_model1(self):
        rec = self._make('x_warroom_model_1')
        transitions = [
            ('action_set_under_review', 'under_review'),
            ('action_set_confirmed', 'confirmed'),
            ('action_set_rejected', 'rejected'),
            ('action_set_pending_validation', 'pending_validation'),
            ('action_set_approved_for_build', 'approved_for_build'),
        ]
        for method, expected in transitions:
            getattr(rec, method)()
            self.assertEqual(rec.state, expected)

    def test_state_transitions_all_models(self):
        for n in range(1, 5):
            rec = self._make(f'x_warroom_model_{n}', name=f'Transitions {n}')
            rec.action_set_under_review()
            self.assertEqual(rec.state, 'under_review')
            rec.action_set_approved_for_build()
            self.assertEqual(rec.state, 'approved_for_build')

    def test_name_required(self):
        with self.assertRaises(Exception):
            self.env['x_warroom_model_1'].create({'x_validation_status': 'draft'})

    def test_source_ref_optional(self):
        rec = self._make('x_warroom_model_1')
        self.assertFalse(rec.x_source_ref)
        rec.x_source_ref = 'FRD-Supply-001'
        self.assertEqual(rec.x_source_ref, 'FRD-Supply-001')

    def test_x_validation_status_done(self):
        rec = self._make('x_warroom_model_1', x_validation_status='done')
        self.assertEqual(rec.x_validation_status, 'done')

    def test_wizard_create_with_all_fields(self):
        wizard = self.env['workflow.review.wizard'].create({
            'review_notes': 'Reviewed and approved',
            'reviewer': 'QA Team',
        })
        self.assertEqual(wizard.review_notes, 'Reviewed and approved')
        self.assertTrue(wizard.review_date)

    def test_wizard_create_minimal(self):
        wizard = self.env['workflow.review.wizard'].create({})
        self.assertTrue(wizard.id > 0)
        self.assertTrue(wizard.review_date)
