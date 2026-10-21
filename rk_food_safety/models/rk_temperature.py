# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkTemperatureLog(models.Model):
    """A single reading, manual or pushed by a sensor gateway."""

    _name = "rk.temperature.log"
    _description = "Temperature log"
    _order = "date desc, id desc"

    date = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    equipment = fields.Selection(
        [("chiller", "Chiller"), ("freezer", "Freezer"), ("hot_hold", "Hot hold"),
         ("receiving", "Goods receiving"), ("blast", "Blast chiller"), ("other", "Other")],
        required=True, default="chiller",
    )
    equipment_name = fields.Char(string="Unit / area")
    value = fields.Float(string="Reading °C", required=True)
    temp_min = fields.Float(string="Min °C", default=0.0)
    temp_max = fields.Float(string="Max °C", default=5.0)
    is_ok = fields.Boolean(compute="_compute_is_ok", store=True, string="In range")
    source = fields.Selection(
        [("manual", "Manual entry"), ("sensor", "Sensor / IoT"), ("api", "Imported")],
        default="manual", required=True,
    )
    recorded_by_id = fields.Many2one("res.users", string="Recorded by", default=lambda self: self.env.user)
    corrective_action = fields.Text()
    note = fields.Char()

    @api.depends("value", "temp_min", "temp_max")
    def _compute_is_ok(self):
        for log in self:
            log.is_ok = log.temp_min <= log.value <= log.temp_max

    @api.model_create_multi
    def create(self, vals_list):
        logs = super().create(vals_list)
        logs.filtered(lambda l: not l.is_ok)._notify_breach()
        return logs

    def _notify_breach(self):
        for log in self:
            self.env["bus.bus"]._sendone(
                "rk_food_safety",
                "temperature_breach",
                {
                    "outlet": log.outlet_id.display_name,
                    "equipment": dict(self._fields["equipment"].selection).get(log.equipment),
                    "value": log.value,
                    "range": f"{log.temp_min}–{log.temp_max} °C",
                },
            )
        return True
