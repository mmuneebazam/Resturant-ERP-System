# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosConfig(models.Model):
    """Link the POS profile back to the kit's outlet master."""

    _inherit = "pos.config"

    rk_outlet_id = fields.Many2one("rk.outlet", string="Outlet", ondelete="set null", copy=False, index=True)
    rk_brand_id = fields.Many2one(related="rk_outlet_id.brand_id", store=True, string="Brand")
    rk_format = fields.Selection(related="rk_outlet_id.format", store=True, string="Format")
    rk_manager_id = fields.Many2one(related="rk_outlet_id.manager_id", string="Outlet manager")
    rk_seats = fields.Integer(related="rk_outlet_id.seats", string="Seats")

    @api.model_create_multi
    def create(self, vals_list):
        configs = super().create(vals_list)
        for config in configs:
            if config.rk_outlet_id and not config.rk_outlet_id.pos_config_id:
                config.rk_outlet_id.pos_config_id = config
        return configs
