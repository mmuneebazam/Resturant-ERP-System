# -*- coding: utf-8 -*-
from odoo import _, fields, models


class RkForecastGenerate(models.TransientModel):
    _name = "rk.forecast.generate"
    _description = "Generate forecasts"

    date_from = fields.Date(required=True, default=lambda self: fields.Date.add(fields.Date.context_today(self), days=1))
    date_to = fields.Date(required=True, default=lambda self: fields.Date.add(fields.Date.context_today(self), days=1))
    outlet_ids = fields.Many2many("rk.outlet", string="Outlets")
    daypart_ids = fields.Many2many("rk.daypart", string="Day-parts")
    weeks = fields.Integer(string="Weeks of history", default=4)
    result = fields.Char(readonly=True)

    def action_generate(self):
        self.ensure_one()
        outlets = self.outlet_ids or self.env["rk.outlet"].search([("pos_config_id", "!=", False)])
        created = self.env["rk.forecast"]._generate_for(
            outlets, self.date_from, self.date_to, self.daypart_ids or None, self.weeks or 4
        )
        self.result = _("%(count)s forecast line(s) created.", count=created)
        return {
            "type": "ir.actions.act_window",
            "res_model": "rk.forecast",
            "view_mode": "list,pivot,form",
            "domain": [("date", ">=", self.date_from), ("date", "<=", self.date_to)],
            "name": _("Forecasts"),
        }
