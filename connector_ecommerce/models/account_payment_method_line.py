# Copyright 2011-2013 Akretion (Sébastien Beau)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    @api.model
    def _get_import_rules(self):
        return [
            ("always", "Always"),
            ("never", "Never"),
            ("paid", "Paid"),
            ("authorized", "Authorized"),
        ]

    days_before_cancel = fields.Integer(
        default=30,
        help="After 'n' days, if the import rule is not fulfilled, the "
        "sales order import will be canceled.",
    )
    import_rule = fields.Selection(
        selection="_get_import_rules",
        default="always",
        required=True,
    )
    workflow_process_id = fields.Many2one(
        comodel_name="sale.workflow.process",
        string="Automatic Workflow",
    )
