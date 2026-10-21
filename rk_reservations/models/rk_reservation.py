# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RkReservation(models.Model):
    _name = "rk.reservation"
    _description = "Reservation"
    _order = "start desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default=lambda self: _("New"), readonly=True, copy=False, index=True)
    partner_id = fields.Many2one("res.partner", string="Guest")
    guest_name = fields.Char(compute="_compute_guest_name", store=True, readonly=False)
    phone = fields.Char()
    email = fields.Char()
    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    table_id = fields.Many2one("restaurant.table", string="Table", ondelete="restrict")
    party_size = fields.Integer(required=True, default=2)
    start = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    duration_minutes = fields.Integer(string="Turn time (min)", default=90, required=True)
    end = fields.Datetime(compute="_compute_end", store=True)
    channel = fields.Selection(
        [("phone", "Phone"), ("web", "Web"), ("walkin", "Walk-in"), ("platform", "Platform"), ("vip", "VIP")],
        default="phone", required=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("seated", "Seated"), ("completed", "Completed"),
         ("no_show", "No-show"), ("cancelled", "Cancelled")],
        default="draft", required=True, tracking=True, index=True,
    )
    deposit_required = fields.Boolean()
    deposit_amount = fields.Monetary(currency_field="currency_id")
    deposit_paid = fields.Boolean()
    currency_id = fields.Many2one(related="company_id.currency_id")
    pos_order_id = fields.Many2one("pos.order", string="POS order", readonly=True, copy=False)
    seated_at = fields.Datetime(readonly=True, copy=False)
    table_seats = fields.Integer(related="table_id.seats", string="Table seats")
    note = fields.Text()
    special_requests = fields.Char()

    _reservation_name_uniq = models.Constraint("UNIQUE(name)", "The reservation reference must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rk.reservation") or _("New")
        return super().create(vals_list)

    @api.depends("partner_id", "guest_name")
    def _compute_guest_name(self):
        for reservation in self:
            reservation.guest_name = reservation.guest_name or reservation.partner_id.name

    @api.depends("start", "duration_minutes")
    def _compute_end(self):
        for reservation in self:
            reservation.end = fields.Datetime.add(
                reservation.start, minutes=reservation.duration_minutes or 90
            )

    @api.constrains("table_id", "start", "duration_minutes", "state")
    def _check_table_availability(self):
        for reservation in self:
            if not reservation.table_id or reservation.state in ("cancelled", "no_show", "completed"):
                continue
            clash = self.search(
                [
                    ("id", "!=", reservation.id),
                    ("table_id", "=", reservation.table_id.id),
                    ("state", "in", ("draft", "confirmed", "seated")),
                    ("start", "<", reservation.end),
                    ("end", ">", reservation.start),
                ],
                limit=1,
            )
            if clash:
                raise ValidationError(
                    _("Table %(table)s is already booked for %(guest)s from %(start)s to %(end)s.",
                      table=reservation.table_id.display_name,
                      guest=clash.guest_name,
                      start=clash.start,
                      end=clash.end)
                )

    @api.constrains("party_size", "table_id")
    def _check_seats(self):
        for reservation in self:
            if reservation.table_id and reservation.party_size > reservation.table_id.seats:
                raise ValidationError(
                    _("Party of %(party)s does not fit table %(table)s (%(seats)s seats).",
                      party=reservation.party_size,
                      table=reservation.table_id.display_name,
                      seats=reservation.table_id.seats)
                )

    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_seat(self):
        """Seat the guests and open the POS order on that table when possible."""
        for reservation in self:
            if reservation.table_id and reservation.outlet_id.pos_config_id:
                session = reservation.outlet_id._rk_open_session()
                if session:
                    order = self.env["pos.order"].create(
                        {
                            "session_id": session.id,
                            "table_id": reservation.table_id.id,
                            "partner_id": reservation.partner_id.id or False,
                            "amount_tax": 0.0,
                            "amount_total": 0.0,
                            "amount_paid": 0.0,
                            "amount_return": 0.0,
                            "state": "draft",
                        }
                    )
                    self.pos_order_id = order.id
            self.write({"state": "seated", "seated_at": fields.Datetime.now()})
        return True

    def action_complete(self):
        self.write({"state": "completed"})
        return True

    def action_no_show(self):
        self.write({"state": "no_show"})
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.model
    def _cron_flag_no_shows(self):
        """Anything still confirmed 30 minutes after its start time is a no-show."""
        limit = fields.Datetime.subtract(fields.Datetime.now(), minutes=30)
        stale = self.search([("state", "=", "confirmed"), ("start", "<", limit)])
        stale.action_no_show()
        return len(stale)
