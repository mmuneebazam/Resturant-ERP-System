# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkCashVariance(models.Model):
    """Expected cash from the POS session vs what was counted in the drawer."""

    _name = "rk.cash.variance"
    _description = "Cash variance"
    _order = "date desc, id desc"
    _inherit = ["mail.thread"]

    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="restrict")
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    session_id = fields.Many2one("pos.session", string="POS session", ondelete="set null")
    expected_cash = fields.Monetary(currency_field="currency_id")
    counted_cash = fields.Monetary(currency_field="currency_id")
    variance = fields.Monetary(compute="_compute_variance", store=True, currency_field="currency_id")
    variance_pct = fields.Float(compute="_compute_variance", store=True, string="Variance %", digits=(6, 2))
    tolerance = fields.Monetary(currency_field="currency_id", default=10.0, string="Tolerance")
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("explained", "Explained"), ("approved", "Approved")],
        default="draft", required=True, tracking=True,
    )
    explanation = fields.Text()
    approved_by_id = fields.Many2one("res.users", string="Approved by", readonly=True, copy=False)

    @api.depends("expected_cash", "counted_cash")
    def _compute_variance(self):
        for record in self:
            record.variance = (record.counted_cash or 0.0) - (record.expected_cash or 0.0)
            record.variance_pct = (
                record.variance / record.expected_cash * 100.0 if record.expected_cash else 0.0
            )

    @api.onchange("session_id")
    def _onchange_session(self):
        if self.session_id:
            self.outlet_id = self.session_id.config_id.rk_outlet_id
            self.expected_cash = self.session_id.cash_register_balance_end_real

    def action_submit(self):
        self.write({"state": "open"})
        return True

    def action_explain(self):
        for record in self:
            if not record.explanation:
                record.explanation = _("Difference within tolerance.")
            record.write({"state": "explained"})
        return True

    def action_approve(self):
        self.write({"state": "approved", "approved_by_id": self.env.user.id})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft", "approved_by_id": False})
        return True
