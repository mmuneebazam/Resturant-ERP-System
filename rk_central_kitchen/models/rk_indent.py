# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RkIndent(models.Model):
    """An outlet's request for goods from the central kitchen."""

    _name = "rk.indent"
    _description = "Outlet indent"
    _order = "date_required desc, name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default=lambda self: _("New"), copy=False, readonly=True, index=True)
    outlet_id = fields.Many2one("rk.outlet", string="Requesting outlet", required=True, ondelete="restrict")
    kitchen_id = fields.Many2one(
        "rk.outlet", string="Supplying kitchen", required=True, ondelete="restrict",
        domain=[("format", "=", "central_kitchen")],
    )
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    date_required = fields.Date(required=True, default=fields.Date.context_today)
    requested_by_id = fields.Many2one("res.users", string="Requested by", default=lambda self: self.env.user)
    approved_by_id = fields.Many2one("res.users", string="Approved by", readonly=True, copy=False)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("planned", "In production plan"),
            ("received", "Received"),
            ("cancelled", "Cancelled"),
        ],
        default="draft", required=True, tracking=True, index=True,
    )
    line_ids = fields.One2many("rk.indent.line", "indent_id", string="Lines", copy=True)
    notes = fields.Text()
    line_count = fields.Integer(compute="_compute_totals")
    total_requested = fields.Float(compute="_compute_totals", string="Requested qty")
    total_approved = fields.Float(compute="_compute_totals", string="Approved qty")
    production_plan_id = fields.Many2one("rk.production.plan", string="Production plan", readonly=True, copy=False)
    dispatch_ids = fields.One2many("rk.dispatch", "indent_id", string="Dispatches")

    @api.depends("line_ids.qty_requested", "line_ids.qty_approved")
    def _compute_totals(self):
        for indent in self:
            indent.line_count = len(indent.line_ids)
            indent.total_requested = sum(indent.line_ids.mapped("qty_requested"))
            indent.total_approved = sum(indent.line_ids.mapped("qty_approved"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rk.indent") or _("New")
        return super().create(vals_list)

    # ------------------------------------------------------------------
    def action_fill_from_par(self):
        """Populate the indent with every item below par for this outlet."""
        ParLevel = self.env["rk.par.level"]
        for indent in self:
            indent.line_ids.unlink()
            pars = ParLevel.search([("outlet_id", "=", indent.outlet_id.id)])
            commands = []
            for par in pars.filtered(lambda p: p.suggested_qty > 0):
                commands.append(
                    (0, 0, {
                        "product_id": par.product_id.id,
                        "par_qty": par.par_qty,
                        "qty_on_hand": par.qty_on_hand,
                        "qty_requested": par.suggested_qty,
                    })
                )
            indent.line_ids = commands
            if not commands:
                raise UserError(_("Every item is at or above par for %s.", indent.outlet_id.name))
        return True

    def action_submit(self):
        self.filtered(lambda i: i.state == "draft").write({"state": "submitted"})
        return True

    def action_approve(self):
        for indent in self:
            if indent.state != "submitted":
                raise UserError(_("Only submitted indents can be approved."))
            for line in indent.line_ids:
                if not line.qty_approved:
                    line.qty_approved = line.qty_requested
            indent.write({"state": "approved", "approved_by_id": self.env.user.id})
        return True

    def action_reject(self):
        self.write({"state": "rejected"})
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    def action_open_plan(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "rk.production.plan",
            "res_id": self.production_plan_id.id,
            "view_mode": "form",
        }


class RkIndentLine(models.Model):
    _name = "rk.indent.line"
    _description = "Indent line"
    _order = "indent_id, product_id"

    indent_id = fields.Many2one("rk.indent", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product", required=True, ondelete="restrict")
    uom_id = fields.Many2one(related="product_id.uom_id", string="UoM")
    par_qty = fields.Float(string="Par")
    qty_on_hand = fields.Float(string="On hand")
    qty_requested = fields.Float(required=True, default=0.0)
    qty_approved = fields.Float(default=0.0)
    qty_dispatched = fields.Float(compute="_compute_dispatched", string="Dispatched")
    qty_received = fields.Float(compute="_compute_dispatched", string="Received")
    price_unit = fields.Float(string="Unit cost", compute="_compute_value")
    value = fields.Float(compute="_compute_value", string="Value")
    note = fields.Char()

    @api.depends("indent_id.dispatch_ids.state", "indent_id.dispatch_ids.line_ids.qty_sent",
                 "indent_id.dispatch_ids.line_ids.qty_received")
    def _compute_dispatched(self):
        for line in self:
            dispatches = line.indent_id.dispatch_ids.filtered(lambda d: d.state != "cancelled")
            moves = dispatches.line_ids.filtered(lambda dl: dl.product_id == line.product_id)
            line.qty_dispatched = sum(moves.mapped("qty_sent"))
            line.qty_received = sum(moves.mapped("qty_received"))

    @api.depends("product_id", "qty_approved")
    def _compute_value(self):
        for line in self:
            line.price_unit = line.product_id.standard_price
            line.value = line.price_unit * (line.qty_approved or 0.0)
