# © 2026 Avosdim
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class ConnectorEcommerceDebugListener(Component):
    _name = "connector.ecommerce.debug.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["account.move"]

    def on_invoice_validated(self, record):
        _logger.info(
            "connector_ecommerce debug: on_invoice_validated fired "
            "for account.move id=%s name=%s move_type=%s state=%s",
            record.id,
            record.name,
            record.move_type,
            record.state,
        )
