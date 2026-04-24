from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestWarFinanceControl(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.FinControl = self.env['war.finance.control']
        self.AccountMove = self.env['account.move']

    def _deactivate_controls(self):
        self.FinControl.search([('company_id', '=', self.company.id)]).write({'active': False})

    def _general_journal(self):
        return self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.company.id),
        ], limit=1)

    def _two_accounts(self):
        return self.env['account.account'].search([
            ('company_id', '=', self.company.id),
            ('deprecated', '=', False),
        ], limit=2)

    def _make_entry(self, amount, journal, accounts):
        return self.AccountMove.create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'line_ids': [
                (0, 0, {'account_id': accounts[0].id, 'debit': amount, 'credit': 0.0, 'name': 'D'}),
                (0, 0, {'account_id': accounts[1].id, 'debit': 0.0, 'credit': amount, 'name': 'C'}),
            ],
        })

    def test_seed_exists(self):
        control = self.FinControl.search([], limit=1)
        self.assertTrue(control)

    def test_create_with_defaults(self):
        ctrl = self.FinControl.create({'name': 'Test Ctrl', 'journal_threshold': 5000.0})
        self.assertEqual(ctrl.company_id, self.company)
        self.assertTrue(ctrl.active)
        self.assertEqual(ctrl.currency_id, self.company.currency_id)

    def test_threshold_zero_is_valid(self):
        ctrl = self.FinControl.create({'name': 'Zero', 'journal_threshold': 0.0})
        self.assertEqual(ctrl.journal_threshold, 0.0)

    def test_threshold_blocks_high_entry(self):
        self._deactivate_controls()
        self.FinControl.create({
            'name': 'Strict',
            'journal_threshold': 100.0,
            'company_id': self.company.id,
        })
        journal = self._general_journal()
        accounts = self._two_accounts()
        if not journal or len(accounts) < 2:
            self.skipTest('Insufficient accounting setup')
        move = self._make_entry(500.0, journal, accounts)
        with self.assertRaises(ValidationError):
            move.action_post()

    def test_entry_below_threshold_passes(self):
        self._deactivate_controls()
        self.FinControl.create({
            'name': 'Relaxed',
            'journal_threshold': 10000.0,
            'company_id': self.company.id,
        })
        journal = self._general_journal()
        accounts = self._two_accounts()
        if not journal or len(accounts) < 2:
            self.skipTest('Insufficient accounting setup')
        move = self._make_entry(50.0, journal, accounts)
        move.action_post()
        self.assertEqual(move.state, 'posted')

    def test_no_active_control_never_blocks(self):
        self._deactivate_controls()
        journal = self._general_journal()
        accounts = self._two_accounts()
        if not journal or len(accounts) < 2:
            self.skipTest('Insufficient accounting setup')
        move = self._make_entry(999999.0, journal, accounts)
        move.action_post()
        self.assertEqual(move.state, 'posted')

    def test_inactive_control_does_not_block(self):
        self._deactivate_controls()
        self.FinControl.create({
            'name': 'Inactive',
            'journal_threshold': 1.0,
            'company_id': self.company.id,
            'active': False,
        })
        journal = self._general_journal()
        accounts = self._two_accounts()
        if not journal or len(accounts) < 2:
            self.skipTest('Insufficient accounting setup')
        move = self._make_entry(50000.0, journal, accounts)
        move.action_post()
        self.assertEqual(move.state, 'posted')
