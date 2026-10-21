# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkAggregatorSettlement(models.Model):
    """What the platform says it owes vs what our imported orders say."""

    _name = "rk.aggregator.settlement"
    _description = "Aggregator settlement"
    _order = "period_end desc, id desc"

    name = fields.Char(default=lambda self: _("New"), readonly=True, copy=False)
    platform_id = fields.Many2one("rk.aggregator.platform", required=True, ondelete="restrict")
    company_id = fields.Many2one(related="platform_id.channel_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    period_start = fields.Date(required=True)
    period_end = fields.Date(required=True)
    outlet_ids = fields.Many2many("rk.outlet", string="Outlets")
    order_ids = fields.One2many("rk.aggregator.order", "settlement_id", string="Orders")
    reported_gross = fields.Monetary(currency_field="currency_id")
    reported_commission = fields.Monetary(currency_field="currency_id")
    reported_net = fields.Monetary(currency_field="currency_id")
    computed_gross = fields.Monetary(compute="_compute_computed", store=True, currency_field="currency_id")
    computed_commission = fields.Monetary(compute="_compute_computed", store=True, currency_field="currency_id")
    gross_difference = fields.Monetary(compute="_compute_computed", store=True, currency_field="currency_id")
    order_count = fields.Integer(compute="_compute_computed", store=True)
    state = fields.Selection(
        [("draft", "Draft"), ("matched", "Matched"), ("disputed", "Disputed"), ("closed", "Closed")],
        default="draft", required=True,
    )
    note = fields.Text()

    @api.depends("order_ids.amount_total", "order_ids.commission_amount")
    def _compute_computed(self):
        for settlement in self:
            imported = settlement.order_ids.filtered(lambda o: o.state == "imported")
            settlement.computed_gross = sum(imported.mapped("amount_total"))
            settlement.computed_commission = sum(imported.mapped("commission_amount"))
            settlement.gross_difference = settlement.computed_gross - (settlement.reported_gross or 0.0)
            settlement.order_count = len(imported)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rk.aggregator.settlement") or _("New")
        return super().create(vals_list)

    def action_collect_orders(self):
        domain = [
            ("platform_id", "=", self.platform_id.id),
            ("received_at", ">=", fields.Datetime.to_datetime(self.period_start)),
            ("received_at", "<=", fields.Datetime.to_datetime(self.period_end).replace(hour=23, minute=59)),
            ("settlement_id", "=", False),
        ]
        if self.outlet_ids:
            domain.append(("outlet_id", "in", self.outlet_ids.ids))
        orders = self.env["rk.aggregator.order"].search(domain)
        orders.write({"settlement_id": self.id})
        self._compute_computed()
        self.state = "matched" if abs(self.gross_difference) < 0.05 else "disputed"
        return True

    def action_close(self):
        self.write({"state": "closed"})
        return True
