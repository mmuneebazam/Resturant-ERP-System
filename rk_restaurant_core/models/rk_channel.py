# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkChannel(models.Model):
    """A sales channel. Dine-in and Talabat cost very different amounts to serve."""

    _name = "rk.channel"
    _description = "Sales Channel"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(default=0)
    channel_type = fields.Selection(
        [
            ("dine_in", "Dine-in"),
            ("takeaway", "Takeaway"),
            ("delivery", "Own delivery"),
            ("aggregator", "Aggregator"),
            ("catering", "Catering / events"),
            ("franchise", "Franchise"),
        ],
        required=True,
        default="dine_in",
    )
    commission_pct = fields.Float(
        string="Platform Commission %",
        help="Commission charged by the channel on net sales. Used by the aggregator "
        "settlement and by contribution-margin reporting.",
    )
    requires_settlement = fields.Boolean(
        compute="_compute_requires_settlement", store=True, readonly=False
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    note = fields.Text()

    _channel_code_uniq = models.Constraint(
        "UNIQUE(code, company_id)", "The channel code must be unique per company."
    )

    @api.depends("channel_type")
    def _compute_requires_settlement(self):
        for channel in self:
            channel.requires_settlement = channel.channel_type in ("aggregator", "delivery", "franchise")

    @api.depends("name", "code")
    def _compute_display_name(self):
        for channel in self:
            channel.display_name = f"{channel.name} [{channel.code}]" if channel.code else channel.name
