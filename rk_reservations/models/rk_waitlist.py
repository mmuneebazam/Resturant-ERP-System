# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkWaitlist(models.Model):
    _name = "rk.waitlist"
    _description = "Walk-in waitlist"
    _order = "arrived_at"

    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="cascade", index=True)
    guest_name = fields.Char(required=True)
    phone = fields.Char()
    party_size = fields.Integer(required=True, default=2)
    quoted_minutes = fields.Integer(string="Quoted wait (min)", default=15)
    arrived_at = fields.Datetime(default=fields.Datetime.now, required=True)
    seated_at = fields.Datetime(readonly=True)
    actual_minutes = fields.Float(compute="_compute_actual", string="Actual wait (min)")
    state = fields.Selection(
        [("waiting", "Waiting"), ("seated", "Seated"), ("left", "Left")], default="waiting", required=True
    )
    reservation_id = fields.Many2one("rk.reservation", readonly=True, copy=False)

    def _compute_actual(self):
        now = fields.Datetime.now()
        for entry in self:
            end = entry.seated_at or now
            entry.actual_minutes = (end - entry.arrived_at).total_seconds() / 60.0

    def action_seat(self):
        """Convert the walk-in into a reservation and mark both as seated."""
        for entry in self:
            reservation = self.env["rk.reservation"].create(
                {
                    "guest_name": entry.guest_name,
                    "phone": entry.phone,
                    "party_size": entry.party_size,
                    "outlet_id": entry.outlet_id.id,
                    "channel": "walkin",
                    "state": "seated",
                    "seated_at": fields.Datetime.now(),
                }
            )
            entry.write({"state": "seated", "seated_at": fields.Datetime.now(), "reservation_id": reservation.id})
        return True

    def action_left(self):
        self.write({"state": "left"})
        return True
