# © 2013-TODAY Akretion (Sébastien Beau)
# © 2018 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from contextlib import contextmanager

from odoo import Command
from odoo.addons.component.tests.common import TransactionComponentRegistryCase

from ..components.sale_order_onchange import OnChangeManager, SaleOrderOnChange


class TestOnchange(TransactionComponentRegistryCase):
    """Test if the onchanges are applied correctly on a sales order"""

    def setUp(self):
        super().setUp()
        self._setup_registry(self)
        self.addCleanup(self._teardown_registry, self)
        self.collection = self.env["collection.base"]
        OnChangeManager._build_component(self.comp_registry)
        SaleOrderOnChange._build_component(self.comp_registry)
        self.collection_record = self.collection.new()

        @contextmanager
        def get_base():
            # Our WorkContext, it will be passed along in every
            # components so we can share data transversally.
            # We are working with sale.order in the following tests,
            # unless we change it in the test.
            with self.collection_record.work_on(
                "sale.order",
                # we use a custom registry only
                # for the sake of the tests
                components_registry=self.comp_registry,
            ) as work:
                # We get the 'base' component, handy to test the base
                # methods component, many_components, ...
                yield work.component_by_name("base")

        self.get_base = get_base

    def test_play_onchange(self):
        """Play the onchange ConnectorUnit on a sales order"""
        product_model = self.env["product.product"]
        partner_model = self.env["res.partner"]
        tax_model = self.env["account.tax"]

        partner = partner_model.create(
            {"name": "seb", "zip": "69100", "city": "Villeurbanne"}
        )
        partner_invoice = partner_model.create(
            {
                "name": "Guewen",
                "zip": "1015",
                "city": "Lausanne",
                "type": "invoice",
                "parent_id": partner.id,
            }
        )
        tax_group = self.env["account.tax.group"].create({"name": "My Tax Group"})
        tax = tax_model.create(
            {
                "name": "My Tax",
                "amount": 1.0,
                "tax_group_id": tax_group.id,
                "country_id": self.env.ref("base.us").id,
            }
        )
        product = product_model.create(
            {
                "default_code": "MyCode",
                "name": "My Product",
                "weight": 15,
                "taxes_id": [Command.set(tax.ids)],
            }
        )

        order_vals = {
            "name": "mag_10000001",
            "partner_id": partner.id,
            "company_id": self.env.company.id,
            "order_line": [
                Command.create(
                    {
                        "product_id": product.id,
                        "price_unit": 20,
                        "name": "My Real Name",
                        "product_uom_qty": 1,
                        "sequence": 1,
                    }
                ),
            ],
        }

        extra_lines = [
            Command.create(
                {
                    "product_id": product.id,
                    "price_unit": 10,
                    "name": "Line 2",
                    "product_uom_qty": 2,
                    "sequence": 2,
                }
            ),
        ]

        with self.get_base() as base:
            onchange = base.component(usage="ecommerce.onchange.manager.sale.order")
            order = onchange.play(order_vals, extra_lines)

        self.assertEqual(order["partner_invoice_id"], partner_invoice.id)
        self.assertEqual(len(order["order_line"]), 1)
        line = order["order_line"][0][2]
        self.assertEqual(line["name"], "My Real Name")
        self.assertEqual(line["product_uom_id"], product.uom_id.id)
        self.assertEqual(len(line["tax_ids"]), 1)
        self.assertEqual(line["tax_ids"][0][:2], (Command.LINK, tax.id))
        line = extra_lines[0][2]
        self.assertEqual(line["name"], "Line 2")
        self.assertEqual(line["product_uom_id"], product.uom_id.id)
        self.assertEqual(len(line["tax_ids"]), 1)
        self.assertEqual(line["tax_ids"][0][:2], (Command.LINK, tax.id))
