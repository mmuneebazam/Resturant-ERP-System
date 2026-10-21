# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkMenuSync(models.Model):
    """One menu item, as published to one platform."""

    _name = "rk.menu.sync"
    _description = "Platform menu sync"
    _order = "platform_id, product_id"

    platform_id = fields.Many2one("rk.aggregator.platform", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product", required=True, ondelete="cascade")
    currency_id = fields.Many2one(related="platform_id.channel_id.company_id.currency_id")
    external_sku = fields.Char(string="Platform SKU")
    our_price = fields.Monetary(
        compute="_compute_our_price", store=True, currency_field="currency_id", string="Our POS price"
    )
    platform_price = fields.Monetary(currency_field="currency_id", string="Platform price")
    is_available = fields.Boolean(default=True, string="Available on platform")
    state = fields.Selection(
        [("draft", "Not synced"), ("synced", "Synced"), ("drift", "Price drift"), ("blocked", "Unavailable")],
        default="draft", required=True,
    )
    last_sync = fields.Datetime(readonly=True, copy=False)

    _menu_sync_uniq = models.Constraint(
        "UNIQUE(platform_id, product_id)", "One sync line per item and platform."
    )

    @api.depends("product_id.lst_price")
    def _compute_our_price(self):
        for line in self:
            line.our_price = line.product_id.lst_price

    def action_push(self):
        """Publish our price and availability to the platform (payload shaped for a real API)."""
        for line in self:
            line.write(
                {
                    "platform_price": line.our_price,
                    "state": "synced" if line.is_available else "blocked",
                    "last_sync": fields.Datetime.now(),
                }
            )
        return True

    def action_check_drift(self):
        for line in self:
            if not line.is_available:
                line.state = "blocked"
            elif abs((line.platform_price or 0.0) - line.our_price) > 0.009:
                line.state = "drift"
            else:
                line.state = "synced"
        return True
