# -*- coding: utf-8 -*-
"""Post-install bootstrap: make the kit usable on a stock Odoo database."""
import logging

from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)

BRAND_NAMES = ["Main brand", "Second brand", "Third brand"]


def _ensure_analytic(env, outlet):
    """Give every outlet an analytic account so costs and sales can be tagged."""
    if outlet.analytic_account_id:
        return outlet.analytic_account_id
    plan = env["account.analytic.plan"].search([("name", "=", "Restaurant Kit")], limit=1)
    if not plan:
        plan = env["account.analytic.plan"].create({"name": "Restaurant Kit"})
    account = env["account.analytic.account"].create(
        {
            "name": f"{outlet.code} {outlet.name}",
            "code": outlet.code,
            "plan_id": plan.id,
            "company_id": outlet.company_id.id or env.company.id,
        }
    )
    outlet.analytic_account_id = account
    return account


def post_init_hook(env):
    """Create one outlet per existing POS profile, and a central kitchen."""
    env = env(user=SUPERUSER_ID)
    brand = env.ref("rk_restaurant_core.brand_blaze", raise_if_not_found=False)
    if not brand:
        brand = env["rk.brand"].create({"name": "Main brand", "code": "MAIN"})

    channels = env["rk.channel"].search([])
    dayparts = env["rk.daypart"].search([])

    for config in env["pos.config"].search([("rk_outlet_id", "=", False)]):
        outlet = env["rk.outlet"].create(
            {
                "name": config.name,
                "code": (config.name or "OUT")[:8].upper().replace(" ", "-"),
                "brand_id": brand.id,
                "company_id": config.company_id.id,
                "format": "casual",
                "pos_config_id": config.id,
                "channel_ids": [(6, 0, channels.ids)],
                "daypart_ids": [(6, 0, dayparts.ids)],
                "seats": 60,
            }
        )
        _ensure_analytic(env, outlet)
        _logger.info("rk_restaurant_core: outlet %s linked to POS %s", outlet.name, config.name)

    if not env["rk.outlet"].search_count([("format", "=", "central_kitchen")]):
        kitchen = env["rk.outlet"].create(
            {
                "name": "Central Kitchen",
                "code": "CK-01",
                "brand_id": brand.id,
                "company_id": env.company.id,
                "format": "central_kitchen",
                "warehouse_id": env["stock.warehouse"].search(
                    [("company_id", "=", env.company.id)], limit=1
                ).id,
                "daypart_ids": [(6, 0, dayparts.ids)],
            }
        )
        _ensure_analytic(env, kitchen)
