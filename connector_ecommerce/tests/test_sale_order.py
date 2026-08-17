# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestSaleOrder(common.TransactionCase):
    def test_workflow_process_field_is_owned_by_oca(self):
        field = self.env["sale.order"]._fields["workflow_process_id"]

        self.assertFalse(field.compute)
        self.assertEqual(field.ondelete, "restrict")
        self.assertFalse(field.copy)
