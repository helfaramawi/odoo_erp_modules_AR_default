from odoo.tests.common import TransactionCase


class TestWarRoomItem(TransactionCase):
    def test_sequence_generation(self):
        rec = self.env['war.room.item'].create({'name': 'Test Item', 'item_type': 'gap'})
        self.assertTrue(rec.sequence.startswith('WRI-'))
