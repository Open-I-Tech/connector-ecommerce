# © 2013 Camptocamp SA
# © 2018 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest import mock

from odoo import Command
from odoo.tests import common


class TestInvoiceEvent(common.TransactionCase):
    """Test if the events on the invoice are fired correctly"""

    def setUp(self):
        super().setUp()
        self.invoice_model = self.env["account.move"]
        partner_model = self.env["res.partner"]
        receivable_account = self.env["account.account"].create(
            {
                "name": "Test Receivable",
                "code": "TREC",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        revenue_account = self.env["account.account"].create(
            {
                "name": "Test Revenue",
                "code": "TREV",
                "account_type": "income",
            }
        )
        partner = partner_model.create(
            {
                "name": "Hodor",
                "property_account_receivable_id": receivable_account.id,
            }
        )
        product = self.env["product.product"].create(
            {
                "name": "Test Invoice Product",
                "list_price": 200,
            }
        )
        sale_journal = self.env["account.journal"].create(
            {
                "name": "Test Sale Journal",
                "code": "TSJ",
                "type": "sale",
                "default_account_id": revenue_account.id,
            }
        )
        invoice_vals = {
            "partner_id": partner.id,
            "company_id": self.env.company.id,
            "journal_id": sale_journal.id,
            "move_type": "out_invoice",
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": "LCD Screen",
                        "product_id": product.id,
                        "account_id": revenue_account.id,
                        "quantity": 5,
                        "price_unit": 200,
                    }
                )
            ],
        }
        self.invoice = self.invoice_model.create(invoice_vals)

    def test_event_validated(self):
        """Test if the ``on_invoice_validated`` event is fired
        when an invoice is validated"""
        assert self.invoice, "The invoice has not been created"

        mock_method = "odoo.addons.component_event.models.base.Base._event"
        with mock.patch(mock_method) as mock_event:
            self.invoice.action_post()
            self.assertEqual(self.invoice.state, "posted")
            mock_event("on_invoice_validated").notify.assert_any_call(self.invoice)

    def test_event_paid(self):
        """Test if the ``on_invoice_paid`` event is fired
        when an invoice is paid"""
        assert self.invoice, "The invoice has not been created"

        mock_method = "odoo.addons.component_event.models.base.Base._event"
        with mock.patch(mock_method) as mock_event:
            self.assertEqual(self.invoice.state, "draft")
            self.invoice.action_post()
            self.assertEqual(self.invoice.state, "posted")
            self.invoice._invoice_paid_hook()
            mock_event("on_invoice_paid").notify.assert_any_call(self.invoice)
