# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            "connector_ecommerce.account_payment_mode_form_inherit",
            "connector_ecommerce.account_payment_mode_tree_inherit",
        ],
    )
