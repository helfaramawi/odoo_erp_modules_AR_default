from odoo.tests.common import TransactionCase


class TestWarFinanceControl(TransactionCase):
    def test_seed_exists(self):
        control = self.env['war.finance.control'].search([], limit=1)
        self.assertTrue(control)
