# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RkDispatch(models.Model):
    """A shipment from the central kitchen to an outlet, with receipt variance."""

    _name = "rk.dispatch"
    _description = "Kitchen dispatch"
    _order = "date desc, name desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default=lambda self: _("New"), readonly=True, copy=False, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    kitchen_id = fields.Many2one("rk.outlet", required=True, ondelete="restrict", domain=[("format", "=", "central_kitchen")])
    outlet_id = fields.Many2one("rk.outlet", string="Destination outlet", required=True, ondelete="restrict")
    indent_id = fields.Many2one("rk.indent", string="Indent", ondelete="set null")
    company_id = fields.Many2one(related="kitchen_id.company_id", store=True)
    transport_reference = fields.Char(string="Vehicle / route")
    temperature_c = fields.Float(string="Load temperature (°C)")
    temperature_ok = fields.Boolean(compute="_compute_temperature_ok", store=True, string="Cold chain OK")
    state = fields.Selection(
        [("draft", "Draft"), ("in_transit", "In transit"), ("delivered", "Delivered"), ("cancelled", "Cancelled")],
        default="draft", required=True, tracking=True, index=True,
    )
    line_ids = fields.One2many("rk.dispatch.line", "dispatch_id", string="Lines", copy=True)
    total_qty = fields.Float(compute="_compute_total", string="Dispatched qty")
    variance_qty = fields.Float(compute="_compute_total", string="Variance")
    notes = fields.Text()

    @api.depends("line_ids.qty_sent", "line_ids.qty_received")
    def _compute_total(self):
        for dispatch in self:
            dispatch.total_qty = sum(dispatch.line_ids.mapped("qty_sent"))
            dispatch.variance_qty = sum(dispatch.line_ids.mapped("variance_qty"))

    @api.depends("temperature_c")
    def _compute_temperature_ok(self):
        for dispatch in self:
            dispatch.temperature_ok = not dispatch.temperature_c or 0 <= dispatch.temperature_c <= 4

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rk.dispatch") or _("New")
        return super().create(vals_list)

    def action_fill_from_indent(self):
        self.ensure_one()
        if not self.indent_id:
            raise UserError(_("Select an indent first."))
        commands = [
            (0, 0, {"product_id": line.product_id.id, "qty_sent": line.qty_approved or line.qty_requested})
            for line in self.indent_id.line_ids
        ]
        self.line_ids.unlink()
        self.line_ids = commands
        return True

    def action_dispatch(self):
        self.write({"state": "in_transit"})
        self.indent_id.message_post(body=_("Dispatched on %s by %s.", self.name, self.kitchen_id.name))
        return True

    def action_confirm_receipt(self):
        for dispatch in self:
            if dispatch.state != "in_transit":
                raise UserError(_("Only in-transit dispatches can be received."))
            for line in dispatch.line_ids:
                if not line.qty_received:
                    line.qty_received = line.qty_sent
            dispatch.write({"state": "delivered"})
            if dispatch.indent_id:
                dispatch.indent_id.write({"state": "received"})
            if any(line.variance_qty for line in dispatch.line_ids):
                dispatch._log_variances()
        return True

    def _log_variances(self):
        self.ensure_one()
        body = "<ul>"
        for line in self.line_ids.filtered("variance_qty"):
            body += f"<li>{line.product_id.display_name}: sent {line.qty_sent}, received {line.qty_received}</li>"
        body += "</ul>"
        self.message_post(
            body=_("Receipt variance recorded for %s:", self.name) + body,
            subtype_xmlid="mail.mt_comment",
        )

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class RkDispatchLine(models.Model):
    _name = "rk.dispatch.line"
    _description = "Dispatch line"

    dispatch_id = fields.Many2one("rk.dispatch", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product", required=True, ondelete="restrict")
    uom_id = fields.Many2one(related="product_id.uom_id", string="UoM")
    qty_sent = fields.Float(default=0.0)
    qty_received = fields.Float(default=0.0)
    variance_qty = fields.Float(compute="_compute_variance", string="Variance")
    reason = fields.Selection(
        [("short", "Short delivered"), ("damaged", "Damaged in transit"),
         ("quality", "Rejected by outlet"), ("over", "Over delivered")],
        string="Variance reason",
    )

    @api.depends("qty_sent", "qty_received")
    def _compute_variance(self):
        for line in self:
            line.variance_qty = (line.qty_received or 0.0) - (line.qty_sent or 0.0)
