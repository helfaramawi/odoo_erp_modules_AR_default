from odoo.tests.common import TransactionCase


class TestWarRoomItem(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Model = self.env['war.room.item']

    def _create(self, **kw):
        vals = {'name': 'Test Item', 'item_type': 'gap'}
        vals.update(kw)
        return self.Model.create(vals)

    def test_sequence_generation(self):
        rec = self._create()
        self.assertTrue(rec.sequence.startswith('WRI-'))

    def test_sequence_unique_per_record(self):
        r1 = self._create(name='Item A')
        r2 = self._create(name='Item B')
        self.assertNotEqual(r1.sequence, r2.sequence)

    def test_explicit_sequence_not_overwritten(self):
        rec = self._create(sequence='CUSTOM-001')
        self.assertEqual(rec.sequence, 'CUSTOM-001')

    def test_default_status_is_draft(self):
        rec = self._create()
        self.assertEqual(rec.status, 'draft')

    def test_default_priority_is_medium(self):
        rec = self._create()
        self.assertEqual(rec.priority, 'medium')

    def test_default_owner_is_current_user(self):
        rec = self._create()
        self.assertEqual(rec.owner_id, self.env.user)

    def test_all_item_types_accepted(self):
        for itype in ('assumption', 'gap', 'risk', 'decision', 'open_question'):
            rec = self._create(name=f'Type {itype}', item_type=itype)
            self.assertEqual(rec.item_type, itype)

    def test_all_status_values_accepted(self):
        for status in ('draft', 'in_progress', 'blocked', 'closed'):
            rec = self._create(name=f'Status {status}', status=status)
            self.assertEqual(rec.status, status)

    def test_all_priority_values_accepted(self):
        for prio in ('low', 'medium', 'high', 'critical'):
            rec = self._create(name=f'Prio {prio}', priority=prio)
            self.assertEqual(rec.priority, prio)

    def test_name_required(self):
        with self.assertRaises(Exception):
            self.Model.create({'item_type': 'gap'})

    def test_item_type_required(self):
        with self.assertRaises(Exception):
            self.Model.create({'name': 'No Type'})

    def test_status_can_be_updated(self):
        rec = self._create()
        rec.status = 'in_progress'
        self.assertEqual(rec.status, 'in_progress')
        rec.status = 'closed'
        self.assertEqual(rec.status, 'closed')

    def test_related_requirement_id_stored(self):
        rec = self._create(related_requirement_id='REQ-001')
        self.assertEqual(rec.related_requirement_id, 'REQ-001')
