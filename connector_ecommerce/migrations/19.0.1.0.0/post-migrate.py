# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _translated_name(value, lang):
    if not isinstance(value, dict):
        return value
    return value.get(lang) or value.get("en_US") or next(iter(value.values()), False)


def _payment_mode_rows(env, has_workflow):
    if has_workflow:
        env.cr.execute(
            """
            SELECT id,
                   name,
                   company_id,
                   bank_account_link,
                   fixed_journal_id,
                   payment_method_id,
                   import_rule,
                   days_before_cancel,
                   workflow_process_id
              FROM account_payment_mode
             WHERE payment_method_id IS NOT NULL
            """
        )
    else:
        env.cr.execute(
            """
            SELECT id,
                   name,
                   company_id,
                   bank_account_link,
                   fixed_journal_id,
                   payment_method_id,
                   import_rule,
                   days_before_cancel,
                   NULL
              FROM account_payment_mode
             WHERE payment_method_id IS NOT NULL
            """
        )
    return env.cr.fetchall()


def _journal_ids(env, mode_id, bank_account_link, fixed_journal_id):
    if bank_account_link == "fixed":
        return [fixed_journal_id] if fixed_journal_id else []
    if not openupgrade.table_exists(
        env.cr, "account_payment_mode_variable_journal_rel"
    ):
        return []
    env.cr.execute(
        """
        SELECT journal_id
          FROM account_payment_mode_variable_journal_rel
         WHERE payment_mode_id = %s
        """,
        (mode_id,),
    )
    return [row[0] for row in env.cr.fetchall()]


def _matching_payment_method_lines(env, company_id, payment_method_id, journal_ids):
    if not journal_ids:
        return []
    env.cr.execute(
        """
        SELECT line.id
          FROM account_payment_method_line AS line
          JOIN account_journal AS journal ON journal.id = line.journal_id
         WHERE line.payment_method_id = %s
           AND line.journal_id = ANY(%s)
           AND journal.company_id = %s
        """,
        (payment_method_id, journal_ids, company_id),
    )
    return [row[0] for row in env.cr.fetchall()]


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    required_columns = (
        "import_rule",
        "days_before_cancel",
        "bank_account_link",
        "fixed_journal_id",
        "payment_method_id",
    )
    if not openupgrade.table_exists(
        env.cr, "account_payment_mode"
    ) or not openupgrade.table_exists(env.cr, "account_payment_method_line"):
        return
    if not all(
        openupgrade.column_exists(env.cr, "account_payment_mode", column)
        for column in required_columns
    ):
        return

    has_workflow = openupgrade.column_exists(
        env.cr, "account_payment_mode", "workflow_process_id"
    )
    payment_method_lines = env["account.payment.method.line"]
    for (
        mode_id,
        mode_name,
        company_id,
        bank_account_link,
        fixed_journal_id,
        payment_method_id,
        import_rule,
        days_before_cancel,
        workflow_process_id,
    ) in _payment_mode_rows(env, has_workflow):
        journal_ids = _journal_ids(
            env, mode_id, bank_account_link, fixed_journal_id
        )
        line_ids = _matching_payment_method_lines(
            env, company_id, payment_method_id, journal_ids
        )
        if len(line_ids) != 1:
            _logger.warning(
                "Payment mode %s was not migrated: expected one matching payment "
                "method line, found %s.",
                mode_id,
                len(line_ids),
            )
            continue

        values = {
            "import_rule": import_rule or "always",
            "days_before_cancel": days_before_cancel,
        }
        name = _translated_name(mode_name, env.lang)
        if name:
            values["name"] = name
        if has_workflow:
            values["workflow_process_id"] = workflow_process_id
        payment_method_lines.browse(line_ids).write(values)
