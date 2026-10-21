# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    rk_hourly_rate = fields.Monetary(
        string="Cost rate / hour", currency_field="rk_currency_id",
        help="Fully loaded hourly cost used by outlet labour reporting.",
    )
    rk_currency_id = fields.Many2one(related="company_id.currency_id", string="Currency")
    rk_home_outlet_id = fields.Many2one("rk.outlet", string="Home outlet")
