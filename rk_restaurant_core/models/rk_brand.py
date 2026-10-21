# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkBrand(models.Model):
    """A consumer-facing brand. One brand may run several outlets and formats."""

    _name = "rk.brand"
    _description = "Restaurant Brand"
    _order = "sequence, name"
    _check_company_auto = True

    name = fields.Char(required=True, translate=False)
    code = fields.Char(required=True, help="Short code used in reports and integrations, e.g. BLZ.")
    sequence = fields.Integer(default=10)
    color = fields.Integer(default=0)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    description = fields.Text()
    target_food_cost_pct = fields.Float(string="Target food cost %", default=32.0)
    target_labour_cost_pct = fields.Float(string="Target labour cost %", default=24.0)
    target_prime_cost_pct = fields.Float(string="Target prime cost %", default=58.0)
    outlet_ids = fields.One2many("rk.outlet", "brand_id", string="Outlets")
    outlet_count = fields.Integer(compute="_compute_outlet_count")
    target_food_cost_pct = fields.Float(
        string="Target Food Cost %", default=32.0, help="Menu engineering target used by recipe costing."
    )
    target_labour_cost_pct = fields.Float(string="Target Labour Cost %", default=24.0)
    target_prime_cost_pct = fields.Float(string="Target Prime Cost %", default=58.0)

    _brand_code_uniq = models.Constraint(
        "UNIQUE(code, company_id)", "The brand code must be unique per company."
    )

    @api.depends("outlet_ids")
    def _compute_outlet_count(self):
        data = self.env["rk.outlet"]._read_group(
            [("brand_id", "in", self.ids)], ["brand_id"], ["__count"]
        )
        counts = {brand.id: count for brand, count in data}
        for brand in self:
            brand.outlet_count = counts.get(brand.id, 0)

    @api.depends("name", "code")
    def _compute_display_name(self):
        for brand in self:
            brand.display_name = f"{brand.name} [{brand.code}]" if brand.code else brand.name

    def action_open_outlets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Outlets — %s", self.name),
            "res_model": "rk.outlet",
            "view_mode": "kanban,list,form",
            "domain": [("brand_id", "=", self.id)],
            "context": {"default_brand_id": self.id},
        }
